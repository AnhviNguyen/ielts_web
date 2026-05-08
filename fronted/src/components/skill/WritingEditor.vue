<template>
  <div class="writing-editor">
    <!-- Toolbar -->
    <div class="editor-toolbar">
      <div class="editor-actions">
        <button class="editor-action" title="Bold" @click="execCmd('bold')"><b>B</b></button>
        <button class="editor-action" title="Italic" @click="execCmd('italic')"><i>I</i></button>
        <button class="editor-action" title="Undo" @click="execCmd('undo')">↩</button>
        <button class="editor-action" title="Redo" @click="execCmd('redo')">↪</button>
      </div>
      <div class="word-counter">
        Số từ: <span :class="{ 'wc-ok': wordCount >= minWords, 'wc-warn': wordCount > 0 && wordCount < minWords }">{{ wordCount }}</span>
        / {{ minWords }}+
      </div>
    </div>

    <!-- Textarea -->
    <textarea
      class="writing-textarea"
      :placeholder="placeholder"
      :value="modelValue"
      @input="handleInput"
    ></textarea>

    <!-- Footer -->
    <div class="editor-footer">
      <div class="footer-actions">
        <button class="btn-ghost btn-sm" @click="$emit('save')">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
          Lưu nháp
        </button>
        <button class="btn-ghost btn-sm" @click="$emit('aiHint')">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="6" height="6" rx="1"/><path d="M9 1v2M15 1v2M9 21v2M15 21v2M1 9h2M1 15h2M21 9h2M21 15h2"/><rect x="2" y="2" width="20" height="20" rx="2"/></svg>
          AI gợi ý
        </button>
      </div>
      <button class="btn-primary" @click="$emit('submit')">
        Nộp bài & Chấm điểm ✓
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useWordCount } from '@/composables/useWordCount.js'

const props = defineProps({
  modelValue:  { type: String, default: '' },
  placeholder: { type: String, default: 'Bắt đầu viết bài...' },
  minWords:    { type: Number, default: 150 },
})

const emit = defineEmits(['update:modelValue', 'save', 'aiHint', 'submit'])

const { wordCount, updateText } = useWordCount()

function handleInput(e) {
  const val = e.target.value
  emit('update:modelValue', val)
  updateText(val)
}

function execCmd(cmd) {
  document.execCommand(cmd)
}
</script>

<style scoped>
.writing-editor {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--r);
  display: flex;
  flex-direction: column;
  height: 100%;
}

.editor-toolbar {
  padding: 10px 16px;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}

.editor-actions { display: flex; gap: 6px; }

.editor-action {
  width: 30px; height: 30px;
  border-radius: 6px;
  background: var(--bg);
  border: 1px solid var(--border2);
  font-size: 13px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s;
  color: var(--ink2);
}

.editor-action:hover { background: var(--border); }

.word-counter {
  font-size: 12px;
  color: var(--ink3);
}

.word-counter span { font-weight: 700; color: var(--ink); }
.wc-ok { color: var(--green) !important; }
.wc-warn { color: var(--amber) !important; }

.writing-textarea {
  flex: 1;
  padding: 20px;
  font-size: 14px;
  line-height: 1.9;
  font-family: var(--font-body);
  color: var(--ink);
  border: none;
  outline: none;
  resize: none;
  background: transparent;
  min-height: 200px;
}

.editor-footer {
  padding: 12px 16px;
  border-top: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}

.footer-actions { display: flex; gap: 8px; }

.btn-ghost {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 7px 12px; border-radius: var(--r-sm);
  background: transparent; border: none;
  font-size: 12px; font-weight: 600;
  cursor: pointer; color: var(--ink2);
  font-family: var(--font-body);
  transition: background 0.15s;
}
.btn-ghost:hover { background: var(--bg2); }

.btn-sm { padding: 6px 12px; font-size: 12px; }

.btn-primary {
  display: inline-flex; align-items: center; gap: 7px;
  padding: 9px 18px; border-radius: var(--r-sm);
  background: var(--green); color: #fff;
  font-size: 13px; font-weight: 600;
  cursor: pointer; border: none;
  transition: all 0.18s;
  font-family: var(--font-body);
}
.btn-primary:hover { background: #245c42; transform: translateY(-1px); box-shadow: 0 4px 12px rgba(45,106,79,0.3); }
</style>
