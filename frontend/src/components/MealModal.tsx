import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Close, Save } from '@mui/icons-material'
import { MealData } from '@/data/ketoMeals'
import { useAddMealToCalendar } from '@/hooks/useApi'
import { format } from 'date-fns'
import { useAuthStore } from '@/store/authStore'
import { useQueryClient } from '@tanstack/react-query'

interface MealModalProps {
  isOpen: boolean
  onClose: () => void
  selectedDate: Date
  mealData?: MealData | null
  onSave: (date: Date, mealData: MealData) => void
  selectedMealType?: string | null
}

export function MealModal({ isOpen, onClose, selectedDate, mealData, onSave, selectedMealType }: MealModalProps) {
  const [formData, setFormData] = useState<MealData>({
    breakfast: mealData?.breakfast || '',
    lunch: mealData?.lunch || '',
    dinner: mealData?.dinner || '',
    snack: mealData?.snack || ''
  })

  const handleInputChange = (field: keyof MealData, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const handleSave = () => {
    onSave(selectedDate, formData)
    onClose()
  }

  const handleClose = () => {
    setFormData({
      breakfast: mealData?.breakfast || '',
      lunch: mealData?.lunch || '',
      dinner: mealData?.dinner || '',
      snack: mealData?.snack || ''
    })
    onClose()
  }

  const allMeals = [
    { key: 'breakfast', label: '아침', icon: '🌅', placeholder: '아침 메뉴를 입력하세요' },
    { key: 'lunch', label: '점심', icon: '☀️', placeholder: '점심 메뉴를 입력하세요' },
    { key: 'dinner', label: '저녁', icon: '🌙', placeholder: '저녁 메뉴를 입력하세요' },
    { key: 'snack', label: '간식', icon: '🍎', placeholder: '간식 메뉴를 입력하세요' }
  ]

  // 선택된 식사 시간이 있으면 해당 시간만, 없으면 모든 시간 표시
  const meals = selectedMealType 
    ? allMeals.filter(meal => meal.key === selectedMealType)
    : allMeals

  // 모달에서 입력한 값을 캘린더에 추가하기
  const addMealMutation = useAddMealToCalendar()
  const user = useAuthStore(state => state.user)
  const queryClient = useQueryClient()
  const addMeal = async () => {
    const dateStr = format(selectedDate, 'yyyy-MM-dd')
    const targets = selectedMealType
      ? [selectedMealType]
      : (['breakfast','lunch','dinner','snack'] as const)

    // 각 타겟 슬롯에 대해 입력값이 있는 경우만 전송하고, 캐시를 즉시 병합 업데이트
    const createdPlans: any[] = []
    for (const slot of targets) {
      const text = String(formData[slot as keyof MealData] || '').trim()
      if (!text) continue
      try {
        const result = await addMealMutation.mutateAsync({
          user_id: user?.id || '',
          date: dateStr,
          slot: slot as any,
          type: 'recipe',
          ref_id: '',
          title: text
        })
        createdPlans.push(result)
      } catch (e: any) {
        console.error('캘린더 추가 실패:', e)
        alert(e?.response?.data?.detail || '저장 중 오류가 발생했습니다')
        return
      }
    }

    // plans-range 캐시 병합 업데이트 (완전 새로고침 없이 반영)
    try {
      const queries = queryClient.getQueriesData<any>({ queryKey: ['plans-range'] })
      queries.forEach(([qKey, qData]) => {
        if (!Array.isArray(qData)) return
        const keyArr = qKey as unknown as any[]
        const start = keyArr?.[1]
        const end = keyArr?.[2]
        const qUserId = keyArr?.[3]

        if (!start || !end || !qUserId) return

        const inRange = (d: string) => d >= start && d <= end

        let changed = false
        let next = [...qData]

        for (const plan of createdPlans) {
          if (plan?.user_id !== qUserId) continue
          if (!inRange(plan?.date)) continue
          const idx = next.findIndex((p: any) => p.id === plan.id)
          if (idx >= 0) {
            next[idx] = plan
          } else {
            next = [...next, plan]
          }
          changed = true
        }

        if (changed) {
          // 날짜 기준 정렬 유지
          next.sort((a: any, b: any) => (a.date < b.date ? -1 : a.date > b.date ? 1 : 0))
          queryClient.setQueryData(qKey, next)
        }
      })
    } catch (e) {
      // 캐시 업데이트 실패 시에는 무효화로 폴백
      queryClient.invalidateQueries({ queryKey: ['plans-range'] })
    }
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
          <CardTitle className="text-xl font-bold">
            {selectedDate.toLocaleDateString('ko-KR', { 
              year: 'numeric', 
              month: 'long', 
              day: 'numeric' 
            })} {selectedMealType ? allMeals.find(m => m.key === selectedMealType)?.label : '식단'}
          </CardTitle>
        </CardHeader>
        
        <CardContent className="space-y-6">
          {meals.map((meal) => (
            <div key={meal.key} className="space-y-2">
              <label className="text-sm font-medium flex items-center gap-2">
                <span className="text-lg">{meal.icon}</span>
                {meal.label}
              </label>
              <Input
                value={String(formData[meal.key as keyof MealData] || '')}
                onChange={(e) => handleInputChange(meal.key as keyof MealData, e.target.value)}
                placeholder={meal.placeholder}
                className="w-full"
              />
            </div>
          ))}
          
          <div className="flex gap-3 pt-4">
            <Button onClick={addMeal} className="flex-1">
              <Save className="h-4 w-4 mr-2" />
              저장
            </Button>
            <Button variant="outline" onClick={handleClose} className="flex-1">
              취소
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}