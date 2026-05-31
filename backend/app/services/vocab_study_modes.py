"""Study mode catalog — single source for API and docs."""

from app.schemas import VocabStudyModeInfo

VOCAB_STUDY_MODES: list[VocabStudyModeInfo] = [
    VocabStudyModeInfo(
        id="flashcard",
        label="Flashcard",
        description="Lật thẻ: từ tiếng Anh, phiên âm ↔ nghĩa tiếng Việt và ví dụ.",
    ),
    VocabStudyModeInfo(
        id="typing",
        label="Gõ từ vựng",
        description="Nghe phát âm và gõ đúng từ tiếng Anh.",
    ),
    VocabStudyModeInfo(
        id="reading",
        label="Đọc hiểu",
        description="Đọc câu ví dụ và điền đúng từ tiếng Anh vào chỗ trống.",
    ),
    VocabStudyModeInfo(
        id="dictation",
        label="Nghe chép",
        description="Nghe phát âm (TTS) và gõ lại đúng từ tiếng Anh.",
    ),
    VocabStudyModeInfo(
        id="speaking",
        label="Speaking",
        description="Ghi âm và kiểm tra phát âm từ (Whisper + mô hình pron_scorer).",
    ),
]
