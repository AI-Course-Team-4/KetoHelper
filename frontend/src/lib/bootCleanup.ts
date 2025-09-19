const AUTH_STORAGE_KEY = 'keto-auth'

export function cleanupLocalAuthArtifacts() {
  try {
    // 1) Sanitize our own persisted store
    const raw = typeof window !== 'undefined' ? window.localStorage.getItem(AUTH_STORAGE_KEY) : null
    if (raw) {
      const parsed = JSON.parse(raw)
      const persistedState = parsed && typeof parsed === 'object' ? parsed.state : null
      if (persistedState && typeof persistedState === 'object') {
        // Drop tokens if present
        if ('accessToken' in persistedState || 'refreshToken' in persistedState) {
          const sanitized = {
            version: 2,
            state: { user: persistedState.user ?? null },
          }
          window.localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(sanitized))
        }
      }
    }

    // 2) Remove legacy/foreign auth keys we don't use anymore
    const legacyExactKeys = [
      'access_token',
      'refresh_token',
      'token',
      'id_token',
      'auth-storage',
      'nextauth.message',
    ]
    for (const key of legacyExactKeys) {
      try { window.localStorage.removeItem(key) } catch {}
    }

    const legacyPrefixes = ['kakao_', 'nextauth.']
    try {
      for (let i = 0; i < window.localStorage.length; i++) {
        const key = window.localStorage.key(i)
        if (!key) continue
        if (legacyPrefixes.some((p) => key.startsWith(p))) {
          try { window.localStorage.removeItem(key) } catch {}
        }
      }
    } catch {}
  } catch {
    // Ignore JSON/storage errors silently
  }
}

export function clearChatHistoryStorage() {
  try { window.localStorage.removeItem('keto-coach-chat') } catch {}
}

export function clearNaverOAuthState() {
  try { window.sessionStorage.removeItem('naver_oauth_state') } catch {}
}

// Run cleanup on import
try { cleanupLocalAuthArtifacts() } catch {}


