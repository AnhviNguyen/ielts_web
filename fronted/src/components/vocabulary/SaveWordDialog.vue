<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div v-if="visible" class="fixed inset-0 z-[10000] flex items-center justify-center bg-black/40 p-4" @click.self="close">
        <div class="w-full max-w-[400px] overflow-hidden rounded-[20px] bg-white shadow-[0_24px_80px_rgba(0,0,0,0.18)]">
          <div class="flex items-center justify-between border-b border-slate-100 px-5 py-4">
            <span class="text-[15px] font-bold text-slate-900">Lưu từ vựng</span>
            <button type="button" class="cursor-pointer rounded-lg p-1 text-slate-400 hover:bg-slate-100" @click="close">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
          </div>

          <div class="px-5 py-4">
            <div class="mb-4 flex flex-col gap-2 rounded-xl border border-slate-200 bg-slate-50 p-3 text-[13px]">
              <div>
                <span class="text-[10px] font-bold uppercase tracking-wider text-slate-400">Từ</span>
                <div class="text-[17px] font-extrabold text-green-700">{{ word?.word }}</div>
                <span v-if="word?.word_type" class="mt-1 inline-block rounded-md bg-green-100 px-2 py-0.5 text-[10px] font-semibold uppercase text-green-700">{{ word.word_type }}</span>
              </div>
              <div v-if="word?.phonetic"><span class="text-[10px] font-bold uppercase text-slate-400">Phiên âm </span><span class="font-mono text-slate-600">/{{ word.phonetic }}/</span></div>
              <div v-if="word?.meaning_en"><span class="text-[10px] font-bold uppercase text-blue-700">EN </span>{{ word.meaning_en }}</div>
              <div v-if="word?.meaning_vi"><span class="text-[10px] font-bold uppercase text-green-700">VI </span>{{ word.meaning_vi }}</div>
              <div v-if="word?.example" class="italic text-slate-500">{{ word.example }}</div>
            </div>

            <template v-if="!loading && !hasTopics">
              <p class="mb-2 text-[13px] text-slate-500">Chưa có topic. Tạo topic đầu tiên để lưu từ.</p>
              <input
                ref="createInputRef"
                v-model="newTopicName"
                class="ct-input w-full"
                placeholder="Tên topic..."
                @keydown.enter="createFirstTopic"
              />
            </template>

            <template v-else-if="!loading">
              <AppSelect
                v-model="selectedTopicId"
                label="Topic"
                :hint="lastTopicHint"
                :options="topicOptions"
              />

              <button
                v-if="!showNewTopicForm"
                type="button"
                class="link-btn mt-2"
                @click="openNewTopicForm"
              >
                + Tạo topic mới
              </button>
              <div v-else class="mt-2 flex flex-wrap items-center gap-2">
                <input
                  ref="createInputRef"
                  v-model="newTopicName"
                  class="ct-input min-w-[120px] flex-1"
                  placeholder="Tên topic mới..."
                  @keydown.enter="confirmCreate"
                  @keydown.escape="showNewTopicForm = false"
                />
                <span class="profile-page shrink-0"><button type="button" class="btn btn-primary" @click="confirmCreate">Tạo</button></span>
                <button type="button" class="ct-btn shrink-0" @click="showNewTopicForm = false">Hủy</button>
              </div>
            </template>

            <div v-else class="py-2 text-[13px] text-slate-400">Đang tải topic...</div>

            <p v-if="errorMsg" class="mt-2 text-xs text-rose-600">{{ errorMsg }}</p>
            <p v-if="successMsg" class="mt-2 text-xs font-semibold text-green-700">{{ successMsg }}</p>
          </div>

          <div class="flex justify-end gap-2 border-t border-slate-100 px-5 py-3.5">
            <button type="button" class="ct-btn disabled:cursor-not-allowed disabled:opacity-40" :disabled="saving" @click="close">Hủy</button>
            <span class="profile-page">
              <button type="button" class="btn btn-primary disabled:cursor-not-allowed disabled:opacity-40" :disabled="saveDisabled" @click="onSave">
                {{ saving ? 'Đang lưu...' : (hasTopics ? 'Lưu' : 'Tạo topic & lưu') }}
              </button>
            </span>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import AppSelect from '@/components/ui/AppSelect.vue'
import { getTopics, createTopic, saveWord } from '@/services/vocabularyService.js'
import { resolveDefaultTopicId, setLastSaveTopicId, getLastSaveTopicId } from '@/utils/vocabTopicPreference.js'

const props = defineProps({
  visible: { type: Boolean, default: false },
  word: { type: Object, default: null },
  sourceType: { type: String, default: 'reading' },
  sourceQuizId: { type: [String, Number], default: null },
})

const emit = defineEmits(['close', 'saved'])

const topics = ref([])
const loading = ref(false)
const saving = ref(false)
const selectedTopicId = ref(null)
const showNewTopicForm = ref(false)
const newTopicName = ref('')
const errorMsg = ref('')
const successMsg = ref('')
const createInputRef = ref(null)

const hasTopics = computed(() => topics.value.length > 0)

const topicOptions = computed(() =>
  topics.value.map((t) => ({
    value: t.id,
    label: `${t.name} (${t.word_count} từ)`,
  })),
)

const lastTopicHint = computed(() => {
  const lastId = getLastSaveTopicId()
  if (!lastId || !hasTopics.value) return ''
  const t = topics.value.find((x) => x.id === lastId)
  if (t && selectedTopicId.value === lastId) return `Topic gần nhất: ${t.name}`
  return ''
})

const saveDisabled = computed(() => {
  if (saving.value || loading.value) return true
  if (!props.word?.word?.trim()) return true
  if (hasTopics.value) return !selectedTopicId.value
  return !newTopicName.value.trim()
})

watch(() => props.visible, async (open) => {
  if (!open) return
  errorMsg.value = ''
  successMsg.value = ''
  showNewTopicForm.value = false
  newTopicName.value = ''
  loading.value = true
  try {
    topics.value = await getTopics()
    if (topics.value.length) {
      selectedTopicId.value = resolveDefaultTopicId(topics.value)
    } else {
      selectedTopicId.value = null
      await nextTick()
      createInputRef.value?.focus()
    }
  } catch {
    errorMsg.value = 'Không tải được topic. Thử lại sau.'
    topics.value = []
  } finally {
    loading.value = false
  }
})

watch(selectedTopicId, (id) => {
  if (id) setLastSaveTopicId(id)
})

function openNewTopicForm() {
  showNewTopicForm.value = true
  newTopicName.value = ''
  nextTick(() => createInputRef.value?.focus())
}

async function createFirstTopic() {
  await confirmCreate()
}

async function confirmCreate() {
  const name = newTopicName.value.trim()
  if (!name) return
  errorMsg.value = ''
  try {
    const t = await createTopic(name)
    topics.value.push(t)
    selectedTopicId.value = t.id
    setLastSaveTopicId(t.id)
    showNewTopicForm.value = false
    newTopicName.value = ''
  } catch {
    errorMsg.value = 'Không tạo được topic.'
  }
}

function close() {
  if (saving.value) return
  emit('close')
}

async function onSave() {
  errorMsg.value = ''
  successMsg.value = ''

  let topicId = selectedTopicId.value

  if (!hasTopics.value) {
    const name = newTopicName.value.trim()
    if (!name) {
      errorMsg.value = 'Nhập tên topic trước khi lưu.'
      return
    }
    try {
      const t = await createTopic(name)
      topics.value = [t]
      topicId = t.id
      selectedTopicId.value = t.id
    } catch {
      errorMsg.value = 'Không tạo được topic.'
      return
    }
  }

  if (!topicId || !props.word) return

  saving.value = true
  try {
    await saveWord(topicId, {
      word: props.word.word,
      phonetic: props.word.phonetic || '',
      word_type: props.word.word_type || '',
      meaning_en: props.word.meaning_en || '',
      meaning_vi: props.word.meaning_vi || '',
      example: props.word.example || '',
      example_vi: props.word.example_vi || '',
      source_type: props.sourceType || 'reading',
      source_quiz_id: props.sourceQuizId ? String(props.sourceQuizId) : null,
    })
    setLastSaveTopicId(topicId)
    const topicName = topics.value.find((t) => t.id === topicId)?.name || 'topic'
    successMsg.value = `Đã lưu "${props.word.word}" vào ${topicName}.`
    emit('saved', { topicId, topicName, word: props.word })
    setTimeout(() => close(), 500)
  } catch (e) {
    const detail = e?.response?.data?.detail
    errorMsg.value = typeof detail === 'string' ? detail : 'Lưu từ thất bại.'
  } finally {
    saving.value = false
  }
}
</script>
