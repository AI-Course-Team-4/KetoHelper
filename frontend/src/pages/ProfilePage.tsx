import { useState, useEffect, useMemo, useContext, useRef } from 'react'
import { useNavigate, UNSAFE_NavigationContext } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Person, GpsFixed, Warning, ThumbDown } from '@mui/icons-material'
import { CircularProgress, Box, Typography, Stack, Card, CardContent, CardHeader, Autocomplete, Chip, TextField, Checkbox } from '@mui/material'
import { useProfileStore, useProfileHelpers } from '@/store/profileStore'
import { useAuthStore } from '@/store/authStore'
import { toast } from 'react-hot-toast'

interface OptionType {
  id: number
  name: string
  category: string
  label: string
  description?: string
}

export function ProfilePage() {
  const navigation = useContext(UNSAFE_NavigationContext)?.navigator as any
  const navigate = useNavigate()
  const { user, updateUser } = useAuthStore()
  const { 
    profile, 
    error,
    loadMasterData,
    loadProfile,
    updateProfile
  } = useProfileStore()
  const { 
    getAllergiesByCategory,
    getDislikesByCategory 
  } = useProfileHelpers()

  const [nickname, setNickname] = useState('')
  const [goalsKcal, setGoalsKcal] = useState('')
  const [goalsCarbsG, setGoalsCarbsG] = useState('')

  // 로컬 상태 (알레르기, 비선호 재료)
  const [localAllergyIds, setLocalAllergyIds] = useState<number[]>([])
  const [localDislikeIds, setLocalDislikeIds] = useState<number[]>([])

  // 저장된 데이터 (변경 감지용)
  const [savedNickname, setSavedNickname] = useState('')
  const [savedGoalsKcal, setSavedGoalsKcal] = useState('')
  const [savedGoalsCarbsG, setSavedGoalsCarbsG] = useState('')
  const [savedAllergyIds, setSavedAllergyIds] = useState<number[]>([])
  const [savedDislikeIds, setSavedDislikeIds] = useState<number[]>([])

  // 일괄 저장 중 토스트 중복 방지 플래그
  const isBulkSavingRef = useRef<boolean>(false)
  const isNavigatingRef = useRef<boolean>(false)


  // 알레르기/비선호 재료 옵션들을 미리 계산
  const allergyOptions = useMemo(() => {
    return Object.entries(getAllergiesByCategory()).flatMap(([category, allergies]) => 
      allergies.map(allergy => ({
        id: allergy.id,
        name: allergy.name,
        category: category,
        label: `${category} - ${allergy.name}`,
        description: allergy.description
      }))
    )
  }, [getAllergiesByCategory])

  const dislikeOptions = useMemo(() => {
    return Object.entries(getDislikesByCategory()).flatMap(([category, dislikes]) => 
      dislikes.map(dislike => ({
        id: dislike.id,
        name: dislike.name,
        category: category,
        label: `${category} - ${dislike.name}`,
        description: dislike.description
      }))
    )
  }, [getDislikesByCategory])

  // 선택된 알레르기/비선호 재료 객체들
  const selectedAllergies = useMemo(() => {
    return localAllergyIds.map(id => allergyOptions.find(option => option.id === id)).filter(Boolean) as OptionType[]
  }, [localAllergyIds, allergyOptions])

  const selectedDislikes = useMemo(() => {
    return localDislikeIds.map(id => dislikeOptions.find(option => option.id === id)).filter(Boolean) as OptionType[]
  }, [localDislikeIds, dislikeOptions])

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
      const nicknameOrUndefined = profile.nickname && profile.nickname.trim() !== '' ? profile.nickname : undefined
      const newNickname = nicknameOrUndefined ?? profile.social_nickname ?? user?.name ?? ''
      const newGoalsKcal = profile.goals_kcal ? profile.goals_kcal.toLocaleString() : ''
      const newGoalsCarbsG = profile.goals_carbs_g ? String(profile.goals_carbs_g) : ''
      
      
      setNickname(newNickname)
      setGoalsKcal(newGoalsKcal)
      setGoalsCarbsG(newGoalsCarbsG)
      
      // 로컬 상태 초기화
      setLocalAllergyIds(profile.selected_allergy_ids || [])
      setLocalDislikeIds(profile.selected_dislike_ids || [])
      
      // 저장된 데이터도 업데이트
      setSavedNickname(newNickname)
      setSavedGoalsKcal(newGoalsKcal)
      setSavedGoalsCarbsG(newGoalsCarbsG)
      setSavedAllergyIds(profile.selected_allergy_ids || [])
      setSavedDislikeIds(profile.selected_dislike_ids || [])
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
      alert('로그아웃 되었습니다. 메인 페이지로 이동합니다.')
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
  const hasAllergyChanged = JSON.stringify(localAllergyIds.sort()) !== JSON.stringify(savedAllergyIds.sort())
  const hasDislikeChanged = JSON.stringify(localDislikeIds.sort()) !== JSON.stringify(savedDislikeIds.sort())
  const hasAnyChanges = hasBasicInfoChanged || hasKetoGoalsChanged || hasAllergyChanged || hasDislikeChanged

  // 공통 확인/저장 유틸 - 최신 상태로 변경분만 순차 저장
  const confirmAndSaveIfNeeded = async (): Promise<boolean> => {
    if (!hasAnyChanges) return true
    isBulkSavingRef.current = true
    isNavigatingRef.current = true
    console.group('[Profile] Unsaved changes before navigation')
    if (hasBasicInfoChanged) console.log('BasicInfo - nickname (current -> saved):', nickname, '->', savedNickname)
    if (hasKetoGoalsChanged) {
      console.log('KetoGoals - goalsKcal (current -> saved):', goalsKcal, '->', savedGoalsKcal)
      console.log('KetoGoals - goalsCarbsG (current -> saved):', goalsCarbsG, '->', savedGoalsCarbsG)
    }
    if (hasAllergyChanged) console.log('Allergies - current IDs:', localAllergyIds, 'saved IDs:', savedAllergyIds)
    if (hasDislikeChanged) console.log('Dislikes - current IDs:', localDislikeIds, 'saved IDs:', savedDislikeIds)
    console.groupEnd()
    const ok = window.confirm('변경내용이 저장되지 않았습니다. 저장하시겠습니까?')
    if (!ok) { isNavigatingRef.current = false; return false }
    if (hasBasicInfoChanged) await handleSaveBasicInfo()
    if (hasKetoGoalsChanged) await handleSaveKetoGoals()
    if (hasAllergyChanged) await handleSaveAllergy()
    if (hasDislikeChanged) await handleSaveDislike()
    isBulkSavingRef.current = false
    // 전역 Toaster의 기본 지속 시간을 사용
    toast.success('변경사항이 저장되었습니다')
    return true
  }

  // 라우터 차단 방식: 모든 내부 네비게이션에서 확실히 개입
  useEffect(() => {
    if (!navigation?.block) return
    const unblock = navigation.block(async (tx: any) => {
      const proceed = await confirmAndSaveIfNeeded()
      if (!proceed) return
      // 아주 짧은 지연을 주어 토스트가 보일 시간을 확보
      setTimeout(() => {
        unblock()
        tx.retry()
      }, 80)
    })
    return unblock
  }, [navigation, hasAnyChanges, hasBasicInfoChanged, hasKetoGoalsChanged, hasAllergyChanged, hasDislikeChanged, nickname, savedNickname, goalsKcal, savedGoalsKcal, goalsCarbsG, savedGoalsCarbsG, localAllergyIds, savedAllergyIds, localDislikeIds, savedDislikeIds])

  // 보조 가드: a/Link 클릭을 캡처해 확인/저장을 보장 (SPA 내부 전환 유지)
  useEffect(() => {
    const handler = async (event: MouseEvent) => {
      const target = event.target as Element | null
      const anchor = target?.closest('a') as HTMLAnchorElement | null
      if (!anchor) return
      if (anchor.target === '_blank') return
      const href = anchor.getAttribute('href') || ''
      if (!href || href.startsWith('#') || href.startsWith('javascript:')) return
      const isSameOrigin = anchor.host === window.location.host
      if (!isSameOrigin) return
      if (!hasAnyChanges) return
      event.preventDefault()
      const ok = await confirmAndSaveIfNeeded()
      if (ok) {
        // SPA 내비게이션으로 이동 (전체 리로드 금지)
        setTimeout(() => navigate(href), 0)
      }
    }
    document.addEventListener('click', handler, true)
    return () => document.removeEventListener('click', handler, true)
  }, [hasAnyChanges, confirmAndSaveIfNeeded, navigate])

  // 내부 라우팅 차단 훅 제거됨: 링크 클릭시 저장 후 이동 로직으로 대체

  const handleSaveBasicInfo = async () => {
    if (!user?.id) {
      toast.error("로그인이 필요합니다")
      return
    }

    // 입력값 정제
    const inputNickname = (nickname ?? '').trim()
    // 요구사항: 빈값으로 저장하되, 화면/초기화 시에는 social_nickname으로 표시
    const nextNickname = inputNickname === '' ? '' : inputNickname

    // 닉네임 미완성 한글 검증 (선택사항)
    if (nextNickname && /[ㄱ-ㅎㅏ-ㅣ]/.test(nextNickname)) {
      toast.error("닉네임에 미완성 한글이 포함되어 있습니다")
      return
    }

    setIsBasicInfoLoading(true)
    try {
      await updateProfile(user.id, {
        nickname: nextNickname, // 빈 문자열도 그대로 저장
        goals_kcal: profile?.goals_kcal,
        goals_carbs_g: profile?.goals_carbs_g,
        selected_allergy_ids: profile?.selected_allergy_ids,
        selected_dislike_ids: profile?.selected_dislike_ids,
      })
      
      // 저장 성공 시 저장된 데이터 업데이트
      setSavedNickname(nextNickname)
      
      // 헤더 등 표시 이름 업데이트: 닉네임이 비어 있으면 socialNickname 사용
      updateUser({ name: nextNickname || (user as any)?.socialNickname || user.name })
      
      if (!isBulkSavingRef.current) toast.success("기본 정보가 저장되었습니다")
    } catch (error) {
      toast.error('기본 정보 저장에 실패했습니다')
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
      
      if (!isBulkSavingRef.current) toast.success("키토 목표가 저장되었습니다")
    } catch (error) {
      // 에러는 스토어에서 처리됨
    } finally {
      setIsKetoGoalsLoading(false)
    }
  }

  const handleSaveAllergy = async () => {
    if (!user?.id) {
      toast.error("로그인이 필요합니다")
      return
    }

    setIsAllergyLoading(true)
    try {
      await updateProfile(user.id, {
        selected_allergy_ids: localAllergyIds
      })
      
      // 저장 성공 시 저장된 데이터 업데이트
      setSavedAllergyIds([...localAllergyIds])
      
      if (!isBulkSavingRef.current) toast.success("알레르기 정보가 저장되었습니다")
    } catch (error) {
      // 에러는 스토어에서 처리됨
    } finally {
      setIsAllergyLoading(false)
    }
  }

  const handleSaveDislike = async () => {
    if (!user?.id) {
      toast.error("로그인이 필요합니다")
      return
    }

    setIsDislikeLoading(true)
    try {
      await updateProfile(user.id, {
        selected_dislike_ids: localDislikeIds
      })
      
      // 저장 성공 시 저장된 데이터 업데이트
      setSavedDislikeIds([...localDislikeIds])
      
      if (!isBulkSavingRef.current) toast.success("비선호 재료 정보가 저장되었습니다")
    } catch (error) {
      // 에러는 스토어에서 처리됨
    } finally {
      setIsDislikeLoading(false)
    }
  }




  // 로그인하지 않은 경우 아무것도 렌더링하지 않음 (리다이렉트 중)
  if (!user || isNavigatingRef.current) {
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

      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: '1fr 1fr' }, gap: 3, alignItems: 'stretch' }}>
        {/* 기본 정보 */}
        <Box sx={{ display: 'flex', flexDirection: 'column' }}>
          <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <CardHeader
              title={
                <Stack direction="row" alignItems="center" spacing={1}>
                  <Person sx={{ fontSize: 20, color: 'text.primary' }} />
                  <span>기본 정보</span>
                </Stack>
              }
            />
            <CardContent sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
              <Stack spacing={2} sx={{ flex: 1 }}>
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
        <Box sx={{ display: 'flex', flexDirection: 'column' }}>
          <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <CardHeader
              title={
                <Stack direction="row" alignItems="center" spacing={1}>
                  <GpsFixed sx={{ fontSize: 20, color: 'success.main' }} />
                  <span>키토 목표</span>
                </Stack>
              }
            />
            <CardContent sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
              <Stack spacing={2} sx={{ flex: 1 }}>
            <div>
              <label className="text-sm font-medium">일일 목표 칼로리 (kcal)</label> 
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
                '저장'
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
          <CardHeader
            title={
              <Stack direction="row" alignItems="center" spacing={1}>
                <Warning sx={{ fontSize: 20, color: 'error.main' }} />
                <span>알레르기</span>
              </Stack>
            }
          />
          <CardContent>
            <Stack spacing={2}>
            <Autocomplete<OptionType, true, false, false>
              id="allergy-autocomplete"
              multiple
              disableCloseOnSelect={true}
              options={allergyOptions}
              groupBy={(option) => option.category}
              getOptionLabel={(option) => option.label}
              isOptionEqualToValue={(option, value) => option.id === value.id}
              value={selectedAllergies}
              onChange={(_, newValue) => {
                const newAllergyIds = newValue.map(item => item.id)
                setLocalAllergyIds(newAllergyIds)
              }}
              renderInput={(params) => (
                <TextField
                  {...params}
                  placeholder="알레르기를 선택하세요"
                  variant="outlined"
                />
              )}
              noOptionsText="해당하는 알레르기가 없습니다"
              renderValue={(value, getTagProps) =>
                value.map((option, index) => {
                  const safeOption = option as OptionType
                            return (
                    <Chip
                      {...getTagProps({ index })}
                      key={`allergy-chip-${safeOption.id}-${index}`}
                      label={safeOption.name}
                      color="error"
                      variant="outlined"
                      onDelete={() => {
                        const newAllergyIds = localAllergyIds.filter(id => id !== safeOption.id)
                        setLocalAllergyIds(newAllergyIds)
                        console.log('알레르기 개별 삭제:', safeOption.name, '새로운 IDs:', newAllergyIds)
                      }}
                    />
                  )
                })
              }
              renderOption={(props, option) => {
                const isSelected = localAllergyIds.includes(option.id)
                const { key, ...optionProps } = props
                      return (
                  <Box component="li" key={key} {...optionProps}>
                    <Checkbox
                      checked={isSelected}
                      sx={{ mr: 1 }}
                    />
                    <Box 
                      sx={{ 
                        flex: 1,
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'flex-start',
                        py: 0.5,
                        transition: 'all 0.2s ease-in-out'
                      }}
                    >
                      <Box sx={{ flex: 1 }}>
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          {option.name}
                        </Typography>
                        {option.description && (
                          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5, fontStyle: 'italic' }}>
                            {option.description}
                          </Typography>
                        )}
                      </Box>
                    </Box>
                  </Box>
                )
              }}
            />
            
            <Button 
              onClick={handleSaveAllergy} 
              className="w-full mt-2"
              variant="contained"
              disabled={isAllergyLoading || !hasAllergyChanged}
            >
              {isAllergyLoading ? (
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

        {/* 비선호 재료 */}
        <Box>
        <Card>
            <CardHeader
              title={
                <Stack direction="row" alignItems="center" spacing={1}>
                  <ThumbDown sx={{ fontSize: 20, color: 'warning.main' }} />
                  <span>비선호 재료</span>
                </Stack>
              }
            />
          <CardContent>
            <Stack spacing={2}>
            <Autocomplete<OptionType, true, false, false>
              id="dislike-autocomplete"
              multiple
              disableCloseOnSelect={true}
              options={dislikeOptions}
              groupBy={(option) => option.category}
              getOptionLabel={(option) => option.label}
              isOptionEqualToValue={(option, value) => option.id === value.id}
              value={selectedDislikes}
              onChange={(_, newValue) => {
                const newDislikeIds = newValue.map(item => item.id)
                setLocalDislikeIds(newDislikeIds)
              }}
              renderInput={(params) => (
                <TextField
                  {...params}
                  placeholder="비선호 재료를 선택하세요"
                  variant="outlined"
                />
              )}
              noOptionsText="해당하는 비선호 재료가 없습니다"
              renderValue={(value, getTagProps) =>
                value.map((option, index) => {
                  const safeOption = option as OptionType
                            return (
                    <Chip
                      {...getTagProps({ index })}
                      key={`dislike-chip-${safeOption.id}-${index}`}
                      label={safeOption.name}
                      color="warning"
                      variant="outlined"
                      onDelete={() => {
                        const newDislikeIds = localDislikeIds.filter(id => id !== safeOption.id)
                        setLocalDislikeIds(newDislikeIds)
                        console.log('비선호 재료 개별 삭제:', safeOption.name, '새로운 IDs:', newDislikeIds)
                      }}
                    />
                  )
                })
              }
              renderOption={(props, option) => {
                const isSelected = localDislikeIds.includes(option.id)
                const { key, ...optionProps } = props
                      return (
                  <Box component="li" key={key} {...optionProps}>
                    <Checkbox
                      checked={isSelected}
                      sx={{ mr: 1 }}
                    />
                    <Box 
                      sx={{ 
                        flex: 1,
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'flex-start',
                        py: 0.5,
                        transition: 'all 0.2s ease-in-out'
                      }}
                    >
                      <Box sx={{ flex: 1 }}>
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          {option.name}
                        </Typography>
                        {option.description && (
                          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5, fontStyle: 'italic' }}>
                            {option.description}
                          </Typography>
                        )}
                      </Box>
                    </Box>
                  </Box>
                )
              }}
            />
            
            <Button 
              onClick={handleSaveDislike} 
              className="w-full mt-2"
              variant="contained"
              disabled={isDislikeLoading || !hasDislikeChanged}
            >
              {isDislikeLoading ? (
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
      </Box>

      
    </Box>
  )
}