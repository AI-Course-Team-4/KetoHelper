import { Routes, Route } from 'react-router-dom'
import { Layout } from '@/components/Layout'
import { ChatPage } from '@/pages/ChatPage'
import { MapPage } from '@/pages/MapPage'
import { CalendarPage } from '@/pages/CalendarPage'
import { ProfilePage } from '@/pages/ProfilePage'
// Toaster는 react-hot-toast로 대체됨
import NaverCallback from '@/pages/NaverCallback'
import { Toaster as HotToaster } from 'react-hot-toast'
import { MainPage } from '@/pages/MainPage'
import { SubscribePage } from '@/pages/SubscribePage'

function App() {
  return (
    <div className="min-h-screen bg-background">
      <Layout>
        <Routes>
          <Route path="/" element={<MainPage />} />
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/map" element={<MapPage />} />
          <Route path="/calendar" element={<CalendarPage />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/auth/naver/callback" element={<NaverCallback />} />
          <Route path="/subscribe" element={<SubscribePage />} />
        </Routes>
      </Layout>
      <HotToaster position="top-center" />
    </div>
  )
}

export default App
