import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/common'
import { User, Target, AlertTriangle, Trash2, Plus, Loader2 } from 'lucide-react'
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

  const [nickname, setNickname] = useState(profile?.nickname ?? user?.name ?? '')
  const [goalsKcal, setGoalsKcal] = useState(profile?.goals_kcal ? profile.goals_kcal.toLocaleString() : '')
  const [goalsCarbsG, setGoalsCarbsG] = useState(profile?.goals_carbs_g ? String(profile.goals_carbs_g) : '')
  const [selectedAllergyId, setSelectedAllergyId] = useState<string>('')
  const [selectedDislikeId, setSelectedDislikeId] = useState<string>('')

  // 원본 데이터 저장 (변경 감지용)
  const [originalNickname, setOriginalNickname] = useState(profile?.nickname ?? user?.name ?? '')
  const [originalGoalsKcal, setOriginalGoalsKcal] = useState(profile?.goals_kcal ? profile.goals_kcal.toLocaleString() : '')
  const [originalGoalsCarbsG, setOriginalGoalsCarbsG] = useState(profile?.goals_carbs_g ? String(profile.goals_carbs_g) : '')

  // 마스터 데이터 및 프로필 로드
  useEffect(() => {
    loadMasterData()
    if (user?.id) {
      loadProfile(user.id)
    }
  }, [user?.id, loadProfile, loadMasterData])


  // 프로필 데이터가 변경되면 로컬 상태 업데이트
  useEffect(() => {
    if (profile) {
      const newNickname = profile.nickname ?? user?.name ?? ''
      const newGoalsKcal = profile.goals_kcal ? profile.goals_kcal.toLocaleString() : ''
      const newGoalsCarbsG = profile.goals_carbs_g ? String(profile.goals_carbs_g) : ''
      
      setNickname(newNickname)
      setGoalsKcal(newGoalsKcal)
      setGoalsCarbsG(newGoalsCarbsG)
      
      // 원본 데이터도 업데이트
      setOriginalNickname(newNickname)
      setOriginalGoalsKcal(newGoalsKcal)
      setOriginalGoalsCarbsG(newGoalsCarbsG)
    }
  }, [profile, user?.name])

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
  const hasBasicInfoChanged = nickname !== originalNickname
  const hasKetoGoalsChanged = goalsKcal !== originalGoalsKcal || goalsCarbsG !== originalGoalsCarbsG

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
      
      // 저장 성공 시 원본 데이터 업데이트
      setOriginalNickname(nickname)
      
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
      
      // 저장 성공 시 원본 데이터 업데이트
      setOriginalGoalsKcal(goalsKcal)
      setOriginalGoalsCarbsG(goalsCarbsG)
      
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
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      저장 중...
                    </>
                  ) : (
                    '저장'
                  )}
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
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  저장 중...
                </>
              ) : (
                '목표 저장'
              )}
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
                  <Select value={selectedAllergyId} onValueChange={setSelectedAllergyId}>
                    <SelectTrigger className="flex-1" size="lg">
                      <SelectValue placeholder="알레르기를 선택하세요" />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.entries(getAllergiesByCategory()).map(([category, allergies]) => (
                        <div key={category}>
                          <div className="px-2 py-1.5 text-sm font-semibold text-muted-foreground">
                            {category}
                          </div>
                          {allergies.map((allergy) => {
                            const isAlreadySelected = profile?.selected_allergy_ids.includes(allergy.id)
                            return (
                              <SelectItem 
                                key={allergy.id} 
                                value={allergy.id.toString()}
                                disabled={isAlreadySelected}
                              >
                                <div className="flex flex-col">
                                  <div className="flex items-center justify-between">
                                    <span className="font-medium">{allergy.name}</span>
                                    {isAlreadySelected && (
                                      <span className="text-xs text-green-600 ml-2">✓ 이미 추가됨</span>
                                    )}
                                  </div>
                                  {allergy.description && (
                                    <span className="text-xs text-muted-foreground mt-0.5">
                                      {allergy.description}
                                    </span>
                                  )}
                                </div>
                              </SelectItem>
                            )
                          })}
                        </div>
                      ))}
                    </SelectContent>
                  </Select>
                  <Button 
                    onClick={handleAddAllergy} 
                    className="h-12 w-12 flex-shrink-0"
                    disabled={isAllergyLoading || !selectedAllergyId}
                  >
                    {isAllergyLoading ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Plus className="h-4 w-4" />
                    )}
                  </Button>
                </div>
            
                <div className="space-y-3">
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
                          <Trash2 
                            className="h-3 w-3 cursor-pointer" 
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
                      <Trash2 className="h-4 w-4 mr-1" />
                      전체 삭제 ({profile.allergy_names.length}개)
                    </Button>
                  )}
                </div>
            
            {(!profile?.allergy_names || profile.allergy_names.length === 0) && (
              <p className="text-sm text-muted-foreground">
                등록된 알레르기가 없습니다
              </p>
            )}
          </CardContent>
        </Card>

        {/* 비선호 재료 */}
        <Card>
          <CardHeader>
            <CardTitle>비선호 재료</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
                <div className="flex gap-2">
                  <Select value={selectedDislikeId} onValueChange={setSelectedDislikeId}>
                    <SelectTrigger className="flex-1" size="lg">
                      <SelectValue placeholder="비선호 재료를 선택하세요" />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.entries(getDislikesByCategory()).map(([category, dislikes]) => (
                        <div key={category}>
                          <div className="px-2 py-1.5 text-sm font-semibold text-muted-foreground">
                            {category}
                          </div>
                          {dislikes.map((dislike) => {
                            const isAlreadySelected = profile?.selected_dislike_ids.includes(dislike.id)
                            return (
                              <SelectItem 
                                key={dislike.id} 
                                value={dislike.id.toString()}
                                disabled={isAlreadySelected}
                              >
                                <div className="flex flex-col">
                                  <div className="flex items-center justify-between">
                                    <span className="font-medium">{dislike.name}</span>
                                    {isAlreadySelected && (
                                      <span className="text-xs text-green-600 ml-2">✓ 이미 추가됨</span>
                                    )}
                                  </div>
                                  {dislike.description && (
                                    <span className="text-xs text-muted-foreground mt-0.5">
                                      {dislike.description}
                                    </span>
                                  )}
                                </div>
                              </SelectItem>
                            )
                          })}
                        </div>
                      ))}
                    </SelectContent>
                  </Select>
                  <Button 
                    onClick={handleAddDislike} 
                    className="h-12 w-12 flex-shrink-0"
                    disabled={isDislikeLoading || !selectedDislikeId}
                  >
                    {isDislikeLoading ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Plus className="h-4 w-4" />
                    )}
                  </Button>
                </div>
            
                <div className="space-y-3">
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
                          <Trash2 
                            className="h-3 w-3 cursor-pointer" 
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
                      <Trash2 className="h-4 w-4 mr-1" />
                      전체 삭제 ({profile.dislike_names.length}개)
                    </Button>
                  )}
                </div>
            
            {(!profile?.dislike_names || profile.dislike_names.length === 0) && (
              <p className="text-sm text-muted-foreground">
                등록된 비선호 재료가 없습니다
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