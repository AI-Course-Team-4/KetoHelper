import { useState } from 'react'
<<<<<<< HEAD
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { User, Target, AlertTriangle, Trash2, Plus } from 'lucide-react'
import { useProfileStore } from '@/store/profileStore'

export function ProfilePage() {
  const { 
    profile, 
    updateProfile, 
    addAllergy, 
    removeAllergy, 
    addDislike, 
    removeDislike 
  } = useProfileStore()

  const [nickname, setNickname] = useState(profile?.nickname || '')
  const [goalsKcal, setGoalsKcal] = useState(profile?.goals_kcal || '')
  const [goalsCarbsG, setGoalsCarbsG] = useState(profile?.goals_carbs_g || '')
  const [newAllergy, setNewAllergy] = useState('')
  const [newDislike, setNewDislike] = useState('')

  const handleSaveProfile = () => {
    updateProfile({
      nickname: nickname || undefined,
      goals_kcal: goalsKcal ? Number(goalsKcal) : undefined,
      goals_carbs_g: goalsCarbsG ? Number(goalsCarbsG) : undefined,
    })
  }

  const handleAddAllergy = () => {
    if (newAllergy.trim()) {
      addAllergy(newAllergy.trim())
      setNewAllergy('')
    }
  }

  const handleAddDislike = () => {
    if (newDislike.trim()) {
      addDislike(newDislike.trim())
      setNewDislike('')
=======
import {
  Box,
  Typography,
  Card,
  CardContent,
  TextField,
  Button,
  Avatar,
  Grid,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,

  Chip,
} from '@mui/material'
import {
  PhotoCamera,
  Edit,
  Save,
  Cancel,
} from '@mui/icons-material'
import { useAuthStore } from '@store/authStore'
import type { InitialDietSetup } from '../types/index'

const ProfilePage = () => {
  const { user, isAuthenticated } = useAuthStore()
  const [isEditing, setIsEditing] = useState(false)
  const [profileImage, setProfileImage] = useState(user?.profileImage || '')
  const [name, setName] = useState(user?.name || '')
  const [id] = useState(user?.id || '')
  const [dietSetupOpen, setDietSetupOpen] = useState(false)
  const [dietSetup, setDietSetup] = useState<InitialDietSetup>({
    currentWeight: user?.dietPlan?.currentWeight || 70,
    targetWeight: user?.dietPlan?.targetWeight || 65,
    intensity: user?.dietPlan?.intensity || 'medium',
    timeframe: 12,
    activityLevel: 'moderate',
  })
  const displayName = name || id || '';

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

  const handleImageUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = (e) => {
        setProfileImage(e.target?.result as string)
      }
      reader.readAsDataURL(file)
    }
  }

  const handleSaveProfile = () => {
    // TODO: API 호출로 프로필 정보 업데이트
    console.log('Saving profile:', { name, profileImage })
    setIsEditing(false)
  }

  const handleCancelEdit = () => {
    setName(user?.name || '')
    setProfileImage(user?.profileImage || '')
    setIsEditing(false)
  }

  const handleDietSetupSave = () => {
    // TODO: API 호출로 다이어트 설정 저장
    console.log('Saving diet setup:', dietSetup)
    setDietSetupOpen(false)
  }

  const calculateEstimatedDays = () => {
    const weightDiff = dietSetup.currentWeight - dietSetup.targetWeight
    const intensityMultiplier = {
      low: 0.25,
      medium: 0.5,
      high: 0.75,
    }[dietSetup.intensity]

    // 주당 감량 목표 (kg)
    const weeklyGoal = intensityMultiplier
    const estimatedWeeks = Math.ceil(weightDiff / weeklyGoal)
    return estimatedWeeks * 7
  }

  const getIntensityDescription = (intensity: string) => {
    switch (intensity) {
      case 'low':
        return '천천히 건강하게 (주 0.25kg 감량)'
      case 'medium':
        return '적당한 속도로 (주 0.5kg 감량)'
      case 'high':
        return '빠른 속도로 (주 0.75kg 감량)'
      default:
        return ''
>>>>>>> origin/dev
    }
  }

  return (
<<<<<<< HEAD
    <div className="space-y-6">
      {/* 헤더 */}
      <div>
        <h1 className="text-2xl font-bold text-gradient">프로필 설정</h1>
        <p className="text-muted-foreground mt-1">
          개인 정보와 키토 다이어트 목표를 설정하세요
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 기본 정보 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <User className="h-5 w-5 mr-2" />
              기본 정보
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium">닉네임</label>
              <Input
                value={nickname}
                onChange={(e) => setNickname(e.target.value)}
                placeholder="닉네임을 입력하세요"
                className="mt-1"
              />
            </div>
            
            <Button onClick={handleSaveProfile} className="w-full">
              저장
            </Button>
          </CardContent>
        </Card>

        {/* 키토 목표 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Target className="h-5 w-5 mr-2" />
              키토 목표
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium">일일 목표 칼로리</label>
              <Input
                type="number"
                value={goalsKcal}
                onChange={(e) => setGoalsKcal(e.target.value)}
                placeholder="1500"
                className="mt-1"
              />
              <p className="text-xs text-muted-foreground mt-1">
                개인의 기초대사율과 활동량을 고려하세요
              </p>
            </div>
            
            <div>
              <label className="text-sm font-medium">일일 최대 탄수화물 (g)</label>
              <Input
                type="number"
                value={goalsCarbsG}
                onChange={(e) => setGoalsCarbsG(e.target.value)}
                placeholder="20-30"
                className="mt-1"
              />
              <p className="text-xs text-muted-foreground mt-1">
                키토시스 유지를 위해 20-30g 권장
              </p>
            </div>
            
            <Button onClick={handleSaveProfile} className="w-full">
              목표 저장
            </Button>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 알레르기 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <AlertTriangle className="h-5 w-5 mr-2" />
              알레르기
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              <Input
                value={newAllergy}
                onChange={(e) => setNewAllergy(e.target.value)}
                placeholder="알레르기를 입력하세요"
                onKeyPress={(e) => e.key === 'Enter' && handleAddAllergy()}
                className="flex-1"
              />
              <Button onClick={handleAddAllergy} size="sm">
                <Plus className="h-4 w-4" />
              </Button>
            </div>
            
            <div className="flex flex-wrap gap-2">
              {profile?.allergies?.map((allergy) => (
                <Badge 
                  key={allergy} 
                  variant="destructive" 
                  className="flex items-center gap-1"
                >
                  {allergy}
                  <Trash2 
                    className="h-3 w-3 cursor-pointer" 
                    onClick={() => removeAllergy(allergy)}
                  />
                </Badge>
              ))}
            </div>
            
            {(!profile?.allergies || profile.allergies.length === 0) && (
              <p className="text-sm text-muted-foreground">
                등록된 알레르기가 없습니다
              </p>
            )}
          </CardContent>
        </Card>

        {/* 비선호 음식 */}
        <Card>
          <CardHeader>
            <CardTitle>비선호 음식</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              <Input
                value={newDislike}
                onChange={(e) => setNewDislike(e.target.value)}
                placeholder="싫어하는 음식을 입력하세요"
                onKeyPress={(e) => e.key === 'Enter' && handleAddDislike()}
                className="flex-1"
              />
              <Button onClick={handleAddDislike} size="sm">
                <Plus className="h-4 w-4" />
              </Button>
            </div>
            
            <div className="flex flex-wrap gap-2">
              {profile?.dislikes?.map((dislike) => (
                <Badge 
                  key={dislike} 
                  variant="outline" 
                  className="flex items-center gap-1"
                >
                  {dislike}
                  <Trash2 
                    className="h-3 w-3 cursor-pointer" 
                    onClick={() => removeDislike(dislike)}
                  />
                </Badge>
              ))}
            </div>
            
            {(!profile?.dislikes || profile.dislikes.length === 0) && (
              <p className="text-sm text-muted-foreground">
                등록된 비선호 음식이 없습니다
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* 키토 가이드 */}
      <Card>
        <CardHeader>
          <CardTitle>키토 다이어트 가이드</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">70-80%</div>
              <div className="text-sm text-green-700">지방</div>
              <div className="text-xs text-muted-foreground mt-1">
                주 에너지원
              </div>
            </div>
            
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">15-25%</div>
              <div className="text-sm text-blue-700">단백질</div>
              <div className="text-xs text-muted-foreground mt-1">
                근육 유지
              </div>
            </div>
            
            <div className="text-center p-4 bg-orange-50 rounded-lg">
              <div className="text-2xl font-bold text-orange-600">5-10%</div>
              <div className="text-sm text-orange-700">탄수화물</div>
              <div className="text-xs text-muted-foreground mt-1">
                최소 섭취
              </div>
            </div>
          </div>
          
          <div className="mt-6 space-y-2">
            <h4 className="font-medium">💡 키토 성공 팁</h4>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li>• 충분한 물 섭취 (하루 2-3L)</li>
              <li>• 전해질 보충 (나트륨, 칼륨, 마그네슘)</li>
              <li>• 점진적 탄수화물 감소</li>
              <li>• 규칙적인 식사 시간</li>
              <li>• 스트레스 관리와 충분한 수면</li>
            </ul>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
=======
    <Box>
      {/* <Typography variant="h3" sx={{ fontWeight: 700, mb: 4 }}>
        👤 프로필 설정
      </Typography> */}

      <Grid container spacing={4}>
        {/* 기본 프로필 정보 */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent sx={{ p: 4 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  기본 정보
                </Typography>
                {!isEditing ? (
                  <IconButton onClick={() => { setIsEditing(true) }}>
                    <Edit />
                  </IconButton>
                ) : (
                  <Box>
                    <IconButton onClick={handleSaveProfile} color="primary">
                      <Save />
                    </IconButton>
                    <IconButton onClick={handleCancelEdit}>
                      <Cancel />
                    </IconButton>
                  </Box>
                )}
              </Box>

              {/* 프로필 사진 */}
              <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mb: 4 }}>
                <Box sx={{ position: 'relative', mb: 2 }}>
                  <Avatar
                    src={profileImage}
                    alt={name}
                    sx={{
                      width: 120,
                      height: 120,
                      fontSize: '2rem',
                    }}
                  >
                    {name?.charAt(0)}
                  </Avatar>
                  {isEditing && (
                    <IconButton
                      sx={{
                        position: 'absolute',
                        bottom: 0,
                        right: 0,
                        backgroundColor: 'primary.main',
                        color: 'white',
                        '&:hover': {
                          backgroundColor: 'primary.dark',
                        },
                      }}
                      component="label"
                    >
                      <PhotoCamera />
                      <input
                        type="file"
                        hidden
                        accept="image/*"
                        onChange={handleImageUpload}
                      />
                    </IconButton>
                  )}
                </Box>
                <Typography variant="body2" color="text.secondary">
                  {isEditing ? '사진을 클릭하여 변경하세요' : '프로필 사진'}
                </Typography>
              </Box>

              {/* 사용자 정보 */}
              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="이름"
                    value={displayName}
                    onChange={(e) => setName(e.target.value)}
                    disabled={!isEditing}
                    variant={isEditing ? 'outlined' : 'filled'}
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="이메일"
                    value={user?.email || ''}
                    disabled
                    variant="filled"
                    helperText="이메일은 변경할 수 없습니다"
                  />
                </Grid>
                <Grid item xs={12}>
                  <FormControl fullWidth disabled={!isEditing}>
                    <InputLabel>키토 경험 레벨</InputLabel>
                    <Select
                      value={user?.preferences?.experienceLevel || 'beginner'}
                      label="키토 경험 레벨"
                    >
                      <MenuItem value="beginner">초보자</MenuItem>
                      <MenuItem value="intermediate">중급자</MenuItem>
                      <MenuItem value="advanced">고급자</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* 다이어트 계획 */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent sx={{ p: 4 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  다이어트 계획
                </Typography>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={() => setDietSetupOpen(true)}
                >
                  설정하기
                </Button>
              </Box>

              {user?.dietPlan ? (
                <Box>
                  <Grid container spacing={2} sx={{ mb: 3 }}>
                    <Grid item xs={6}>
                      <Box sx={{ textAlign: 'center', p: 2, backgroundColor: 'action.hover', borderRadius: 1 }}>
                        <Typography variant="h4" color="primary.main" sx={{ fontWeight: 700 }}>
                          {user.dietPlan.currentWeight}kg
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          현재 체중
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={6}>
                      <Box sx={{ textAlign: 'center', p: 2, backgroundColor: 'action.hover', borderRadius: 1 }}>
                        <Typography variant="h4" color="secondary.main" sx={{ fontWeight: 700 }}>
                          {user.dietPlan.targetWeight}kg
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          목표 체중
                        </Typography>
                      </Box>
                    </Grid>
                  </Grid>

                  <Box sx={{ mb: 3 }}>
                    <Typography variant="body1" sx={{ mb: 1 }}>
                      <strong>다이어트 강도:</strong> {getIntensityDescription(user.dietPlan.intensity)}
                    </Typography>
                    <Typography variant="body1" sx={{ mb: 1 }}>
                      <strong>목표 달성까지:</strong> {user.dietPlan.daysRemaining}일 남음
                    </Typography>
                    <Typography variant="body1">
                      <strong>일일 칼로리 목표:</strong> {user.dietPlan.dailyCalories}kcal
                    </Typography>
                  </Box>

                  <Box>
                    <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                      마크로 뉴트리언트 목표
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                      <Chip
                        label={`탄수화물 ${user.dietPlan.macroTargets.carbs}%`}
                        size="small"
                        color="warning"
                      />
                      <Chip
                        label={`단백질 ${user.dietPlan.macroTargets.protein}%`}
                        size="small"
                        color="info"
                      />
                      <Chip
                        label={`지방 ${user.dietPlan.macroTargets.fat}%`}
                        size="small"
                        color="success"
                      />
                    </Box>
                  </Box>
                </Box>
              ) : (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
                    아직 다이어트 계획이 설정되지 않았습니다.
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    개인 맞춤 다이어트 계획을 설정하여 더 효과적인 키토 다이어트를 시작하세요.
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* 다이어트 설정 다이얼로그 */}
      <Dialog open={dietSetupOpen} onClose={() => setDietSetupOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            🎯 개인 맞춤 다이어트 계획 설정
          </Typography>
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={3} sx={{ mt: 1 }}>
            {/* 현재 체중 */}
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="현재 체중 (kg)"
                type="number"
                value={dietSetup.currentWeight}
                onChange={(e) => setDietSetup(prev => ({ ...prev, currentWeight: Number(e.target.value) }))}
                inputProps={{ min: 30, max: 200 }}
              />
            </Grid>

            {/* 목표 체중 */}
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="목표 체중 (kg)"
                type="number"
                value={dietSetup.targetWeight}
                onChange={(e) => setDietSetup(prev => ({ ...prev, targetWeight: Number(e.target.value) }))}
                inputProps={{ min: 30, max: 200 }}
              />
            </Grid>

            {/* 다이어트 강도 */}
            <Grid item xs={12}>
              <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 600 }}>
                다이어트 강도
              </Typography>
              <FormControl fullWidth>
                <Select
                  value={dietSetup.intensity}
                  onChange={(e) => setDietSetup(prev => ({ ...prev, intensity: e.target.value as any }))}
                >
                  <MenuItem value="low">천천히 건강하게 (주 0.25kg 감량)</MenuItem>
                  <MenuItem value="medium">적당한 속도로 (주 0.5kg 감량)</MenuItem>
                  <MenuItem value="high">빠른 속도로 (주 0.75kg 감량)</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            {/* 활동 수준 */}
            <Grid item xs={12}>
              <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 600 }}>
                일상 활동 수준
              </Typography>
              <FormControl fullWidth>
                <Select
                  value={dietSetup.activityLevel}
                  onChange={(e) => setDietSetup(prev => ({ ...prev, activityLevel: e.target.value as any }))}
                >
                  <MenuItem value="sedentary">좌식 생활 (운동 거의 안함)</MenuItem>
                  <MenuItem value="light">가벼운 활동 (주 1-3회 운동)</MenuItem>
                  <MenuItem value="moderate">보통 활동 (주 3-5회 운동)</MenuItem>
                  <MenuItem value="active">활발한 활동 (주 6-7회 운동)</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            {/* 예상 기간 */}
            <Grid item xs={12}>
              <Card sx={{ p: 3, backgroundColor: 'primary.light', color: 'primary.contrastText' }}>
                <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
                  📊 예상 다이어트 결과
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Typography variant="body1">
                      <strong>감량 목표:</strong> {(dietSetup.currentWeight - dietSetup.targetWeight).toFixed(1)}kg
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body1">
                      <strong>예상 기간:</strong> 약 {Math.ceil(calculateEstimatedDays() / 7)}주
                    </Typography>
                  </Grid>
                  <Grid item xs={12}>
                    <Typography variant="body2" sx={{ mt: 1, opacity: 0.9 }}>
                      * 개인차가 있을 수 있으며, 건강한 속도로 진행하는 것이 중요합니다.
                    </Typography>
                  </Grid>
                </Grid>
              </Card>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDietSetupOpen(false)}>
            취소
          </Button>
          <Button variant="contained" onClick={handleDietSetupSave}>
            설정 저장
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default ProfilePage
>>>>>>> origin/dev
