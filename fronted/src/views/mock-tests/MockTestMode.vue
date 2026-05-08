<template>
  <div class="page-wrapper">
    <div class="container" style="max-width: 980px">
      <div v-if="loading" class="card p-6 text-center text-[var(--ink2)]">Loading…</div>
      <div v-else-if="!mockTest" class="card p-6 text-center">
        <div class="text-lg font-semibold mb-2">Mock test not found</div>
        <RouterLink to="/" class="btn btn-primary">Về trang chủ</RouterLink>
      </div>

      <template v-else>
        <div class="mb-5">
          <RouterLink to="/" class="text-sm text-[var(--ink2)] hover:text-[var(--ink)]">← Danh sách đề</RouterLink>
          <h1 class="text-xl font-semibold mt-2">{{ mockTest.title }}</h1>
          <div class="text-sm text-[var(--ink2)] mt-1">
            {{ skillLabel(mockTest.skill_id) }} · {{ mockTest.book_code }} · #{{ mockTest.id }}
          </div>
        </div>

        <div class="grid gap-4 md:grid-cols-2">
          <button class="card p-5 text-left hover:shadow transition-shadow" @click="startFull">
            <div class="text-xs font-semibold text-[var(--ink2)] mb-1">Full Test</div>
            <div class="text-lg font-semibold">{{ fullMeta?.question_count }} câu · {{ fullMeta?.time }} phút</div>
            <div class="text-sm text-[var(--ink2)] mt-2">Làm full test như thi thật</div>
          </button>

          <div class="card p-5">
            <div class="text-xs font-semibold text-[var(--ink2)] mb-3">Luyện theo Part</div>
            <div class="grid gap-2">
              <button
                v-for="p in partMetas"
                :key="p.key"
                class="rounded-xl border border-[var(--border2)] bg-[var(--surface)] px-4 py-3 text-left hover:border-[var(--ink3)]"
                @click="startPart(p)"
              >
                <div class="flex items-center justify-between gap-3">
                  <div class="font-semibold">{{ p.label }}</div>
                  <div class="text-xs text-[var(--ink2)]">{{ p.question_count }} câu · {{ p.time }} phút</div>
                </div>
              </button>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getMockTest } from '@/services/mockTestService.js'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const mockTest = ref(null)

function skillLabel(skillId) {
  if (String(skillId) === '1') return 'Reading'
  if (String(skillId) === '2') return 'Listening'
  if (String(skillId) === '8') return 'Speaking'
  return `Skill ${skillId}`
}

const fullMeta = computed(() => mockTest.value?.quizzes?.full)

const partMetas = computed(() => {
  const q = mockTest.value?.quizzes || {}
  return Object.entries(q)
    .filter(([k]) => k.startsWith('part_'))
    .sort((a, b) => a[0].localeCompare(b[0], undefined, { numeric: true }))
    .map(([key, meta]) => ({
      key,
      label: key.replace('_', ' ').replace('part', 'Part'),
      ...meta,
    }))
})

function startFull() {
  if (!fullMeta.value?.id) return
  router.push(`/quiz/${fullMeta.value.id}`)
}

function startPart(p) {
  if (!p?.id) return
  router.push(`/quiz/${p.id}`)
}

onMounted(async () => {
  loading.value = true
  try {
    mockTest.value = await getMockTest(route.params.id)
  } finally {
    loading.value = false
  }
})
</script>

