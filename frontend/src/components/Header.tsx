import { useState } from 'react'
import { Menu, Search, User, LogOut } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useAuthStore } from '@/store/authStore'
import { useProfileStore } from '@/store/profileStore'
import { authService } from '@/lib/authService'
import { toast } from 'react-hot-toast'
import { LoginModal } from './LoginModal'
import { useNavigate, useLocation } from 'react-router-dom'
import { cleanupLocalAuthArtifacts, clearChatHistoryStorage, clearNaverOAuthState } from '@/lib/bootCleanup'
import { shouldRedirectOnTokenExpiry } from '@/lib/routeUtils'

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
            <Menu className="h-5 w-5" />
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
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
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
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="sm" className="relative">
                  {avatarSrc && !avatarError ? (
                    <img
                      src={avatarSrc}
                      alt="profile"
                      loading="lazy"
                      onError={() => setAvatarError(true)}
                      className="h-7 w-7 rounded-full object-cover"
                    />
                  ) : (
                    <User className="h-7 w-7" />
                  )}
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                {/* 사용자 정보 요약 */}
                <div className="px-3 py-2 flex items-center gap-2">
                  {avatarSrc && !avatarError ? (
                    <img
                      src={avatarSrc}
                      alt="profile"
                      className="h-8 w-8 rounded-full object-cover"
                    />
                  ) : (
                    <User className="h-8 w-8" />
                  )}
                  <div className="min-w-0">
                    <div className="text-sm font-medium truncate">{user?.name || '사용자'}</div>
                    {user?.email && (
                      <div className="text-xs text-muted-foreground truncate">{user.email}</div>
                    )}
                  </div>
                </div>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => navigate('/profile')}>
                  <User className="mr-2 h-4 w-4" />
                  <span>프로필 설정</span>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem className="text-red-600" onClick={handleLogout}>
                  <LogOut className="mr-2 h-4 w-4" />
                  <span>로그아웃</span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
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