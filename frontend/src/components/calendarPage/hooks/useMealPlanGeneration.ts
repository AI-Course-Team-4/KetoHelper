import { useState } from 'react'
import { format } from 'date-fns'
import { MealData, generateRandomMeal } from '@/data/ketoMeals'
import { useGenerateMealPlan, useCreatePlan } from '@/hooks/useApi'
import { useAuthStore } from '@/store/authStore'
import { useQueryClient } from '@tanstack/react-query'

// 백엔드 응답에서 식사 제목을 안전하게 추출하는 헬퍼 함수
const extractMealTitle = (mealData: any): string => {
  if (!mealData) return ''
  
  if (typeof mealData === 'string') {
    return mealData
  }
  
  if (typeof mealData === 'object' && mealData !== null) {
    // 백엔드 응답 형식: {title: "...", type: "simple"}
    return mealData.title || mealData.content || mealData.name || ''
  }
  
  return ''
}

export function useMealPlanGeneration() {
  const [selectedDays, setSelectedDays] = useState(7)
  const [isGeneratingMealPlan, setIsGeneratingMealPlan] = useState(false)

  const { user } = useAuthStore()
  const generateMealPlan = useGenerateMealPlan()
  const createPlan = useCreatePlan()
  const queryClient = useQueryClient()

  // AI 식단표 자동 저장 함수
  const handleAutoSaveMealPlan = async (mealPlanData: Record<string, MealData>) => {
    if (!user?.id) {
      console.error('❌ 사용자 ID가 없습니다.')
      return
    }

    try {
      console.log('💾 AI 식단표 자동 저장 시작...')
      
      let successCount = 0
      const totalDays = Object.keys(mealPlanData).length
      const savedDays: string[] = []

      // 각 날짜별로 식단 저장
      for (const [dateString, dayMeals] of Object.entries(mealPlanData)) {
        try {
          // 각 식사 시간대별로 개별 plan 생성
          const mealSlots = ['breakfast', 'lunch', 'dinner', 'snack'] as const
          let daySuccessCount = 0

          for (const slot of mealSlots) {
            const mealContent = dayMeals[slot]
            if (mealContent && mealContent.trim()) {
              try {
                const planData = {
                  user_id: user.id,
                  date: dateString,
                  slot: slot,
                  type: 'recipe' as const,
                  ref_id: '',
                  title: mealContent.trim(),
                  location: undefined,
                  macros: undefined,
                  notes: undefined
                }

                const result = await createPlan.mutateAsync(planData)
                if (result) {
                  daySuccessCount++
                  console.log(`✅ ${dateString} ${slot} 저장 완료`)
                }
              } catch (slotError) {
                console.error(`❌ ${dateString} ${slot} 저장 실패:`, slotError)
              }
            }
          }

          if (daySuccessCount > 0) {
            successCount++
            savedDays.push(dateString)
            console.log(`✅ ${dateString} 식단 저장 완료 (${daySuccessCount}/4)`)
          }

        } catch (dayError) {
          console.error(`❌ ${dateString} 날짜 저장 실패:`, dayError)
        }
      }

      // 저장 결과 처리
      if (successCount > 0) {
        console.log(`🎉 AI 식단표 자동 저장 완료: ${successCount}/${totalDays}일`)
        
        // 캘린더 데이터 새로고침
        queryClient.invalidateQueries({ queryKey: ['plans-range'] })
        
        // 성공 알림
        alert(`✅ AI 식단표가 자동으로 저장되었습니다!\n\n📅 저장된 일수: ${successCount}일\n🗓️ 저장된 날짜: ${savedDays.slice(0, 3).join(', ')}${savedDays.length > 3 ? '...' : ''}`)
        
      } else {
        console.error('❌ 모든 식단 저장 실패')
        alert('❌ 식단 저장에 실패했습니다. 다시 시도해주세요.')
      }

    } catch (error) {
      console.error('❌ AI 식단표 자동 저장 중 오류:', error)
      alert('❌ 식단 저장 중 오류가 발생했습니다. 다시 시도해주세요.')
    }
  }

  // AI 식단표 생성 버튼 클릭 핸들러
  const handleGenerateMealPlan = async () => {
    if (!user?.id) {
      alert('로그인이 필요합니다.')
      return
    }

    setIsGeneratingMealPlan(true)

    try {
      console.log('🤖 AI 식단표 생성 시작...')

      // AI 식단 생성 API 호출 (개인화된 엔드포인트 사용 - 프로필 자동 적용)
      const mealPlanData = await generateMealPlan.mutateAsync({
        user_id: user.id,
        days: selectedDays
      })

      console.log('✅ AI 식단표 생성 완료:', mealPlanData)

      // 백엔드 응답을 프론트엔드 형식으로 변환
      let convertedMealPlan: Record<string, MealData> = {}
      
      try {
        if (mealPlanData.days && Array.isArray(mealPlanData.days)) {
          // 백엔드에서 받은 days 배열을 날짜 키 형식으로 변환
          const startDate = new Date()
          
          mealPlanData.days.forEach((dayMeals: any, index: number) => {
            try {
              const currentDate = new Date(startDate)
              currentDate.setDate(startDate.getDate() + index)
              
              // 날짜 유효성 검사
              if (isNaN(currentDate.getTime())) {
                console.warn(`⚠️ 유효하지 않은 날짜 (인덱스 ${index}):`, currentDate)
                return
              }
              
              const dateString = format(currentDate, 'yyyy-MM-dd')
              
              // 백엔드 응답을 프론트엔드 MealData 형식으로 변환
              convertedMealPlan[dateString] = {
                breakfast: extractMealTitle(dayMeals.breakfast) || '아침 메뉴',
                lunch: extractMealTitle(dayMeals.lunch) || '점심 메뉴',
                dinner: extractMealTitle(dayMeals.dinner) || '저녁 메뉴',
                snack: extractMealTitle(dayMeals.snack) || '간식'
              }
            } catch (dayError) {
              console.error(`❌ ${index}일차 데이터 변환 오류:`, dayError, dayMeals)
            }
          })
          
          console.log(`✅ ${Object.keys(convertedMealPlan).length}일치 식단표 변환 완료`)
        } else {
          // 폴백: 기존 형식 그대로 사용 (날짜 키가 있는 객체)
          if (typeof mealPlanData === 'object' && mealPlanData !== null) {
            convertedMealPlan = mealPlanData as Record<string, MealData>
            console.log('📝 기존 형식 사용 (날짜 키 객체)')
          } else {
            console.warn('⚠️ 예상치 못한 데이터 형식:', mealPlanData)
            throw new Error('식단 데이터 형식이 올바르지 않습니다.')
          }
        }
      } catch (conversionError) {
        console.error('❌ 식단표 변환 중 오류:', conversionError)
        throw new Error('식단표 데이터 변환에 실패했습니다.')
      }

      console.log('🔄 변환된 식단표:', convertedMealPlan)

      // AI 식단표 생성 완료 후 자동으로 캘린더에 저장
      await handleAutoSaveMealPlan(convertedMealPlan)

    } catch (error) {
      console.error('❌ AI 식단표 생성 실패:', error)

      // 사용자에게 오류 메시지 표시
      const errorMessage = error instanceof Error ? error.message : '알 수 없는 오류가 발생했습니다.'
      alert(`AI 식단표 생성에 실패했습니다.\n${errorMessage}\n\n기본 식단으로 대체합니다.`)

      // 폴백: 로컬 랜덤 식단 생성
      console.log('📝 폴백: 로컬 랜덤 식단 생성')
      const newMealData: Record<string, MealData> = {}

      try {
        // 선택된 일수만큼 랜덤 식단 생성
        for (let day = 0; day < selectedDays; day++) {
          const currentDate = new Date()
          if (isNaN(currentDate.getTime())) {
            console.error('❌ 현재 날짜가 유효하지 않습니다.')
            break
          }

          currentDate.setDate(currentDate.getDate() + day)
          const dateString = format(currentDate, 'yyyy-MM-dd')

          // 선택된 일수만큼 식단 생성
          newMealData[dateString] = generateRandomMeal()
        }

        if (Object.keys(newMealData).length > 0) {
          // 폴백 식단도 자동 저장
          await handleAutoSaveMealPlan(newMealData)
        } else {
          console.error('❌ 폴백 식단 생성 실패')
          alert('식단 생성에 완전히 실패했습니다. 다시 시도해주세요.')
        }
      } catch (fallbackError) {
        console.error('❌ 폴백 식단 생성 중 오류:', fallbackError)
        alert('기본 식단 생성도 실패했습니다. 잠시 후 다시 시도해주세요.')
      }

    } finally {
      setIsGeneratingMealPlan(false)
    }
  }

  return {
    selectedDays,
    setSelectedDays,
    isGeneratingMealPlan,
    handleGenerateMealPlan
  }
}
