const DASHBOARD_TABS = new Set(['home', 'reports', 'forecast', 'progress', 'study'])

/** Map current route to a page-guide config key (null = no guide). */
export function resolvePageGuideKey(route) {
  const path = route.path

  if (path === '/dashboard') {
    const tab = route.query.tab
    if (tab && DASHBOARD_TABS.has(tab) && tab !== 'home') return `dashboard-${tab}`
    return 'dashboard'
  }

  const rules = [
    [/^\/reading$/, 'reading'],
    [/^\/listening$/, 'listening'],
    [/^\/writing\/ielts$/, 'writing'],
    [/^\/writing\/translation\/practice\//, 'writing-translation-practice'],
    [/^\/writing\/translation/, 'writing-translation'],
    [/^\/writing$/, 'writing-hub'],
    [/^\/speaking$/, 'speaking'],
    [/^\/conversation\/[^/]+$/, 'conversation-practice'],
    [/^\/conversation$/, 'conversation'],
    [/^\/vocabulary\/practice\//, 'vocabulary-practice'],
    [/^\/vocabulary$/, 'vocabulary'],
    [/^\/shadowing\/[a-zA-Z0-9_-]{11}/, 'shadowing-practice'],
    [/^\/shadowing$/, 'shadowing'],
    [/^\/full-exam$/, 'full-exam'],
    [/^\/history$/, 'history'],
    [/^\/profile$/, 'profile'],
    [/^\/leaderboard$/, 'leaderboard'],
    [/^\/mock-tests\//, 'mock-test'],
    [/^\/quiz\//, 'quiz'],
    [/^\/writing\/editor\//, 'writing-editor'],
  ]

  for (const [pattern, key] of rules) {
    if (pattern.test(path)) return key
  }

  return null
}
