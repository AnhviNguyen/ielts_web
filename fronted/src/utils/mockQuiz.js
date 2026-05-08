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

export function buildParagraphsFromVocabs(vocabs) {
  const groups = (vocabs || []).filter((v) => Array.isArray(v.children) && v.children.length)
  // 1-based paragraph indices (to match locate_info.paragraph)
  return groups.map((g, idx) => ({
    paragraph: idx + 1,
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
  }))
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

