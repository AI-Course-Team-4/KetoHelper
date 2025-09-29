import { useState } from 'react'
import { Menu, Search, Person, Logout } from '@mui/icons-material'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
// DropdownMenu는 MUI Menu로 대체 예정
import { useAuthStore } from '@/store/authStore'
import { useProfileStore } from '@/store/profileStore'
import { authService } from '@/services/AuthService'
import { toast } from 'react-hot-toast'
import { LoginModal } from './LoginModal'
import { useNavigate, useLocation } from 'react-router-dom'
import { cleanupLocalAuthArtifacts, clearChatHistoryStorage, clearNaverOAuthState } from '@/lib/bootCleanup'

export function Header() {
  const [, setIsSearchOpen] = useState(false)
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false)
  const [avatarError, setAvatarError] = useState(false)
  const { user, clear } = useAuthStore()
  const { clearProfile } = useProfileStore()
  const navigate = useNavigate()
  const location = useLocation()
  const avatarSrc = user?.profileImage
    ? user.profileImage.replace(/^http:/, 'https:')
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
    
    // 수동 로그아웃은 항상 메인 페이지로 (사용자가 의도한 행동)
    navigate('/')
    
    // 수동 로그아웃 플래그 리셋
    setTimeout(() => {
      if (typeof window !== 'undefined') {
        (window as any).isManualLogout = false
      }
    }, 1000)
  }

  const handleMenuClick = () => {
    navigate('/')
  }

  return (
    <header className="bg-white border-b border-border shadow-sm">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        {/* 로고 */}
        <div className="flex items-center space-x-4" onClick={handleMenuClick} style={{ cursor: 'pointer' }}>
          <Button
            variant="ghost"
            size="sm"
            className="lg:hidden"
          >
            <Menu sx={{ fontSize: 20 }} />
          </Button>
          
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-keto-primary rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">K</span>
            </div>
            <span className="font-bold text-xl text-gradient">KetoHelper</span>
          </div>
        </div>

        {/* 검색바 */}
        <div className="flex-1 max-w-md mx-4">
          <div className="relative">
            <Search sx={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', fontSize: 16, color: 'text.secondary' }} />
            <Input
              placeholder="레시피나 식당을 검색해보세요..."
              className="pl-10"
              onFocus={() => setIsSearchOpen(true)}
              onBlur={() => setIsSearchOpen(false)}
            />
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