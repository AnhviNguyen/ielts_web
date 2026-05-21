/** Study mode catalog for VocabPractice (data only). */
export const VOCAB_PRACTICE_MODES = [
  { id: 'flashcard', label: 'Flashcard' },
  { id: 'reading', label: 'Đọc hiểu' },
  { id: 'dictation', label: 'Nghe chép' },
  { id: 'typing', label: 'Gõ từ vựng' },
]

export const VOCAB_PRACTICE_MODE_IDS = VOCAB_PRACTICE_MODES.map((m) => m.id)
