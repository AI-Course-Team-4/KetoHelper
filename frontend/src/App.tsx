import { Routes, Route } from 'react-router-dom'
<<<<<<< HEAD
import { Layout } from '@/components/Layout'
import { ChatPage } from '@/pages/ChatPage'
import { MapPage } from '@/pages/MapPage'
import { CalendarPage } from '@/pages/CalendarPage'
import { ProfilePage } from '@/pages/ProfilePage'
import { Toaster } from '@/components/ui/toaster'

function App() {
  return (
    <div className="min-h-screen bg-background">
      <Layout>
        <Routes>
          <Route path="/" element={<ChatPage />} />
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/map" element={<MapPage />} />
          <Route path="/calendar" element={<CalendarPage />} />
          <Route path="/profile" element={<ProfilePage />} />
        </Routes>
      </Layout>
      <Toaster />
    </div>
=======
import { Box } from '@mui/material'

import Layout from '@/components/common/Layout'
import HomePage from '@pages/HomePage'
import MealsPage from '@pages/MealsPage'
import RestaurantsPage from '@pages/RestaurantsPage'
import LoginPage from '@pages/LoginPage'
import SettingsPage from '@pages/SettingsPage'
import ProfilePage from '@pages/ProfilePage'
import PreferencesPage from '@pages/PreferencesPage'
import CalendarPage from '@pages/CalendarPage'
import SubscriptionPage from '@pages/SubscriptionPage'
import NotFoundPage from '@pages/NotFoundPage'

function App() {
  return (
    <Box sx={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="meals" element={<MealsPage />} />
          <Route path="restaurants" element={<RestaurantsPage />} />
          <Route path="calendar" element={<CalendarPage />} />
          <Route path="profile" element={<ProfilePage />} />
          <Route path="preferences" element={<PreferencesPage />} />
          <Route path="subscription" element={<SubscriptionPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/auth/naver/callback" element={<LoginPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </Box>
>>>>>>> origin/dev
  )
}

export default App
