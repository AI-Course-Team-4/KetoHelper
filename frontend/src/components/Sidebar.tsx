import { Link, useLocation } from 'react-router-dom'
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Divider,
  Box,
  useTheme,
  useMediaQuery,
  Typography,
  Button,
  Chip,
  Avatar,
  LinearProgress,
  IconButton,
} from '@mui/material'
import {
  Home,
  Restaurant,
  MenuBook,
  Settings,
  Info,
  CalendarMonth,
  Payment,
  Person,
  FavoriteBorder,
  EmojiEvents,
  TrendingDown,
  Logout,
  ChevronLeft,
  ChevronRight,
  Today,
  EventNote,
} from '@mui/icons-material'
import { useAppStore } from '@store/appStore'
import { useAuthStore } from '@store/authStore'
import { useNavigate } from 'react-router-dom'
import { toast } from 'react-hot-toast'
import { authService } from '@services/authService'

const sidebarWidth = 240

const getMenuItems = (hasSubscription: boolean) => [
  { text: '홈', icon: <Home />, path: '/' },
  { text: '추천 식단', icon: <MenuBook />, path: '/meals' },
  { text: '추천 식당', icon: <Restaurant />, path: '/restaurants' },
  ...(hasSubscription ? [
    { text: '캘린더', icon: <CalendarMonth />, path: '/calendar' }
  ] : []),
]

const getBottomMenuItems = (isAuthenticated: boolean) => [
  ...(isAuthenticated ? [
    { text: '프로필 설정', icon: <Person />, path: '/profile' },
    { text: '선호도 설정', icon: <FavoriteBorder />, path: '/preferences' },
    { text: '구독', icon: <Payment />, path: '/subscription' },
    { text: '설정', icon: <Settings />, path: '/settings' },
  ] : [
    { text: '로그인', icon: <Person />, path: '/login' },
  ]),
  { text: '정보', icon: <Info />, path: '/about' },
]

const Sidebar = () => {
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))
  const location = useLocation()
  const navigate = useNavigate()
  
  const { isSidebarOpen, toggleSidebar } = useAppStore()
  const { user, isAuthenticated, logout } = useAuthStore()

  const hasSubscription = user?.subscription?.isActive || false
  const menuItems = getMenuItems(hasSubscription)
  const bottomMenuItems = getBottomMenuItems(isAuthenticated)
  const displayName = user?.name || user?.id || '';

  const handleLogout = async () => {
    try {
      // 데모 모드에서는 API 호출 없이 바로 로그아웃
      if (user?.id?.startsWith('demo-') || user?.id?.startsWith('guest-')) {
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
      console.error('로그아웃 API 실패:', error)
      logout()
      navigate('/')
      toast.success('로그아웃되었습니다.')
    }
    
    if (isMobile) {
      toggleSidebar() // 모바일에서는 사이드바 닫기
    }
  }

  const isActive = (path: string) => {
    if (path === '/') {
      return location.pathname === '/'
    }
    return location.pathname.startsWith(path)
  }

  // 임시 데이터 (실제로는 user 객체에서 가져옴)
  const progressData = {
    daysRemaining: user?.dietPlan?.daysRemaining || 45,
    targetWeight: user?.dietPlan?.targetWeight || 65,
    currentWeight: user?.dietPlan?.currentWeight || 70,
    streakDays: 12,
    completionRate: 75,
  }

  const sidebarContent = (
    <Box sx={{ width: sidebarWidth, height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* 사이드바 헤더 - 데스크톱에서만 닫기 버튼 표시 */}
      {!isMobile && (
        <Box sx={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center', 
          p: 1, 
          borderBottom: '1px solid',
          borderColor: 'divider',
          minHeight: '56px'
        }}>
          <Typography variant="h6" sx={{ pl: 1, fontWeight: 600, color: 'primary.main' }}>
            🥑 Menu
          </Typography>
          <IconButton 
            onClick={toggleSidebar}
            size="small"
            sx={{ 
              transition: 'transform 0.2s ease',
              '&:hover': {
                transform: 'scale(1.1)',
                backgroundColor: 'action.hover',
              }
            }}
          >
            <ChevronLeft />
          </IconButton>
        </Box>
      )}

      {/* 사용자 정보 및 진행률 (로그인 시) */}
      {isAuthenticated && user && (
        <Box sx={{ p: 2, backgroundColor: 'primary.light', color: 'primary.contrastText', mb: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <Avatar
              src={user.profileImage}
              alt={displayName}
              sx={{ mr: 2, width: 40, height: 40 }}
            />
            <Box>
              <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                {displayName}
              </Typography>
              {hasSubscription && (
                <Chip
                  label="프리미엄"
                  size="small"
                  sx={{ backgroundColor: 'warning.main', color: 'white', fontSize: '0.7rem' }}
                />
              )}
            </Box>
          </Box>

          {user.dietPlan && (
            <>
              {/* D-day */}
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <EmojiEvents sx={{ mr: 1, fontSize: 16 }} />
                  목표까지 D-{progressData.daysRemaining}
                </Typography>
              </Box>

              {/* 목표 체중 */}
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <TrendingDown sx={{ mr: 1, fontSize: 16 }} />
                  목표: {progressData.targetWeight}kg
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={((progressData.currentWeight - progressData.targetWeight) / (progressData.currentWeight - progressData.targetWeight)) * 100}
                  sx={{ 
                    backgroundColor: 'rgba(255,255,255,0.3)', 
                    '& .MuiLinearProgress-bar': { backgroundColor: 'white' }
                  }}
                />
                <Typography variant="caption" sx={{ fontSize: '0.7rem' }}>
                  현재: {progressData.currentWeight}kg
                </Typography>
              </Box>

              {/* 연속 일수 */}
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" sx={{ fontSize: '0.8rem' }}>
                  🔥 {progressData.streakDays}일 연속 실천 중!
                </Typography>
              </Box>
            </>
          )}

          {/* 구독 버튼 (비구독자만) */}
          {!hasSubscription && (
            <Button
              component={Link}
              to="/subscription"
              variant="contained"
              size="small"
              fullWidth
              sx={{
                backgroundColor: 'warning.main',
                color: 'white',
                '&:hover': { backgroundColor: 'warning.dark' }
              }}
            >
              프리미엄 구독하기
            </Button>
          )}
        </Box>
      )}

      {/* 구독자 전용 캘린더 위젯 */}
      {isAuthenticated && hasSubscription && (
        <Box sx={{ p: 2, borderBottom: '1px solid', borderColor: 'divider' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <Today sx={{ mr: 1, color: 'primary.main' }} />
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              오늘의 일정
            </Typography>
            <Button
              component={Link}
              to="/calendar"
              size="small"
              sx={{ ml: 'auto', minWidth: 'auto', p: 0.5 }}
            >
              <EventNote fontSize="small" />
            </Button>
          </Box>

          {/* 오늘 날짜 */}
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {new Date().toLocaleDateString('ko-KR', { 
              year: 'numeric', 
              month: 'long', 
              day: 'numeric',
              weekday: 'long'
            })}
          </Typography>

          {/* 오늘의 식단 요약 */}
          <Box sx={{ backgroundColor: 'grey.50', borderRadius: 1, p: 1.5 }}>
            {(() => {
              // 동적 식단 데이터 (시간에 따라 변화)
              const currentHour = new Date().getHours()
              const todayMeals = [
                { 
                  meal: '아침', 
                  completed: currentHour >= 9, 
                  name: '아보카도 에그 베네딕트',
                  time: '07:30'
                },
                { 
                  meal: '점심', 
                  completed: currentHour >= 14, 
                  name: '그릴드 치킨 샐러드',
                  time: '12:30'
                },
                { 
                  meal: '저녁', 
                  completed: currentHour >= 20, 
                  name: '연어 스테이크',
                  time: '19:00'
                }
              ]
              
              const completedCount = todayMeals.filter(m => m.completed).length
              const totalCount = todayMeals.length
              
              return (
                <>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                    <Typography variant="body2" sx={{ fontWeight: 600, color: 'primary.main' }}>
                      오늘의 식단
                    </Typography>
                    <Chip 
                      label={`${completedCount}/${totalCount} 완료`}
                      size="small" 
                      color={completedCount === totalCount ? "success" : completedCount > 0 ? "warning" : "default"}
                      sx={{ height: 20, fontSize: '0.7rem' }}
                    />
                  </Box>
                  
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                    {todayMeals.map((item, index) => (
                      <Box key={index} sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <Box sx={{ display: 'flex', flexDirection: 'column' }}>
                          <Typography variant="caption" color="text.secondary">
                            {item.meal}
                          </Typography>
                          <Typography variant="caption" sx={{ fontSize: '0.6rem', color: 'text.disabled' }}>
                            {item.time}
                          </Typography>
                        </Box>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <Typography variant="caption" sx={{ fontSize: '0.7rem', mr: 0.5, maxWidth: 80, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                            {item.name}
                          </Typography>
                          <Box
                            sx={{
                              width: 8,
                              height: 8,
                              borderRadius: '50%',
                              backgroundColor: item.completed ? 'success.main' : 'grey.300'
                            }}
                          />
                        </Box>
                      </Box>
                    ))}
                  </Box>
                </>
              )
            })()}

            {/* 캘린더로 이동 버튼 */}
            <Button
              component={Link}
              to="/calendar"
              variant="outlined"
              size="small"
              fullWidth
              sx={{ 
                mt: 1.5, 
                py: 0.5,
                fontSize: '0.7rem',
                borderColor: 'primary.light',
                '&:hover': {
                  backgroundColor: 'primary.light',
                  color: 'white'
                }
              }}
            >
              전체 캘린더 보기
            </Button>
          </Box>
        </Box>
      )}

      {/* 메인 메뉴 */}
      <List sx={{ flex: 1, pt: isAuthenticated ? 1 : 2 }}>
        {menuItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton
              component={Link}
              to={item.path}
              onClick={isMobile ? toggleSidebar : undefined}
              selected={isActive(item.path)}
              sx={{
                mx: 1,
                borderRadius: 2,
                '&.Mui-selected': {
                  backgroundColor: theme.palette.primary.light + '20',
                  color: theme.palette.primary.main,
                  '&:hover': {
                    backgroundColor: theme.palette.primary.light + '30',
                  },
                },
              }}
            >
              <ListItemIcon
                sx={{
                  color: isActive(item.path) ? theme.palette.primary.main : 'inherit',
                  minWidth: 40,
                }}
              >
                {item.icon}
              </ListItemIcon>
              <ListItemText 
                primary={item.text}
                primaryTypographyProps={{
                  fontWeight: isActive(item.path) ? 600 : 400,
                }}
              />
            </ListItemButton>
          </ListItem>
        ))}
      </List>

      {/* 하단 메뉴 */}
      <Box>
        <Divider sx={{ mx: 2 }} />
        <List sx={{ pb: 2 }}>
          {bottomMenuItems.map((item) => (
            <ListItem key={item.text} disablePadding>
              <ListItemButton
                component={Link}
                to={item.path}
                onClick={isMobile ? toggleSidebar : undefined}
                selected={isActive(item.path)}
                sx={{
                  mx: 1,
                  borderRadius: 2,
                  '&.Mui-selected': {
                    backgroundColor: theme.palette.primary.light + '20',
                    color: theme.palette.primary.main,
                    '&:hover': {
                      backgroundColor: theme.palette.primary.light + '30',
                    },
                  },
                }}
              >
                <ListItemIcon
                  sx={{
                    color: isActive(item.path) ? theme.palette.primary.main : 'inherit',
                    minWidth: 40,
                  }}
                >
                  {item.icon}
                </ListItemIcon>
                <ListItemText 
                  primary={item.text}
                  primaryTypographyProps={{
                    fontWeight: isActive(item.path) ? 600 : 400,
                  }}
                />
              </ListItemButton>
            </ListItem>
          ))}
          
          {/* 로그아웃 버튼 (로그인 상태일 때만) */}
          {isAuthenticated && (
            <ListItem disablePadding>
              <ListItemButton
                onClick={handleLogout}
                sx={{
                  mx: 1,
                  borderRadius: 2,
                  color: 'error.main',
                  '&:hover': {
                    backgroundColor: 'error.light',
                    color: 'error.dark',
                  },
                }}
              >
                <ListItemIcon sx={{ color: 'inherit', minWidth: 40 }}>
                  <Logout />
                </ListItemIcon>
                <ListItemText 
                  primary="로그아웃"
                  primaryTypographyProps={{
                    fontWeight: 500,
                  }}
                />
              </ListItemButton>
            </ListItem>
          )}
        </List>
      </Box>
    </Box>
  )

  return (
    <>
      {/* 데스크톱 사이드바 */}
      {!isMobile && (
        <>
          {/* 전체 사이드바 */}
          <Drawer
            variant="persistent"
            anchor="left"
            open={isSidebarOpen}
            sx={{
              width: isSidebarOpen ? sidebarWidth : 0,
              flexShrink: 0,
              transition: 'width 0.3s ease',
              '& .MuiDrawer-paper': {
                width: sidebarWidth,
                boxSizing: 'border-box',
                borderRight: '1px solid',
                borderColor: 'divider',
                top: '64px', // AppBar 높이만큼 아래로
                height: 'calc(100vh - 64px)',
                transition: 'transform 0.3s ease',
              },
            }}
          >
            {sidebarContent}
          </Drawer>

          {/* 미니 사이드바 (닫혔을 때) */}
          {!isSidebarOpen && (
            <Box
              sx={{
                width: '64px',
                backgroundColor: 'background.paper',
                borderRight: '1px solid',
                borderColor: 'divider',
                height: 'calc(100vh - 64px)',
                position: 'fixed',
                top: '64px',
                left: 0,
                zIndex: 1200,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                py: 1,
              }}
            >
              {/* 메뉴 열기 버튼 */}
              <IconButton 
                onClick={toggleSidebar}
                sx={{ 
                  mb: 2,
                  transition: 'transform 0.2s ease',
                  '&:hover': {
                    transform: 'scale(1.1)',
                    backgroundColor: 'action.hover',
                  }
                }}
              >
                <ChevronRight />
              </IconButton>

              {/* 주요 메뉴 아이콘들 */}
              {menuItems.slice(0, 4).map((item) => (
                <IconButton
                  key={item.text}
                  component={Link}
                  to={item.path}
                  sx={{
                    mb: 1,
                    color: isActive(item.path) ? 'primary.main' : 'text.secondary',
                    '&:hover': {
                      backgroundColor: 'action.hover',
                    }
                  }}
                  title={item.text}
                >
                  {item.icon}
                </IconButton>
              ))}
            </Box>
          )}
        </>
      )}

      {/* 모바일 사이드바 */}
      {isMobile && (
        <Drawer
          variant="temporary"
          anchor="left"
          open={isSidebarOpen}
          onClose={toggleSidebar}
          ModalProps={{
            keepMounted: true, // 성능 향상을 위해
          }}
          sx={{
            '& .MuiDrawer-paper': {
              width: sidebarWidth,
              boxSizing: 'border-box',
            },
          }}
        >
          {sidebarContent}
        </Drawer>
      )}
    </>
  )
}

export default Sidebar
