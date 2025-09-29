import { useState } from 'react'
import { Menu, Person, Logout } from '@mui/icons-material'
import { Button } from '@/components/ui/button'
// DropdownMenu는 MUI Menu로 대체 예정
import { useAuthStore } from '@/store/authStore'
import { useProfileStore } from '@/store/profileStore'
import { useNavigationStore } from '@/store/navigationStore'
import { authService } from '@/lib/authService'
import { toast } from 'react-hot-toast'
import { LoginModal } from './LoginModal'
import { useNavigate, useLocation } from 'react-router-dom'
import { cleanupLocalAuthArtifacts, clearChatHistoryStorage, clearNaverOAuthState } from '@/lib/bootCleanup'
import { shouldRedirectOnTokenExpiry } from '@/lib/routeUtils'

export function Header() {
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false)
  const [avatarError, setAvatarError] = useState(false)
  const { user, clear } = useAuthStore()
  const { clearProfile } = useProfileStore()
  const { toggleCollapsed } = useNavigationStore()
  const navigate = useNavigate()
  const location = useLocation()
  const avatarSrc = user?.profileImage
    ? user.profileImage.replace(/^http:/, 'https:')
    : undefined

  const handleLogin = () => {
    setIsLoginModalOpen(true)
  }

  const handleLogout = async () => {
    try {
      await authService.logout()
      toast.success('성공적으로 로그아웃 되었습니다.')
    } catch {
      // ignore
    }
    
    // 🧹 프로필 데이터 완전 클리어 (다른 사용자 데이터 잔여 방지)
    clearProfile()
    console.log('🗑️ 로그아웃: 프로필 스토어 클리어 완료')
    
    // 현재 경로에 따라 리다이렉트 여부 결정
    const shouldRedirect = shouldRedirectOnTokenExpiry(location.pathname)
    
    clear(shouldRedirect)
    try { cleanupLocalAuthArtifacts() } catch {}
    try { clearChatHistoryStorage() } catch {}
    try { clearNaverOAuthState() } catch {}
    
    // 수동 로그아웃은 항상 메인 페이지로 (사용자가 의도한 행동)
    navigate('/')
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
        <div className="flex items-center space-x-2">
          {user ? (
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="sm" onClick={() => navigate('/profile')}>
                {avatarSrc && !avatarError ? (
                  <img
                    src={avatarSrc}
                    alt="profile"
                    loading="lazy"
                    onError={() => setAvatarError(true)}
                    className="h-7 w-7 rounded-full object-cover"
                  />
                ) : (
                  <Person sx={{ fontSize: 28 }} />
                )}
              </Button>
              <Button variant="ghost" size="sm" onClick={handleLogout}>
                <Logout sx={{ fontSize: 16 }} />
              </Button>
            </div>
          ) : (
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