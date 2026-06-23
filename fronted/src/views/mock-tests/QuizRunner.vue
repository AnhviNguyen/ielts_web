<template>
  <div class="quiz-runner min-h-screen bg-[var(--bg)]">
    <!-- Exit confirm dialog -->
    <Teleport to="body">
      <div v-if="showExitConfirm" class="fixed inset-0 z-[500] flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-black/40" @click="showExitConfirm = false"></div>
        <div class="relative z-10 w-full max-w-sm rounded-xl border border-[var(--border)] bg-[var(--bg-surface)] p-6 shadow-xl">
          <div class="mb-1 text-[14px] font-bold text-[var(--ink)]">Thoát bài thi?</div>
          <p class="mb-5 text-[13px] text-[var(--ink3)]">Tiến trình làm bài sẽ không được lưu. Bạn có chắc muốn thoát?</p>
          <div class="flex justify-end gap-2">
            <button class="ct-btn text-[12px]" @click="showExitConfirm = false">Tiếp tục</button>
            <button class="ct-btn text-[12px]" style="border-color:#e11d48;color:#e11d48" @click="confirmExit">Thoát</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Speaking submit warning — visible when submitting from header or footer -->
    <Teleport to="body">
      <Transition name="toast">
        <div
          v-if="isSpeaking && evalError"
          class="fixed left-1/2 top-20 z-[700] w-[min(440px,calc(100%-2rem))] -translate-x-1/2 rounded-xl border border-[var(--rose-l)] bg-[var(--rose-bg)] px-5 py-3.5 text-center text-[13px] font-semibold text-[var(--rose)] shadow-xl"
          role="alert"
        >
          {{ evalError }}
        </div>
      </Transition>
    </Teleport>

    <!-- Speaking: toolbar cố định bên trái -->
    <PracticeToolbar
      v-if="practiceMode && isSpeaking"
      :practice-mode="practiceMode"
      v-model:model-note="practiceNote"
      @tool-changed="onToolbarToolChanged"
    />
    <!-- Reading / Listening practice: 3 công cụ dọc bên trái, ngoài vùng đề IELTS -->
    <ReadingToolbar
      v-if="practiceMode && !isSpeaking"
      floating
      v-model:model-note="practiceNote"
      @tool-changed="onToolbarToolChanged"
    />
    <ExamHeader
      :title="quizTitle"
      :subtitle="quizSubtitle"
      :remaining-seconds="store.remainingSeconds"
      :show-back="!isSpeaking"
      @back="showExitConfirm = true"
      @submit="submit(false)"
    />

    <div class="exam-container py-5 sm:py-6" data-tour="quiz-content">
      <AppLoading v-if="store.loading" message="Đang tải đề..." />
      <div v-else-if="!store.quiz" class="card p-6 text-center">
        <div class="text-lg font-semibold mb-2">Quiz not found</div>
        <RouterLink to="/dashboard" class="btn btn-primary">Về trang chủ</RouterLink>
      </div>

      <template v-else>
        <!-- Speaking evaluation overlay -->
        <Teleport to="body">
          <div v-if="evaluating" class="fixed inset-0 z-[600] flex items-center justify-center bg-black/60">
            <div class="flex flex-col items-center gap-4 rounded-2xl bg-[var(--bg-surface)] p-8 text-[var(--ink)] shadow-2xl">
              <div class="h-10 w-10 animate-spin rounded-full border-4 border-[var(--spotify-green)] border-t-transparent"/>
              <p class="text-sm font-semibold">Đang phân tích bài nói…</p>
              <p class="text-[11px] text-[var(--ink3)]">Pronunciation · Transcription · AI Feedback</p>
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
                      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--spotify-green)" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
                      Kết quả câu {{ currentSpeakingIdx + 1 }}
                    </div>
                    <div class="flex gap-2">
                      <button
                        class="ct-btn px-3 py-1.5 text-[12px]"
                        @click="router.push({ path: '/speaking/result', state: speakingResultState(currentSpeakingEval) })"
                      >
                        Xem chi tiết
                      </button>
                      <button
                        v-if="currentSpeakingIdx < speakingFlat.length - 1"
                        class="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-[12px] font-semibold text-white"
                        style="background:var(--spotify-green)"
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
                      <div class="mb-3 text-xs font-bold uppercase tracking-wider text-[var(--spotify-green)]">Strengths</div>
                      <ul class="space-y-1.5">
                        <li
                          v-for="(s, i) in currentSpeakingEval.result.strengths || []"
                          :key="`st_${i}`"
                          class="flex items-start gap-2 text-sm text-[var(--ink)]"
                        >
                          <span class="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[var(--spotify-green)]"/>
                          {{ s }}
                        </li>
                        <li v-if="!(currentSpeakingEval.result.strengths || []).length" class="text-sm text-[var(--ink3)]">—</li>
                      </ul>
                    </div>
                    <div class="card p-5">
                      <div class="mb-3 text-xs font-bold uppercase tracking-wider text-[var(--amber)]">Improvements</div>
                      <ul class="space-y-1.5">
                        <li
                          v-for="(imp, i) in currentSpeakingEval.result.improvements || []"
                          :key="`im_${i}`"
                          class="flex items-start gap-2 text-sm text-[var(--ink)]"
                        >
                          <span class="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[var(--amber)]"/>
                          {{ imp }}
                        </li>
                        <li v-if="!(currentSpeakingEval.result.improvements || []).length" class="text-sm text-[var(--ink3)]">—</li>
                      </ul>
                    </div>
                  </div>

                  <div v-if="speakingOverallComment" class="card border-l-4 border-l-[var(--spotify-green)] p-5">
                    <div class="mb-2 text-xs font-bold uppercase tracking-wider text-[var(--spotify-green)]">Nhận xét tổng quan</div>
                    <p class="text-sm leading-relaxed text-[var(--ink)]">{{ speakingOverallComment }}</p>
                  </div>
              </div>
            </template>
          </SpeakingPracticePanel>

          <div v-if="practiceMode && evalError" class="mx-auto mt-4 max-w-3xl rounded-lg border border-[var(--rose-l)] bg-[var(--rose-bg)] px-4 py-2 text-xs text-[var(--rose)]">
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
                  ? 'border-[var(--spotify-green)] bg-[var(--green-bg)] text-[var(--spotify-green)]'
                  : 'border-[var(--border2)] bg-[var(--bg-surface)] text-[var(--ink2)] hover:border-[var(--spotify-green)] hover:text-[var(--spotify-green)]'"
              >
                <svg width="11" height="11" viewBox="0 0 24 24" fill="currentColor"><path d="M20 2H4a2 2 0 0 0-2 2v18l4-4h14a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2z"/></svg>
                Need help? Click here.
              </button>
            </div>

            <div
              class="mx-auto flex max-w-7xl flex-col gap-0 overflow-hidden rounded-2xl border border-[var(--border)] bg-[var(--bg-surface)] lg:flex-row"
            >
              <div class="min-w-0 flex-1 p-4 sm:p-5 lg:p-6" :class="chatOpen ? 'lg:border-r lg:border-[var(--border)]' : ''">
                <div v-for="sec in sections" :key="sec.key" class="mb-6">
                  <div class="mb-2 text-xs font-semibold text-[var(--ink2)]">{{ sec.title }}</div>
                  <div class="mb-3 text-sm text-[var(--ink2)]" v-if="sec.description" v-html="sanitizeQuizHtml(sec.description)"></div>
                  <div class="grid gap-3">
                    <QuizImage v-if="sec.image" :uuid="sec.image" />
                    <div
                      v-for="it in sec.items || []"
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
                        class="mt-3 overflow-hidden rounded-xl border border-[var(--spotify-green)]/30 bg-[var(--green-bg)]"
                      >
                        <!-- Result header -->
                        <div class="flex items-center justify-between border-b border-[var(--spotify-green)]/30 px-4 py-2.5">
                          <div class="flex items-center gap-2 text-[12px] font-semibold text-[var(--spotify-green-dark)]">
                            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
                            Kết quả câu {{ it.question.order }}
                          </div>
                          <button
                            class="text-[11px] text-[var(--spotify-green-dark)] underline hover:no-underline"
                            @click.stop="router.push({ path: '/speaking/result', state: speakingResultState(speakingEvalByQuestion[String(it.question.id)]) })"
                          >
                            Xem chi tiết
                          </button>
                        </div>
                        <!-- Score summary row -->
                        <div class="grid grid-cols-2 divide-x divide-[var(--spotify-green)]/30 sm:grid-cols-4">
                          <div class="px-4 py-3 text-center">
                            <div class="text-[11px] text-[var(--ink3)]">Band</div>
                            <div class="text-lg font-bold text-[var(--spotify-green-dark)]">
                              {{ Number(speakingEvalByQuestion[String(it.question.id)]?.result?.band_estimate || 0).toFixed(1) }}
                            </div>
                          </div>
                          <div class="px-4 py-3 text-center">
                            <div class="text-[11px] text-[var(--ink3)]">Grammar</div>
                            <div class="text-base font-semibold text-[var(--ink)]">
                              {{ Number(speakingEvalByQuestion[String(it.question.id)]?.result?.grammar?.score || 0).toFixed(1) }}<span class="text-[10px] text-[var(--ink3)]">/9</span>
                            </div>
                          </div>
                          <div class="px-4 py-3 text-center">
                            <div class="text-[11px] text-[var(--ink3)]">Vocab</div>
                            <div class="text-base font-semibold text-[var(--ink)]">
                              {{ Number(speakingEvalByQuestion[String(it.question.id)]?.result?.vocabulary?.score || 0).toFixed(1) }}<span class="text-[10px] text-[var(--ink3)]">/9</span>
                            </div>
                          </div>
                          <div class="px-4 py-3 text-center">
                            <div class="text-[11px] text-[var(--ink3)]">Pron.</div>
                            <div class="text-base font-semibold text-[var(--ink)]">
                              {{ Number(speakingEvalByQuestion[String(it.question.id)]?.result?.pronunciation?.total || 0).toFixed(1) }}<span class="text-[10px] text-[var(--ink3)]">/10</span>
                            </div>
                          </div>
                        </div>
                        <!-- Transcript snippet -->
                        <div
                          v-if="speakingEvalByQuestion[String(it.question.id)]?.result?.transcript"
                          class="border-t border-[var(--spotify-green)]/30 px-4 py-2.5 text-[12px] text-[var(--ink2)]"
                        >
                          <span class="mr-1 font-semibold text-[var(--spotify-green-dark)]">Bài nói:</span>
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

                <div v-if="evalError" class="mt-3 rounded-lg border border-[var(--rose-l)] bg-[var(--rose-bg)] px-4 py-2 text-xs text-[var(--rose)]">
                  {{ evalError }}
                </div>
              </div>

              <Transition name="slide">
                <SpeakingChatbot
                  v-if="chatOpen"
                  class="w-full shrink-0 lg:w-80"
                  :question-text="speakingCurrentQuestion"
                  @close="chatOpen = false"
                />
              </Transition>
            </div>
          </template>
        </div>

        <!-- Resizable two-panel layout (Reading / Listening) -->
        <div v-else class="flex flex-col gap-5 lg:flex-row lg:gap-6" ref="layoutEl">
          <!-- Left panel -->
          <div class="quiz-split-left flex min-w-0 w-full flex-col gap-4 lg:shrink-0" :style="splitLeftStyle">
            <template v-if="isListening">
              <ExamAudioPlayer
                ref="playerRef"
                :src="audioSrc"
                :title="activePart?.title || 'Listening'"
                :subtitle="`File: ${activePart?.file_id || '—'}`"
                :seek-to="seekTo"
                @time="onAudioTime"
              />
              <!-- Practice: highlight / ghi chú / tra từ giống Reading -->
              <div v-if="practiceMode" class="card overflow-hidden">
                <div class="border-b border-[var(--border)] px-4 py-2.5 text-xs font-semibold text-[var(--ink2)]">{{ activePart?.title }}</div>
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
                @seek="onTranscriptSeek"
              />
            </template>

            <template v-else>
              <div class="card overflow-hidden">
                <div
                  class="border-b border-[var(--border)] px-4 py-2.5 text-xs font-semibold text-[var(--ink2)]"
                  :class="practiceMode ? '' : 'pt-3'"
                >{{ activePart?.title }}</div>
                <div class="overflow-y-auto p-4" style="max-height: calc(100vh - 220px)">
                  <!-- Passage title from parts[].content (e.g. <h2> heading) -->
                  <div
                    v-if="activePart?.content"
                    class="passage-title mb-3"
                    v-html="sanitizeQuizHtml(activePart.content)"
                  />
                  <!-- Instruction (e.g. "You should spend about 20 minutes on Q1-13") -->
                  <div
                    v-if="activePartInstruction"
                    class="mb-3 text-xs italic text-[var(--ink3)]"
                    v-html="sanitizeQuizHtml(activePartInstruction)"
                  />
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
                    <template v-for="p in activeParagraphs" :key="p.paragraph">
                      <div v-if="p.isEmpty" class="h-3" />
                      <div
                        v-else
                        class="reading-paragraph"
                        :class="isHighlightedParagraph(p.paragraph) ? 'is-highlight' : ''"
                      >
                        <span class="para-tag">{{ p.paragraph }}</span>
                        <span>{{ p.text }}</span>
                      </div>
                    </template>
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
            v-show="isLgUp"
            class="hidden w-2 cursor-col-resize items-center justify-center group lg:flex"
            @mousedown.prevent="startResize"
          >
            <div class="h-12 w-0.5 rounded-full bg-[var(--border2)] group-hover:bg-[var(--spotify-green)] transition-colors"></div>
          </div>

          <!-- Right: question list -->
          <div class="card flex-1 overflow-auto p-4" style="max-height: calc(100vh - 140px)" ref="rightCol">
            <div v-for="sec in sections" :key="sec.key" class="mb-6">
              <div class="text-xs font-semibold text-[var(--ink2)] mb-2">{{ sec.title }}</div>
              <div class="text-sm text-[var(--ink2)] mb-3" v-if="sec.description" v-html="sanitizeQuizHtml(sec.description)"></div>

              <!-- GAP_FILLING: HTML with inline blanks -->
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

              <!-- MATCHING_*: drag-and-drop option chips to question slots -->
              <MatchingSet
                v-else-if="sec.kind === 'matching'"
                :title="sec.title"
                :description="sec.description"
                :options="sec.options"
                :questions="sec.questions"
                :answers="matchingAnswers(sec)"
                :allow-reuse="sec.allowReuse"
                :is-current="isMatchingSectionCurrent(sec)"
                @answer="onMatchingAnswer"
              />

              <!-- Default items (TABLE_SELECTION with image, SINGLE_CHOICE, etc.) -->
              <div v-else class="grid gap-3">
                <!-- Optional question-set image (map/diagram for MAP_DIAGRAM_LABEL) -->
                <QuizImage v-if="sec.image" :uuid="sec.image" />

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
                      ? 'border-[var(--spotify-green)]/30 bg-[var(--green-bg)]'
                      : 'border-[var(--rose-l)] bg-[var(--rose-bg)]'"
                  >
                    <!-- Status row -->
                    <div
                      class="flex items-center gap-2 px-4 py-2.5 font-semibold"
                      :class="getPracticeReveal(it).ok ? 'text-[var(--spotify-green-dark)]' : 'text-[var(--rose)]'"
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
                      :class="getPracticeReveal(it).ok ? 'border-[var(--spotify-green)]/30' : 'border-[var(--rose-l)]'"
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
import AppLoading from '@/components/ui/AppLoading.vue'
import ExamHeader from '@/components/mock-tests/ExamHeader.vue'
import ExamAudioPlayer from '@/components/mock-tests/ExamAudioPlayer.vue'
import TranscriptPanel from '@/components/mock-tests/TranscriptPanel.vue'
import QuestionNavGrid from '@/components/mock-tests/QuestionNavGrid.vue'
import QuestionRenderer from '@/components/mock-tests/QuestionRenderer.vue'
import GapFillingSet from '@/components/mock-tests/GapFillingSet.vue'
import MatchingSet from '@/components/mock-tests/MatchingSet.vue'
import QuizImage from '@/components/mock-tests/QuizImage.vue'
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
import { useFullExamStore } from '@/stores/fullExam.js'
import { breakRoute, nextStage, stageRoute } from '@/utils/fullExamNav.js'
import { partAudioSrc } from '@/utils/audio.js'
import { saveAnnotation } from '@/services/vocabularyService.js'
import { buildParagraphsFromVocabs, extractParagraphSpans, isListeningQuiz } from '@/utils/mockQuiz.js'
import { useTranscript } from '@/composables/useTranscript.js'
import { useMediaQuery } from '@/composables/useMediaQuery.js'
import apiClient from '@/api/client.js'
import { clearLanguageAnalysisCache } from '@/services/speakingAnalysisService.js'
import { pollTaskResult } from '@/utils/taskPolling.js'
import { speakingResultState } from '@/utils/speakingResultNav.js'
import { sanitizeHtml, sanitizeQuizHtml } from '@/utils/sanitizeHtml.js'

const route = useRoute()
const router = useRouter()
const store = useMockQuizStore()
const practiceStore = usePracticeStore()
const fullExamStore = useFullExamStore()
const practiceMode = computed(() => route.query.mode === 'practice')
const isFullExam = computed(() => route.query.fullExam === '1' && route.query.session)
const fullExamStage = computed(() => route.query.stage || '')

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

  // Exam mode: pause countdown while AI evaluates (don't waste exam time waiting)
  const shouldPauseTimer = isSpeaking.value && !practiceMode.value
  if (shouldPauseTimer) store.pauseTimer()

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

    const { data: evalResponse } = await apiClient.post('/speaking/evaluate', formData, {
      timeout: 120_000,
      transformRequest: [
        (data, headers) => {
          delete headers['Content-Type']
          delete headers['content-type']
          return data
        },
      ],
    })

    let result = evalResponse
    if (evalResponse?.task_id) {
      result = await pollTaskResult(`/speaking/evaluate/result/${evalResponse.task_id}`, {
        timeoutMs: 180_000,
      })
    }

    const audioUrl = URL.createObjectURL(blob)

    // Store result keyed by question ID (works for both practice and exam mode)
    const payload = { result, audioUrl, question: questionText, questionId: qid }
    lastSpeakingEval.value = payload
    if (qid) speakingEvalByQuestion.value[qid] = { ...payload }

    // Do NOT auto-advance — let the user review the result and click "Next" manually.
  } catch (err) {
    evalError.value = err?.response?.data?.detail || err.message || 'Đánh giá thất bại, vui lòng thử lại.'
  } finally {
    evaluating.value = false
    if (shouldPauseTimer) store.resumeTimer()
  }
}

const questionEls = new Map()
const rightCol = ref(null)
const layoutEl  = ref(null)
const playerRef = ref(null)   // template ref to ExamAudioPlayer

const currentAudioTime = ref(0)
const seekTo = ref(null)

function onAudioTime(t) {
  currentAudioTime.value = t
}

// ─── Exit confirmation ───
const showExitConfirm = ref(false)
function confirmExit() { showExitConfirm.value = false; router.push('/dashboard') }

const handleBeforeUnload = (e) => { e.preventDefault(); e.returnValue = '' }

// ─── Resizable layout ───
const isLgUp = useMediaQuery('(min-width: 1024px)')
const leftWidth = ref(580)
const splitLeftStyle = computed(() => {
  if (!isLgUp.value) return {}
  return { flex: `0 0 ${leftWidth.value}px`, width: `${leftWidth.value}px` }
})
let isResizing = false
let resizeStartX = 0
let resizeStartW = 0

function startResize(e) {
  if (!isLgUp.value) return
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

const speakingOverallComment = computed(() => {
  const c = (currentSpeakingEval.value?.result?.overall_comment || '').trim()
  if (!c) return ''
  if (/^llm analysis unavailable\.?$/i.test(c)) return ''
  return c
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

// Instruction text for current part (e.g. "You should spend 20 minutes on Q1-13...")
// Replace {start_question} and {end_question} with actual first/last question order numbers.
const activePartInstruction = computed(() => {
  const raw = activePart.value?.instruction?.content
  if (!raw) return ''
  const partQuestions = store.flat.filter((x) => x.partId === activePart.value?.id)
  if (!partQuestions.length) return raw
  const orders = partQuestions.map((x) => x.question.order).filter(Number.isFinite)
  const start = Math.min(...orders)
  const end = Math.max(...orders)
  return raw.replace(/\{start_question\}/g, String(start)).replace(/\{end_question\}/g, String(end))
})

const audioSrc = computed(() => partAudioSrc(activePart.value))

// ── transcript composable ────────────────────────────────────────────────
const transcript = useTranscript(activeParagraphs, currentAudioTime)

function onTranscriptSeek(t) {
  seekTo.value = t
  transcript.clearForced()
}

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

/** Question set types that use drag-and-drop matching instead of per-question select */
const _MATCHING_TYPES = new Set(['MATCHING_HEADINGS', 'MATCHING_FEATURES', 'MATCHING_ENDINGS'])

const sections = computed(() => {
  const parts = store.quiz?.parts || []
  const out = []
  for (const part of parts) {
    for (const qs of part.question_sets || []) {
      const key = `${part.id}_${qs.id}`
      const qt = String(qs.question_type || '').toUpperCase()

      if (qt === 'GAP_FILLING') {
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

      if (_MATCHING_TYPES.has(qt)) {
        out.push({
          key,
          kind: 'matching',
          title: qs.title || `Part ${part.passage}`,
          description: qs.description || '',
          options: qs.options || [],
          allowReuse: qs.allow_reuse || false,
          questions: (qs.questions || []).map((q) => ({
            id: q.id,
            order: q.order,
            sort: q.sort,
            text: q.text || q.title || '',
            locateInfo: q.locate_info,
            matchingParagraph: q.matching_heading_paragraph,
          })),
          partId: part.id,
          questionSetId: qs.id,
        })
        continue
      }

      const items = store.flat.filter((x) => x.partId === part.id && x.questionSetId === qs.id)
      out.push({
        key,
        kind: 'items',
        title: qs.title || `Part ${part.passage}`,
        description: qs.description || '',
        image: qs.image || '',
        items,
      })
    }
  }
  return out
})

/** Collect answers for a matching section as {questionId: optionKey} */
function matchingAnswers(sec) {
  const out = {}
  for (const q of sec.questions || []) {
    out[q.id] = store.answers[q.id] || ''
  }
  return out
}

/** Check if any question in a matching section is the current one */
function isMatchingSectionCurrent(sec) {
  const orders = new Set((sec.questions || []).map((q) => q.order))
  return orders.has(store.currentOrder)
}

function onMatchingAnswer({ questionId, value }) {
  store.setAnswer(questionId, value || '')
}

// ── Practice: per-question answer reveal (server-side) ───────────────────────
const practiceRevealedIds = ref(new Set())
const practiceRevealCache = ref({})

async function revealAnswer(questionId) {
  if (!practiceMode.value) return
  const qid = String(questionId)
  if (practiceRevealedIds.value.has(qid)) return
  const sessionId = practiceStore.currentSession?.session_id
  if (!sessionId) return
  const res = await practiceStore.checkAnswer(sessionId, questionId, store.answers[questionId])
  if (!res) return
  practiceRevealCache.value = {
    ...practiceRevealCache.value,
    [qid]: {
      ok: res.is_correct,
      correctAnswer: res.correct_answers?.length
        ? res.correct_answers.join(' / ')
        : (res.correct_answer ?? '—'),
      explain: res.explain || '',
      userAnswer: res.user_answer,
    },
  }
  const next = new Set(practiceRevealedIds.value)
  next.add(qid)
  practiceRevealedIds.value = next
}

function practiceSetAnswer(questionId, value) {
  store.setAnswer(questionId, value)
  void revealAnswer(questionId)
}

function getPracticeReveal(item) {
  const qid = String(item.question?.id ?? '')
  if (!practiceRevealedIds.value.has(qid)) return null
  return practiceRevealCache.value[qid] || null
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

function _advanceFullExam(payload) {
  const sess = fullExamStore.getSession()
  if (!sess || route.query.session !== sess.sessionId) return false
  const stage = fullExamStage.value || (isSpeaking.value ? 'speaking' : isListening.value ? 'listening' : 'reading')
  fullExamStore.recordStageResult(stage, payload)
  router.push(breakRoute(sess, stage))
  return true
}

async function submit(auto) {
  // Save annotations before submitting (fire-and-forget)
  await _persistAnnotation()

  if (isSpeaking.value) {
    const hasEvaluations = Object.keys(speakingEvalByQuestion.value || {}).length > 0
    if (!hasEvaluations) {
      evalError.value = 'Bạn cần đánh giá ít nhất 1 bài speaking trước khi nộp.'
      window.scrollTo({ top: 0, behavior: 'smooth' })
      return
    }
    try {
      const { data } = await apiClient.get('/speaking/attempt-summary', {
        params: { quiz_id: String(route.params.quizId || 'speaking'), attempt_id: speakingAttemptId.value },
      })
      if (isFullExam.value) {
        if (_advanceFullExam({
          band: data?.average?.band_estimate,
          summary: data?.average || {},
          items: data?.items || [],
          attempt_id: data?.attempt_id,
        })) return
      }
      router.push({
        path: '/speaking/result',
        state: speakingResultState({
          summary: data,
          question: `Speaking quiz #${route.params.quizId}`,
          mode: 'attempt-summary',
        }),
      })
      return
    } catch (err) {
      evalError.value = err?.response?.data?.detail || err?.message || 'Không tải được tổng kết speaking.'
      return
    }
  }

  store.submit({ auto })
  let currentSession = practiceStore.currentSession
  const routeQuizId = Number(route.params.quizId)
  const subject = isListening.value ? 'listening' : 'reading'

  if (!currentSession?.session_id || Number(currentSession?.quiz?.id) !== routeQuizId) {
    currentSession = await practiceStore.startSession(subject, routeQuizId)
  }

  if (currentSession?.session_id && Number(currentSession?.quiz?.id) === routeQuizId) {
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
      if (isFullExam.value) {
        if (_advanceFullExam({
          correct: submitted.score,
          total: submitted.total_questions,
          estimatedBand: submitted.estimated_band,
          band: submitted.estimated_band,
        })) return
      }
      router.push({
        path: `/results/${currentSession.session_id}`,
        query: { annotationSession: practiceSessionId.value },
      })
      return
    }
  }

  evalError.value = 'Không thể nộp bài. Vui lòng tải lại trang và thử lại.'
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
  try {
    const qid = Number(route.params.quizId)
    await store.loadQuiz(route.params.quizId)
    if (!isSpeaking.value) {
      const subject = isListening.value ? 'listening' : 'reading'
      let sess = practiceStore.currentSession
      if (!sess?.session_id || Number(sess.quiz?.id) !== qid) {
        sess = await practiceStore.startSession(subject, qid)
      }
      if (sess?.quiz) {
        store.hydrateQuiz(sess.quiz)
      }
    }
    await nextTick()
    scrollToOrder(store.currentOrder)
  } catch (err) {
    console.error('Quiz load failed', err)
  }
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
