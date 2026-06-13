/** Redirect URI must match Google Cloud Console + backend GOOGLE_REDIRECT_URI */
export function googleRedirectUri() {
  const fromEnv = import.meta.env.VITE_GOOGLE_REDIRECT_URI
  if (fromEnv) return fromEnv.replace(/\/$/, '')
  return `${window.location.origin}/auth/google/callback`
}
