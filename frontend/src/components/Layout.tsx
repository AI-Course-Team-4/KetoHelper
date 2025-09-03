import { Outlet } from 'react-router-dom'
import { Box, Container, useTheme, useMediaQuery } from '@mui/material'
import Header from './Header'
import Footer from './Footer'
import Sidebar from './Sidebar'
import { useAppStore } from '@store/appStore'

const Layout = () => {
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))
  const { isSidebarOpen } = useAppStore()

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <Header />
      
      <Box sx={{ display: 'flex', flex: 1 }}>
        <Sidebar />
        
        <Box
          component="main"
          sx={{
            flex: 1,
            transition: 'margin-left 0.3s ease',
            marginLeft: isMobile ? '0' : (isSidebarOpen ? '240px' : '64px'), // 닫혔을 때도 미니 사이드바 공간 확보
            minHeight: 'calc(100vh - 64px)', // AppBar 높이 제외
          }}
        >
          <Container
            maxWidth="lg"
            sx={{
              py: { xs: 2, sm: 3 },
              px: { xs: 1, sm: 2, md: 3 },
              minHeight: '100%',
            }}
          >
            <Outlet />
          </Container>
        </Box>
      </Box>
      
      <Footer />
    </Box>
  )
}

export default Layout
