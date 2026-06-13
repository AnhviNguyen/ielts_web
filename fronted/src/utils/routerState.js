/** Plain copy for vue-router history.state (structured clone rejects Vue proxies). */
export function cloneRouterState(value) {
  if (value == null) return value
  return JSON.parse(JSON.stringify(value))
}
