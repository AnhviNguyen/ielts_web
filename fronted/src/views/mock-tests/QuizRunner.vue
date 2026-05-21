<template>
  <div class="min-h-screen bg-[var(--bg)]">
    <!-- Exit confirm dialog -->
    <Teleport to="body">
      <div v-if="showExitConfirm" class="fixed inset-0 z-[500] flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-black/40" @click="showExitConfirm = false"></div>
        <div class="relative z-10 w-full max-w-sm rounded-xl bg-white p-6 shadow-xl">
          <div class="mb-1 text-base font-bold text-[var(--ink)]">Thoát bài thi?</div>
          <p class="mb-5 text-[13px] text-[var(--ink3)]">Tiến trình làm bài sẽ không được lưu. Bạn có chắc muốn thoát?</p>
          <div class="flex justify-end gap-2">
            <button class="ct-btn" @click="showExitConfirm = false">Tiếp tục làm</button>
            <button class="ct-btn" style="border-color:#e11d48;color:#e11d48" @click="confirmExit">Thoát</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Floating toolbar chỉ cho Speaking (Listening dùng ReadingToolbar + ReadingPassage trong panel) -->
    <PracticeToolbar
      v-if="practiceMode && isSpeaking"
      :practice-mode="practiceMode"
      v-model:model-note="practiceNote"
      @tool-changed="onToolbarToolChanged"
    />
    <ExamHeader
      :title="quizTitle"
      :subtitle="quizSubtitle"
      :remaining-seconds="store.remainingSeconds"
      @submit="submit(false)"
    />

    <div class="exam-container py-5 sm:py-6">
      <div v-if="store.loading" class="card p-6 text-center text-[var(--ink2)]">Loading…</div>
      <div v-else-if="!store.quiz" class="card p-6 text-center">
        <div class="text-lg font-semibold mb-2">Quiz not found</div>
        <RouterLink to="/dashboard" class="btn btn-primary">Về trang chủ</RouterLink>
      </div>

      <template v-else>
        <!-- Speaking evaluation overlay -->
        <Teleport to="body">
          <div v-if="evaluating" class="fixed inset-0 z-[600] flex items-center justify-center bg-black/60">
            <div class="flex flex-col items-center gap-4 rounded-2xl bg-[#0f0f1a] p-8 text-white shadow-2xl">
              <div class="h-10 w-10 animate-spin rounded-full border-4 border-[#6c63ff] border-t-transparent"/>
              <p class="text-sm font-semibold">Đang phân tích bài nói…</p>
              <p class="text-[11px] text-[#a0a0c0]">Pronunciation · Transcription · AI Feedback</p>
            </div>
          </div>
        </Teleport>

        <!-- Speaking mode -->
        <div v-if="isSpeaking">
          <!-- ── PRACTICE speaking: centered panel layout ── -->
          <SpeakingPracticePanel
            v-if="practiceMode"
            :current-index="currentSpeakingIdx"
            :total="speakingFlat.length"
            :part-title="currentSpeakingItem?.partTitle || (currentSpeakingItem ? `Part ${currentSpeakingIdx + 1}` : '')"
            :chat-open="chatOpen"
            :can-prev="currentSpeakingIdx > 0"
            :can-next="currentSpeakingIdx < speakingFlat.length - 1"
            @exit="showExitConfirm = true"
            @prev="prevSpeaking"
            @next="nextSpeaking"
            @toggle-chat="chatOpen = !chatOpen"
          >
            <QuestionRenderer
              v-if="currentSpeakingItem"
              :key="currentSpeakingItem.question.id"
              :item="currentSpeakingItem"
              :answer="store.answers[currentSpeakingItem.question.id]"
              :is-current="true"
              speaking-compact
              @update:answer="(v) => store.setAnswer(currentSpeakingItem.question.id, v)"
              @evaluate-speaking="onEvaluateSpeaking"
            />

            <template #chat>
              <Transition name="slide">
                <SpeakingChatbot
                  v-if="chatOpen"
                  class="w-full shrink-0 lg:w-[340px]"
                  :question-text="speakingCurrentQuestion"
                  @close="chatOpen = false"
                />
              </Transition>
            </template>

            <template v-if="currentSpeakingEval?.result" #feedback>
              <div class="space-y-5">
                  <div class="flex flex-wrap items-center justify-between gap-2">
                    <div class="flex items-center gap-2 text-[14px] font-semibold text-[var(--ink)]">
                      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#34d399" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
                      Kết quả câu {{ currentSpeakingIdx + 1 }}
                    </div>
                    <div class="flex gap-2">
                      <button
                        class="ct-btn px-3 py-1.5 text-[12px]"
                        @click="router.push({ path: '/speaking/result', state: currentSpeakingEval })"
                      >
                        Xem chi tiết
                      </button>
                      <button
                        v-if="currentSpeakingIdx < speakingFlat.length - 1"
                        class="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-[12px] font-semibold text-white"
                        style="background:#34d399"
                        @click="nextSpeaking"
                      >
                        Câu tiếp theo
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
                      </button>
                    </div>
                  </div>

                  <div class="grid grid-cols-1 gap-5 xl:grid-cols-2">
                    <div class="card p-6">
                      <div class="mb-4 flex items-center gap-2 text-[var(--ink2)]">
                        <span class="text-xs font-bold uppercase tracking-wider">Band Score</span>
                      </div>
                      <div class="flex items-center gap-6">
                        <BandScoreRing :band="currentSpeakingEval.result.band_estimate || 0" />
                        <div class="flex-1 space-y-2 text-sm text-[var(--ink2)]">
                          <div class="flex justify-between">
                            <span>Grammar</span>
                            <span class="font-semibold text-[var(--ink)]">{{ Number(currentSpeakingEval.result.grammar?.score || 0).toFixed(1) }}/9</span>
                          </div>
                          <div class="flex justify-between">
                            <span>Vocabulary</span>
                            <span class="font-semibold text-[var(--ink)]">{{ Number(currentSpeakingEval.result.vocabulary?.score || 0).toFixed(1) }}/9</span>
                          </div>
                          <div class="flex justify-between">
                            <span>Pronunciation</span>
                            <span class="font-semibold text-[var(--ink)]">{{ Number(currentSpeakingEval.result.pronunciation?.total || 0).toFixed(1) }}/10</span>
                          </div>
                        </div>
                      </div>
                      <div class="mt-5">
                        <AudioPlayer :audio-url="currentSpeakingEval.audioUrl" />
                      </div>
                    </div>

                    <div class="card p-6">
                      <div class="mb-4 flex items-center gap-2 text-[var(--ink2)]">
                        <span class="text-xs font-bold uppercase tracking-wider">Pronunciation</span>
                      </div>
                      <div class="grid grid-cols-2 gap-y-5 gap-x-4">
                        <CircularScore :score="currentSpeakingEval.result.pronunciation?.accuracy || 0" label="Accuracy" />
                        <CircularScore :score="currentSpeakingEval.result.pronunciation?.fluency || 0" label="Fluency" />
                        <CircularScore :score="currentSpeakingEval.result.pronunciation?.prosodic || 0" label="Prosodic" />
                        <CircularScore :score="currentSpeakingEval.result.pronunciation?.total || 0" label="Total" :size="96" />
                      </div>
                    </div>
                  </div>

                  <TranscriptHighlight
                    :transcript="currentSpeakingEval.result.transcript || ''"
                    :word-timestamps="currentSpeakingEval.result.word_timestamps || []"
                  />

                  <div class="grid grid-cols-1 gap-5 xl:grid-cols-2">
                    <GrammarCard
                      :transcript="currentSpeakingEval.result.transcript || ''"
                      :question-text="speakingCurrentQuestion"
                      :score="Number(currentSpeakingEval.result.grammar?.score || 0)"
                      :errors="currentSpeakingEval.result.grammar?.errors || []"
                      :evaluate-result="currentSpeakingEval.result"
                    />
                    <VocabCard
                      :transcript="currentSpeakingEval.result.transcript || ''"
                      :question-text="speakingCurrentQuestion"
                      :score="Number(currentSpeakingEval.result.vocabulary?.score || 0)"
                      :feedback="currentSpeakingEval.result.vocabulary?.feedback || []"
                      :evaluate-result="currentSpeakingEval.result"
                    />
                  </div>

                  <div class="grid grid-cols-1 gap-5 xl:grid-cols-2">
                    <div class="card p-5">
                      <div class="mb-3 text-xs font-bold uppercase tracking-wider text-[#34d399]">Strengths</div>
                      <ul class="space-y-1.5">
                        <li
                          v-for="(s, i) in currentSpeakingEval.result.strengths || []"
                          :key="`st_${i}`"
                          class="flex items-start gap-2 text-sm text-[var(--ink)]"
                        >
                          <span class="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[#34d399]"/>
                          {{ s }}
                        </li>
                        <li v-if="!(currentSpeakingEval.result.strengths || []).length" class="text-sm text-[var(--ink3)]">—</li>
                      </ul>
                    </div>
                    <div class="card p-5">
                      <div class="mb-3 text-xs font-bold uppercase tracking-wider text-[#f59e0b]">Improvements</div>
                      <ul class="space-y-1.5">
                        <li
                          v-for="(imp, i) in currentSpeakingEval.result.improvements || []"
                          :key="`im_${i}`"
                          class="flex items-start gap-2 text-sm text-[var(--ink)]"
                        >
                          <span class="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[#f59e0b]"/>
                          {{ imp }}
                        </li>
                        <li v-if="!(currentSpeakingEval.result.improvements || []).length" class="text-sm text-[var(--ink3)]">—</li>
                      </ul>
                    </div>
                  </div>

                  <div v-if="currentSpeakingEval.result.overall_comment" class="card border-l-4 border-l-[#34d399] p-5">
                    <div class="mb-2 text-xs font-bold uppercase tracking-wider text-[#34d399]">Overall comment</div>
                    <p class="text-sm leading-relaxed text-[var(--ink)]">{{ currentSpeakingEval.result.overall_comment }}</p>
                  </div>
              </div>
            </template>
          </SpeakingPracticePanel>

          <div v-if="practiceMode && evalError" class="mx-auto mt-4 max-w-3xl rounded-lg border border-[#f43f5e44] bg-[#f43f5e11] px-4 py-2 text-xs text-[#f43f5e]">
            {{ evalError }}
          </div>

          <!-- ── EXAM speaking: all questions + nav grid ── -->
          <template v-else-if="!practiceMode">
            <div class="mb-4 flex items-center justify-between gap-3">
              <QuestionNavGrid
                :questions="navQuestions"
                :nav-parts="navParts"
                :current-order="store.currentOrder"
                :answered-map="store.answers"
                @go="goToOrder"
                class="min-w-0 flex-1"
              />
              <button
                type="button"
                @click="chatOpen = !chatOpen"
                class="flex shrink-0 items-center gap-1.5 rounded-full border px-3 py-1.5 text-[11px] font-semibold transition-colors"
                :class="chatOpen
                  ? 'border-[#34d399] bg-[#34d39911] text-[#34d399]'
                  : 'border-[var(--border2)] bg-white text-[var(--ink2)] hover:border-[#34d399] hover:text-[#34d399]'"
              >
                <svg width="11" height="11" viewBox="0 0 24 24" fill="currentColor"><path d="M20 2H4a2 2 0 0 0-2 2v18l4-4h14a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2z"/></svg>
                Need help? Click here.
              </button>
            </div>

            <div
              class="mx-auto flex max-w-7xl gap-0 overflow-hidden rounded-2xl border border-[var(--border)] bg-white"
            >
              <div class="min-w-0 flex-1 p-5 sm:p-6" :class="chatOpen ? 'border-r border-[var(--border)]' : ''">
                <div v-for="sec in sections" :key="sec.key" class="mb-6">
                  <div class="mb-2 text-xs font-semibold text-[var(--ink2)]">{{ sec.title }}</div>
                  <div class="mb-3 text-sm text-[var(--ink2)]" v-if="sec.description" v-html="sec.description"></div>
                  <div class="grid gap-3">
                    <div
                      v-for="it in sec.items"
                      :key="it.question.id"
                      :ref="(el) => registerQuestionEl(it.question.order, el)"
                      @click="setCurrent(it.question.order)"
                    >
                      <QuestionRenderer
                        :item="it"
                        :answer="store.answers[it.question.id]"
                        :is-current="store.currentOrder === it.question.order"
                        @update:answer="(v) => store.setAnswer(it.question.id, v)"
                        @evaluate-speaking="onEvaluateSpeaking"
                      />

                      <!-- Inline result for this question (exam speaking) -->
                      <div
                        v-if="speakingEvalByQuestion[String(it.question.id)]"
                        class="mt-3 overflow-hidden rounded-xl border border-[#d1fae5] bg-[#f0fdf4]"
                      >
                        <!-- Result header -->
                        <div class="flex items-center justify-between border-b border-[#d1fae5] px-4 py-2.5">
                          <div class="flex items-center gap-2 text-[12px] font-semibold text-[#059669]">
                            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
                            Kết quả câu {{ it.question.order }}
                          </div>
                          <button
                            class="text-[11px] text-[#059669] underline hover:no-underline"
                            @click.stop="router.push({ path: '/speaking/result', state: speakingEvalByQuestion[String(it.question.id)] })"
                          >
                            Xem chi tiết
                          </button>
                        </div>
                        <!-- Score summary row -->
                        <div class="grid grid-cols-2 divide-x divide-[#d1fae5] sm:grid-cols-4">
                          <div class="px-4 py-3 text-center">
                            <div class="text-[11px] text-[#6b7280]">Band</div>
                            <div class="text-lg font-bold text-[#059669]">
                              {{ Number(speakingEvalByQuestion[String(it.question.id)]?.result?.band_estimate || 0).toFixed(1) }}
                            </div>
                          </div>
                          <div class="px-4 py-3 text-center">
                            <div class="text-[11px] text-[#6b7280]">Grammar</div>
                            <div class="text-base font-semibold text-[var(--ink)]">
                              {{ Number(speakingEvalByQuestion[String(it.question.id)]?.result?.grammar?.score || 0).toFixed(1) }}<span class="text-[10px] text-[#9ca3af]">/9</span>
                            </div>
                          </div>
                          <div class="px-4 py-3 text-center">
                            <div class="text-[11px] text-[#6b7280]">Vocab</div>
                            <div class="text-base font-semibold text-[var(--ink)]">
                              {{ Number(speakingEvalByQuestion[String(it.question.id)]?.result?.vocabulary?.score || 0).toFixed(1) }}<span class="text-[10px] text-[#9ca3af]">/9</span>
                            </div>
                          </div>
                          <div class="px-4 py-3 text-center">
                            <div class="text-[11px] text-[#6b7280]">Pron.</div>
                            <div class="text-base font-semibold text-[var(--ink)]">
                              {{ Number(speakingEvalByQuestion[String(it.question.id)]?.result?.pronunciation?.total || 0).toFixed(1) }}<span class="text-[10px] text-[#9ca3af]">/10</span>
                            </div>
                          </div>
                        </div>
                        <!-- Transcript snippet -->
                        <div
                          v-if="speakingEvalByQuestion[String(it.question.id)]?.result?.transcript"
                          class="border-t border-[#d1fae5] px-4 py-2.5 text-[12px] text-[#374151]"
                        >
                          <span class="mr-1 font-semibold text-[#059669]">Bài nói:</span>
                          {{ speakingEvalByQuestion[String(it.question.id)]?.result?.transcript }}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                <div class="mt-6 flex items-center justify-between gap-2">
                  <button type="button" class="btn btn-secondary" @click="showExitConfirm = true">Thoát</button>
                  <button type="button" class="btn btn-primary" @click="submit(false)">Nộp bài &amp; Xem kết quả</button>
                </div>

                <div v-if="evalError" class="mt-3 rounded-lg border border-[#f43f5e44] bg-[#f43f5e11] px-4 py-2 text-xs text-[#f43f5e]">
                  {{ evalError }}
                </div>
              </div>

              <Transition name="slide">
                <SpeakingChatbot
                  v-if="chatOpen"
                  :question-text="speakingCurrentQuestion"
                  @close="chatOpen = false"
                />
              </Transition>
            </div>
          </template>
        </div>

        <!-- Resizable two-panel layout (Reading / Listening) -->
        <div v-else class="flex gap-5 lg:gap-6" ref="layoutEl">
          <!-- Left panel -->
          <div class="flex flex-col gap-4 min-w-0" :style="{ flex: `0 0 ${leftWidth}px`, width: leftWidth + 'px' }">
            <template v-if="isListening">
              <ExamAudioPlayer
                ref="playerRef"
                :src="audioSrc"
                :title="activePart?.title || 'Listening'"
                :subtitle="`File: ${activePart?.file_id || '—'}`"
                :seek-to="seekTo"
                @time="(t) => (currentAudioTime.value = t)"
              />
              <!-- Practice: highlight / ghi chú / tra từ giống Reading -->
              <div v-if="practiceMode" class="card overflow-hidden">
                <div class="px-4 pt-3 pb-1 text-xs font-semibold text-[var(--ink2)]">{{ activePart?.title }}</div>
                <ReadingToolbar
                  v-model:model-note="practiceNote"
                  @tool-changed="onToolbarToolChanged"
                />
                <div class="overflow-y-auto p-4" style="max-height: calc(100vh - 280px)">
                  <ReadingPassage
                    ref="readingPassageRef"
                    :paragraphs="activeParagraphs"
                    :active-tool="practiceActiveTool"
                    :highlight-color="practiceHighlightColor"
                    :source-type="isListening ? 'listening' : 'reading'"
                    :source-quiz-id="String(route.params.quizId || '')"
                    @highlights-changed="onHighlightsChanged"
                  />
                </div>
              </div>
              <TranscriptPanel
                v-else
                :paragraphs="activeParagraphs"
                :current-time="currentAudioTime"
                :highlighted-ids="transcript.highlightedIds.value"
                @seek="(t) => { seekTo.value = t; transcript.clearForced() }"
              />
            </template>

            <template v-else>
              <div class="card overflow-hidden">
                <div class="px-4 pt-3 pb-1 text-xs font-semibold text-[var(--ink2)]">{{ activePart?.title }}</div>
                <!-- Inline toolbar for practice mode -->
                <ReadingToolbar
                  v-if="practiceMode"
                  v-model:model-note="practiceNote"
                  @tool-changed="onToolbarToolChanged"
                />
                <!-- Passage area: scrollable -->
                <div class="overflow-y-auto p-4" style="max-height: calc(100vh - 220px)">
                  <!-- Practice mode: enhanced passage with tool support -->
                  <ReadingPassage
                    v-if="practiceMode"
                    ref="readingPassageRef"
                    :paragraphs="activeParagraphs"
                    :active-tool="practiceActiveTool"
                    :highlight-color="practiceHighlightColor"
                    :source-type="isListening ? 'listening' : 'reading'"
                    :source-quiz-id="String(route.params.quizId || '')"
                    @highlights-changed="onHighlightsChanged"
                  />
                  <!-- Exam mode: plain passage -->
                  <div v-else class="reading-passage">
                    <div
                      v-for="p in activeParagraphs"
                      :key="p.paragraph"
                      class="reading-paragraph"
                      :class="isHighlightedParagraph(p.paragraph) ? 'is-highlight' : ''"
                    >
                      <span class="para-tag">{{ p.paragraph }}</span>
                      <span>{{ p.text }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </template>

            <QuestionNavGrid
              :questions="navQuestions"
              :nav-parts="navParts"
              :current-order="store.currentOrder"
              :answered-map="store.answers"
              @go="goToOrder"
            />
          </div>

          <!-- Drag divider -->
          <div
            class="flex w-2 cursor-col-resize items-center justify-center group"
            @mousedown.prevent="startResize"
          >
            <div class="h-12 w-0.5 rounded-full bg-[var(--border2)] group-hover:bg-[#34d399] transition-colors"></div>
          </div>

          <!-- Right: question list -->
          <div class="card flex-1 overflow-auto p-4" style="max-height: calc(100vh - 140px)" ref="rightCol">
            <div v-for="sec in sections" :key="sec.key" class="mb-6">
              <div class="text-xs font-semibold text-[var(--ink2)] mb-2">{{ sec.title }}</div>
              <div class="text-sm text-[var(--ink2)] mb-3" v-if="sec.description" v-html="sec.description"></div>

              <GapFillingSet
                v-if="sec.kind === 'gap'"
                :title="sec.title"
                :description="sec.description"
                :html="sec.content"
                :questions="sec.questions"
                :answers="store.answers"
                :is-current="isAnyOrderCurrent(sec.questions)"
                @answer="({questionId, value}) => store.setAnswer(questionId, value)"
              />

              <div v-else class="grid gap-3">
                <div
                  v-for="it in sec.items"
                  :key="it.question.id"
                  :ref="(el) => registerQuestionEl(it.question.order, el)"
                  @click="setCurrent(it.question.order)"
                >
                  <QuestionRenderer
                    :item="it"
                    :answer="store.answers[it.question.id]"
                    :is-current="store.currentOrder === it.question.order"
                    @update:answer="(v) => practiceMode ? practiceSetAnswer(it.question.id, v) : store.setAnswer(it.question.id, v)"
                    @jump-audio="onJumpAudio"
                  />

                  <!-- Practice: inline answer reveal -->
                  <div
                    v-if="practiceMode && getPracticeReveal(it)"
                    class="mt-1 overflow-hidden rounded-xl border text-[13px]"
                    :class="getPracticeReveal(it).ok
                      ? 'border-[#bbf7d0] bg-[#f0fdf4]'
                      : 'border-[#fecaca] bg-[#fef2f2]'"
                  >
                    <!-- Status row -->
                    <div
                      class="flex items-center gap-2 px-4 py-2.5 font-semibold"
                      :class="getPracticeReveal(it).ok ? 'text-[#059669]' : 'text-[#dc2626]'"
                    >
                      <svg v-if="getPracticeReveal(it).ok" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
                      <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                      {{ getPracticeReveal(it).ok ? 'Đúng!' : 'Sai' }}
                      <span
                        v-if="!getPracticeReveal(it).ok"
                        class="ml-1 font-normal text-[var(--ink2)]"
                      >Đáp án đúng: <strong class="text-[var(--ink)]">{{ getPracticeReveal(it).correctAnswer }}</strong></span>
                    </div>
                    <!-- Explanation -->
                    <div
                      v-if="getPracticeReveal(it).explain"
                      class="border-t px-4 py-2.5 text-[12px] leading-relaxed text-[var(--ink2)]"
                      :class="getPracticeReveal(it).ok ? 'border-[#bbf7d0]' : 'border-[#fecaca]'"
                    >
                      <span class="mr-1 font-semibold text-[var(--ink)]">Giải thích:</span>
                      {{ getPracticeReveal(it).explain }}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div class="mt-6 flex items-center justify-between gap-2">
              <button class="btn btn-secondary" @click="showExitConfirm = true">Thoát</button>
              <button class="btn btn-primary" @click="submit(false)">Nộp bài</button>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ExamHeader from '@/components/mock-tests/ExamHeader.vue'
import ExamAudioPlayer from '@/components/mock-tests/ExamAudioPlayer.vue'
import TranscriptPanel from '@/components/mock-tests/TranscriptPanel.vue'
import QuestionNavGrid from '@/components/mock-tests/QuestionNavGrid.vue'
import QuestionRenderer from '@/components/mock-tests/QuestionRenderer.vue'
import GapFillingSet from '@/components/mock-tests/GapFillingSet.vue'
import PracticeToolbar from '@/components/mock-tests/PracticeToolbar.vue'
import SpeakingPracticePanel from '@/components/mock-tests/SpeakingPracticePanel.vue'
import ReadingPassage from '@/components/reading/ReadingPassage.vue'
import ReadingToolbar from '@/components/reading/ReadingToolbar.vue'
import SpeakingChatbot from '@/components/speaking/SpeakingChatbot.vue'
import BandScoreRing from '@/components/speaking/BandScoreRing.vue'
import CircularScore from '@/components/speaking/CircularScore.vue'
import TranscriptHighlight from '@/components/speaking/TranscriptHighlight.vue'
import GrammarCard from '@/components/speaking/GrammarCard.vue'
import VocabCard from '@/components/speaking/VocabCard.vue'
import AudioPlayer from '@/components/speaking/AudioPlayer.vue'
import { useMockQuizStore } from '@/stores/mockQuiz.js'
import { usePracticeStore } from '@/stores/practice.js'
import { buildAudioSrc } from '@/utils/audio.js'
import { saveAnnotation } from '@/services/vocabularyService.js'
import { buildParagraphsFromVocabs, extractParagraphSpans, isListeningQuiz } from '@/utils/mockQuiz.js'
import { isCorrectAnswer, scoreQuiz } from '@/utils/scoring.js'
import { useTranscript } from '@/composables/useTranscript.js'
import apiClient from '@/api/client.js'
import { clearLanguageAnalysisCache } from '@/services/speakingAnalysisService.js'

const route = useRoute()
const router = useRouter()
const store = useMockQuizStore()
const practiceStore = usePracticeStore()
const practiceMode = computed(() => route.query.mode === 'practice')

// ─── Speaking evaluation + chatbot ───
const evaluating = ref(false)
const evalError  = ref(null)
const chatOpen   = ref(false)
const lastSpeakingEval       = ref(null)
const speakingEvalByQuestion = ref({})
const speakingAttemptId      = ref(`sp_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`)
const currentEvalQuestionId  = ref(null)  // tracks which exam-mode question is being evaluated

async function onEvaluateSpeaking({ blob, questionText, questionId }) {
  // Capture qid BEFORE any await to avoid race condition if the user
  // navigates to the next question while evaluation is still in-flight.
  const qid = String(
    questionId ?? currentSpeakingItem.value?.question?.id ?? ''
  )
  currentEvalQuestionId.value = qid || null

  evaluating.value = true
  evalError.value  = null
  try {
    const formData = new FormData()
    formData.append('file', blob, 'recording.webm')
    formData.append('question_text', questionText)
    formData.append('persist_result', 'true')
    formData.append('quiz_id', String(route.params.quizId || 'speaking'))
    formData.append('question_id', qid)
    formData.append('attempt_id', speakingAttemptId.value)

    // apiClient default Content-Type is application/json; delete it so the
    // browser can set multipart/form-data with the correct boundary automatically.
    // Override timeout: ML pipeline (Whisper + wav2vec2 + LLM) can take 60-120 s.
    clearLanguageAnalysisCache()

    const { data: result } = await apiClient.post('/speaking/evaluate', formData, {
      timeout: 120_000,
      transformRequest: [
        (data, headers) => {
          delete headers['Content-Type']
          delete headers['content-type']
          return data
        },
      ],
    })

    const audioUrl = URL.createObjectURL(blob)

    // Store result keyed by question ID (works for both practice and exam mode)
    const payload = { result, audioUrl, question: questionText, questionId: qid }
    lastSpeakingEval.value = payload
    if (qid) speakingEvalByQuestion.value[qid] = { ...payload }

    // Do NOT auto-advance — let the user review the result and click "Next" manually.
  } catch (err) {
    evalError.value = err.message || 'Evaluation failed. Please try again.'
  } finally {
    evaluating.value = false
  }
}

const questionEls = new Map()
const rightCol = ref(null)
const layoutEl  = ref(null)
const playerRef = ref(null)   // template ref to ExamAudioPlayer

const currentAudioTime = ref(0)
const seekTo = ref(null)

// ─── Exit confirmation ───
const showExitConfirm = ref(false)
function confirmExit() { showExitConfirm.value = false; router.push('/dashboard') }

const handleBeforeUnload = (e) => { e.preventDefault(); e.returnValue = '' }

// ─── Resizable layout ───
const leftWidth = ref(580)
let isResizing = false
let resizeStartX = 0
let resizeStartW = 0

function startResize(e) {
  isResizing = true
  resizeStartX = e.clientX
  resizeStartW = leftWidth.value
  document.body.style.userSelect = 'none'
  document.body.style.cursor = 'col-resize'
}
function onMouseMove(e) {
  if (!isResizing) return
  const delta = e.clientX - resizeStartX
  const containerW = layoutEl.value?.clientWidth || 1200
  leftWidth.value = Math.max(280, Math.min(containerW - 340, resizeStartW + delta))
}
function onMouseUp() {
  if (!isResizing) return
  isResizing = false
  document.body.style.userSelect = ''
  document.body.style.cursor = ''
}

const isListening = computed(() => isListeningQuiz(store.quiz))
const isReading   = computed(() => !isListening.value && !isSpeaking.value)
const isSpeaking  = computed(() => store.flat.some(x => String(x.questionSetType || '').toLowerCase() === 'speaking'))

// ── Speaking practice: one question at a time ─────────────────────────────
const speakingFlat = computed(() =>
  store.flat.filter((x) => {
    const q = x.question || {}
    const t1 = String(x.questionSetType || '').toLowerCase()
    const t2 = String(q.question_type || '').toLowerCase()
    const t3 = String(q.type || '').toLowerCase()
    return t1 === 'speaking' || t2 === 'speaking' || t3 === 'speaking'
  })
)
const speakingPracticeIndex = ref(0)
const currentSpeakingIdx = computed(() => {
  const max = Math.max(0, speakingFlat.value.length - 1)
  return Math.min(Math.max(0, speakingPracticeIndex.value), max)
})
const currentSpeakingItem = computed(() => speakingFlat.value[currentSpeakingIdx.value] ?? null)
const currentSpeakingEval = computed(() => {
  const qid = String(currentSpeakingItem.value?.question?.id ?? '')
  return qid ? speakingEvalByQuestion.value[qid] : null
})

function prevSpeaking() {
  const idx = currentSpeakingIdx.value - 1
  if (idx < 0) return
  speakingPracticeIndex.value = idx
  const prev = speakingFlat.value[idx]
  if (prev?.question?.order != null) goToOrder(prev.question.order)
}
function nextSpeaking() {
  const idx = currentSpeakingIdx.value + 1
  if (idx >= speakingFlat.value.length) return
  speakingPracticeIndex.value = idx
  const next = speakingFlat.value[idx]
  if (next?.question?.order != null) goToOrder(next.question.order)
}

// The text of the currently-active speaking question (fed to chatbot)
const speakingCurrentQuestion = computed(() => {
  const item = practiceMode.value ? currentSpeakingItem.value : store.currentItem
  if (!item) return ''
  const q = item.question || {}
  return q.text || q.title || q.content || ''
})

const quizTitle = computed(() => store.quiz?.title || `Quiz #${route.params.quizId}`)
const quizSubtitle = computed(() => {
  const skill = isListening.value ? 'Listening' : isSpeaking.value ? 'Speaking' : 'Reading'
  return `${skill} · ${store.totalQuestions} câu`
})

const navQuestions = computed(() => store.flat.map((x) => ({ order: x.question.order, id: x.question.id })))

const navParts = computed(() => {
  const parts = store.quiz?.parts || []
  return parts.map((p, i) => {
    const qs = store.flat.filter(x => x.partId === p.id).map(x => ({ order: x.question.order, id: x.question.id }))
    const label = `Part ${p.passage || (i + 1)}`
    return { id: p.id, label, questions: qs }
  })
})

const activePart = computed(() => {
  const pid = store.currentItem?.partId
  return store.quiz?.parts?.find((p) => p.id === pid) || store.quiz?.parts?.[0] || null
})

const activeParagraphs = computed(() => buildParagraphsFromVocabs(activePart.value?.vocabs || []))

const audioSrc = computed(() => buildAudioSrc(activePart.value?.file_id))

// ── transcript composable ────────────────────────────────────────────────
const transcript = useTranscript(activeParagraphs, currentAudioTime)

const currentLocateInfo = computed(() => store.currentItem?.question?.locate_info)
const highlightSpans = computed(() => extractParagraphSpans(currentLocateInfo.value))

function isHighlightedParagraph(paragraph) {
  if (!highlightSpans.value.length) return false
  return highlightSpans.value.some((r) => paragraph >= r.startParagraph && paragraph <= r.endParagraph)
}

function registerQuestionEl(order, el) {
  if (!order || !el) return
  const dom = el?.$el ?? el
  questionEls.set(order, dom)
}

function scrollToOrder(order) {
  const el = questionEls.get(order)
  if (!el) return
  if (typeof el.scrollIntoView === 'function') el.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function setCurrent(order) {
  store.gotoOrder(order)
}

async function goToOrder(order) {
  store.gotoOrder(order)
  await nextTick()
  scrollToOrder(order)
}

function isAnyOrderCurrent(questions) {
  const orders = new Set((questions || []).map((q) => q.order))
  return orders.has(store.currentOrder)
}

/**
 * Called when the user clicks the green play button on a question.
 * @param {{ time: number, locateInfo: object }} payload
 */
function onJumpAudio({ time, locateInfo } = {}) {
  if (Number.isFinite(time)) {
    playerRef.value?.seekAndPlay(time)
  }
  if (locateInfo) {
    transcript.activateLocateInfo(locateInfo)
  }
}

const sections = computed(() => {
  const parts = store.quiz?.parts || []
  const out = []
  for (const part of parts) {
    for (const qs of part.question_sets || []) {
      const key = `${part.id}_${qs.id}`
      if (qs.question_type === 'GAP_FILLING') {
        out.push({
          key,
          kind: 'gap',
          title: qs.title || `Part ${part.passage}`,
          description: qs.description || '',
          content: qs.content || '',
          questions: (qs.questions || []).map((q) => ({ id: q.id, sort: q.sort, order: q.order })),
        })
        continue
      }
      const items = store.flat.filter((x) => x.partId === part.id && x.questionSetId === qs.id)
      out.push({
        key,
        kind: 'items',
        title: qs.title || `Part ${part.passage}`,
        description: qs.description || '',
        items,
      })
    }
  }
  return out
})

// ── Practice: per-question answer reveal ─────────────────────────────────────
// Keyed by String(question.id) → true once the user has selected any answer
const practiceRevealedIds = ref(new Set())

function revealAnswer(questionId) {
  if (!practiceMode.value) return
  const next = new Set(practiceRevealedIds.value)
  next.add(String(questionId))
  practiceRevealedIds.value = next
}

function practiceSetAnswer(questionId, value) {
  store.setAnswer(questionId, value)
  revealAnswer(questionId)
}

function getPracticeReveal(item) {
  const qid  = String(item.question?.id ?? '')
  if (!practiceRevealedIds.value.has(qid)) return null
  const q    = item.question || {}
  const userAnswer = store.answers[q.id]
  const ok   = isCorrectAnswer({ question: q, userAnswer })
  // Build display for correct answer
  const ca   = q.correct_answers?.length
    ? q.correct_answers.join(' / ')
    : (q.correct_answer ?? '—')
  return { ok, correctAnswer: ca, explain: q.explain || '', userAnswer }
}

// ── Reading practice tools state ──────────────────────────────────────────────
const readingPassageRef        = ref(null)
const practiceActiveTool       = ref(null)
const practiceHighlightColor   = ref('yellow')
const practiceNote             = ref('')
const practiceSessionId        = ref(`session_${Date.now()}_${Math.random().toString(36).slice(2,7)}`)
const practiceHighlights       = ref([])

function onHighlightsChanged(hs) {
  practiceHighlights.value = hs
}

// Listen to toolbar events
function onToolbarToolChanged({ tool, color }) {
  practiceActiveTool.value     = tool
  practiceHighlightColor.value = color || 'yellow'
}

async function _persistAnnotation() {
  if (!practiceMode.value) return
  try {
    await saveAnnotation(practiceSessionId.value, {
      session_id: practiceSessionId.value,
      quiz_id:    String(route.params.quizId || ''),
      highlights: practiceHighlights.value,
      note:       practiceNote.value,
    })
  } catch { /* non-critical */ }
}

async function submit(auto) {
  // Save annotations before submitting (fire-and-forget)
  await _persistAnnotation()

  if (isSpeaking.value) {
    const hasEvaluations = Object.keys(speakingEvalByQuestion.value || {}).length > 0
    if (!hasEvaluations) {
      evalError.value = 'Bạn cần đánh giá ít nhất 1 câu speaking trước khi nộp.'
      return
    }
    try {
      const { data } = await apiClient.get('/speaking/attempt-summary', {
        params: { quiz_id: String(route.params.quizId || 'speaking'), attempt_id: speakingAttemptId.value },
      })
      router.push({
        path: '/speaking/result',
        state: {
          summary: data,
          question: `Speaking quiz #${route.params.quizId}`,
          mode: 'attempt-summary',
        },
      })
      return
    } catch (err) {
      evalError.value = err?.response?.data?.detail || err?.message || 'Không tải được tổng kết speaking.'
      return
    }
  }

  store.submit({ auto })
  const currentSession = practiceStore.currentSession
  const sessionQuizId = currentSession?.quiz?.id
  const routeQuizId = Number(route.params.quizId)
  const subject = isListening.value ? 'listening' : 'reading'

  // Real backend flow when this quiz was started via /practice/*/session.
  if (currentSession?.session_id && Number(sessionQuizId) === routeQuizId) {
    const normalizedAnswers = Object.entries(store.answers || {}).reduce((acc, [k, v]) => {
      acc[String(k)] = v
      return acc
    }, {})
    const submitted = await practiceStore.submitSession(
      subject,
      currentSession.session_id,
      normalizedAnswers
    )
    if (submitted) {
      // Pass annotation session id so Review page can load it
      router.push({
        path: `/results/${currentSession.session_id}`,
        query: { annotationSession: practiceSessionId.value },
      })
      return
    }
  }

  // Fallback for legacy mock-test flow.
  const scored = scoreQuiz({ quiz: store.quiz, flat: store.flat, answers: store.answers })
  store.result = {
    quizId: routeQuizId,
    title: store.quiz?.title,
    correct: scored.correct,
    total: scored.total,
    estimatedBand: scored.estimatedBand,
    detailed: scored.detailed,
    answers: store.answers,
    annotationSession: practiceSessionId.value,
  }
  router.push(`/quiz/${route.params.quizId}/result`)
}

watch(
  () => store.remainingSeconds,
  (s) => {
    if (s === 0 && store.quiz && !store.result) submit(true)
  }
)

watch(
  [() => speakingFlat.value, () => store.currentOrder, () => practiceMode.value],
  () => {
    if (!practiceMode.value || !speakingFlat.value.length) return
    const idx = speakingFlat.value.findIndex(
      (x) => String(x.question?.order) === String(store.currentOrder)
    )
    if (idx >= 0) speakingPracticeIndex.value = idx
  },
  { immediate: true, deep: false }
)

onMounted(async () => {
  await store.loadQuiz(route.params.quizId)
  await nextTick()
  scrollToOrder(store.currentOrder)
  window.addEventListener('beforeunload', handleBeforeUnload)
  window.addEventListener('mousemove', onMouseMove)
  window.addEventListener('mouseup', onMouseUp)
})

onUnmounted(() => {
  store.stopTimer()
  window.removeEventListener('beforeunload', handleBeforeUnload)
  window.removeEventListener('mousemove', onMouseMove)
  window.removeEventListener('mouseup', onMouseUp)
})
</script>

<style scoped>
.slide-enter-active, .slide-leave-active { transition: all 0.2s ease; }
.slide-enter-from, .slide-leave-to { opacity: 0; transform: translateX(20px); }

.reading-passage {
  max-height: 420px;
  overflow: auto;
  padding-right: 8px;
}
.reading-paragraph {
  display: flex;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid transparent;
  margin-bottom: 10px;
  background: var(--surface);
}
.reading-paragraph.is-highlight {
  border-color: rgba(124, 106, 247, 0.35);
  background: rgba(124, 106, 247, 0.08);
}
.para-tag {
  min-width: 28px;
  height: 22px;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  color: var(--ink2);
  border: 1px solid var(--border2);
  background: var(--bg);
}
</style>

