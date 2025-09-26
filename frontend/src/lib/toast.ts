import { toast } from 'react-hot-toast'

// 전역 토스트 유틸리티 - 중복 방지 및 일관성 보장
export const showToast = {
  // 성공 토스트
  success: (message: string, options?: any) => {
    return toast.success(message, {
      duration: 3000,
      position: 'top-center',
      ...options
    })
  },

  // 에러 토스트
  error: (message: string, options?: any) => {
    return toast.error(message, {
      duration: 4000,
      position: 'top-center',
      ...options
    })
  },

  // 정보 토스트
  info: (message: string, options?: any) => {
    return toast(message, {
      duration: 3000,
      position: 'top-center',
      icon: 'ℹ️',
      ...options
    })
  },

  // 로딩 토스트
  loading: (message: string, options?: any) => {
    return toast.loading(message, {
      position: 'top-center',
      ...options
    })
  },

  // 토스트 제거
  dismiss: (toastId?: string) => {
    if (toastId) {
      toast.dismiss(toastId)
    } else {
      toast.dismiss()
    }
  },

  // 모든 토스트 제거
  remove: () => {
    toast.remove()
  }
}

// 자주 사용하는 토스트들
// 로그아웃 직후 한 번의 진입에서 "로그인 필요" 토스트를 억제하기 위한 플래그
const JUST_LOGGED_OUT_KEY = 'just-logged-out'
export const markJustLoggedOut = () => {
  try { sessionStorage.setItem(JUST_LOGGED_OUT_KEY, '1') } catch {}
}
export const consumeJustLoggedOut = (): boolean => {
  try {
    const v = sessionStorage.getItem(JUST_LOGGED_OUT_KEY) === '1'
    if (v) sessionStorage.removeItem(JUST_LOGGED_OUT_KEY)
    return v
  } catch { return false }
}

export const commonToasts = {
  sessionExpired: () => {
    return showToast.error('로그인이 만료되었습니다. 메인페이지로 이동합니다.', {
      id: 'session-expired',
      duration: 3000
    })
  },

  loginRequired: () => {
    // 로그아웃 직후 첫 진입에서는 억제
    if (consumeJustLoggedOut()) return
    return showToast.error('로그인이 필요한 페이지입니다.', {
      id: 'login-required',
      duration: 2000
    })
  },

  networkError: () => {
    return showToast.error('네트워크 오류가 발생했습니다. 다시 시도해주세요.', {
      id: 'network-error',
      duration: 3000
    })
  },

  success: (message: string) => {
    return showToast.success(message, {
      duration: 2000
    })
  }
}
