"""SpeechBrain G2P + g2p-en/CMU for phoneme lookup; GOP wav2vec2 + Whisper for ASR."""

from __future__ import annotations

import logging
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


def _speechbrain_enabled() -> bool:
    """SpeechBrain breaks lazy imports (librosa/k2) on Python 3.13 — skip unless forced."""
    flag = os.getenv("SPEECHBRAIN_ENABLED", "").strip().lower()
    if flag in {"0", "false", "no"}:
        return False
    if flag in {"1", "true", "yes"}:
        return True
    return sys.version_info < (3, 13)

_UNSET = object()
_G2P: Any = _UNSET
_G2P_EN = None
_CMUDICT: dict[str, list[list[str]]] | None = None

_G2P_SOURCE = os.getenv("SPEECHBRAIN_G2P_MODEL", "speechbrain/soundchoice-g2p")
_MODEL_ROOT = Path(__file__).resolve().parents[2] / "pretrained_models"


def _savedir(name: str) -> str:
    path = _MODEL_ROOT / name
    path.mkdir(parents=True, exist_ok=True)
    return str(path)


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


def _get_g2p():
    global _G2P
    if not _speechbrain_enabled():
        if _G2P is _UNSET:
            _G2P = None
        return None
    if _G2P is not _UNSET:
        return None if _G2P is None else _G2P
    try:
        from speechbrain.inference.text import GraphemeToPhoneme
        from speechbrain.utils.fetching import LocalStrategy

        logger.info("Loading SpeechBrain G2P (%s) …", _G2P_SOURCE)
        _G2P = GraphemeToPhoneme.from_hparams(
            source=_G2P_SOURCE,
            savedir=_savedir("speechbrain-g2p"),
            local_strategy=LocalStrategy.COPY,
        )
        logger.info("SpeechBrain G2P ready.")
    except Exception as exc:
        logger.warning("SpeechBrain G2P unavailable, using g2p-en/CMU fallback: %s", exc)
        _G2P = None
    return _G2P


def _base_arpabet(symbol: str) -> str:
    return re.sub(r"\d+$", "", (symbol or "").strip().upper())


def _clean_g2p_output(raw: list[str] | str) -> list[str]:
    if isinstance(raw, str):
        tokens = raw.split()
    else:
        tokens = list(raw)
    out: list[str] = []
    for tok in tokens:
        base = _base_arpabet(tok)
        if base and base.isalpha():
            out.append(base)
    return out


def _spelling_variants(word: str) -> list[str]:
    w = word.lower()
    variants = [w]
    if w.endswith("isers"):
        variants.append(w[:-5] + "izers")
    if w.endswith("izer"):
        variants.append(w[:-2] + "iser")
    if w.endswith("isation"):
        variants.append(w[:-7] + "ization")
    if w.endswith("ised"):
        variants.append(w[:-3] + "ized")
    if w.endswith("our"):
        variants.append(w[:-3] + "or")
    # Plural / inflection fallbacks (e.g. manatees → manatee)
    if w.endswith("ies") and len(w) > 4:
        variants.append(w[:-3] + "y")
    if w.endswith("es") and len(w) > 3:
        variants.append(w[:-2])
        variants.append(w[:-1])
    elif w.endswith("s") and len(w) > 2 and not w.endswith("ss"):
        variants.append(w[:-1])
    seen: set[str] = set()
    ordered: list[str] = []
    for v in variants:
        if v not in seen:
            seen.add(v)
            ordered.append(v)
    return ordered


def _ensure_cmudict() -> dict[str, list[list[str]]]:
    global _CMUDICT
    if _CMUDICT is not None:
        return _CMUDICT
    import nltk
    from nltk.corpus import cmudict

    try:
        nltk.data.find("corpora/cmudict")
    except LookupError:
        nltk.download("cmudict", quiet=True)
    _CMUDICT = cmudict.dict()
    return _CMUDICT


def _cmu_phonemes(word: str) -> list[str]:
    cmu = _ensure_cmudict()
    for variant in _spelling_variants(word):
        pronunciations = cmu.get(variant)
        if pronunciations:
            return _clean_g2p_output(pronunciations[0])
    return []


def _get_g2p_en():
    global _G2P_EN
    if _G2P_EN is None:
        import nltk
        from g2p_en import G2p

        try:
            nltk.data.find("taggers/averaged_perceptron_tagger_eng")
        except LookupError:
            nltk.download("averaged_perceptron_tagger_eng", quiet=True)
        _G2P_EN = G2p()
    return _G2P_EN


def _g2p_en_phonemes(word: str) -> list[str]:
    try:
        raw = _get_g2p_en()(word)
        return _clean_g2p_output(raw)
    except Exception as exc:
        logger.warning("g2p-en failed for %r: %s", word, exc)
        return []


def _speechbrain_g2p_phonemes(word: str) -> list[str]:
    global _G2P
    g2p = _get_g2p()
    if not g2p:
        return []
    try:
        return _clean_g2p_output(g2p(word))
    except Exception as exc:
        logger.warning("SpeechBrain G2P inference failed for %r: %s — disabling", word, exc)
        _G2P = None
        return []


def word_to_phonemes(word: str) -> list[str]:
    """ARPAbet phoneme sequence — g2p-en/CMU locally; SpeechBrain when enabled."""
    cleaned = re.sub(r"[^a-zA-Z'-]", "", (word or "").strip())
    if not cleaned:
        return []

    # Fast local backends first — avoid loading SpeechBrain on every lookup.
    backends = [_g2p_en_phonemes, _cmu_phonemes]
    if _speechbrain_enabled():
        backends.append(_speechbrain_g2p_phonemes)

    for variant in _spelling_variants(cleaned):
        for fn in backends:
            phonemes = fn(variant)
            if phonemes:
                logger.info("G2P %r → %s (%s)", cleaned, phonemes, fn.__name__)
                return phonemes

    logger.warning("No phonemes found for %r", cleaned)
    return []


def _whisper_transcribe(wav_path: str) -> str:
    from ml.whisper_asr import transcribe_audio

    result = transcribe_audio(
        wav_path,
        language="en",
        word_timestamps=False,
        condition_on_previous_text=False,
    )
    return (result.get("transcript") or "").strip()


def transcribe_audio(wav_path: str) -> str:
    """Transcribe mono 16 kHz WAV — GOP wav2vec2-base-960h (shared with shadowing), then Whisper."""
    try:
        from app.services.gop_pronunciation_service import load_audio_16k, transcribe_audio_16k

        audio_16k = load_audio_16k(wav_path)
        text = transcribe_audio_16k(audio_16k).strip()
        if text:
            logger.info("ASR (GOP wav2vec2) %s → %r", wav_path, text)
            return text
    except Exception as exc:
        logger.warning("GOP wav2vec2 ASR failed for %s: %s — falling back to Whisper", wav_path, exc)

    try:
        text = _whisper_transcribe(wav_path)
        logger.info("ASR (Whisper) %s → %r", wav_path, text)
        return text
    except Exception as exc:
        logger.warning("Whisper ASR failed for %s: %s", wav_path, exc)
        return ""
