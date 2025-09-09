import { Box, Container, Typography, Link, Grid, Divider } from '@mui/material'
import { Link as RouterLink } from 'react-router-dom'

const Footer = () => {
  const currentYear = new Date().getFullYear()

  return (
    <Box
      component="footer"
      sx={{
        backgroundColor: 'background.paper',
        borderTop: '1px solid',
        borderColor: 'divider',
        py: 6,
        mt: 'auto',
      }}
    >
      <Container maxWidth="lg">
        <Grid container spacing={4}>
          {/* 로고 및 설명 */}
          <Grid item xs={12} md={4}>
            <Typography variant="h6" sx={{ fontWeight: 700, mb: 2, color: 'primary.main' }}>
              🥑 KetoHelper
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              AI 기반 키토제닉 다이어트 식단 추천 및 관리 서비스입니다. 
              건강한 키토 라이프스타일을 시작해보세요.
            </Typography>
          </Grid>

          {/* 서비스 링크 */}
          <Grid item xs={12} sm={6} md={2}>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
              서비스
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Link
                component={RouterLink}
                to="/meals"
                color="text.secondary"
                underline="hover"
                variant="body2"
              >
                식단 추천
              </Link>
              <Link
                component={RouterLink}
                to="/restaurants"
                color="text.secondary"
                underline="hover"
                variant="body2"
              >
                식당 추천
              </Link>
              <Link
                component={RouterLink}
                to="/settings"
                color="text.secondary"
                underline="hover"
                variant="body2"
              >
                설정
              </Link>
            </Box>
          </Grid>

          {/* 정보 링크 */}
          <Grid item xs={12} sm={6} md={2}>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
              정보
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Link
                href="#"
                color="text.secondary"
                underline="hover"
                variant="body2"
              >
                키토 가이드
              </Link>
              <Link
                href="#"
                color="text.secondary"
                underline="hover"
                variant="body2"
              >
                영양 정보
              </Link>
              <Link
                href="#"
                color="text.secondary"
                underline="hover"
                variant="body2"
              >
                FAQ
              </Link>
            </Box>
          </Grid>

          {/* 지원 링크 */}
          <Grid item xs={12} sm={6} md={2}>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
              지원
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Link
                href="#"
                color="text.secondary"
                underline="hover"
                variant="body2"
              >
                문의하기
              </Link>
              <Link
                href="#"
                color="text.secondary"
                underline="hover"
                variant="body2"
              >
                개발자 정보
              </Link>
              <Link
                href="https://github.com/your-username/mainProject-Team4"
                color="text.secondary"
                underline="hover"
                variant="body2"
                target="_blank"
                rel="noopener noreferrer"
              >
                GitHub
              </Link>
            </Box>
          </Grid>

          {/* 법적 정보 */}
          <Grid item xs={12} sm={6} md={2}>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
              법적 정보
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Link
                href="#"
                color="text.secondary"
                underline="hover"
                variant="body2"
              >
                이용약관
              </Link>
              <Link
                href="#"
                color="text.secondary"
                underline="hover"
                variant="body2"
              >
                개인정보처리방침
              </Link>
              <Link
                href="#"
                color="text.secondary"
                underline="hover"
                variant="body2"
              >
                쿠키 정책
              </Link>
            </Box>
          </Grid>
        </Grid>

        <Divider sx={{ my: 4 }} />

        {/* 저작권 정보 */}
        <Box
          sx={{
            display: 'flex',
            flexDirection: { xs: 'column', sm: 'row' },
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: 2,
          }}
        >
          <Typography variant="body2" color="text.secondary">
            © {currentYear} KetoHelper. All rights reserved.
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Made with ❤️ for the Keto Community
          </Typography>
        </Box>
      </Container>
    </Box>
  )
}

export default Footer
