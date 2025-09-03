import { useState, useEffect } from 'react'
import { Box, Paper, Typography, Button, Divider, CircularProgress, Alert } from '@mui/material'
import { Google } from '@mui/icons-material'
import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '@store/authStore'
import { googleAuthService } from '@services/googleAuthService'
import { authService } from '@services/authService'
import { toast } from 'react-hot-toast'

const LoginPage = () => {
  const navigate = useNavigate()
  const { setUser, setLoading } = useAuthStore()
  const [isGoogleLoading, setIsGoogleLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Google Client ID 확인
  const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID

  useEffect(() => {
    // Google API 초기화
    googleAuthService.initialize().catch((err) => {
      console.error('Google API 초기화 실패:', err)
      setError('Google 로그인 서비스를 초기화할 수 없습니다.')
    })
  }, [])

  const handleGoogleLogin = async () => {
    // 임시로 가짜 사용자 데이터로 로그인 시뮬레이션
    setIsGoogleLoading(true)
    setError(null)

    try {
      // 임시 사용자 데이터
      const mockUser = {
        id: 'demo-user-123',
        name: '홍길동',
        email: 'demo@ketohelper.com',
        profileImage: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150&h=150&fit=crop&crop=face',
        preferences: {
          allergies: ['땅콩', '새우'],
          dislikes: ['브로콜리'],
          dietaryRestrictions: ['글루텐 프리']
        },
        subscription: {
          isActive: true,
          plan: 'premium' as const,
          startDate: '2024-01-01',
          endDate: '2024-12-31',
          autoRenewal: true
        },
        dietPlan: {
          currentWeight: 70,
          targetWeight: 65,
          intensity: 'medium' as const,
          startDate: '2024-01-01',
          estimatedEndDate: '2024-06-01',
          daysRemaining: 45,
          dailyCalories: 1500,
          macroTargets: {
            carbs: 5,
            protein: 25,
            fat: 70
          }
        },
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      }

      // 0.5초 로딩 시뮬레이션
      await new Promise(resolve => setTimeout(resolve, 500))
      
      // 사용자 정보 저장
      setUser(mockUser)
      
      toast.success(`환영합니다, ${mockUser.name}님! (데모 모드)`)
      navigate('/')
      
    } catch (error: any) {
      console.error('로그인 실패:', error)
      setError(error.message || '로그인 중 오류가 발생했습니다.')
      toast.error('로그인에 실패했습니다.')
    } finally {
      setIsGoogleLoading(false)
    }
  }

  // 구독자가 아닌 사용자로 로그인하는 핸들러 (추가)
  const handleGuestLogin = async () => {
    setIsGoogleLoading(true)
    setError(null)

    try {
      // 비구독 사용자 데이터
      const guestUser = {
        id: 'guest-user-456',
        name: '김철수',
        email: 'guest@ketohelper.com',
        profileImage: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&h=150&fit=crop&crop=face',
        preferences: {
          allergies: [],
          dislikes: ['양파'],
          dietaryRestrictions: []
        },
        subscription: {
          isActive: false,
          plan: 'free' as const,
          startDate: undefined,
          endDate: undefined,
          autoRenewal: false
        },
        dietPlan: {
          currentWeight: 75,
          targetWeight: 70,
          intensity: 'low' as const,
          startDate: '2024-01-15',
          estimatedEndDate: '2024-08-15',
          daysRemaining: 120,
          dailyCalories: 1800,
          macroTargets: {
            carbs: 10,
            protein: 25,
            fat: 65
          }
        },
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      }

      await new Promise(resolve => setTimeout(resolve, 500))
      setUser(guestUser)
      
      toast.success(`환영합니다, ${guestUser.name}님! (무료 사용자)`)
      navigate('/')
      
    } catch (error: any) {
      setError(error.message || '로그인 중 오류가 발생했습니다.')
    } finally {
      setIsGoogleLoading(false)
    }
  }

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #2E7D32 0%, #4CAF50 100%)',
        p: 2,
      }}
    >
      <Paper
        elevation={8}
        sx={{
          p: 4,
          width: '100%',
          maxWidth: 400,
          textAlign: 'center',
          borderRadius: 3,
        }}
      >
        {/* 로고 */}
        <Typography variant="h3" sx={{ mb: 1, color: 'primary.main' }}>
          🥑
        </Typography>
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
          KetoHelper
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
          키토 라이프스타일을 시작해보세요
        </Typography>
        
        <Typography variant="body2" color="text.secondary" sx={{ mb: 4, fontStyle: 'italic' }}>
          💡 데모 모드: 두 종류의 사용자 경험을 미리 체험해보세요
        </Typography>

        {/* 에러 메시지 */}
        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        {/* Google Client ID 설정 안내 */}
        {(!googleClientId || googleClientId === 'your-google-client-id') && (
          <Alert severity="warning" sx={{ mb: 3 }}>
            <Typography variant="body2">
              Google 로그인을 사용하려면 환경 변수를 설정해주세요:
            </Typography>
            <Typography variant="body2" sx={{ mt: 1, fontFamily: 'monospace', fontSize: '0.8rem' }}>
              VITE_GOOGLE_CLIENT_ID=your-actual-client-id
            </Typography>
          </Alert>
        )}

        {/* 데모 로그인 버튼들 */}
        <Box sx={{ mb: 3, display: 'flex', flexDirection: 'column', gap: 2 }}>
          <Button
            fullWidth
            variant="contained"
            size="large"
            startIcon={isGoogleLoading ? <CircularProgress size={20} color="inherit" /> : <Google />}
            onClick={handleGoogleLogin}
            disabled={isGoogleLoading}
            sx={{
              py: 1.5,
              backgroundColor: '#4285f4',
              '&:hover': {
                backgroundColor: '#3367d6',
              },
            }}
          >
            {isGoogleLoading ? '로그인 중...' : '데모 로그인 (프리미엄 사용자)'}
          </Button>

          <Button
            fullWidth
            variant="outlined"
            size="large"
            onClick={handleGuestLogin}
            disabled={isGoogleLoading}
            sx={{
              py: 1.5,
              borderColor: '#ff9800',
              color: '#ff9800',
              '&:hover': {
                backgroundColor: '#ff9800',
                color: 'white',
              },
            }}
          >
            데모 로그인 (무료 사용자)
          </Button>
        </Box>

        <Divider sx={{ my: 3 }}>
          <Typography variant="body2" color="text.secondary">
            또는
          </Typography>
        </Divider>

        {/* 게스트로 계속하기 */}
        <Button
          fullWidth
          variant="outlined"
          size="large"
          component={Link}
          to="/"
          sx={{ mb: 2 }}
        >
          게스트로 둘러보기
        </Button>

        {/* 개인정보 처리방침 */}
        <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
          로그인 시 <Link to="/privacy">개인정보처리방침</Link> 및{' '}
          <Link to="/terms">이용약관</Link>에 동의하는 것으로 간주됩니다.
        </Typography>
      </Paper>
    </Box>
  )
}

export default LoginPage
