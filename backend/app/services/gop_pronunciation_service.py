"""Wav2Vec2 CTC forced alignment + GOP (Goodness of Pronunciation) scoring."""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

_WAV2VEC2_MODEL = os.getenv("GOP_WAV2VEC2_MODEL", "facebook/wav2vec2-base-960h")
_MODEL_ROOT = Path(__file__).resolve().parents[2] / "pretrained_models" / "wav2vec2-gop"

_PROCESSOR = None
_MODEL = None
_BLANK_ID: int | None = None

_TOKEN_SEP = "|"
_UNK_ID = 3


@dataclass
class _CharGop:
    index: int
    char: str
    gop: float
    confidence: float
    frame_count: int = 1


@dataclass
class _AlignmentResult:
    char_gops: list[_CharGop]
    path: list[int]
    blank_id: int


def _get_wav2vec2():
    global _PROCESSOR, _MODEL, _BLANK_ID
    if _MODEL is not None:
        return _PROCESSOR, _MODEL, _BLANK_ID

    from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor

    _MODEL_ROOT.mkdir(parents=True, exist_ok=True)
    logger.info("Loading Wav2Vec2 GOP model (%s) …", _WAV2VEC2_MODEL)
    _PROCESSOR = Wav2Vec2Processor.from_pretrained(_WAV2VEC2_MODEL, cache_dir=str(_MODEL_ROOT))
    _MODEL = Wav2Vec2ForCTC.from_pretrained(_WAV2VEC2_MODEL, cache_dir=str(_MODEL_ROOT))
    _MODEL.eval()
    _BLANK_ID = int(_PROCESSOR.tokenizer.pad_token_id)
    logger.info("Wav2Vec2 GOP model ready.")
    return _PROCESSOR, _MODEL, _BLANK_ID


def normalize_target_text(text: str) -> str:
    """Uppercase ASCII sentence for wav2vec2-base-960h (lowercase maps to <unk>)."""
    cleaned = re.sub(r"[^a-zA-Z\s']", " ", text or "")
    return " ".join(cleaned.upper().split())


def load_audio_16k(path: str) -> np.ndarray:
    """Load audio file as 16 kHz mono float32 without librosa."""
    from pydub import AudioSegment

    seg = AudioSegment.from_file(path)
    if seg.channels > 1:
        seg = seg.set_channels(1)
    if seg.frame_rate != 16_000:
        seg = seg.set_frame_rate(16_000)
    samples = np.array(seg.get_array_of_samples(), dtype=np.float32)
    max_val = float(2 ** (8 * seg.sample_width - 1))
    if max_val > 0:
        samples /= max_val
    return samples.astype(np.float32)


def _gop_unit(gop: float) -> float:
    return float(1.0 / (1.0 + np.exp(-(gop * 2.0 + 1.0))))


def _frame_gop(log_probs, frame_idx: int, token_id: int) -> float:
    import torch

    lp = log_probs[frame_idx]
    other = torch.cat([lp[:token_id], lp[token_id + 1 :]], dim=0)
    if other.numel() == 0:
        return float(lp[token_id].item())
    return float(lp[token_id].item() - other.max().item())


def _encode_log_probs(audio_16k: np.ndarray):
    import torch
    import torch.nn.functional as F

    processor, model, blank_id = _get_wav2vec2()
    inputs = processor(audio_16k, sampling_rate=16_000, return_tensors="pt", padding=True)
    with torch.no_grad():
        logits = model(inputs.input_values).logits
    log_probs = F.log_softmax(logits, dim=-1)[0].cpu()
    return log_probs, blank_id


def _bucket_frames_by_token(path: list[int], token_ids: list[int], blank_id: int) -> list[list[int]]:
    """Group all CTC frames per target token index (handles repeated frames per char)."""
    buckets: list[list[int]] = [[] for _ in token_ids]
    target_idx = 0
    frame = 0
    total = len(path)

    while frame < total and target_idx < len(token_ids):
        tok = path[frame]
        if tok == blank_id:
            frame += 1
            continue

        expected = token_ids[target_idx]
        if tok != expected:
            # Skip stray frames; forced path should recover on next match.
            frame += 1
            continue

        while frame < total and path[frame] == expected:
            buckets[target_idx].append(frame)
            frame += 1
        target_idx += 1

    return buckets


def _align_chars(log_probs, token_ids: list[int], blank_id: int) -> _AlignmentResult:
    import torch
    from torchaudio.functional import forced_align

    if not token_ids:
        return _AlignmentResult(char_gops=[], path=[], blank_id=blank_id)

    targets = torch.tensor(token_ids, dtype=torch.int32)
    time_steps = int(log_probs.shape[0])
    paths, _scores = forced_align(
        log_probs.unsqueeze(0),
        targets.unsqueeze(0),
        torch.tensor([time_steps], dtype=torch.int32),
        torch.tensor([len(token_ids)], dtype=torch.int32),
        blank=blank_id,
    )
    path = paths[0].tolist()
    buckets = _bucket_frames_by_token(path, token_ids, blank_id)

    chars: list[_CharGop] = []
    for idx, frames in enumerate(buckets):
        if frames:
            frame_gops = [_frame_gop(log_probs, f, token_ids[idx]) for f in frames]
            mean_gop = float(np.mean(frame_gops))
        else:
            mean_gop = -3.0

        chars.append(
            _CharGop(
                index=idx,
                char="",
                gop=mean_gop,
                confidence=_gop_unit(mean_gop),
                frame_count=max(len(frames), 0),
            )
        )

    return _AlignmentResult(char_gops=chars, path=path, blank_id=blank_id)


def _word_token_groups(tokens: list[str]) -> list[list[int]]:
    """Split token indices by '|' separator — apostrophes stay inside the word group."""
    groups: list[list[int]] = [[]]
    for ti, tok in enumerate(tokens):
        if tok == _TOKEN_SEP:
            if groups[-1]:
                groups.append([])
            continue
        groups[-1].append(ti)
    if groups and not groups[-1]:
        groups.pop()
    return groups


def _compute_fluency(
    path: list[int],
    blank_id: int,
    token_ids: list[int],
    tokens: list[str],
    audio_16k: np.ndarray,
) -> float:
    """
    Fluency 0–1 from:
    - speech frame ratio (non-blank CTC frames / total frames)
    - speaking pace (letters per second vs natural read-aloud range)
    - pause penalty (long blank runs relative to speech)
    """
    if not path:
        return 0.0

    total_frames = len(path)
    blank_mask = [p == blank_id for p in path]
    blank_frames = sum(blank_mask)
    speech_frames = total_frames - blank_frames
    speech_ratio = speech_frames / total_frames

    # Longest consecutive blank run → excessive pauses lower fluency.
    longest_pause = 0
    current_pause = 0
    for is_blank in blank_mask:
        if is_blank:
            current_pause += 1
            longest_pause = max(longest_pause, current_pause)
        else:
            current_pause = 0
    pause_ratio = longest_pause / total_frames
    pause_score = float(np.clip(1.0 - pause_ratio * 2.5, 0.0, 1.0))

    letter_count = sum(
        1 for tid, tok in zip(token_ids, tokens, strict=False)
        if tok not in {_TOKEN_SEP, "<unk>"}
    )
    duration_s = max(len(audio_16k) / 16_000, 0.1)
    chars_per_sec = letter_count / duration_s
    # Read-aloud shadowing: ~8–18 letters/s is natural; <4 too slow, >22 rushed.
    pace_score = float(np.clip((chars_per_sec - 4.0) / (16.0 - 4.0), 0.0, 1.0))

    fluency = 0.45 * speech_ratio + 0.30 * pace_score + 0.25 * pause_score
    return float(np.clip(fluency, 0.0, 1.0))


def transcribe_audio_16k(audio_16k: np.ndarray) -> str:
    """Greedy CTC transcription reusing the already-loaded GOP wav2vec2 model.

    No extra RAM — model is a shared singleton loaded for shadowing GOP scoring.
    Replaces the 1.3 GB SpeechBrain ASR (wav2vec2-large) for single-word ASR.
    """
    import torch

    processor, model, _ = _get_wav2vec2()
    inputs = processor(audio_16k, sampling_rate=16_000, return_tensors="pt", padding=True)
    with torch.no_grad():
        logits = model(inputs.input_values).logits
    pred_ids = torch.argmax(logits, dim=-1)
    text = processor.batch_decode(pred_ids)[0]
    return text.strip().lower()


def score_gop(audio_16k: np.ndarray, target_text: str) -> dict[str, Any]:
    """
    Score pronunciation with wav2vec2 CTC forced alignment + GOP.

    Returns score 0–100, per-word results, and 0–10 sub-scores for the UI.
    """
    normalized = normalize_target_text(target_text)
    if not normalized:
        raise ValueError("Câu mục tiêu rỗng hoặc không hợp lệ.")

    if audio_16k.size == 0:
        raise ValueError("Audio rỗng hoặc không hợp lệ.")

    processor, _model, blank_id = _get_wav2vec2()
    token_ids = processor.tokenizer(normalized, add_special_tokens=False).input_ids
    if not token_ids or all(tid == _UNK_ID for tid in token_ids):
        raise ValueError("Không mã hóa được câu mục tiêu cho wav2vec2.")

    log_probs, blank_id = _encode_log_probs(audio_16k)
    alignment = _align_chars(log_probs, token_ids, blank_id)
    char_gops = alignment.char_gops

    tokens = processor.tokenizer.convert_ids_to_tokens(token_ids)
    for ch, tok in zip(char_gops, tokens, strict=False):
        ch.char = tok

    words = normalized.split()
    token_groups = _word_token_groups(tokens)

    if len(token_groups) != len(words):
        logger.warning(
            "Token/word count mismatch: %d words vs %d token groups for %r",
            len(words),
            len(token_groups),
            normalized,
        )

    word_results: list[dict[str, Any]] = []
    wrong_words: list[str] = []

    for wi, word in enumerate(words):
        indices = token_groups[wi] if wi < len(token_groups) else []
        word_chars = [char_gops[i] for i in indices if i < len(char_gops)]

        if word_chars:
            conf = float(np.mean([c.confidence for c in word_chars]))
            word_gop = float(np.mean([c.gop for c in word_chars]))
            frames = sum(c.frame_count for c in word_chars)
        else:
            conf = 0.0
            word_gop = -3.0
            frames = 0

        ok = conf >= 0.58 and frames > 0
        if not ok:
            wrong_words.append(word)
        word_results.append({
            "word": word,
            "ok": ok,
            "spoken": None,
            "gop": round(word_gop, 3),
            "confidence": round(conf, 3),
            "frame_count": frames,
        })

    scored_chars = [c for c in char_gops if c.frame_count > 0]
    if scored_chars:
        gop_mean = float(np.mean([c.confidence for c in scored_chars]))
        raw_gop = float(np.mean([c.gop for c in scored_chars]))
    else:
        gop_mean = 0.0
        raw_gop = -3.0

    fluency_ratio = _compute_fluency(
        alignment.path, alignment.blank_id, token_ids, tokens, audio_16k
    )
    score_100 = round(gop_mean * 100)
    total_10 = round(gop_mean * 10, 1)

    logger.info(
        "GOP target=%r score=%d gop_mean=%.3f fluency=%.3f words=%d wrong=%d",
        normalized,
        score_100,
        gop_mean,
        fluency_ratio,
        len(word_results),
        len(wrong_words),
    )

    return {
        "score": score_100,
        "target_text": target_text.strip(),
        "normalized_text": normalized,
        "transcript": normalized,
        "word_results": word_results,
        "wrong_words": wrong_words,
        "correct_count": sum(1 for w in word_results if w["ok"]),
        "total_words": len(word_results),
        "pronunciation": {
            "gop_mean": round(gop_mean, 3),
            "gop_raw": round(raw_gop, 3),
            "accuracy": total_10,
            "fluency": round(fluency_ratio * 10, 1),
            "prosodic": round(gop_mean * 10, 1),
            "total": round(gop_mean * 0.7 * 10 + fluency_ratio * 0.3 * 10, 1),
        },
    }
