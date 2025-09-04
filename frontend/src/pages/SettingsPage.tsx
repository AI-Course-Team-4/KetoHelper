import { useState } from 'react'
import {
  Box,
  Typography,
  Paper,
  Tabs,
  Tab,
  TextField,
  Button,
  Switch,
  FormControlLabel,
  Chip,
  Divider,
  Alert,
} from '@mui/material'
import { Save, Delete, Add } from '@mui/icons-material'
import { useAuthStore } from '@store/authStore'

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
  const [allergies, setAllergies] = useState(['견과류', '갑각류'])
  const [dislikes, setDislikes] = useState(['버섯', '올리브'])
  const [newAllergy, setNewAllergy] = useState('')
  const [newDislike, setNewDislike] = useState('')
  

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

  const addAllergy = () => {
    if (newAllergy && !allergies.includes(newAllergy)) {
      setAllergies([...allergies, newAllergy])
      setNewAllergy('')
    }
  }

  const removeAllergy = (allergy: string) => {
    setAllergies(allergies.filter(item => item !== allergy))
  }

  const addDislike = () => {
    if (newDislike && !dislikes.includes(newDislike)) {
      setDislikes([...dislikes, newDislike])
      setNewDislike('')
    }
  }

  const removeDislike = (dislike: string) => {
    setDislikes(dislikes.filter(item => item !== dislike))
  }

  return (
    <Box>
      <Typography variant="h3" sx={{ fontWeight: 700, mb: 4 }}>
        ⚙️ 설정
      </Typography>

      <Paper sx={{ width: '100%' }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={activeTab} onChange={handleTabChange}>
            {/* <Tab label="프로필" /> */}
            <Tab label="식품 선호도" />
            <Tab label="알림 설정" />
            <Tab label="계정 관리" />
          </Tabs>
        </Box>

        {/* 식품 선호도 탭 */}
        <TabPanel value={activeTab} index={0}>
          <Typography variant="h6" sx={{ mb: 3 }}>
            식품 선호도
          </Typography>

          {/* 알레르기 */}
          <Box sx={{ mb: 4 }}>
            <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 600 }}>
              알레르기 정보
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
              {allergies.map((allergy) => (
                <Chip
                  key={allergy}
                  label={allergy}
                  onDelete={() => removeAllergy(allergy)}
                  color="error"
                  variant="outlined"
                />
              ))}
            </Box>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <TextField
                size="small"
                placeholder="알레르기 추가"
                value={newAllergy}
                onChange={(e) => setNewAllergy(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && addAllergy()}
              />
              <Button
                variant="outlined"
                size="small"
                startIcon={<Add />}
                onClick={addAllergy}
              >
                추가
              </Button>
            </Box>
          </Box>

          {/* 비선호 음식 */}
          <Box sx={{ mb: 4 }}>
            <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 600 }}>
              비선호 음식
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
              {dislikes.map((dislike) => (
                <Chip
                  key={dislike}
                  label={dislike}
                  onDelete={() => removeDislike(dislike)}
                  color="warning"
                  variant="outlined"
                />
              ))}
            </Box>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <TextField
                size="small"
                placeholder="비선호 음식 추가"
                value={newDislike}
                onChange={(e) => setNewDislike(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && addDislike()}
              />
              <Button
                variant="outlined"
                size="small"
                startIcon={<Add />}
                onClick={addDislike}
              >
                추가
              </Button>
            </Box>
          </Box>

          <Button variant="contained" startIcon={<Save />}>
            선호도 저장
          </Button>
        </TabPanel>

        {/* 알림 설정 탭 */}
        <TabPanel value={activeTab} index={1}>
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
        <TabPanel value={activeTab} index={2}>
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
