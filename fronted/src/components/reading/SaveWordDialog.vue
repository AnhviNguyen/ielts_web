<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div v-if="visible" class="modal-overlay" @click.self="$emit('close')">
        <div class="modal-box">
          <div class="modal-header">
            <span class="modal-title">Lưu từ vựng</span>
            <button class="modal-close" @click="$emit('close')">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
          </div>

          <div class="modal-body">
            <div class="word-preview">
              <span class="word-text">{{ word?.word }}</span>
              <span v-if="word?.word_type" class="word-type">{{ word.word_type }}</span>
            </div>

            <div class="label">Chọn topic</div>

            <div v-if="loading" class="loading-row">Đang tải topic...</div>
            <div v-else class="topic-list">
              <button
                v-for="t in topics"
                :key="t.id"
                class="topic-btn"
                :class="{ active: selectedTopicId === t.id }"
                @click="selectedTopicId = t.id"
              >
                <span>{{ t.name }}</span>
                <span class="topic-count">{{ t.word_count }}</span>
              </button>

              <!-- Create new topic inline -->
              <div v-if="creating" class="new-topic-row">
                <input
                  v-model="newTopicName"
                  class="new-topic-input"
                  placeholder="Tên topic mới..."
                  @keydown.enter="confirmCreate"
                  @keydown.escape="creating = false"
                  autofocus
                />
                <button class="new-topic-ok" @click="confirmCreate">OK</button>
              </div>
              <button v-else class="topic-btn add-btn" @click="creating = true">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                Tạo topic mới
              </button>
            </div>
          </div>

          <div class="modal-footer">
            <button class="btn-cancel" @click="$emit('close')">Hủy</button>
            <button class="btn-save" :disabled="!selectedTopicId" @click="save">Lưu</button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, watch } from 'vue'
import { getTopics, createTopic } from '@/services/vocabularyService.js'

const props = defineProps({
  visible: Boolean,
  word: Object,
})
const emit = defineEmits(['close', 'saved'])

const topics         = ref([])
const loading        = ref(false)
const selectedTopicId = ref(null)
const creating       = ref(false)
const newTopicName   = ref('')

watch(() => props.visible, async (v) => {
  if (v) {
    loading.value = true
    try {
      topics.value = await getTopics()
      if (topics.value.length) selectedTopicId.value = topics.value[0].id
    } finally {
      loading.value = false
    }
  }
})

async function confirmCreate() {
  const name = newTopicName.value.trim()
  if (!name) return
  try {
    const t = await createTopic(name)
    topics.value.push(t)
    selectedTopicId.value = t.id
    creating.value = false
    newTopicName.value = ''
  } catch {}
}

function save() {
  emit('saved', { topicId: selectedTopicId.value, word: props.word })
  emit('close')
}
</script>

<style scoped>
.modal-overlay {
  position: fixed; inset: 0; z-index: 10000;
  background: rgba(0,0,0,.4);
  display: flex; align-items: center; justify-content: center; padding: 16px;
}
.modal-box {
  background: #fff; border-radius: 20px; width: 100%; max-width: 400px;
  box-shadow: 0 24px 80px rgba(0,0,0,.18); overflow: hidden;
}
.modal-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 20px; border-bottom: 1px solid #f1f5f9;
}
.modal-title { font-size: 15px; font-weight: 700; color: #0f172a; }
.modal-close { background: none; border: none; cursor: pointer; color: #94a3b8; padding: 4px; border-radius: 8px; }
.modal-close:hover { background: #f1f5f9; color: #374151; }

.modal-body { padding: 16px 20px; }
.word-preview {
  display: flex; align-items: center; gap: 10px;
  margin-bottom: 14px; padding: 10px 14px;
  background: #f0fdf4; border-radius: 10px;
}
.word-text { font-size: 16px; font-weight: 800; color: #15803d; }
.word-type {
  font-size: 11px; font-weight: 600; text-transform: uppercase;
  background: #dcfce7; color: #15803d; border-radius: 6px; padding: 2px 8px;
}

.label { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .06em; color: #94a3b8; margin-bottom: 8px; }
.loading-row { font-size: 13px; color: #94a3b8; padding: 10px 0; }
.topic-list { display: flex; flex-direction: column; gap: 4px; max-height: 200px; overflow-y: auto; }

.topic-btn {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 12px; border: 1.5px solid #e2e8f0; border-radius: 10px;
  background: #f8fafc; cursor: pointer; font-size: 13px; color: #374151;
  transition: all .15s; text-align: left;
}
.topic-btn:hover { border-color: #15803d; background: #f0fdf4; }
.topic-btn.active { border-color: #15803d; background: #dcfce7; font-weight: 700; color: #15803d; }
.topic-count { font-size: 11px; color: #94a3b8; }
.add-btn { color: #15803d; border-style: dashed; gap: 6px; justify-content: flex-start; }

.new-topic-row { display: flex; gap: 6px; }
.new-topic-input {
  flex: 1; border: 1.5px solid #15803d; border-radius: 8px;
  padding: 8px 10px; font-size: 13px; outline: none;
}
.new-topic-ok {
  padding: 8px 14px; background: #15803d; color: #fff;
  border: none; border-radius: 8px; cursor: pointer; font-size: 13px; font-weight: 600;
}

.modal-footer {
  display: flex; justify-content: flex-end; gap: 8px;
  padding: 14px 20px; border-top: 1px solid #f1f5f9;
}
.btn-cancel {
  padding: 8px 18px; border: 1px solid #e2e8f0; border-radius: 8px;
  background: #f8fafc; color: #475569; font-size: 13px; cursor: pointer;
}
.btn-save {
  padding: 8px 22px; background: #15803d; color: #fff;
  border: none; border-radius: 8px; font-size: 13px; font-weight: 700; cursor: pointer;
}
.btn-save:disabled { opacity: .4; cursor: not-allowed; }

.modal-fade-enter-active, .modal-fade-leave-active { transition: opacity .2s; }
.modal-fade-enter-from, .modal-fade-leave-to { opacity: 0; }
</style>
