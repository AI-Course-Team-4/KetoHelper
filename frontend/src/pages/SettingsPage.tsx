import { useState } from 'react'
import {
  Box,
  Typography,
  Paper,
  Tabs,
  Tab,
  Button,
  Switch,
  FormControlLabel,
  Divider,
  Alert,
} from '@mui/material'
import { Save, Delete } from '@mui/icons-material'
import { useAuthStore } from '@store/authStore'
import ProfilePage from './ProfilePage'
import PreferencesPage from './PreferencesPage'


interface TabPanelProps {
  children?: React.ReactNode
  index: number
  value: number
}


function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props


  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`settings-tabpanel-${index}`}
      aria-labelledby={`settings-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  )
}


const SettingsPage = () => {
  const { isAuthenticated } = useAuthStore()
  const [activeTab, setActiveTab] = useState(0)

  if (!isAuthenticated) {
    return (
      <Box sx={{ textAlign: 'center', py: 8 }}>
        <Typography variant="h5" sx={{ mb: 2 }}>
          로그인이 필요한 서비스입니다
        </Typography>
        <Button variant="contained" href="/login">
          로그인하기
        </Button>
      </Box>
    )
  }


  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue)
  }


  return (
    <Box>
      <Typography variant="h3" sx={{ fontWeight: 700, mb: 4 }}>
        ⚙️ 설정
      </Typography>


      <Paper sx={{ width: '100%' }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={activeTab} onChange={handleTabChange}>
            <Tab label="프로필" />
            <Tab label="식품 선호도" />
            <Tab label="알림 설정" />
            <Tab label="계정 관리" />
          </Tabs>
        </Box>


        {/* 프로필 탭 */}
        <TabPanel value={activeTab} index={0}>
          <Typography variant="h6" sx={{ mb: 3 }}>
            프로필 설정
          </Typography>
          <ProfilePage />
        </TabPanel>


        {/* 식품 선호도 탭 */}
        <TabPanel value={activeTab} index={1}>
          <Typography variant="h6" sx={{ mb: 3 }}>
            식품 선호도 설정
          </Typography>
          <PreferencesPage />
        </TabPanel>


        {/* 알림 설정 탭 */}
        <TabPanel value={activeTab} index={2}>
          <Typography variant="h6" sx={{ mb: 3 }}>
            알림 설정
          </Typography>


          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <FormControlLabel
              control={<Switch defaultChecked />}
              label="식사 시간 알림"
            />
            <FormControlLabel
              control={<Switch defaultChecked />}
              label="새로운 추천 알림"
            />
            <FormControlLabel
              control={<Switch />}
              label="주간 리포트 수신"
            />
            <FormControlLabel
              control={<Switch defaultChecked />}
              label="마케팅 정보 수신"
            />
          </Box>


          <Box sx={{ mt: 3 }}>
            <Button variant="contained" startIcon={<Save />}>
              알림 설정 저장
            </Button>
          </Box>
        </TabPanel>


        {/* 계정 관리 탭 */}
        <TabPanel value={activeTab} index={3}>
          <Typography variant="h6" sx={{ mb: 3 }}>
            계정 관리
          </Typography>


          <Alert severity="info" sx={{ mb: 3 }}>
            계정 관련 중요한 설정들을 관리할 수 있습니다.
          </Alert>


          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            <Box>
              <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 600 }}>
                데이터 내보내기
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                개인 데이터를 JSON 형식으로 다운로드할 수 있습니다.
              </Typography>
              <Button variant="outlined">
                데이터 내보내기
              </Button>
            </Box>


            <Divider />


            <Box>
              <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 600, color: 'error.main' }}>
                계정 삭제
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                계정을 삭제하면 모든 데이터가 영구적으로 삭제됩니다. 이 작업은 되돌릴 수 없습니다.
              </Typography>
              <Button
                variant="outlined"
                color="error"
                startIcon={<Delete />}
              >
                계정 삭제
              </Button>
            </Box>
          </Box>
        </TabPanel>
      </Paper>
    </Box>
  )
}


export default SettingsPage



