import { Routes, Route } from 'react-router-dom'
import { Layout } from '@/components/Layout'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { ChatPage } from '@/pages/ChatPage'
import { MapPage } from '@/pages/MapPage'
import { CalendarPage } from '@/pages/CalendarPage'
import { ProfilePage } from '@/pages/ProfilePage'
import NaverCallback from '@/pages/NaverCallback'
import { MainPage } from '@/pages/MainPage'
import { SubscribePage } from '@/pages/SubscribePage'
import { AuthRouteGuard } from '@/components/AuthRouteGuard'

function App() {
  return (
    <div className="min-h-screen bg-background">
      <Layout>
        <AuthRouteGuard />
        <Routes>
          {/* 공개 페이지 */}
          <Route path="/" element={<MainPage />} />
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/map" element={<MapPage />} />
          <Route path="/auth/naver/callback" element={<NaverCallback />} />
          
          {/* 인증 필요 페이지 */}
          <Route path="/calendar" element={
            <ProtectedRoute>
              <CalendarPage />
            </ProtectedRoute>
          } />
          <Route path="/profile" element={
            <ProtectedRoute>
              <ProfilePage />
            </ProtectedRoute>
          } />
          {/* 구독 페이지 */}
          <Route path="/subscribe" element={<SubscribePage />} />
        </Routes>
      </Layout>
    </div>
  )
}

export default App
