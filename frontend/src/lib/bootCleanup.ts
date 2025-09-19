const AUTH_STORAGE_KEY = 'keto-auth'

export function cleanupLocalAuthArtifacts() {
  try {
    // 1) 우리 앱의 저장 상태에서 토큰 흔적 정리
    const raw = typeof window !== 'undefined' ? window.localStorage.getItem(AUTH_STORAGE_KEY) : null
    if (raw) {
      const parsed = JSON.parse(raw)
      const persistedState = parsed && typeof parsed === 'object' ? parsed.state : null
      if (persistedState && typeof persistedState === 'object') {
        // 토큰 필드가 있으면 제거
        if ('accessToken' in persistedState || 'refreshToken' in persistedState) {
          const sanitized = {
            version: 2,
            state: { user: persistedState.user ?? null },
          }
          window.localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(sanitized))
        }
      }
    }

    // 2) 더 이상 사용하지 않는 과거/외부 인증 관련 키 제거
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
    // JSON/스토리지 오류는 무시
  }
}

export function clearChatHistoryStorage() {
  try { window.localStorage.removeItem('keto-coach-chat') } catch {}
}

export function clearNaverOAuthState() {
  try { window.sessionStorage.removeItem('naver_oauth_state') } catch {}
}

// 모듈 임포트 시 즉시 정리 실행
try { cleanupLocalAuthArtifacts() } catch {}


