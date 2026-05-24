<template>
  <div class="mx-auto max-w-7xl space-y-5">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h1 class="text-xl font-bold text-[var(--ink)]">Admin dashboard</h1>
        <p class="mt-1 text-sm text-[var(--ink3)]">Theo doi nguoi dung, DAU, bai lam va tin hieu bat thuong.</p>
      </div>
      <RouterLink to="/admin/users" class="ct-btn ct-btn-accent">Quan ly nguoi dung</RouterLink>
    </div>

    <div v-if="loading" class="rounded-lg border border-[var(--border)] bg-white p-6 text-sm text-[var(--ink3)]">Dang tai du lieu...</div>
    <div v-else-if="error" class="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">{{ error }}</div>

    <template v-else-if="overview">
      <section class="grid gap-3 sm:grid-cols-2 lg:grid-cols-6">
        <div v-for="card in statCards" :key="card.label" class="rounded-lg border border-[var(--border)] bg-white p-4">
          <div class="text-xs font-semibold uppercase text-[var(--ink3)]">{{ card.label }}</div>
          <div class="mt-2 text-2xl font-bold text-[var(--ink)]">{{ card.value }}</div>
        </div>
      </section>

      <section class="grid gap-4 lg:grid-cols-2">
        <MetricBars
          title="Attempts last 7 days"
          :items="overview.attempts_last_7_days || []"
          value-key="attempts"
          color="#34d399"
        />
        <MetricBars
          title="DAU last 7 days"
          :items="overview.dau_last_7_days || []"
          value-key="active_users"
          color="#60a5fa"
        />
      </section>

      <section class="grid gap-4 lg:grid-cols-2">
        <div class="rounded-lg border border-[var(--border)] bg-white p-4">
          <h2 class="text-sm font-bold text-[var(--ink)]">Average band</h2>
          <div class="mt-4 space-y-2">
            <div v-for="skill in overview.average_band_by_skill" :key="skill.subject" class="flex items-center justify-between rounded-md bg-[var(--bg)] px-3 py-2 text-sm">
              <span class="font-semibold text-[var(--ink)]">{{ skill.subject }}</span>
              <span class="text-[var(--ink2)]">{{ skill.average_band }} band · {{ skill.attempts }} attempts</span>
            </div>
            <div v-if="!overview.average_band_by_skill.length" class="text-sm text-[var(--ink3)]">No band data yet.</div>
          </div>
        </div>

        <div class="rounded-lg border border-[var(--border)] bg-white p-4">
          <h2 class="text-sm font-bold text-[var(--ink)]">Band distribution</h2>
          <div class="mt-4 grid grid-cols-4 gap-2">
            <div v-for="bucket in overview.band_distribution" :key="bucket.label" class="rounded-md bg-[var(--bg)] p-3 text-center">
              <div class="text-lg font-bold">{{ bucket.count }}</div>
              <div class="mt-1 text-xs text-[var(--ink3)]">{{ bucket.label }}</div>
            </div>
          </div>
        </div>
      </section>

      <section class="grid gap-4 lg:grid-cols-2">
        <div class="rounded-lg border border-[var(--border)] bg-white p-4">
          <h2 class="text-sm font-bold text-[var(--ink)]">Streak buckets</h2>
          <div class="mt-4 grid grid-cols-4 gap-2">
            <div v-for="bucket in overview.streak_buckets" :key="bucket.label" class="rounded-md bg-[var(--bg)] p-3 text-center">
              <div class="text-lg font-bold">{{ bucket.count }}</div>
              <div class="mt-1 text-xs text-[var(--ink3)]">{{ bucket.label }} days</div>
            </div>
          </div>
        </div>

        <div class="rounded-lg border border-[var(--border)] bg-white p-4">
          <h2 class="text-sm font-bold text-[var(--ink)]">Retention by streak</h2>
          <div class="mt-4 space-y-2">
            <div v-for="bucket in overview.retention_by_streak" :key="bucket.label" class="rounded-md bg-[var(--bg)] p-3">
              <div class="flex items-center justify-between text-xs">
                <span class="font-semibold text-[var(--ink)]">{{ bucket.label }} days</span>
                <span class="text-[var(--ink3)]">{{ bucket.active_last_7_days }}/{{ bucket.total_users }} recent</span>
              </div>
              <div class="mt-2 h-2 rounded-full bg-white">
                <div class="h-2 rounded-full bg-[#f59e0b]" :style="{ width: `${Math.max(3, bucket.retention_rate)}%` }"></div>
              </div>
              <div class="mt-1 text-[11px] text-[var(--ink3)]">Today {{ bucket.active_today }} · {{ bucket.retention_rate }}%</div>
            </div>
          </div>
        </div>
      </section>

      <section class="rounded-lg border border-[var(--border)] bg-white">
        <div class="flex items-center justify-between border-b border-[var(--border)] px-4 py-3">
          <h2 class="text-sm font-bold text-[var(--ink)]">Suspicious signals</h2>
          <RouterLink to="/admin/leaderboard" class="text-xs font-semibold text-[#059669]">Open leaderboard</RouterLink>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full min-w-[760px] text-left text-sm">
            <thead class="bg-[var(--bg)] text-xs uppercase text-[var(--ink3)]">
              <tr>
                <th class="px-4 py-2">User</th>
                <th class="px-4 py-2">XP</th>
                <th class="px-4 py-2">Streak</th>
                <th class="px-4 py-2">24h</th>
                <th class="px-4 py-2">Reasons</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="user in overview.top_suspicious_users" :key="user.id" class="border-t border-[var(--border)]">
                <td class="px-4 py-3">
                  <RouterLink :to="`/admin/users/${user.id}`" class="font-semibold text-[var(--ink)] hover:text-[#059669]">{{ user.full_name || user.email }}</RouterLink>
                  <div class="text-xs text-[var(--ink3)]">{{ user.email }}</div>
                </td>
                <td class="px-4 py-3">{{ user.xp }}</td>
                <td class="px-4 py-3">{{ user.streak }}</td>
                <td class="px-4 py-3">{{ user.attempts_24h }}</td>
                <td class="px-4 py-3 text-xs text-[var(--ink2)]">{{ user.reasons.join(', ') }}</td>
              </tr>
              <tr v-if="!overview.top_suspicious_users.length">
                <td colspan="5" class="px-4 py-6 text-center text-sm text-[var(--ink3)]">No suspicious signals yet.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { computed, defineComponent, h, onMounted, ref } from 'vue'
import { adminService } from '@/services/adminService.js'

const overview = ref(null)
const loading = ref(true)
const error = ref('')

const statCards = computed(() => [
  { label: 'Users', value: overview.value?.total_users ?? 0 },
  { label: 'Active', value: overview.value?.active_users ?? 0 },
  { label: 'Locked', value: overview.value?.locked_users ?? 0 },
  { label: 'DAU today', value: overview.value?.dau_today ?? 0 },
  { label: 'Attempts today', value: overview.value?.attempts_today ?? 0 },
  { label: 'Suspicious', value: overview.value?.top_suspicious_users?.length ?? 0 },
])

const MetricBars = defineComponent({
  props: {
    title: { type: String, required: true },
    items: { type: Array, default: () => [] },
    valueKey: { type: String, required: true },
    color: { type: String, default: '#34d399' },
  },
  setup(props) {
    return () => {
      const max = Math.max(1, ...props.items.map((item) => Number(item[props.valueKey] || 0)))
      return h('div', { class: 'rounded-lg border border-[var(--border)] bg-white p-4' }, [
        h('h2', { class: 'text-sm font-bold text-[var(--ink)]' }, props.title),
        h('div', { class: 'mt-4 space-y-2' }, props.items.map((item) => {
          const value = Number(item[props.valueKey] || 0)
          const width = `${Math.max(4, Math.round((value / max) * 100))}%`
          return h('div', { class: 'grid grid-cols-[92px_1fr_44px] items-center gap-3 text-xs', key: item.date }, [
            h('span', { class: 'text-[var(--ink3)]' }, item.date),
            h('div', { class: 'h-2 rounded-full bg-[var(--bg2)]' }, [
              h('div', { class: 'h-2 rounded-full', style: { width, backgroundColor: props.color } }),
            ]),
            h('span', { class: 'text-right font-semibold text-[var(--ink)]' }, value),
          ])
        })),
      ])
    }
  },
})

onMounted(async () => {
  loading.value = true
  error.value = ''
  try {
    overview.value = await adminService.getOverview()
  } catch (err) {
    error.value = err.response?.data?.detail || 'Khong tai duoc dashboard admin.'
  } finally {
    loading.value = false
  }
})
</script>
