import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Select } from '@/components/common'
import { Person, GpsFixed, Warning, Delete, Add, ThumbDown } from '@mui/icons-material'
import { CircularProgress, Box, Typography, Stack } from '@mui/material'
import { useProfileStore, useProfileHelpers } from '@/store/profileStore'
import { useAuthStore } from '@/store/authStore'
import { toast } from 'react-hot-toast'

export function ProfilePage() {
  const navigate = useNavigate()
  const { user, updateUser } = useAuthStore()
  const { 
    profile, 
    error,
    loadMasterData,
    loadProfile,
    updateProfile, 
    addAllergy, 
    removeAllergy, 
    addDislike, 
    removeDislike 
  } = useProfileStore()
  const { 
    getAllergiesByCategory,
    getDislikesByCategory 
  } = useProfileHelpers()

  const [nickname, setNickname] = useState('')
  const [goalsKcal, setGoalsKcal] = useState('')
  const [goalsCarbsG, setGoalsCarbsG] = useState('')
  const [selectedAllergyId, setSelectedAllergyId] = useState<string>('')
  const [selectedDislikeId, setSelectedDislikeId] = useState<string>('')

  // 저장된 데이터 (변경 감지용)
  const [savedNickname, setSavedNickname] = useState('')
  const [savedGoalsKcal, setSavedGoalsKcal] = useState('')
  const [savedGoalsCarbsG, setSavedGoalsCarbsG] = useState('')

  // 마스터 데이터 및 프로필 로드
  useEffect(() => {
    loadMasterData()
    if (user?.id) {
      loadProfile(user.id)
    }
  }, [user?.id, loadProfile, loadMasterData])


  // 프로필 데이터가 변경되면 로컬 상태 업데이트
  useEffect(() => {
    if (profile && user?.id) {
      const newNickname = profile.nickname ?? user?.name ?? ''
      const newGoalsKcal = profile.goals_kcal ? profile.goals_kcal.toLocaleString() : ''
      const newGoalsCarbsG = profile.goals_carbs_g ? String(profile.goals_carbs_g) : ''
      
      
      setNickname(newNickname)
      setGoalsKcal(newGoalsKcal)
      setGoalsCarbsG(newGoalsCarbsG)
      
      // 저장된 데이터도 업데이트
      setSavedNickname(newNickname)
      setSavedGoalsKcal(newGoalsKcal)
      setSavedGoalsCarbsG(newGoalsCarbsG)
    } else if (!user) {
      // 로그아웃 시 상태 클리어
      setNickname('')
      setGoalsKcal('')
      setGoalsCarbsG('')
      setSavedNickname('')
      setSavedGoalsKcal('')
      setSavedGoalsCarbsG('')
    }
  }, [profile, user?.name, user?.id])

  // 로그인 상태 확인 - 로그인하지 않은 경우 메인 페이지로 리다이렉트
  useEffect(() => {
    if (!user) {
      console.log('User not authenticated, redirecting to main page')
      navigate('/')
      return
    }
  }, [user, navigate])

  // 로그아웃 시 상태 초기화 (실제로는 위에서 리다이렉트되므로 실행되지 않음)
  useEffect(() => {
    if (!user) {
      setNickname('')
      setGoalsKcal('')
      setGoalsCarbsG('')
    }
  }, [user])

  // 에러 처리
  useEffect(() => {
    if (error) {
      toast.error(error)
    }
  }, [error])

  // 개별 로딩 상태 관리
  const [isBasicInfoLoading, setIsBasicInfoLoading] = useState(false)
  const [isKetoGoalsLoading, setIsKetoGoalsLoading] = useState(false)
  const [isAllergyLoading, setIsAllergyLoading] = useState(false)
  const [isDislikeLoading, setIsDislikeLoading] = useState(false)

  // 변경 감지 로직
  const hasBasicInfoChanged = nickname !== savedNickname
  const hasKetoGoalsChanged = goalsKcal !== savedGoalsKcal || goalsCarbsG !== savedGoalsCarbsG

  const handleSaveBasicInfo = async () => {
    if (!user?.id) {
      toast.error("로그인이 필요합니다")
      return
    }

    // 닉네임 미완성 한글 검증 (선택사항)
    if (nickname && /[ㄱ-ㅎㅏ-ㅣ]/.test(nickname)) {
      toast.error("닉네임에 미완성 한글이 포함되어 있습니다")
      return
    }

    setIsBasicInfoLoading(true)
    try {
      await updateProfile(user.id, {
      nickname: nickname || undefined,
      })
      
      // 저장 성공 시 저장된 데이터 업데이트
      setSavedNickname(nickname)
      
      // authStore의 사용자 이름도 업데이트 (헤더에서 표시되는 이름)
      updateUser({ name: nickname || user.name })
      
      toast.success("기본 정보가 저장되었습니다")
    } catch (error) {
      // 에러는 스토어에서 처리됨
    } finally {
      setIsBasicInfoLoading(false)
    }
  }

  const handleSaveKetoGoals = async () => {
    if (!user?.id) {
      toast.error("로그인이 필요합니다")
      return
    }

    // 입력값 검증 (콤마 제거 후 숫자 변환)
    const kcalValue = goalsKcal ? Number(String(goalsKcal).replace(/,/g, '')) : undefined
    const carbsValue = goalsCarbsG ? Number(String(goalsCarbsG).replace(/,/g, '')) : undefined

    if (goalsKcal && (isNaN(kcalValue!) || kcalValue! <= 0)) {
      toast.error("일일 목표 칼로리는 올바른 숫자여야 합니다")
      return
    }

    if (goalsCarbsG && (isNaN(carbsValue!) || carbsValue! < 0)) {
      toast.error("일일 최대 탄수화물은 올바른 숫자여야 합니다")
      return
    }

    setIsKetoGoalsLoading(true)
    try {
      await updateProfile(user.id, {
        goals_kcal: kcalValue,
        goals_carbs_g: carbsValue,
      })
      
      // 저장 성공 시 저장된 데이터 업데이트
      setSavedGoalsKcal(goalsKcal)
      setSavedGoalsCarbsG(goalsCarbsG)
      
      toast.success("키토 목표가 저장되었습니다")
    } catch (error) {
      // 에러는 스토어에서 처리됨
    } finally {
      setIsKetoGoalsLoading(false)
    }
  }

  const handleAddAllergy = async () => {
    if (!user?.id) {
      toast.error("로그인이 필요합니다")
      return
    }

    if (!selectedAllergyId) {
      toast.error("추가할 알레르기를 선택해주세요")
      return
    }

    setIsAllergyLoading(true)
    try {
      await addAllergy(user.id, parseInt(selectedAllergyId))
      setSelectedAllergyId('')
      toast.success("알레르기가 추가되었습니다")
    } catch (error) {
      // 에러는 스토어에서 처리됨
    } finally {
      setIsAllergyLoading(false)
    }
  }

  const handleRemoveAllergy = async (allergyId: number) => {
    if (!user?.id) return
    
    try {
      await removeAllergy(user.id, allergyId)
      toast.success("알레르기가 제거되었습니다")
    } catch (error) {
      // 에러는 스토어에서 처리됨
    }
  }

  const handleAddDislike = async () => {
    if (!user?.id) {
      toast.error("로그인이 필요합니다")
      return
    }

    if (!selectedDislikeId) {
      toast.error("추가할 비선호 재료를 선택해주세요")
      return
    }

    setIsDislikeLoading(true)
    try {
      await addDislike(user.id, parseInt(selectedDislikeId))
      setSelectedDislikeId('')
      toast.success("비선호 재료가 추가되었습니다")
    } catch (error) {
      // 에러는 스토어에서 처리됨
    } finally {
      setIsDislikeLoading(false)
    }
  }

  const handleRemoveDislike = async (dislikeId: number) => {
    if (!user?.id) return
    
    try {
      await removeDislike(user.id, dislikeId)
      toast.success("비선호 재료가 제거되었습니다")
    } catch (error) {
      // 에러는 스토어에서 처리됨
    }
  }

  // 전체 알레르기 삭제
  const handleClearAllAllergies = async () => {
    if (!user?.id || !profile?.selected_allergy_ids?.length) return
    
    const confirmed = window.confirm(
      `모든 알레르기 ${profile.allergy_names?.length}개를 삭제하시겠습니까?`
    )
    
    if (!confirmed) return
    
    try {
      await updateProfile(user.id, {
        selected_allergy_ids: []
      })
      toast.success("모든 알레르기가 삭제되었습니다")
    } catch (error) {
      toast.error("알레르기 삭제 중 오류가 발생했습니다")
    }
  }

  // 전체 비선호 재료 삭제
  const handleClearAllDislikes = async () => {
    if (!user?.id || !profile?.selected_dislike_ids?.length) return
    
    const confirmed = window.confirm(
      `모든 비선호 재료 ${profile.dislike_names?.length}개를 삭제하시겠습니까?`
    )
    
    if (!confirmed) return
    
    try {
      await updateProfile(user.id, {
        selected_dislike_ids: []
      })
      toast.success("모든 비선호 재료가 삭제되었습니다")
    } catch (error) {
      toast.error("비선호 재료 삭제 중 오류가 발생했습니다")
    }
  }



  // 로그인하지 않은 경우 아무것도 렌더링하지 않음 (리다이렉트 중)
  if (!user) {
    return null
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      {/* 헤더 */}
      <Box>
        <Typography 
          variant="h4" 
          sx={{ 
            fontWeight: 700, 
            color: 'primary.main',
            mb: 0.5
          }}
        >
          프로필 설정
        </Typography>
        <Typography variant="body2" color="text.secondary">
          개인 정보와 키토 다이어트 목표를 설정하세요
        </Typography>
      </Box>

      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: '1fr 1fr' }, gap: 3 }}>
        {/* 기본 정보 */}
        <Box>
          <Card>
          <CardHeader>
            <CardTitle>
              <Stack direction="row" alignItems="center" spacing={1}>
                <Person sx={{ fontSize: 20, color: 'text.primary' }} />
                <Typography variant="h6">기본 정보</Typography>
              </Stack>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Stack spacing={2}>
            {user?.profileImage && (
              <div className="flex items-center gap-3">
                <img
                  src={user.profileImage.startsWith('http:') ? user.profileImage.replace('http:', 'https:') : user.profileImage}
                  alt="avatar"
                  className="h-12 w-12 rounded-full object-cover"
                />
                <div className="text-sm text-muted-foreground">로그인된 사용자</div>
              </div>
            )}

            <div>
              <label className="text-sm font-medium">이메일</label>
              <Input
                value={user?.email || ''}
                placeholder="이메일"
                className="mt-1"
                disabled
              />
            </div>

            <div>
              <label className="text-sm font-medium">닉네임</label>
              <Input
                value={nickname}
                onChange={(e) => setNickname(e.target.value)}
                placeholder="닉네임을 입력하세요"
                className="mt-1"
              />
            </div>
            
                <Button 
                  onClick={handleSaveBasicInfo} 
                  className="w-full"
                  variant="contained"
                  disabled={isBasicInfoLoading || !hasBasicInfoChanged}
                >
                  {isBasicInfoLoading ? (
                    <>
                      <CircularProgress size={16} sx={{ mr: 1 }} />
                      저장 중...
                    </>
                  ) : (
                    '저장'
                  )}
            </Button>
            </Stack>
          </CardContent>
        </Card>
        </Box>

        {/* 키토 목표 */}
        <Box>
          <Card>
            <CardHeader>
              <CardTitle>
                <Stack direction="row" alignItems="center" spacing={1}>
                  <GpsFixed sx={{ fontSize: 20, color: 'success.main' }} />
                  <Typography variant="h6">키토 목표</Typography>
                </Stack>
              </CardTitle>
            </CardHeader>
          <CardContent>
            <Stack spacing={2}>
            <div>
              <label className="text-sm font-medium">일일 목표 칼로리</label>
              <Input
                    type="text"
                    numericOnly
                    min={0}
                    max={3000}
                    useComma
                value={goalsKcal}
                onChange={(e) => setGoalsKcal(e.target.value)}
                placeholder="1500"
                className="mt-1"
              />
              <p className="text-xs text-muted-foreground mt-1">
                    개인의 기초대사율과 활동량을 고려하세요, 최대 3000kcal까지 입력 가능합니다.
              </p>
            </div>
            
            <div>
              <label className="text-sm font-medium">일일 최대 탄수화물 (g)</label>
              <Input
                    type="text"
                    numericOnly
                    min={0}
                    max={50}
                value={goalsCarbsG}
                onChange={(e) => setGoalsCarbsG(e.target.value)}
                    placeholder="20"
                className="mt-1"
              />
              <p className="text-xs text-muted-foreground mt-1">
                    키토시스 유지를 위해 20-30g 권장, 최대 50g까지 입력 가능합니다.
              </p>
            </div>
            
            <Button 
              onClick={handleSaveKetoGoals} 
              className="w-full"
              variant="contained"
              disabled={isKetoGoalsLoading || !hasKetoGoalsChanged}
            >
              {isKetoGoalsLoading ? (
                <>
                  <CircularProgress size={16} sx={{ mr: 1 }} />
                  저장 중...
                </>
              ) : (
                '목표 저장'
              )}
            </Button>
            </Stack>
          </CardContent>
        </Card>
        </Box>
      </Box>

      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: '1fr 1fr' }, gap: 3, mt: 3 }}>
        {/* 알레르기 */}
        <Box>
          <Card>
          <CardHeader>
            <CardTitle>
              <Stack direction="row" alignItems="center" spacing={1}>
                <Warning sx={{ fontSize: 20, color: 'error.main' }} />
                <Typography variant="h6">알레르기</Typography>
              </Stack>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Stack spacing={2}>
            <Stack direction="row" spacing={2}>
                  <Select 
                    value={selectedAllergyId} 
                    onChange={setSelectedAllergyId}
                    options={Object.entries(getAllergiesByCategory()).flatMap(([category, allergies]) => 
                      allergies.map(allergy => ({
                        value: allergy.id.toString(),
                        label: `${category} - ${allergy.name}`,
                        disabled: profile?.selected_allergy_ids.includes(allergy.id)
                      }))
                    )}
                    placeholder="알레르기를 선택하세요"
                    size="medium"
                  />
                  <Button 
                    onClick={handleAddAllergy} 
                    className="h-12 w-12 flex-shrink-0"
                    disabled={isAllergyLoading || !selectedAllergyId}
                  >
                    {isAllergyLoading ? (
                      <CircularProgress size={16} />
                    ) : (
                <Add sx={{ fontSize: 16 }} />
                    )}
              </Button>
            </Stack>
            
            <Stack spacing={1.5}>
            <div className="flex flex-wrap gap-2">
                    {profile?.allergy_names?.map((allergyName, index) => {
                      const allergyId = profile.selected_allergy_ids[index]
                      return (
                <Badge 
                          key={allergyId} 
                          variant="outline" 
                          className="flex items-center gap-1 bg-red-100 text-red-800 border-red-300 hover:bg-red-200"
                        >
                          {allergyName}
                  <Delete 
                    sx={{ fontSize: 12, cursor: 'pointer' }} 
                            onClick={() => handleRemoveAllergy(allergyId)}
                  />
                </Badge>
                      )
                    })}
                  </div>
                  
                  {/* 전체 삭제 버튼 */}
                  {profile?.allergy_names && profile.allergy_names.length > 0 && (
                    <Button
                      onClick={handleClearAllAllergies}
                      variant="outline"
                      size="sm"
                      className="text-red-600 hover:text-red-700 hover:bg-red-50 border-red-300"
                    >
                      <Delete sx={{ fontSize: 16, mr: 0.5 }} />
                      전체 삭제 ({profile.allergy_names.length}개)
                    </Button>
                  )}
            </Stack>
            
            {(!profile?.allergy_names || profile.allergy_names.length === 0) && (
              <Typography variant="body2" color="text.secondary">
                등록된 알레르기가 없습니다
              </Typography>
            )}
            </Stack>
          </CardContent>
        </Card>
        </Box>

        {/* 비선호 재료 */}
        <Box>
          <Card>
            <CardHeader>
              <CardTitle>
                <Stack direction="row" alignItems="center" spacing={1}>
                  <ThumbDown sx={{ fontSize: 20, color: 'warning.main' }} />
                  <Typography variant="h6">비선호 재료</Typography>
                </Stack>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Stack spacing={2}>
            <Stack direction="row" spacing={2}>
                  <Select 
                    value={selectedDislikeId} 
                    onChange={setSelectedDislikeId}
                    options={Object.entries(getDislikesByCategory()).flatMap(([category, dislikes]) => 
                      dislikes.map(dislike => ({
                        value: dislike.id.toString(),
                        label: `${category} - ${dislike.name}`,
                        disabled: profile?.selected_dislike_ids.includes(dislike.id)
                      }))
                    )}
                    placeholder="비선호 재료를 선택하세요"
                    size="medium"
                  />
                  <Button 
                    onClick={handleAddDislike} 
                    className="h-12 w-12 flex-shrink-0"
                    disabled={isDislikeLoading || !selectedDislikeId}
                  >
                    {isDislikeLoading ? (
                      <CircularProgress size={16} />
                    ) : (
                <Add sx={{ fontSize: 16 }} />
                    )}
              </Button>
            </Stack>
            
            <Stack spacing={1.5}>
            <div className="flex flex-wrap gap-2">
                    {profile?.dislike_names?.map((dislikeName, index) => {
                      const dislikeId = profile.selected_dislike_ids[index]
                      return (
                <Badge 
                          key={dislikeId} 
                  variant="outline" 
                          className="flex items-center gap-1 bg-orange-100 text-orange-800 border-orange-300 hover:bg-orange-200"
                >
                          {dislikeName}
                  <Delete 
                    sx={{ fontSize: 12, cursor: 'pointer' }} 
                            onClick={() => handleRemoveDislike(dislikeId)}
                  />
                </Badge>
                      )
                    })}
                  </div>
                  
                  {/* 전체 삭제 버튼 */}
                  {profile?.dislike_names && profile.dislike_names.length > 0 && (
                    <Button
                      onClick={handleClearAllDislikes}
                      variant="outline"
                      size="sm"
                      className="text-orange-600 hover:text-orange-700 hover:bg-orange-50 border-orange-300"
                    >
                      <Delete sx={{ fontSize: 16, mr: 0.5 }} />
                      전체 삭제 ({profile.dislike_names.length}개)
                    </Button>
                  )}
            </Stack>
            
            {(!profile?.dislike_names || profile.dislike_names.length === 0) && (
              <Typography variant="body2" color="text.secondary">
                등록된 비선호 재료가 없습니다
              </Typography>
            )}
            </Stack>
          </CardContent>
        </Card>
        </Box>
      </Box>

      {/* 키토 가이드 */}
      <Card>
        <CardHeader>
          <CardTitle>
            <Typography variant="h6">키토 다이어트 가이드</Typography>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr 1fr' }, gap: 2 }}>
            <Box>
              <Box 
                sx={{ 
                  textAlign: 'center', 
                  p: 2, 
                  bgcolor: 'success.50', 
                  borderRadius: 2 
                }}
              >
                <Typography variant="h4" sx={{ fontWeight: 700, color: 'success.main' }}>
                  70-80%
                </Typography>
                <Typography variant="body2" sx={{ color: 'success.dark' }}>
                  지방
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                  주 에너지원
                </Typography>
              </Box>
            </Box>
            
            <Box>
              <Box 
                sx={{ 
                  textAlign: 'center', 
                  p: 2, 
                  bgcolor: 'primary.50', 
                  borderRadius: 2 
                }}
              >
                <Typography variant="h4" sx={{ fontWeight: 700, color: 'primary.main' }}>
                  15-25%
                </Typography>
                <Typography variant="body2" sx={{ color: 'primary.dark' }}>
                  단백질
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                  근육 유지
                </Typography>
              </Box>
            </Box>
            
            <Box>
              <Box 
                sx={{ 
                  textAlign: 'center', 
                  p: 2, 
                  bgcolor: 'warning.50', 
                  borderRadius: 2 
                }}
              >
                <Typography variant="h4" sx={{ fontWeight: 700, color: 'warning.main' }}>
                  5-10%
                </Typography>
                <Typography variant="body2" sx={{ color: 'warning.dark' }}>
                  탄수화물
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                  최소 섭취
                </Typography>
              </Box>
            </Box>
          </Box>
          
          <Box sx={{ mt: 3 }}>
            <Typography variant="h6" sx={{ fontWeight: 500, mb: 1 }}>
              💡 키토 성공 팁
            </Typography>
            <Stack spacing={0.5}>
              <Typography variant="body2" color="text.secondary">
                • 충분한 물 섭취 (하루 2-3L)
              </Typography>
              <Typography variant="body2" color="text.secondary">
                • 전해질 보충 (나트륨, 칼륨, 마그네슘)
              </Typography>
              <Typography variant="body2" color="text.secondary">
                • 점진적 탄수화물 감소
              </Typography>
              <Typography variant="body2" color="text.secondary">
                • 규칙적인 식사 시간
              </Typography>
              <Typography variant="body2" color="text.secondary">
                • 스트레스 관리와 충분한 수면
              </Typography>
            </Stack>
          </Box>
        </CardContent>
      </Card>
    </Box>
  )
}