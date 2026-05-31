"""Word-level phoneme scoring — Allosaurus + CMU + Whisper (ELSA-style)."""

from __future__ import annotations

import logging
import re
from dataclasses import asdict, dataclass, field
from difflib import SequenceMatcher
from typing import Any

import numpy as np

from app.services.phoneme_recognizer import (
    recognize_ipa_phonemes,
    safe_unlink,
    transcribe_single_word,
    waveform_to_wav_path,
)
from app.services.pronunciation_audio import prepare_speech_waveform
from app.services.speaking_audio_utils import has_speech

logger = logging.getLogger(__name__)

ARPABET_TO_IPA: dict[str, str] = {
    "AA": "ɑ",  "AE": "æ",  "AH": "ʌ",  "AO": "ɔ",  "AW": "aʊ", "AY": "aɪ",
    "B":  "b",  "CH": "tʃ", "D":  "d",  "DH": "ð",  "EH": "ɛ",  "ER": "ɜːr",
    "EY": "eɪ", "F":  "f",  "G":  "ɡ",  "HH": "h",  "IH": "ɪ",  "IY": "iː",
    "JH": "dʒ", "K":  "k",  "L":  "l",  "M":  "m",  "N":  "n",  "NG": "ŋ",
    "OW": "oʊ", "OY": "ɔɪ", "P":  "p",  "R":  "r",  "S":  "s",  "SH": "ʃ",
    "T":  "t",  "TH": "θ",  "UH": "ʊ",  "UW": "uː", "V":  "v",  "W":  "w",
    "Y":  "j",  "Z":  "z",  "ZH": "ʒ",
}

PHONEME_TIPS: dict[str, str] = {
    "TH": "Đặt đầu lưỡi nhẹ giữa hai hàm răng, thổi hơi ra — không phát âm thành /t/ hay /d/",
    "DH": "Giống /θ/ nhưng có tiếng vang (voiced) — lưỡi giữa răng + rung thanh quản",
    "R":  "Cuộn lưỡi về phía sau, không chạm vòm miệng",
    "V":  "Môi dưới chạm nhẹ răng trên, thổi hơi có tiếng — không phát âm thành /b/ hay /w/",
    "AE": "Mở miệng rộng, kéo khóe miệng sang hai bên — 'cat' không phải 'cet'",
    "ER": "Cuộn lưỡi giữa chừng, giữ nguyên — âm 'bird', 'her'",
    "IY": "Kéo dài hơn /i/ trong tiếng Việt — 'see', 'feel'",
}

IPA_SIMILAR: set[frozenset[str]] = {
    frozenset({"θ", "t", "f"}),
    frozenset({"ð", "d", "v", "z"}),
    frozenset({"ʃ", "s", "tʃ", "ʒ"}),
    frozenset({"ɪ", "i", "iː", "iy", "ə"}),
    frozenset({"ʊ", "u", "uː", "uw", "oʊ", "ow"}),
    frozenset({"ʌ", "ə", "ɑ", "ah", "a", "ae", "æ"}),
    frozenset({"ɛ", "e", "æ", "eh", "eɪ", "ey"}),
    frozenset({"ɔ", "o", "ao", "oh", "ɔɪ", "oy"}),
    frozenset({"r", "ɹ", "ɜːr", "er", "l"}),
    frozenset({"ŋ", "n", "ng", "m"}),
    frozenset({"b", "p"}),
    frozenset({"g", "ɡ", "k"}),
    frozenset({"f", "v"}),
    frozenset({"s", "z"}),
    frozenset({"w", "v", "u"}),
    frozenset({"j", "y", "dʒ"}),
    frozenset({"aɪ", "ay", "ɑɪ", "a"}),
    frozenset({"aʊ", "aw"}),
    frozenset({"oʊ", "ow", "ou", "o"}),
    frozenset({"eɪ", "ey", "ei", "e"}),
    frozenset({"ɔɪ", "oy", "oi"}),
    frozenset({"tʃ", "ch", "ʃ"}),
    frozenset({"dʒ", "jh", "j"}),
}

_CMUDICT: dict[str, list[list[str]]] | None = None


def _base_symbol(symbol: str) -> str:
    return re.sub(r"\d+$", "", symbol.upper())


def _arpabet_to_ipa(symbol: str) -> str:
    return ARPABET_TO_IPA.get(_base_symbol(symbol), symbol.lower())


def _ipa_string(phonemes: list[str]) -> str:
    if not phonemes:
        return "/?/"
    if phonemes[0].isupper():
        parts = [_arpabet_to_ipa(p) for p in phonemes]
    else:
        parts = list(phonemes)
    return "/" + "".join(parts) + "/"


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


def lookup_word_phonemes(word: str) -> list[str] | None:
    cleaned = re.sub(r"[^a-z'-]", "", word.lower())
    if not cleaned:
        return None
    pronunciations = _ensure_cmudict().get(cleaned)
    return list(pronunciations[0]) if pronunciations else None


def get_expected_word_info(word: str) -> dict[str, Any] | None:
    phonemes = lookup_word_phonemes(word)
    if not phonemes:
        return None
    ipa_list = [_arpabet_to_ipa(p) for p in phonemes]
    return {"word": word.lower(), "ipa": _ipa_string(phonemes), "phonemes": phonemes, "ipa_list": ipa_list}


def _ipa_similar(a: str, b: str) -> bool:
    if not a or not b:
        return False
    if a == b:
        return True
    for group in IPA_SIMILAR:
        if a in group and b in group:
            return True
    return False


def _ipa_pair_score(expected: str, predicted: str | None) -> float:
    if not predicted:
        return 0.0
    if expected == predicted:
        return 1.0
    if _ipa_similar(expected, predicted):
        return 0.7
    # partial: same first character (e.g. k/kw)
    if expected and predicted and expected[0] == predicted[0]:
        return 0.45
    return 0.0


def _align_ipa_scores(expected_ipa: list[str], predicted_ipa: list[str]) -> list[float]:
    if not expected_ipa:
        return []
    if not predicted_ipa:
        return [0.0] * len(expected_ipa)

    matcher = SequenceMatcher(None, expected_ipa, predicted_ipa, autojunk=False)
    scores = [0.0] * len(expected_ipa)

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                scores[i1 + k] = _ipa_pair_score(expected_ipa[i1 + k], predicted_ipa[j1 + k])
        elif tag == "replace":
            span = min(i2 - i1, j2 - j1)
            for k in range(span):
                scores[i1 + k] = _ipa_pair_score(expected_ipa[i1 + k], predicted_ipa[j1 + k])

    return scores


def _merge_scores(*score_lists: list[float]) -> list[float]:
    if not score_lists:
        return []
    n = max(len(s) for s in score_lists)
    merged = [0.0] * n
    for scores in score_lists:
        for i, s in enumerate(scores):
            merged[i] = max(merged[i], s)
    return merged


def _phoneme_scores_to_letters(word: str, phoneme_scores: list[float]) -> list["LetterDetail"]:
    n, m = len(word), len(phoneme_scores)
    if n == 0:
        return []
    if m == 0:
        return [LetterDetail(char=c, score=0.0, correct=False) for c in word]
    return [
        LetterDetail(
            char=ch,
            score=phoneme_scores[min(int(i * m / n), m - 1)],
            correct=phoneme_scores[min(int(i * m / n), m - 1)] >= 0.65,
        )
        for i, ch in enumerate(word)
    ]


def _verdict(overall: float) -> str:
    if overall >= 85:
        return "Excellent "
    if overall >= 70:
        return "Good "
    if overall >= 50:
        return "Needs Practice "
    return "Keep Trying "


def _resample_if_needed(waveform: np.ndarray, sample_rate: int) -> np.ndarray:
    if sample_rate == 16_000:
        return waveform.astype(np.float32)
    import librosa

    return librosa.resample(waveform.astype(np.float32), orig_sr=sample_rate, target_sr=16_000)


@dataclass
class LetterDetail:
    char: str
    score: float
    correct: bool


@dataclass
class PhonemeDetail:
    symbol: str
    ipa: str
    expected: bool
    score: float
    correct: bool
    tip: str | None = None


@dataclass
class PhonemeResult:
    word: str
    overall_score: float
    phonemes: list[PhonemeDetail] = field(default_factory=list)
    letters: list[LetterDetail] = field(default_factory=list)
    decoded_text: str = ""
    ipa_expected: str = ""
    ipa_predicted: str = ""
    verdict: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["phonemes"] = [
            {"symbol": p.symbol, "ipa": p.ipa, "score": round(p.score, 2), "correct": p.correct, "tip": p.tip}
            for p in self.phonemes
        ]
        data["letters"] = [
            {"char": l.char, "score": round(l.score, 2), "correct": l.correct} for l in self.letters
        ]
        data["overall_score"] = round(self.overall_score, 1)
        return data


class PhonemeScorer:
    """Score pronunciation: Allosaurus acoustic phonemes vs CMU, Whisper word sanity check."""

    def score_word(
        self,
        waveform_np: np.ndarray,
        sample_rate: int,
        expected_word: str,
    ) -> PhonemeResult:
        expected_arpabet = lookup_word_phonemes(expected_word)
        if not expected_arpabet:
            raise ValueError(f"Từ '{expected_word}' không có trong CMU Pronouncing Dictionary.")

        audio = _resample_if_needed(waveform_np, sample_rate)
        audio = prepare_speech_waveform(audio, 16_000)
        if audio.size == 0:
            raise ValueError("Audio rỗng hoặc không hợp lệ.")
        if not has_speech(audio):
            raise ValueError("Không phát hiện giọng nói. Hãy nói to hơn hoặc kiểm tra micro.")

        expected_clean = re.sub(r"[^a-z]", "", expected_word.lower())
        expected_ipa = [_arpabet_to_ipa(p) for p in expected_arpabet]
        n_expected = len(expected_ipa)

        wav_path = waveform_to_wav_path(audio)
        try:
            acoustic_ipa = recognize_ipa_phonemes(wav_path)
            whisper_text, whisper_conf = transcribe_single_word(wav_path, expected_clean)
            word_match = (
                SequenceMatcher(None, expected_clean, whisper_text).ratio()
                if whisper_text
                else 0.0
            )

            # Acoustic alignment (Allosaurus)
            acoustic_scores = _align_ipa_scores(expected_ipa, acoustic_ipa)

            # CMU alignment from heard word (Whisper)
            heard_arpabet = lookup_word_phonemes(whisper_text) if whisper_text else None
            heard_ipa = [_arpabet_to_ipa(p) for p in heard_arpabet] if heard_arpabet else []
            whisper_scores = _align_ipa_scores(expected_ipa, heard_ipa) if heard_ipa else []

            per_phoneme = _merge_scores(acoustic_scores, whisper_scores)
            if len(per_phoneme) != n_expected:
                per_phoneme = (per_phoneme + [0.0] * n_expected)[:n_expected]

            # Whisper heard the right word → boost (short clips often confuse Allosaurus)
            if word_match >= 0.95 or whisper_conf >= 0.88:
                floor = min(0.82 + 0.15 * max(word_match, whisper_conf), 1.0)
                per_phoneme = [max(s, floor) for s in per_phoneme]
            elif word_match >= 0.82:
                floor = min(0.68 + 0.22 * word_match, 1.0)
                per_phoneme = [max(s, floor) for s in per_phoneme]
            elif word_match >= 0.65:
                floor = 0.5 + 0.25 * word_match
                per_phoneme = [max(s, floor) for s in per_phoneme]

            # Partial acoustic match — blend with current scores
            if acoustic_ipa and acoustic_scores:
                ac_mean = float(np.mean(acoustic_scores))
                if ac_mean >= 0.35:
                    whisper_pad = (
                        whisper_scores
                        if len(whisper_scores) == n_expected
                        else [0.0] * n_expected
                    )
                    per_phoneme = [
                        max(p, ac * 0.9)
                        for p, ac in zip(per_phoneme, acoustic_scores, strict=False)
                    ]

            overall = float(np.mean(per_phoneme) * 100) if per_phoneme else 0.0

            logger.info(
                "SCORE word=%s acoustic=%s whisper=%s match=%.2f per=%s overall=%.1f",
                expected_clean,
                acoustic_ipa,
                whisper_text,
                word_match,
                [round(s, 2) for s in per_phoneme],
                overall,
            )

            details: list[PhonemeDetail] = []
            for arpabet, ipa, score in zip(expected_arpabet, expected_ipa, per_phoneme, strict=False):
                base = _base_symbol(arpabet)
                correct = score >= 0.65
                details.append(
                    PhonemeDetail(
                        symbol=arpabet,
                        ipa=ipa,
                        expected=True,
                        score=score,
                        correct=correct,
                        tip=None if correct else PHONEME_TIPS.get(base),
                    )
                )

            predicted_ipa_display = acoustic_ipa or heard_ipa
            return PhonemeResult(
                word=expected_word.lower(),
                overall_score=overall,
                phonemes=details,
                letters=_phoneme_scores_to_letters(expected_word, per_phoneme),
                decoded_text=whisper_text or (" ".join(acoustic_ipa) if acoustic_ipa else ""),
                ipa_expected=_ipa_string(expected_arpabet),
                ipa_predicted=_ipa_string(predicted_ipa_display),
                verdict=_verdict(overall),
            )
        finally:
            safe_unlink(wav_path)


_SCORER: PhonemeScorer | None = None


def get_phoneme_scorer() -> PhonemeScorer:
    global _SCORER
    if _SCORER is None:
        _SCORER = PhonemeScorer()
    return _SCORER
