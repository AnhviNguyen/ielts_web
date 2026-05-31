"""Acoustic phoneme recognition — Allosaurus (IPA) + Whisper word check."""

from __future__ import annotations

import logging
import re
import tempfile
from difflib import SequenceMatcher
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

_ALLOSUARUS = None


def _normalize_ipa(symbol: str) -> str:
    s = symbol.strip().lower()
    aliases = {
        "g": "ɡ",
        "ɾ": "r",
        "ʔ": "",
        "ɝ": "ɜːr",
        "ɚ": "ɜːr",
        "ɜ": "ɜːr",
        "ɜː": "ɜːr",
        "u": "uː",  # allosaurus often short; CMU uses uː for UW
        "i": "iː",
        "o": "oʊ",
        "e": "eɪ",
        "a": "ɑ",
        "ə": "ʌ",   # schwa ↔ AH in many American words
    }
    return aliases.get(s, s)


def waveform_to_wav_path(waveform_16k: np.ndarray) -> str:
    from pydub import AudioSegment

    samples = (np.clip(waveform_16k, -1.0, 1.0) * 32_767).astype(np.int16)
    seg = AudioSegment(
        samples.tobytes(),
        frame_rate=16_000,
        sample_width=2,
        channels=1,
    )
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    tmp_path = tmp.name
    tmp.close()
    seg.export(tmp_path, format="wav")
    return tmp_path


def safe_unlink(path: str) -> None:
    try:
        Path(path).unlink(missing_ok=True)
    except OSError:
        pass


def _get_allosaurus():
    global _ALLOSUARUS
    if _ALLOSUARUS is None:
        from allosaurus.app import read_recognizer

        logger.info("Loading Allosaurus phoneme recognizer …")
        _ALLOSUARUS = read_recognizer()
        logger.info("Allosaurus ready.")
    return _ALLOSUARUS


def recognize_ipa_phonemes(wav_path: str) -> list[str]:
    """Extract IPA phoneme sequence from audio (Allosaurus — ELSA-style acoustic check)."""
    try:
        model = _get_allosaurus()
        raw = model.recognize(wav_path, lang_id="eng", timestamp=False) or ""
        tokens = [_normalize_ipa(t) for t in raw.split() if t.strip()]
        tokens = [t for t in tokens if t]
        logger.info("Allosaurus IPA: %s", tokens)
        return tokens
    except Exception as exc:
        logger.warning("Allosaurus phoneme recognition failed: %s", exc)
        return []


def _best_word_from_transcript(full_text: str, expected_clean: str) -> tuple[str, float]:
    """Pick the token from Whisper output closest to the expected word."""
    if not expected_clean:
        return "", 0.0

    full_clean = re.sub(r"[^a-z]", "", full_text.lower())
    if full_clean == expected_clean:
        return expected_clean, 1.0
    if expected_clean in full_clean:
        return expected_clean, 0.98

    candidates = re.findall(r"[a-z]+", full_text.lower())
    best_tok = full_clean
    best_ratio = SequenceMatcher(None, expected_clean, full_clean).ratio() if full_clean else 0.0

    for tok in candidates:
        ratio = SequenceMatcher(None, expected_clean, tok).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_tok = tok

    return best_tok, best_ratio


def transcribe_single_word(wav_path: str, expected_word: str) -> tuple[str, float]:
    """Whisper single-word transcription; returns best-matching token + confidence 0-1."""
    from ml.model_registry import get_whisper_model

    expected_clean = re.sub(r"[^a-z]", "", expected_word.lower())

    try:
        model = get_whisper_model()
        result = model.transcribe(
            wav_path,
            language="en",
            word_timestamps=True,
            verbose=False,
            condition_on_previous_text=False,
            fp16=False,
            temperature=0,
            no_speech_threshold=0.45,
            logprob_threshold=-1.0,
            compression_ratio_threshold=2.8,
        )

        full_text = (result.get("text") or "").strip()
        best_tok, match_ratio = _best_word_from_transcript(full_text, expected_clean)

        # Word-level probability from timestamps (if available)
        ts_conf = 0.0
        for seg in result.get("segments") or []:
            for w in seg.get("words") or []:
                w_clean = re.sub(r"[^a-z]", "", (w.get("word") or "").lower())
                if not w_clean:
                    continue
                prob = float(w.get("probability") or 0.0)
                r = SequenceMatcher(None, expected_clean, w_clean).ratio()
                if r >= match_ratio - 0.05:
                    ts_conf = max(ts_conf, min(prob, 1.0))

        confidence = max(match_ratio, ts_conf)
        if match_ratio >= 0.92:
            confidence = max(confidence, 0.9)
        elif match_ratio >= 0.78:
            confidence = max(confidence, match_ratio * 0.88)

        logger.info(
            "Whisper raw=%r best=%r match=%.2f conf=%.2f",
            full_text,
            best_tok,
            match_ratio,
            confidence,
        )
        return best_tok, confidence

    except Exception as exc:
        logger.warning("Whisper word transcription failed: %s", exc)
        return "", 0.0
