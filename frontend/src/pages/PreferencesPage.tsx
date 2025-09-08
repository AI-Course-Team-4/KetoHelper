import { useState } from 'react'
import {
  Box,
  Typography,
  Card,
  CardContent,
  TextField,
  Button,
  Grid,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Autocomplete,
  Alert,
  Divider,
  Switch,
  FormControlLabel,
} from '@mui/material'
import {
  Add,
  Save,
  Warning,
  CheckCircle,
  Cancel,
} from '@mui/icons-material'
import { useAuthStore } from '@store/authStore'

const PreferencesPage = () => {
  const { user, isAuthenticated } = useAuthStore()
  
  // 상태 관리
  const [allergies, setAllergies] = useState<string[]>(user?.preferences?.allergies || [])
  const [dislikes, setDislikes] = useState<string[]>(user?.preferences?.dislikes || [])
  const [dietaryRestrictions] = useState<string[]>(user?.preferences?.dietaryRestrictions || [])
  const [newAllergy, setNewAllergy] = useState('')
  const [newDislike, setNewDislike] = useState('')
  const [spicyLevel, setSpicyLevel] = useState(2) // 0-5 단계
  const [preferredCuisines, setPreferredCuisines] = useState<string[]>(['한식', '양식'])
  const [veganFriendly, setVeganFriendly] = useState(false)
  const [glutenFree, setGlutenFree] = useState(false)

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

  // 미리 정의된 알레르기 옵션
  const commonAllergies = [
    '견과류', '갑각류', '생선', '달걀', '우유', '대두', '밀', '복숭아', '토마토', 
    '돼지고기', '쇠고기', '닭고기', '메밀', '땅콩', '아황산류'
  ]

  // 미리 정의된 비선호 음식 옵션
  const commonDislikes = [
    '버섯', '올리브', '치즈', '양파', '마늘', '생강', '고수', '브로콜리',
    '시금치', '당근', '파프리카', '아보카도', '연어', '참치', '새우'
  ]

  // 요리 스타일 옵션
  const cuisineTypes = [
    '한식', '양식', '일식', '중식', '이탈리안', '멕시칸', '인도식', '태국식', 
    '베트남식', '지중해식', '중동식', '남미식'
  ]

  const handleAddAllergy = () => {
    if (newAllergy && !allergies.includes(newAllergy)) {
      setAllergies(prev => [...prev, newAllergy])
      setNewAllergy('')
    }
  }

  const handleRemoveAllergy = (allergy: string) => {
    setAllergies(prev => prev.filter(item => item !== allergy))
  }

  const handleAddDislike = () => {
    if (newDislike && !dislikes.includes(newDislike)) {
      setDislikes(prev => [...prev, newDislike])
      setNewDislike('')
    }
  }

  const handleRemoveDislike = (dislike: string) => {
    setDislikes(prev => prev.filter(item => item !== dislike))
  }

  const handleSavePreferences = () => {
    // TODO: API 호출로 선호도 저장
    const preferences = {
      allergies,
      dislikes,
      dietaryRestrictions,
      spicyLevel,
      preferredCuisines,
      veganFriendly,
      glutenFree,
    }
    console.log('Saving preferences:', preferences)
    // 성공 메시지 표시
  }

  const getSpicyLevelText = (level: number) => {
    const levels = ['전혀 안매움', '약간 매움', '보통 매움', '매움', '아주 매움', '극도로 매움']
    return levels[level]
  }

  return (
    <Box>
      <Typography variant="h3" sx={{ fontWeight: 700, mb: 2 }}>
        ❤️ 선호도 설정
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        개인 선호도를 설정하면 더욱 정확한 맞춤형 추천을 받을 수 있습니다.
      </Typography>

      <Grid container spacing={4}>
        {/* 알레르기 정보 */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent sx={{ p: 4 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <Warning sx={{ mr: 1, color: 'error.main' }} />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  알레르기 정보
                </Typography>
              </Box>
              
              <Alert severity="warning" sx={{ mb: 3 }}>
                알레르기가 있는 식품을 정확히 입력해주세요. 추천에서 완전히 제외됩니다.
              </Alert>

              {/* 기존 알레르기 목록 */}
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 600 }}>
                  현재 알레르기 목록
                </Typography>
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
                  {allergies.map((allergy) => (
                    <Chip
                      key={allergy}
                      label={allergy}
                      onDelete={() => handleRemoveAllergy(allergy)}
                      color="error"
                      variant="outlined"
                      deleteIcon={<Cancel />}
                    />
                  ))}
                  {allergies.length === 0 && (
                    <Typography variant="body2" color="text.secondary">
                      등록된 알레르기가 없습니다.
                    </Typography>
                  )}
                </Box>
              </Box>

              {/* 알레르기 추가 */}
              <Box>
                <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 600 }}>
                  알레르기 추가
                </Typography>
                <Autocomplete
                  freeSolo
                  options={commonAllergies.filter(item => !allergies.includes(item))}
                  value={newAllergy}
                  onInputChange={(_, value) => setNewAllergy(value)}
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      placeholder="알레르기 식품 입력"
                      size="small"
                      onKeyPress={(e) => e.key === 'Enter' && handleAddAllergy()}
                    />
                  )}
                />
                <Button
                  variant="outlined"
                  size="small"
                  startIcon={<Add />}
                  onClick={handleAddAllergy}
                  sx={{ mt: 2 }}
                  disabled={!newAllergy}
                >
                  추가
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* 비선호 음식 */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent sx={{ p: 4 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  비선호 음식
                </Typography>
              </Box>
              
              <Alert severity="info" sx={{ mb: 3 }}>
                선호하지 않는 음식을 설정하면 추천에서 우선적으로 제외됩니다.
              </Alert>

              {/* 기존 비선호 목록 */}
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 600 }}>
                  현재 비선호 음식
                </Typography>
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
                  {dislikes.map((dislike) => (
                    <Chip
                      key={dislike}
                      label={dislike}
                      onDelete={() => handleRemoveDislike(dislike)}
                      color="warning"
                      variant="outlined"
                      deleteIcon={<Cancel />}
                    />
                  ))}
                  {dislikes.length === 0 && (
                    <Typography variant="body2" color="text.secondary">
                      등록된 비선호 음식이 없습니다.
                    </Typography>
                  )}
                </Box>
              </Box>

              {/* 비선호 음식 추가 */}
              <Box>
                <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 600 }}>
                  비선호 음식 추가
                </Typography>
                <Autocomplete
                  freeSolo
                  options={commonDislikes.filter(item => !dislikes.includes(item))}
                  value={newDislike}
                  onInputChange={(_, value) => setNewDislike(value)}
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      placeholder="비선호 음식 입력"
                      size="small"
                      onKeyPress={(e) => e.key === 'Enter' && handleAddDislike()}
                    />
                  )}
                />
                <Button
                  variant="outlined"
                  size="small"
                  startIcon={<Add />}
                  onClick={handleAddDislike}
                  sx={{ mt: 2 }}
                  disabled={!newDislike}
                >
                  추가
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* 선호 요리 스타일 */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent sx={{ p: 4 }}>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
                선호하는 요리 스타일
              </Typography>

              <Autocomplete
                multiple
                options={cuisineTypes}
                value={preferredCuisines}
                onChange={(_, value) => setPreferredCuisines(value)}
                renderTags={(value, getTagProps) =>
                  value.map((option, index) => (
                    <Chip
                      variant="outlined"
                      label={option}
                      {...getTagProps({ index })}
                      key={option}
                    />
                  ))
                }
                renderInput={(params) => (
                  <TextField
                    {...params}
                    placeholder="선호하는 요리 스타일을 선택하세요"
                    helperText="여러 개 선택 가능"
                  />
                )}
              />
            </CardContent>
          </Card>
        </Grid>

        {/* 매운맛 선호도 */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent sx={{ p: 4 }}>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
                매운맛 선호도
              </Typography>

              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>매운맛 정도</InputLabel>
                <Select
                  value={spicyLevel}
                  label="매운맛 정도"
                  onChange={(e) => setSpicyLevel(Number(e.target.value))}
                >
                  {Array.from({ length: 6 }, (_, i) => (
                    <MenuItem key={i} value={i}>
                      {i + 1}단계 - {getSpicyLevelText(i)}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              <Typography variant="body2" color="text.secondary">
                현재 설정: <strong>{getSpicyLevelText(spicyLevel)}</strong>
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* 식단 제한사항 */}
        <Grid item xs={12}>
          <Card>
            <CardContent sx={{ p: 4 }}>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
                추가 식단 제한사항
              </Typography>

              <Grid container spacing={3}>
                <Grid item xs={12} sm={6}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={veganFriendly}
                        onChange={(e) => setVeganFriendly(e.target.checked)}
                      />
                    }
                    label="비건 친화적 식단 선호"
                  />
                  <Typography variant="body2" color="text.secondary">
                    동물성 원료를 사용하지 않는 식단을 우선 추천합니다.
                  </Typography>
                </Grid>

                <Grid item xs={12} sm={6}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={glutenFree}
                        onChange={(e) => setGlutenFree(e.target.checked)}
                      />
                    }
                    label="글루텐 프리 선호"
                  />
                  <Typography variant="body2" color="text.secondary">
                    글루텐이 포함되지 않은 식단을 우선 추천합니다.
                  </Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Divider sx={{ my: 4 }} />

      {/* 저장 버튼 */}
      <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2 }}>
        <Button
          variant="contained"
          size="large"
          startIcon={<Save />}
          onClick={handleSavePreferences}
          sx={{ px: 4 }}
        >
          선호도 저장
        </Button>
        <Button
          variant="outlined"
          size="large"
          onClick={() => window.history.back()}
        >
          취소
        </Button>
      </Box>

      {/* 안내 메시지 */}
      <Alert severity="success" icon={<CheckCircle />} sx={{ mt: 4 }}>
        <Typography variant="body2">
          <strong>💡 팁:</strong> 선호도는 언제든지 변경할 수 있으며, 
          설정할수록 더욱 정확한 맞춤형 추천을 받을 수 있습니다. 
          알레르기 정보는 반드시 정확히 입력해주세요.
        </Typography>
      </Alert>
    </Box>
  )
}

export default PreferencesPage
