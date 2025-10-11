import { format } from 'date-fns'
import { MealData } from '@/data/ketoMeals'
import { useCreatePlan, useUpdatePlan, useDeletePlan } from '@/hooks/useApi'
import { useAuthStore } from '@/store/authStore'
import { useQueryClient } from '@tanstack/react-query'

export function useMealOperations() {
  const { user } = useAuthStore()
  const createPlan = useCreatePlan()
  const updatePlan = useUpdatePlan()
  const deletePlan = useDeletePlan()
  const queryClient = useQueryClient()

  // 날짜 문자열로 변환하는 헬퍼 함수
  const formatDateKey = (date: Date) => {
    try {
      if (!date || isNaN(date.getTime())) {
        console.warn('⚠️ 유효하지 않은 날짜:', date)
        return format(new Date(), 'yyyy-MM-dd')
      }
      return format(date, 'yyyy-MM-dd')
    } catch (error) {
      console.error('❌ 날짜 포맷 변환 오류:', error, date)
      return format(new Date(), 'yyyy-MM-dd')
    }
  }

  // 실제 API를 사용한 식단 저장/수정
  const handleSaveMeal = async (date: Date, newMealData: MealData, planIds: Record<string, Record<string, string>>) => {
    if (!user?.id) {
      alert('로그인이 필요합니다.')
      return
    }

    console.log('💾 API 저장/수정 시작:', { date, newMealData })

    try {
      const dateString = format(date, 'yyyy-MM-dd')
      const dateKey = formatDateKey(date)
      const mealSlots = ['breakfast', 'lunch', 'dinner', 'snack'] as const
      const existingPlanIds = planIds[dateKey] || {}

      for (const slot of mealSlots) {
        const mealTitle = newMealData[slot]
        const existingPlanId = existingPlanIds[slot]

        if (mealTitle && mealTitle.trim()) {
          // 식단이 있는 경우 - 새로 생성 또는 수정
          try {
            const planData = {
              user_id: user.id,
              date: dateString,
              slot: slot,
              type: 'recipe' as const,
              ref_id: '',
              title: mealTitle.trim(),
              location: undefined,
              macros: undefined,
              notes: undefined
            }

            if (existingPlanId) {
              // 기존 plan 업데이트
              await updatePlan.mutateAsync({
                planId: existingPlanId,
                updates: { notes: mealTitle.trim() },
                userId: user.id
              })
              console.log(`✅ ${slot} 수정 완료:`, mealTitle)
            } else {
              // 새 plan 생성
              await createPlan.mutateAsync(planData)
              console.log(`✅ ${slot} 생성 완료:`, mealTitle)
            }
          } catch (error) {
            console.error(`❌ ${slot} 저장/수정 실패:`, error)
          }
        } else if (existingPlanId) {
          // 식단이 비어있지만 기존 plan이 있는 경우 - 삭제
          try {
            await deletePlan.mutateAsync({
              planId: existingPlanId,
              userId: user.id
            })
            console.log(`✅ ${slot} 삭제 완료`)
          } catch (error) {
            console.error(`❌ ${slot} 삭제 실패:`, error)
          }
        }
      }

      // 캘린더 데이터 새로고침
      queryClient.invalidateQueries({ queryKey: ['plans-range'] })
      
      // 캘린더 저장 완료 이벤트 발생
      window.dispatchEvent(new CustomEvent('calendar-saved'))

      console.log('✅ 식단 저장/수정/삭제 완료!')
    } catch (error) {
      console.error('❌ 식단 처리 실패:', error)
      alert('식단 처리에 실패했습니다. 다시 시도해주세요.')
    }
  }

  // 개별 식단 삭제 함수
  const handleDeleteMeal = async (date: Date, mealType: 'breakfast' | 'lunch' | 'dinner' | 'snack', planIds: Record<string, Record<string, string>>) => {
    if (!user?.id) {
      alert('로그인이 필요합니다.')
      return
    }

    const dateKey = formatDateKey(date)
    const planId = planIds[dateKey]?.[mealType]

    if (!planId) {
      alert('삭제할 식단이 없습니다.')
      return
    }

    if (!confirm('이 식단을 삭제하시겠습니까?')) {
      return
    }

    try {
      await deletePlan.mutateAsync({
        planId: planId,
        userId: user.id
      })

      // 캘린더 데이터 새로고침
      queryClient.invalidateQueries({ queryKey: ['plans-range'] })
      
      // 캘린더 저장 완료 이벤트 발생
      window.dispatchEvent(new CustomEvent('calendar-saved'))

      console.log(`✅ ${mealType} 삭제 완료`)
    } catch (error) {
      console.error(`❌ ${mealType} 삭제 실패:`, error)
      alert('식단 삭제에 실패했습니다. 다시 시도해주세요.')
    }
  }

  // 하루 전체 식단 삭제 함수
  const handleDeleteAllMeals = async (date: Date, planIds: Record<string, Record<string, string>>) => {
    if (!user?.id) {
      alert('로그인이 필요합니다.')
      return
    }

    const dateKey = formatDateKey(date)
    const dayPlanIds = planIds[dateKey]

    if (!dayPlanIds || Object.keys(dayPlanIds).length === 0) {
      alert('삭제할 식단이 없습니다.')
      return
    }

    try {
      console.log('🗑️ 하루 전체 식단 삭제 시작...')

      // 모든 식단 삭제를 병렬로 처리
      const deletePromises = Object.entries(dayPlanIds).map(([, planId]) =>
        deletePlan.mutateAsync({
          planId: planId,
          userId: user.id
        })
      )

      await Promise.all(deletePromises)

      // 캘린더 데이터 새로고침
      queryClient.invalidateQueries({ queryKey: ['plans-range'] })
      
      // 캘린더 저장 완료 이벤트 발생
      window.dispatchEvent(new CustomEvent('calendar-saved'))

      console.log(`✅ ${format(date, 'M월 d일')} 전체 식단 삭제 완료`)
      alert(`${format(date, 'M월 d일')} 식단이 모두 삭제되었습니다.`)

    } catch (error) {
      console.error('❌ 전체 식단 삭제 실패:', error)
      alert('전체 식단 삭제에 실패했습니다. 다시 시도해주세요.')
    }
  }

  return {
    handleSaveMeal,
    handleDeleteMeal,
    handleDeleteAllMeals
  }
}
