import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  IconButton,
  Avatar,
  Menu,
  MenuItem,
  Box,
  useTheme,
  useMediaQuery,
} from '@mui/material'
import {
  Menu as MenuIcon,
  AccountCircle,
  Settings,
  Logout,
  Home,
  CalendarMonth,
} from '@mui/icons-material'
import { useAuthStore } from '@store/authStore'
import { useAppStore } from '@store/appStore'
import { authService } from '@services/authService'
import { toast } from 'react-hot-toast'

const Header = () => {
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))
  const navigate = useNavigate()
  
  const { user, isAuthenticated, logout } = useAuthStore()
  const { toggleSidebar } = useAppStore()
  
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)

  const handleProfileMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget)
  }

  const handleProfileMenuClose = () => {
    setAnchorEl(null)
  }

  const handleLogout = async () => {
    try {
      // 데모 모드에서는 API 호출 없이 바로 로그아웃
      if (user?.id?.startsWith('demo-')) {
        logout()
        navigate('/')
        toast.success('로그아웃되었습니다.')
      } else {
        await authService.logout()
        logout()
        navigate('/')
        toast.success('로그아웃되었습니다.')
      }
    } catch (error) {
      // API 호출 실패해도 강제 로그아웃
      console.error('로그아웃 API 실패:', error)
      logout()
      navigate('/')
      toast.success('로그아웃되었습니다.')
    }
    handleProfileMenuClose()
  }

  const handleSettingsClick = () => {
    navigate('/settings')
    handleProfileMenuClose()
  }

  const displayName = user?.name || user?.id || '';

  return (
    <AppBar position="sticky" elevation={1}>
      <Toolbar>
        {/* 햄버거 메뉴 (모든 화면) */}
        <IconButton
          edge="start"
          color="inherit"
          aria-label="사이드바 토글"
          onClick={toggleSidebar}
          sx={{ 
            mr: 2,
            transition: 'transform 0.2s ease',
            '&:hover': {
              transform: 'scale(1.1)',
              backgroundColor: 'rgba(255, 255, 255, 0.1)',
            }
          }}
        >
          <MenuIcon />
        </IconButton>

        {/* 로고 */}
        <Box
          component={Link}
          to="/"
          sx={{
            display: 'flex',
            alignItems: 'center',
            textDecoration: 'none',
            color: 'inherit',
            mr: 4,
          }}
        >
          <Typography variant="h6" sx={{ fontWeight: 700, color: theme.palette.primary.main }}>
            🥑 KetoHelper
          </Typography>
        </Box>

        {/* 네비게이션 메뉴 (데스크톱) */}
        {!isMobile && (
          <Box sx={{ display: 'flex', gap: 2, mr: 'auto' }}>
            <Button
              color="inherit"
              component={Link}
              to="/"
              startIcon={<Home />}
            >
              홈
            </Button>
            <Button
              color="inherit"
              component={Link}
              to="/meals"
            >
              식단 추천
            </Button>
            <Button
              color="inherit"
              component={Link}
              to="/restaurants"
            >
              식당 추천
            </Button>
            
            {/* 구독자 전용 캘린더 메뉴 */}
            {isAuthenticated && user?.subscription?.isActive && (
              <Button
                color="inherit"
                component={Link}
                to="/calendar"
                startIcon={<CalendarMonth />}
                sx={{
                  backgroundColor: 'rgba(255, 255, 255, 0.1)',
                  '&:hover': {
                    backgroundColor: 'rgba(255, 255, 255, 0.2)',
                  },
                  borderRadius: 2,
                  position: 'relative',
                  '&::after': {
                    content: '"✨"',
                    position: 'absolute',
                    top: -2,
                    right: -2,
                    fontSize: '0.7rem',
                    backgroundColor: 'warning.main',
                    borderRadius: '50%',
                    width: 16,
                    height: 16,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }
                }}
              >
                캘린더
              </Button>
            )}
          </Box>
        )}

        {/* 사용자 프로필 또는 로그인 버튼 */}
        <Box sx={{ ml: 'auto' }}>
          {isAuthenticated && user ? (
            <>
              <IconButton
                size="large"
                edge="end"
                aria-label="account of current user"
                aria-controls="primary-search-account-menu"
                aria-haspopup="true"
                onClick={handleProfileMenuOpen}
                color="inherit"
              >
                {user.profileImage ? (
                  <Avatar
                    src={user.profileImage}
                    alt={user.name}
                    sx={{ width: 32, height: 32 }}
                  />
                ) : (
                  <AccountCircle />
                )}
              </IconButton>
              <Menu
                anchorEl={anchorEl}
                anchorOrigin={{
                  vertical: 'bottom',
                  horizontal: 'right',
                }}
                id="primary-search-account-menu"
                keepMounted
                transformOrigin={{
                  vertical: 'top',
                  horizontal: 'right',
                }}
                open={Boolean(anchorEl)}
                onClose={handleProfileMenuClose}
              >
                <MenuItem onClick={handleProfileMenuClose}>
                  <Box sx={{ minWidth: 200 }}>
                    <Typography variant="subtitle2">{displayName}</Typography>
                    <Typography variant="body2" color="text.secondary">
                      {user.email}
                    </Typography>
                  </Box>
                </MenuItem>
                <MenuItem onClick={handleSettingsClick}>
                  <Settings sx={{ mr: 2 }} />
                  설정
                </MenuItem>
                <MenuItem onClick={handleLogout}>
                  <Logout sx={{ mr: 2 }} />
                  로그아웃
                </MenuItem>
              </Menu>
            </>
          ) : (
            <Button
              color="inherit"
              variant="outlined"
              component={Link}
              to="/login"
              sx={{
                borderColor: theme.palette.primary.main,
                color: theme.palette.primary.main,
                '&:hover': {
                  backgroundColor: theme.palette.primary.main,
                  color: 'white',
                },
              }}
            >
              로그인
            </Button>
          )}
        </Box>
      </Toolbar>
    </AppBar>
  )
}

export default Header
