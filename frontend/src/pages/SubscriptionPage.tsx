import { useState } from 'react'
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Grid,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  FormLabel,
  RadioGroup,
  FormControlLabel,
  Radio,
  Divider,
} from '@mui/material'
import {
  Check,
  Star,
  CalendarMonth,
  TrendingUp,
  Restaurant,
  Psychology,
  Support,
} from '@mui/icons-material'
import { useAuthStore } from '@store/authStore'

const SubscriptionPage = () => {
  const { user, isAuthenticated } = useAuthStore()
  const [paymentDialog, setPaymentDialog] = useState(false)
  const [selectedPlan, setSelectedPlan] = useState<'monthly' | 'yearly'>('monthly')
  const [paymentMethod, setPaymentMethod] = useState('card')

  const hasSubscription = user?.subscription?.isActive || false

  const plans = {
    monthly: {
      name: '월간 구독',
      price: 9900,
      originalPrice: null,
      billingCycle: 'monthly' as const,
      savings: null,
    },
    yearly: {
      name: '연간 구독',
      price: 79200,
      originalPrice: 118800,
      billingCycle: 'yearly' as const,
      savings: '33% 절약',
    },
  }

  const features = [
    {
      icon: <CalendarMonth color="primary" />,
      title: '개인 맞춤 식단 캘린더',
      description: '매일의 아침, 점심, 저녁 식단을 체계적으로 관리하세요',
      premium: true,
    },
    {
      icon: <TrendingUp color="primary" />,
      title: '상세 진행률 추적',
      description: '체중 변화, 연속 실천 일수, 목표 달성률을 한눈에 확인',
      premium: true,
    },
    {
      icon: <Psychology color="primary" />,
      title: 'AI 고급 추천 시스템',
      description: '개인 선호도와 목표를 고려한 정밀한 AI 추천',
      premium: true,
    },
    {
      icon: <Restaurant color="primary" />,
      title: '무제한 레시피 및 식당 정보',
      description: '프리미엄 레시피와 키토 친화적 식당 정보 무제한 이용',
      premium: true,
    },
    {
      icon: <Support color="primary" />,
      title: '우선 고객 지원',
      description: '24시간 우선 고객 지원 서비스',
      premium: true,
    },
  ]

  const freeFeatures = [
    '기본 키토 레시피 3개',
    '기본 식당 추천 3개',
    '기본 AI 추천',
    '커뮤니티 이용',
  ]

  const handleSubscribe = () => {
    if (!isAuthenticated) {
      // 로그인 페이지로 리다이렉트
      window.location.href = '/login'
      return
    }
    setPaymentDialog(true)
  }

  const handlePayment = () => {
    // TODO: 실제 결제 로직 구현
    console.log('Payment processing:', {
      plan: selectedPlan,
      paymentMethod,
      amount: plans[selectedPlan].price,
    })
    setPaymentDialog(false)
    // 결제 성공 후 처리
  }

  if (hasSubscription) {
    return (
      <Box>
        <Typography variant="h3" sx={{ fontWeight: 700, mb: 4 }}>
          🎉 구독 관리
        </Typography>

        <Card sx={{ p: 4, mb: 4, background: 'linear-gradient(135deg, #2E7D32 0%, #4CAF50 100%)', color: 'white' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <Star sx={{ mr: 1 }} />
            <Typography variant="h5" sx={{ fontWeight: 600 }}>
              프리미엄 구독 중
            </Typography>
          </Box>
          <Typography variant="body1" sx={{ mb: 3, opacity: 0.9 }}>
            KetoHelper 프리미엄의 모든 기능을 마음껏 이용하세요!
          </Typography>
          
          <Grid container spacing={3}>
            <Grid item xs={12} sm={6}>
              <Typography variant="body2" sx={{ mb: 1 }}>
                <strong>구독 플랜:</strong> {user?.subscription?.plan === 'premium' ? '프리미엄' : '무료'}
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                <strong>다음 결제일:</strong> {user?.subscription?.endDate || '2025-01-20'}
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6}>
              <Typography variant="body2" sx={{ mb: 1 }}>
                <strong>자동 갱신:</strong> {user?.subscription?.autoRenewal ? '활성화' : '비활성화'}
              </Typography>
            </Grid>
          </Grid>
        </Card>

        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
                  이용 중인 프리미엄 기능
                </Typography>
                <List>
                  {features.map((feature, index) => (
                    <ListItem key={index}>
                      <ListItemIcon>{feature.icon}</ListItemIcon>
                      <ListItemText
                        primary={feature.title}
                        secondary={feature.description}
                      />
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                  구독 설정
                </Typography>
                <Button variant="outlined" fullWidth sx={{ mb: 2 }}>
                  결제 정보 변경
                </Button>
                <Button variant="outlined" fullWidth sx={{ mb: 2 }}>
                  자동 갱신 설정
                </Button>
                <Button variant="outlined" color="error" fullWidth>
                  구독 취소
                </Button>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>
    )
  }

  return (
    <Box>
      <Typography variant="h3" sx={{ fontWeight: 700, mb: 2, textAlign: 'center' }}>
        KetoHelper 프리미엄
      </Typography>
      <Typography variant="h6" color="text.secondary" sx={{ mb: 6, textAlign: 'center' }}>
        더욱 체계적이고 효과적인 키토 라이프를 경험하세요
      </Typography>

      {/* 가격 플랜 */}
      <Grid container spacing={3} sx={{ mb: 6 }}>
        <Grid item xs={12} md={6}>
          <Card
            sx={{
              height: '100%',
              border: selectedPlan === 'monthly' ? 2 : 1,
              borderColor: selectedPlan === 'monthly' ? 'primary.main' : 'divider',
              cursor: 'pointer',
            }}
            onClick={() => setSelectedPlan('monthly')}
          >
            <CardContent sx={{ p: 4 }}>
              <Typography variant="h5" sx={{ fontWeight: 600, mb: 2 }}>
                월간 구독
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'baseline', mb: 2 }}>
                <Typography variant="h3" sx={{ fontWeight: 700, color: 'primary.main' }}>
                  ₩9,900
                </Typography>
                <Typography variant="body1" color="text.secondary" sx={{ ml: 1 }}>
                  /월
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                언제든지 취소 가능
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Card
            sx={{
              height: '100%',
              border: selectedPlan === 'yearly' ? 2 : 1,
              borderColor: selectedPlan === 'yearly' ? 'primary.main' : 'divider',
              cursor: 'pointer',
              position: 'relative',
              overflow: 'visible', // Chip이 잘리지 않도록 설정
            }}
            onClick={() => setSelectedPlan('yearly')}
          >
            <Chip
              label="33% 절약"
              color="secondary"
              sx={{
                position: 'absolute',
                top: 10,
                right: 10,
                fontWeight: 600,
                zIndex: 1, // 다른 요소 위에 표시되도록 설정
              }}
            />
            <CardContent sx={{ p: 4 }}>
              <Typography variant="h5" sx={{ fontWeight: 600, mb: 2 }}>
                연간 구독
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'baseline', mb: 1 }}>
                <Typography variant="h3" sx={{ fontWeight: 700, color: 'primary.main' }}>
                  ₩79,200
                </Typography>
                <Typography variant="body1" color="text.secondary" sx={{ ml: 1 }}>
                  /년
                </Typography>
              </Box>
              <Typography variant="body2" sx={{ textDecoration: 'line-through', color: 'text.secondary' }}>
                정가 ₩118,800
              </Typography>
              <Typography variant="body2" color="text.secondary">
                월 ₩6,600 (33% 할인)
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* 기능 비교 */}
      <Card sx={{ mb: 6 }}>
        <CardContent sx={{ p: 4 }}>
          <Typography variant="h5" sx={{ fontWeight: 600, mb: 3, textAlign: 'center' }}>
            프리미엄으로 더 많은 기능을 이용하세요
          </Typography>
          
          <Grid container spacing={4}>
            <Grid item xs={12} md={6}>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2, color: 'text.secondary' }}>
                무료 플랜
              </Typography>
              <List>
                {freeFeatures.map((feature, index) => (
                  <ListItem key={index} sx={{ py: 0.5 }}>
                    <ListItemIcon>
                      <Check color="disabled" />
                    </ListItemIcon>
                    <ListItemText
                      primary={feature}
                      primaryTypographyProps={{ color: 'text.secondary' }}
                    />
                  </ListItem>
                ))}
              </List>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" sx={{ fontWeight: 600, color: 'primary.main' }}>
                  프리미엄 플랜
                </Typography>
                <Star sx={{ ml: 1, color: 'warning.main' }} />
              </Box>
              <List>
                {features.map((feature, index) => (
                  <ListItem key={index} sx={{ py: 1 }}>
                    <ListItemIcon>{feature.icon}</ListItemIcon>
                    <ListItemText
                      primary={feature.title}
                      secondary={feature.description}
                    />
                  </ListItem>
                ))}
              </List>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* 구독 버튼 */}
      <Box sx={{ textAlign: 'center' }}>
        <Button
          variant="contained"
          size="large"
          onClick={handleSubscribe}
          sx={{
            py: 2,
            px: 6,
            fontSize: '1.2rem',
            fontWeight: 600,
          }}
        >
          {selectedPlan === 'yearly' ? '연간 구독하기' : '월간 구독하기'} - ₩{plans[selectedPlan].price.toLocaleString()}
        </Button>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
          언제든지 취소 가능 • 안전한 결제 • 즉시 이용 가능
        </Typography>
      </Box>

      {/* 결제 다이얼로그 */}
      <Dialog open={paymentDialog} onClose={() => setPaymentDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>결제 정보</DialogTitle>
        <DialogContent>
          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" sx={{ mb: 1 }}>
              선택한 플랜: {plans[selectedPlan].name}
            </Typography>
            <Typography variant="body1" color="primary.main" sx={{ fontWeight: 600 }}>
              ₩{plans[selectedPlan].price.toLocaleString()}
              {selectedPlan === 'yearly' && (
                <Typography component="span" variant="body2" sx={{ ml: 1, color: 'text.secondary' }}>
                  (월 ₩6,600)
                </Typography>
              )}
            </Typography>
          </Box>

          <Divider sx={{ mb: 3 }} />

          <FormControl component="fieldset" fullWidth>
            <FormLabel component="legend" sx={{ mb: 2 }}>
              결제 방법을 선택하세요
            </FormLabel>
            <RadioGroup value={paymentMethod} onChange={(e) => setPaymentMethod(e.target.value)}>
              <FormControlLabel value="card" control={<Radio />} label="신용카드/체크카드" />
              <FormControlLabel value="kakao" control={<Radio />} label="카카오페이" />
              <FormControlLabel value="naver" control={<Radio />} label="네이버페이" />
            </RadioGroup>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPaymentDialog(false)}>취소</Button>
          <Button variant="contained" onClick={handlePayment}>
            결제하기
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default SubscriptionPage
