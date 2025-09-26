import { Routes, Route } from 'react-router-dom'
import { Layout } from '@/components/Layout'
import { ChatPage } from '@/pages/ChatPage'
import { MapPage } from '@/pages/MapPage'
import { CalendarPage } from '@/pages/CalendarPage'
import { ProfilePage } from '@/pages/ProfilePage'
import NaverCallback from '@/pages/NaverCallback'
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
    </div>
  )
}

export default App
