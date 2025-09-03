import { Routes, Route } from 'react-router-dom'
import { Box } from '@mui/material'

import Layout from '@components/Layout'
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
import Test from '@pages/Test'

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
          <Route path="test" element={<Test />} />
        </Route>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/auth/naver/callback" element={<LoginPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </Box>
  )
}

export default App
