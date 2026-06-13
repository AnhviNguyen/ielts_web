/** Màu accent theo từng khu vực admin */
export const ADMIN_MODULES = {
  dashboard: { label: 'Tổng quan', color: '#059669', soft: '#ecfdf5', border: '#a7f3d0', gradient: 'from-emerald-50 via-white to-teal-50' },
  users: { label: 'Người dùng', color: '#6366f1', soft: '#eef2ff', border: '#c7d2fe', gradient: 'from-indigo-50 via-white to-violet-50' },
  leaderboard: { label: 'Bảng xếp hạng', color: '#f97316', soft: '#fff7ed', border: '#fed7aa', gradient: 'from-orange-50 via-white to-amber-50' },
  vocab: { label: 'Từ vựng', color: '#14b8a6', soft: '#f0fdfa', border: '#99f6e4', gradient: 'from-teal-50 via-white to-cyan-50' },
  writing: { label: 'Writing CMS', color: '#8b5cf6', soft: '#f5f3ff', border: '#ddd6fe', gradient: 'from-violet-50 via-white to-purple-50' },
  reading: { label: 'Reading CMS', color: '#059669', soft: '#ecfdf5', border: '#a7f3d0', gradient: 'from-emerald-50 via-white to-green-50' },
  listening: { label: 'Listening CMS', color: '#3b82f6', soft: '#eff6ff', border: '#bfdbfe', gradient: 'from-blue-50 via-white to-sky-50' },
  speaking: { label: 'Speaking CMS', color: '#f59e0b', soft: '#fffbeb', border: '#fde68a', gradient: 'from-amber-50 via-white to-yellow-50' },
  conversation: { label: 'Conversation CMS', color: '#ec4899', soft: '#fdf2f8', border: '#fbcfe8', gradient: 'from-pink-50 via-white to-rose-50' },
  translation: { label: 'Translation CMS', color: '#06b6d4', soft: '#ecfeff', border: '#a5f3fc', gradient: 'from-cyan-50 via-white to-sky-50' },
}

export function moduleStyle(key) {
  const m = ADMIN_MODULES[key] || ADMIN_MODULES.dashboard
  return {
    '--admin-accent': m.color,
    '--admin-accent-soft': m.soft,
    '--admin-accent-border': m.border,
  }
}
