import { Box, Typography, Button } from '@mui/material'
import { Home, ArrowBack } from '@mui/icons-material'
import { Link, useNavigate } from 'react-router-dom'

const NotFoundPage = () => {
  const navigate = useNavigate()

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        textAlign: 'center',
        p: 3,
      }}
    >
      <Typography
        variant="h1"
        sx={{
          fontSize: '8rem',
          fontWeight: 700,
          color: 'primary.main',
          mb: 2,
        }}
      >
        404
      </Typography>
      
      <Typography variant="h4" sx={{ fontWeight: 600, mb: 2 }}>
        페이지를 찾을 수 없습니다
      </Typography>
      
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4, maxWidth: 500 }}>
        요청하신 페이지가 존재하지 않거나 이동되었을 수 있습니다.
        홈페이지로 돌아가서 다시 시도해보세요.
      </Typography>
      
      <Box sx={{ display: 'flex', gap: 2, flexDirection: { xs: 'column', sm: 'row' } }}>
        <Button
          variant="contained"
          size="large"
          startIcon={<Home />}
          component={Link}
          to="/"
        >
          홈으로 가기
        </Button>
        
        <Button
          variant="outlined"
          size="large"
          startIcon={<ArrowBack />}
          onClick={() => navigate(-1)}
        >
          이전 페이지
        </Button>
      </Box>
      
      {/* 아바카도 이모지 장식 */}
      <Typography
        sx={{
          fontSize: '4rem',
          mt: 4,
          opacity: 0.3,
        }}
      >
        🥑
      </Typography>
    </Box>
  )
}

export default NotFoundPage
