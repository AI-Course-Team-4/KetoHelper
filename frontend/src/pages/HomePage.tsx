import { Box, Typography, Button, Grid, Card, CardContent, Container } from '@mui/material'
import { Link } from 'react-router-dom'
import { Restaurant, MenuBook, Settings, TrendingUp } from '@mui/icons-material'
import { useAuthStore } from '@store/authStore'

const HomePage = () => {
  const { isAuthenticated, user } = useAuthStore()
  const displayName = user?.name || user?.id || ''

  const quickAccessCards = [
    {
      title: '식단 추천',
      description: 'AI가 추천하는 맞춤형 키토 레시피를 확인해보세요',
      icon: <MenuBook sx={{ fontSize: 40 }} />,
      path: '/meals',
      color: 'primary.main',
    },
    {
      title: '식당 추천',
      description: '근처 키토 친화적인 식당을 찾아보세요',
      icon: <Restaurant sx={{ fontSize: 40 }} />,
      path: '/restaurants',
      color: 'secondary.main',
    },
    {
      title: '설정',
      description: '개인 선호도와 알레르기 정보를 관리하세요',
      icon: <Settings sx={{ fontSize: 40 }} />,
      path: '/settings',
      color: 'success.main',
    },
  ]

  return (
    <Box>
      {/* 히어로 섹션 */}
      <Box
        sx={{
          background: 'linear-gradient(135deg, #2E7D32 0%, #4CAF50 100%)',
          color: 'white',
          py: 8,
          px: 3,
          borderRadius: 3,
          mb: 6,
          textAlign: 'center',
        }}
      >
        <Container maxWidth="md">
          <Typography variant="h2" sx={{ fontWeight: 700, mb: 3 }}>
            🥑 KetoHelper
          </Typography>
          <Typography variant="h5" sx={{ mb: 4, opacity: 0.9 }}>
            AI 기반 키토제닉 다이어트 추천 서비스
          </Typography>
          <Typography variant="body1" sx={{ mb: 4, fontSize: '1.1rem', opacity: 0.8 }}>
            개인화된 식단 추천부터 키토 친화적인 식당 정보까지,
            <br />
            건강한 키토 라이프스타일을 시작해보세요.
          </Typography>
          
          {!isAuthenticated ? (
            <Button
              variant="contained"
              size="large"
              component={Link}
              to="/login"
              sx={{
                backgroundColor: 'white',
                color: 'primary.main',
                px: 4,
                py: 1.5,
                fontSize: '1.1rem',
                '&:hover': {
                  backgroundColor: 'grey.100',
                },
              }}
            >
              시작하기
            </Button>
          ) : (
            <Button
              variant="contained"
              size="large"
              component={Link}
              to="/meals"
              sx={{
                backgroundColor: 'white',
                color: 'primary.main',
                px: 4,
                py: 1.5,
                fontSize: '1.1rem',
                '&:hover': {
                  backgroundColor: 'grey.100',
                },
              }}
            >
              식단 추천 받기
            </Button>
          )}
        </Container>
      </Box>

      {/* 사용자 환영 메시지 (로그인 시) */}
      {isAuthenticated && user && (
        <Box sx={{ mb: 6 }}>
          <Typography variant="h4" sx={{ fontWeight: 600, mb: 2 }}>
            안녕하세요, {displayName}님! 👋
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
            오늘도 건강한 키토 라이프를 이어가세요.
          </Typography>
          
          {/* 간단한 통계 카드 */}
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} sm={4}>
              <Card sx={{ textAlign: 'center', p: 2 }}>
                <CardContent>
                  <TrendingUp sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    키토 진행률
                  </Typography>
                  <Typography variant="h4" color="primary.main" sx={{ fontWeight: 700 }}>
                    75%
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={4}>
              <Card sx={{ textAlign: 'center', p: 2 }}>
                <CardContent>
                  <MenuBook sx={{ fontSize: 40, color: 'secondary.main', mb: 1 }} />
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    시도한 레시피
                  </Typography>
                  <Typography variant="h4" color="secondary.main" sx={{ fontWeight: 700 }}>
                    12
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={4}>
              <Card sx={{ textAlign: 'center', p: 2 }}>
                <CardContent>
                  <Restaurant sx={{ fontSize: 40, color: 'success.main', mb: 1 }} />
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    방문한 식당
                  </Typography>
                  <Typography variant="h4" color="success.main" sx={{ fontWeight: 700 }}>
                    8
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Box>
      )}

      {/* 퀵 액세스 카드 */}
      <Box sx={{ mb: 6 }}>
        <Typography variant="h4" sx={{ fontWeight: 600, mb: 4, textAlign: 'center' }}>
          무엇을 도와드릴까요?
        </Typography>
        
        <Grid container spacing={3}>
          {quickAccessCards.map((card, index) => (
            <Grid item xs={12} md={4} key={index}>
              <Card
                component={Link}
                to={card.path}
                sx={{
                  textDecoration: 'none',
                  height: '100%',
                  transition: 'all 0.3s ease',
                  cursor: 'pointer',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: 4,
                  },
                }}
              >
                <CardContent sx={{ textAlign: 'center', p: 4 }}>
                  <Box sx={{ color: card.color, mb: 2 }}>
                    {card.icon}
                  </Box>
                  <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                    {card.title}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {card.description}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Box>

      {/* 키토 다이어트 소개 섹션 */}
      <Box
        sx={{
          backgroundColor: 'background.paper',
          p: 4,
          borderRadius: 3,
          border: '1px solid',
          borderColor: 'divider',
        }}
      >
        <Typography variant="h5" sx={{ fontWeight: 600, mb: 3, textAlign: 'center' }}>
          키토제닉 다이어트란?
        </Typography>
        
        <Grid container spacing={4}>
          <Grid item xs={12} md={6}>
            <Typography variant="body1" sx={{ mb: 2, lineHeight: 1.8 }}>
              키토제닉 다이어트는 <strong>저탄수화물, 고지방</strong> 식단으로, 
              몸이 탄수화물 대신 지방을 주요 에너지원으로 사용하도록 하는 식단법입니다.
            </Typography>
            <Typography variant="body1" sx={{ lineHeight: 1.8 }}>
              일반적으로 탄수화물 5-10%, 단백질 15-25%, 지방 70-80%의 비율로 구성되며,
              체중 감량과 혈당 관리에 도움이 될 수 있습니다.
            </Typography>
          </Grid>
          <Grid item xs={12} md={6}>
            <Box
              sx={{
                backgroundColor: 'primary.light',
                p: 3,
                borderRadius: 2,
                color: 'primary.contrastText',
              }}
            >
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                KetoHelper의 장점
              </Typography>
              <ul style={{ margin: 0, paddingLeft: '20px' }}>
                <li>AI 기반 개인화 추천</li>
                <li>알레르기 및 선호도 고려</li>
                <li>영양 성분 자동 계산</li>
                <li>키토 친화적 식당 정보</li>
                <li>지속적인 학습 및 개선</li>
              </ul>
            </Box>
          </Grid>
        </Grid>
      </Box>
    </Box>
  )
}

export default HomePage
