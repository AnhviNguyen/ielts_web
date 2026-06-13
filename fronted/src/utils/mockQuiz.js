export function normalizeLocateInfo(locateInfo) {
  if (!locateInfo) return null
  if (Array.isArray(locateInfo?.paragraph_ranges)) return locateInfo
  // Sometimes locate_info is an object keyed by number strings: { "0": { paragraph_ranges: [...] } }
  const firstKey = Object.keys(locateInfo)[0]
  if (firstKey && locateInfo[firstKey]?.paragraph_ranges) return locateInfo[firstKey]
  return null
}

export function extractParagraphSpans(locateInfo) {
  const n = normalizeLocateInfo(locateInfo)
  const ranges = n?.paragraph_ranges || []
  // Return as [{startParagraph, endParagraph}]
  return ranges.map((r) => ({
    startParagraph: r?.start?.paragraph,
    endParagraph: r?.end?.paragraph,
  })).filter((x) => Number.isFinite(x.startParagraph) && Number.isFinite(x.endParagraph))
}

/**
 * Build passage/transcript paragraphs from listening/reading `vocabs`.
 *
 * `locate_info.paragraph` trong JSON = chỉ số 1-based của block gốc trong mảng `vocabs`
 * (bao gồm cả các block rỗng không có children).
 *
 * Các block rỗng (không có children) được giữ lại trong output với flag `isEmpty: true`
 * để ReadingPassage có thể render khoảng cách giữa các đoạn văn (đặc biệt với Format B
 * như Orange 16→20 không có YouPass Builder, dùng blank block làm separator).
 */
export function buildParagraphsFromVocabs(vocabs) {
  const out = []
  const arr = vocabs || []
  for (let i = 0; i < arr.length; i++) {
    const g = arr[i]
    const hasChildren = Array.isArray(g.children) && g.children.length > 0
    if (!hasChildren) {
      // Blank separator block — preserve paragraph index but mark as empty
      out.push({
        paragraph: i + 1,
        id: g.id,
        isEmpty: true,
        text: '',
        children: [],
      })
      continue
    }
    out.push({
      paragraph: i + 1,
      id: g.id,
      speaker: g.children?.[0]?.meta?.speaker,
      text: g.children.map((c) => c.value).join(' ').trim(),
      children: g.children.map((c) => ({
        id: c.id,
        text: c.value,
        from: c.meta?.from,
        to: c.meta?.to,
        speaker: c.meta?.speaker,
      })),
    })
  }
  return out
}

function optionText(opt) {
  return String(opt?.text ?? '').trim()
}

function optionKey(opt) {
  return String(opt?.option ?? '').trim()
}

function optionHasText(options) {
  return (options || []).some((o) => optionText(o))
}

function optionsIncomplete(options) {
  const list = Array.isArray(options) ? options : []
  if (!list.length) return true
  return list.some((o) => !optionText(o))
}

/** Resolve MCQ options from per-question list and/or question-set list. */
export function resolveChoiceOptions(perQ, setOpts) {
  const per = Array.isArray(perQ) ? perQ : []
  const set = Array.isArray(setOpts) ? setOpts : []

  const perMap = Object.fromEntries(per.map((o) => [optionKey(o), optionText(o)]).filter(([k]) => k))
  const setMap = Object.fromEntries(set.map((o) => [optionKey(o), optionText(o)]).filter(([k]) => k))
  const keys = per.length
    ? per.map((o) => optionKey(o)).filter(Boolean)
    : set.map((o) => optionKey(o)).filter(Boolean)

  if (!keys.length) return []

  return keys.map((key) => ({
    option: key,
    text: perMap[key] || setMap[key] || '',
  }))
}

/** True when set-level options can safely backfill a question (shared option bank). */
export function canUseSetOptionFallback(perQ, setOpts) {
  const per = Array.isArray(perQ) ? perQ : []
  const set = Array.isArray(setOpts) ? setOpts : []
  if (!per.length || !set.length) return true
  if (!optionsIncomplete(per)) return false
  return !optionHasText(per)
}

export function flattenQuizQuestions(quiz) {
  const parts = quiz?.parts || []
  const out = []
  for (const part of parts) {
    const questionSets = part?.question_sets || []
    for (const qs of questionSets) {
      const questions = qs?.questions || []
      for (const q of questions) {
        out.push({
          partId: part.id,
          partTitle: part.title,
          passage: part.passage,
          questionSetId: qs.id,
          questionSetTitle: qs.title,
          questionSetType: qs.question_type,
          questionSetDescription: qs.description,
          questionSetContent: qs.content,
          questionSetOptions: qs.options || [],
          questionSetMaxSelections: qs.max_selections || 0,
          question: q,
        })
      }
    }
  }
  // For speaking quizzes, order values repeat per set — use global sort instead
  const isSpeaking = out.some(x => String(x.questionSetType || '').toLowerCase() === 'speaking')
  if (isSpeaking) {
    out.sort((a, b) => (a.question?.sort ?? 0) - (b.question?.sort ?? 0))
  } else {
    out.sort((a, b) => (a.question?.order ?? 0) - (b.question?.order ?? 0))
  }
  return out
}

export function isListeningQuiz(quiz) {
  // In data: type 10 listening, type 9 reading (from mock_test files)
  return String(quiz?.type) === '10'
}

