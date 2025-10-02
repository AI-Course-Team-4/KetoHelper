import { useState, useEffect } from 'react'
import { Menu, Logout } from '@mui/icons-material'
import { Button } from '@/components/ui/button'
// DropdownMenu는 MUI Menu로 대체 예정
import { useAuthStore } from '@/store/authStore'
import { useProfileStore } from '@/store/profileStore'
import { useNavigationStore } from '@/store/navigationStore'
import { useAuth } from '@/contexts/AuthContext'
import { authService } from '@/services/AuthService'
import { toast } from 'react-hot-toast'
import { LoginModal } from './LoginModal'
import { useNavigate, useLocation } from 'react-router-dom'
import { cleanupLocalAuthArtifacts, clearChatHistoryStorage, clearNaverOAuthState } from '@/lib/bootCleanup'

export function Header() {
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false)
  const [avatarError, setAvatarError] = useState(false)
  const { user } = useAuthStore()
  const { loading } = useAuth()
  const { profile, clearProfile, loadProfile, isLoading: profileLoading } = useProfileStore()
  const { toggleCollapsed } = useNavigationStore()
  const navigate = useNavigate()
  const location = useLocation()
  
  // 사용자가 로그인되어 있을 때 프로필 데이터 로드
  useEffect(() => {
    if (user?.id && !profile && !profileLoading) {
      loadProfile(user.id)
    }
  }, [user?.id, profile, profileLoading, loadProfile])
  
  // 프로필 이미지 우선순위: profile.profile_image_url > user.profileImage
  // 프로필이 로드되기 전까지는 user.profileImage 사용
  const profileImageUrl = profile?.profile_image_url || user?.profileImage
  const avatarSrc = profileImageUrl
    ? profileImageUrl.replace(/^http:/, 'https:')
    : undefined
    

  const handleLogin = () => {
    setIsLoginModalOpen(true)
  }

  const handleLogout = async () => {
    // 수동 로그아웃 플래그 설정 (axios 인터셉터에서 토스트 표시 방지)
    if (typeof window !== 'undefined') {
      (window as any).isManualLogout = true
    }
    
    try {
      await authService.logout()
      toast.success('성공적으로 로그아웃 되었습니다.')
    } catch {
      // ignore
    }
    
    // 🧹 프로필 데이터 완전 클리어 (다른 사용자 데이터 잔여 방지)
    clearProfile()
    console.log('🗑️ 로그아웃: 프로필 스토어 클리어 완료')
    
    // AuthService.clearMemory()에서 Zustand store도 함께 초기화하므로 중복 제거
    // clear(shouldRedirect) // 제거됨 - AuthService에서 처리
    
    // 기타 정리 작업
    try { cleanupLocalAuthArtifacts() } catch {}
    try { clearChatHistoryStorage() } catch {}
    try { clearNaverOAuthState() } catch {}
    
    // 수동 로그아웃 처리: 공개 페이지(채팅/지도)는 그대로 유지
    const currentPath = location.pathname
    const stayOnPage = currentPath.startsWith('/chat') || currentPath.startsWith('/map')
    if (!stayOnPage) {
      navigate('/')
    }
    
    // 수동 로그아웃 플래그 리셋
    setTimeout(() => {
      if (typeof window !== 'undefined') {
        (window as any).isManualLogout = false
      }
    }, 1000)
  }

  const handleMenuClick = () => {
    toggleCollapsed()
  }

  return (
    <header className="bg-white border-b border-border shadow-sm">
      <div className="w-full h-16 flex items-center justify-between">
        {/* 로고 */}
        <div className="flex items-center space-x-4">
          <Button
            variant="ghost"
            size="sm"
            className="lg:hidden hover:bg-transparent"
            onClick={handleMenuClick}
          >
            <Menu sx={{ fontSize: 20 }} />
          </Button>
          
          <div 
            className="flex items-center space-x-2 cursor-pointer"
            onClick={() => navigate('/')}
          >
            <div className="w-8 h-8 bg-keto-primary rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">K</span>
            </div>
            <span className="font-bold text-xl text-gradient">KetoHelper</span>
          </div>
        </div>

        {/* 사용자 메뉴 */}
        <div className="flex items-center space-x-2 pr-5">
          {loading ? (
            // 로딩 중일 때는 사용자 메뉴 영역을 숨김
            null
          ) : user ? (
            // 로그인된 사용자
            <div className="flex items-center gap-2">
              {avatarSrc && !avatarError ? (
                <Button variant="ghost" size="sm" onClick={() => navigate('/profile')}>
                  <img
                    src={avatarSrc}
                    alt="profile"
                    loading="lazy"
                    onError={() => setAvatarError(true)}
                    className="h-7 w-7 rounded-full object-cover"
                  />
                </Button>
              ) : (
                <Button variant="ghost" size="sm" onClick={() => navigate('/profile')}>
                  <div className="h-7 w-7 rounded-full bg-gray-200 flex items-center justify-center">
                    <span className="text-gray-500 text-xs font-medium">
                      {user.name ? user.name.charAt(0).toUpperCase() : 'U'}
                    </span>
                  </div>
                </Button>
              )}
              <Button variant="ghost" size="sm" onClick={handleLogout}>
                <Logout sx={{ fontSize: 16 }} />
              </Button>
            </div>
          ) : (
            // 로그아웃 상태 - 로그인 버튼 표시
            <Button variant="default" size="sm" onClick={handleLogin}>
              로그인
            </Button>
          )}
        </div>
      </div>

      {/* 로그인 모달 */}
      <LoginModal 
        open={isLoginModalOpen} 
        onOpenChange={setIsLoginModalOpen} 
      />
    </header>
  )
}