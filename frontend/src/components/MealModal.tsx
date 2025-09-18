import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { X, Save, Plus } from 'lucide-react'
import { MealData } from '@/data/ketoMeals'

interface MealModalProps {
  isOpen: boolean
  onClose: () => void
  selectedDate: Date
  mealData?: MealData | null
  onSave: (date: Date, mealData: MealData) => void
}

export function MealModal({ isOpen, onClose, selectedDate, mealData, onSave }: MealModalProps) {
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

  if (!isOpen) return null

  const meals = [
    { key: 'breakfast', label: '아침', icon: '🌅', placeholder: '아침 메뉴를 입력하세요' },
    { key: 'lunch', label: '점심', icon: '☀️', placeholder: '점심 메뉴를 입력하세요' },
    { key: 'dinner', label: '저녁', icon: '🌙', placeholder: '저녁 메뉴를 입력하세요' },
    { key: 'snack', label: '간식', icon: '🍎', placeholder: '간식 메뉴를 입력하세요' }
  ]

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
          <CardTitle className="text-xl font-bold">
            {selectedDate.toLocaleDateString('ko-KR', { 
              year: 'numeric', 
              month: 'long', 
              day: 'numeric' 
            })} 식단
          </CardTitle>
          <Button variant="ghost" size="sm" onClick={handleClose}>
            <X className="h-4 w-4" />
          </Button>
        </CardHeader>
        
        <CardContent className="space-y-6">
          {meals.map((meal) => (
            <div key={meal.key} className="space-y-2">
              <label className="text-sm font-medium flex items-center gap-2">
                <span className="text-lg">{meal.icon}</span>
                {meal.label}
              </label>
              <Input
                value={formData[meal.key as keyof MealData] || ''}
                onChange={(e) => handleInputChange(meal.key as keyof MealData, e.target.value)}
                placeholder={meal.placeholder}
                className="w-full"
              />
            </div>
          ))}
          
          <div className="flex gap-3 pt-4">
            <Button onClick={handleSave} className="flex-1">
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
