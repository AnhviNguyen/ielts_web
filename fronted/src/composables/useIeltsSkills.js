/**
 * src/composables/useIeltsSkills.js
 * ─────────────────────────────────
 * Single source of truth cho IELTS skill configuration.
 * OCP: thêm skill mới chỉ cần thêm entry vào SKILLS array.
 * Không cần sửa component nào.
 */

export const SKILLS = [
  {
    id: 'reading',
    name: 'Reading',
    nameVi: 'Đọc',
    icon: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>`,
    color: 'blue',
    colorHex: '#4895ef',
    colorDark: '#1a4e8f',
    colorBg: '#dbeafe',
    route: '/reading',
    totalLabel: '48 bài',
    pendingLabel: '12 chưa làm',
    progress: 75,
  },
  {
    id: 'listening',
    name: 'Listening',
    nameVi: 'Nghe',
    icon: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 18v-6a9 9 0 0 1 18 0v6"/><path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3zM3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z"/></svg>`,
    color: 'green',
    colorHex: '#52b788',
    colorDark: '#2d6a4f',
    colorBg: '#d8f3dc',
    route: '/listening',
    totalLabel: '36 bài',
    pendingLabel: '20 chưa làm',
    progress: 44,
  },
  {
    id: 'writing',
    name: 'Writing',
    nameVi: 'Viết',
    icon: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>`,
    color: 'amber',
    colorHex: '#f4845f',
    colorDark: '#b5450b',
    colorBg: '#fde8dc',
    route: '/writing',
    totalLabel: '24 đề',
    pendingLabel: '15 chưa làm',
    progress: 38,
  },
  {
    id: 'speaking',
    name: 'Speaking',
    nameVi: 'Nói',
    icon: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>`,
    color: 'rose',
    colorHex: '#e05780',
    colorDark: '#9b1d3a',
    colorBg: '#fce4ec',
    route: '/speaking',
    totalLabel: '30 topic',
    pendingLabel: '18 chưa làm',
    progress: 40,
  },
  {
    id: 'vocabulary',
    name: 'Từ vựng',
    nameVi: 'Từ vựng',
    icon: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>`,
    color: 'violet',
    colorHex: '#9b72cf',
    colorDark: '#5c35a8',
    colorBg: '#ede9ff',
    route: '/vocabulary',
    totalLabel: '320 từ',
    pendingLabel: '45 cần ôn',
    progress: 62,
  },
]

/** Get a skill config by id */
export function getSkill(id) {
  return SKILLS.find(s => s.id === id) ?? SKILLS[0]
}

/** Composable hook để dùng trong component */
export function useIeltsSkills() {
  return { SKILLS, getSkill }
}
