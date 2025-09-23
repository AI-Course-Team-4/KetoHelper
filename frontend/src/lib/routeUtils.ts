/**
 * 라우트 권한 관리 유틸리티
 */

// 로그인이 필요한 경로들
const PROTECTED_ROUTES = [
  '/profile',
  '/settings', 
  '/dashboard',
  '/calendar',
  '/subscribe',
  '/my-plans',
  '/favorites'
]

// 공개 경로들 (로그인 없이 접근 가능)
const PUBLIC_ROUTES = [
  '/',
  '/map',
  '/recipes',
  '/search',
  '/about',
  '/help'
]

/**
 * 현재 경로가 로그인이 필요한 경로인지 확인
 */
export function isProtectedRoute(pathname: string): boolean {
  return PROTECTED_ROUTES.some(route => 
    pathname.startsWith(route)
  )
}

/**
 * 현재 경로가 공개 경로인지 확인
 */
export function isPublicRoute(pathname: string): boolean {
  return PUBLIC_ROUTES.some(route => 
    pathname === route || (route !== '/' && pathname.startsWith(route))
  )
}

/**
 * 토큰 만료 시 현재 경로에 따른 처리 방식 결정
 */
export function shouldRedirectOnTokenExpiry(pathname: string): boolean {
  // 보호된 경로면 리다이렉트 필요
  if (isProtectedRoute(pathname)) {
    return true
  }
  
  // 공개 경로면 현재 페이지 유지
  return false
}

/**
 * 라우트 가드: 로그인이 필요한 페이지 접근 시 체크
 */
export function checkRouteAccess(pathname: string, isAuthenticated: boolean): {
  allowed: boolean
  shouldRedirect: boolean
  redirectTo?: string
} {
  // 보호된 경로에 미인증 사용자가 접근하는 경우
  if (isProtectedRoute(pathname) && !isAuthenticated) {
    return {
      allowed: false,
      shouldRedirect: true,
      redirectTo: '/'
    }
  }
  
  // 모든 경우에 접근 허용
  return {
    allowed: true,
    shouldRedirect: false
  }
}
