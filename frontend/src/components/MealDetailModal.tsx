import { Dialog, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { AccessTime, Restaurant, GpsFixed, Star, RestaurantMenu, LocalFireDepartment } from '@mui/icons-material'

interface MealDetailModalProps {
  isOpen: boolean
  onClose: () => void
  mealType: 'breakfast' | 'lunch' | 'dinner' | 'snack'
  mealContent: string
  mealInfo: {
    label: string
    icon: string
    time: string
  }
}

// 키토 점수 계산 (예시)
const calculateMealKetoScore = (mealContent: string): number => {
  if (!mealContent || mealContent.trim() === '') return 0
  
  // 키토 친화적 키워드들
  const ketoFriendlyKeywords = [
    '아보카도', '연어', '계란', '치즈', '베이컨', '올리브오일', '견과류', 
    '아몬드', '호두', '코코넛', '버터', '크림', '치킨', '스테이크', '새우'
  ]
  
  const lowerContent = mealContent.toLowerCase()
  const score = ketoFriendlyKeywords.filter(keyword => 
    lowerContent.includes(keyword)
  ).length
  
  return Math.min(score * 15 + 40, 100) // 기본 40점 + 키워드당 15점
}

// 예상 영양성분 계산 (예시)
const estimateNutrition = (mealContent: string) => {
  const ketoScore = calculateMealKetoScore(mealContent)
  
  return {
    calories: Math.floor(300 + Math.random() * 300), // 300-600 칼로리
    carbs: Math.floor(5 + (100 - ketoScore) * 0.3), // 키토 점수가 높을수록 탄수화물 적음
    protein: Math.floor(20 + Math.random() * 30), // 20-50g
    fat: Math.floor(15 + Math.random() * 25) // 15-40g
  }
}

// 키토 팁 생성
const generateKetoTips = (mealType: string): string[] => {
  const tips = {
    breakfast: [
      "아침에는 탄수화물을 최소화하고 건강한 지방을 충분히 섭취하세요",
      "계란과 아보카도는 완벽한 키토 아침 조합입니다",
      "커피에 MCT 오일이나 버터를 추가해보세요"
    ],
    lunch: [
      "점심에는 양질의 단백질과 녹색 채소를 중심으로 구성하세요",
      "샐러드에는 올리브오일 드레싱을 사용하세요",
      "가공식품보다는 자연 그대로의 식재료를 선택하세요"
    ],
    dinner: [
      "저녁에는 소화가 잘 되는 가벼운 단백질을 선택하세요",
      "생선류는 오메가-3가 풍부해 키토 다이어트에 이상적입니다",
      "저녁 7시 이후에는 식사를 피하는 것이 좋습니다"
    ],
    snack: [
      "간식으로는 견과류나 치즈가 좋습니다",
      "과일보다는 베리류를 선택하세요",
      "간헐적 단식을 고려해 간식을 줄여보세요"
    ]
  }
  
  return tips[mealType as keyof typeof tips] || []
}

export function MealDetailModal({ 
  isOpen, 
  onClose, 
  mealType, 
  mealContent, 
  mealInfo 
}: MealDetailModalProps) {
  const ketoScore = calculateMealKetoScore(mealContent)
  const nutrition = estimateNutrition(mealContent)
  const tips = generateKetoTips(mealType)
  
  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600'
    if (score >= 60) return 'text-yellow-600'
    return 'text-red-600'
  }
  
  const getScoreBadge = (score: number) => {
    if (score >= 80) return { text: '키토 완벽', color: 'bg-green-100 text-green-800' }
    if (score >= 60) return { text: '키토 양호', color: 'bg-yellow-100 text-yellow-800' }
    return { text: '키토 부족', color: 'bg-red-100 text-red-800' }
  }
  
  const scoreBadge = getScoreBadge(ketoScore)

  return (
    <Dialog open={isOpen} onClose={onClose} onOpenChange={onClose}>
      <DialogHeader>
        <DialogTitle className="flex items-center gap-2">
          <span className="text-2xl">{mealInfo.icon}</span>
          {mealInfo.label} 상세정보
        </DialogTitle>
      </DialogHeader>

      <div className="space-y-4">
          {/* 메뉴 정보 */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Restaurant sx={{ fontSize: 16 }} />
                  메뉴
                </div>
                <div className="flex items-center gap-2">
                  <AccessTime sx={{ fontSize: 16 }} />
                  <span className="text-sm">{mealInfo.time}</span>
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-lg font-medium mb-3">{mealContent || '계획된 식단이 없습니다'}</p>
              {mealContent && (
                <div className="flex items-center gap-2">
                  <Badge className={scoreBadge.color}>
                    {scoreBadge.text}
                  </Badge>
                  <span className={`text-sm font-medium ${getScoreColor(ketoScore)}`}>
                    {ketoScore}점
                  </span>
                </div>
              )}
            </CardContent>
          </Card>

          {/* 영양 정보 */}
          {mealContent && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2">
                  <GpsFixed sx={{ fontSize: 16 }} />
                  예상 영양성분
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center">
                    <div className="flex items-center justify-center gap-1 mb-1">
                      <LocalFireDepartment sx={{ fontSize: 16, color: 'orange.500' }} />
                      <span className="text-2xl font-bold text-orange-600">{nutrition.calories}</span>
                    </div>
                    <p className="text-sm text-muted-foreground">칼로리</p>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-red-600">{nutrition.carbs}g</div>
                    <p className="text-sm text-muted-foreground">탄수화물</p>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">{nutrition.protein}g</div>
                    <p className="text-sm text-muted-foreground">단백질</p>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-purple-600">{nutrition.fat}g</div>
                    <p className="text-sm text-muted-foreground">지방</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* 키토 팁 */}
          {mealContent && tips.length > 0 && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2">
                  <RestaurantMenu sx={{ fontSize: 16 }} />
                  키토 팁
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {tips.map((tip, index) => (
                    <div key={index} className="flex items-start gap-2">
                      <Star className="h-4 w-4 text-yellow-500 mt-0.5 flex-shrink-0" />
                      <p className="text-sm text-muted-foreground">{tip}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* 액션 버튼 */}
          <div className="flex gap-2 pt-2">
            <Button className="flex-1" onClick={onClose}>
              확인
            </Button>
          </div>
        </div>
    </Dialog>
  )
}