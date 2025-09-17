import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { User, Target, AlertTriangle, Trash2, Plus } from 'lucide-react'
import { useProfileStore } from '@/store/profileStore'
import { useAuthStore } from '@/store/authStore'

export function ProfilePage() {
  const { 
    profile, 
    updateProfile, 
    addAllergy, 
    removeAllergy, 
    addDislike, 
    removeDislike 
  } = useProfileStore()
  const { user } = useAuthStore()

  const [nickname, setNickname] = useState(profile?.nickname ?? user?.name ?? '')
  const [goalsKcal, setGoalsKcal] = useState(profile?.goals_kcal || '')
  const [goalsCarbsG, setGoalsCarbsG] = useState(profile?.goals_carbs_g || '')
  const [newAllergy, setNewAllergy] = useState('')
  const [newDislike, setNewDislike] = useState('')

  // 로그아웃 시 닉네임 입력칸 공백 처리
  useEffect(() => {
    if (!user) {
      setNickname('')
    }
  }, [user])

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
    }
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
