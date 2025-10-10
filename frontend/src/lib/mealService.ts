import { supabase } from './supabaseClient'
import { MealData } from '@/data/ketoMeals'

export interface MealLogRecord {
  id: string
  user_id: string
  date: string
  meal_type: 'breakfast' | 'lunch' | 'dinner' | 'snack'
  eaten: boolean
  note?: string
  created_at: string
  updated_at: string
}

/**
 * Supabase 식단 데이터 관리 서비스 (meal_log 테이블 사용)
 */
export class MealService {
  /**
   * 특정 날짜의 식단 데이터 조회 (meal_log 테이블)
   */
  static async getMealByDate(date: string, userId: string): Promise<MealData | null> {
    try {
      if (!userId) {
        throw new Error('로그인이 필요합니다.')
      }

      const { data, error } = await supabase
        .from('meal_log')
        .select('*')
        .eq('date', date)
        .eq('user_id', userId)

      if (error) {
        throw error
      }

      if (!data || data.length === 0) {
        return null
      }

      // meal_log 레코드들을 MealData 형식으로 변환
      const mealData: MealData = {
        breakfast: '',
        lunch: '',
        dinner: '',
        snack: '',
        breakfastCompleted: false,
        lunchCompleted: false,
        dinnerCompleted: false,
        snackCompleted: false
      }

      // 🔍 URL 가져오기 시도 (meal_plan_item -> recipe_blob_emb)
      for (const log of data) {
        const mealType = log.meal_type
        const mealContent = log.note || ''
        let recipeUrl: string | undefined = undefined

        // mealplan_id가 있으면 URL 가져오기 시도
        if (log.mealplan_id) {
          try {
            // meal_plan_item에서 recipe_blob_id 찾기
            const { data: planItems } = await supabase
              .from('meal_plan_item')
              .select('recipe_blob_id')
              .eq('mealplan_id', log.mealplan_id)
              .eq('meal_type', mealType)
              .eq('planned_date', date)
              .limit(1)
              .single()

            // recipe_blob_emb에서 URL 찾기
            if (planItems?.recipe_blob_id) {
              const { data: recipe } = await supabase
                .from('recipe_blob_emb')
                .select('url')
                .eq('id', planItems.recipe_blob_id)
                .limit(1)
                .single()
              
              if (recipe?.url) {
                recipeUrl = recipe.url
              }
            }
          } catch (urlError) {
            // URL 조회 실패 시 무시
          }
        }

        // 데이터 할당
        if (mealType === 'breakfast') {
          mealData.breakfast = mealContent
          mealData.breakfastUrl = recipeUrl
          mealData.breakfastCompleted = log.eaten
        } else if (mealType === 'lunch') {
          mealData.lunch = mealContent
          mealData.lunchUrl = recipeUrl
          mealData.lunchCompleted = log.eaten
        } else if (mealType === 'dinner') {
          mealData.dinner = mealContent
          mealData.dinnerUrl = recipeUrl
          mealData.dinnerCompleted = log.eaten
        } else if (mealType === 'snack') {
          mealData.snack = mealContent
          mealData.snackUrl = recipeUrl
          mealData.snackCompleted = log.eaten
        }
      }

      return mealData
    } catch (error) {
      console.error('식단 조회 실패:', error)
      return null
    }
  }

  /**
   * 여러 날짜의 식단 데이터 조회 (meal_log 테이블)
   */
  static async getMealsByDateRange(startDate: string, endDate: string, userId: string): Promise<Record<string, MealData>> {
    try {
      if (!userId) {
        throw new Error('로그인이 필요합니다.')
      }

      const { data, error } = await supabase
        .from('meal_log')
        .select('*')
        .gte('date', startDate)
        .lte('date', endDate)
        .eq('user_id', userId)

      if (error) throw error

      const mealDataByDate: Record<string, MealData> = {}

      data?.forEach((log: MealLogRecord) => {
        const dateKey = log.date

        if (!mealDataByDate[dateKey]) {
          mealDataByDate[dateKey] = {
            breakfast: '',
            lunch: '',
            dinner: '',
            snack: '',
            breakfastCompleted: false,
            lunchCompleted: false,
            dinnerCompleted: false,
            snackCompleted: false
          }
        }

        const mealType = log.meal_type
        if (mealType === 'breakfast') {
          mealDataByDate[dateKey].breakfast = log.note || ''
          mealDataByDate[dateKey].breakfastCompleted = log.eaten
        } else if (mealType === 'lunch') {
          mealDataByDate[dateKey].lunch = log.note || ''
          mealDataByDate[dateKey].lunchCompleted = log.eaten
        } else if (mealType === 'dinner') {
          mealDataByDate[dateKey].dinner = log.note || ''
          mealDataByDate[dateKey].dinnerCompleted = log.eaten
        } else if (mealType === 'snack') {
          mealDataByDate[dateKey].snack = log.note || ''
          mealDataByDate[dateKey].snackCompleted = log.eaten
        }
      })

      return mealDataByDate
    } catch (error) {
      console.error('식단 범위 조회 실패:', error)
      return {}
    }
  }

  /**
   * 식단 데이터 저장 (meal_log 테이블에 개별 레코드로 저장)
   */
  static async saveMeal(date: string, mealData: MealData, userId: string): Promise<boolean> {
    try {
      if (!userId) {
        throw new Error('로그인이 필요합니다.')
      }

      // 기존 해당 날짜 데이터 삭제
      await supabase
        .from('meal_log')
        .delete()
        .eq('date', date)
        .eq('user_id', userId)

      // 새로운 meal_log 레코드들 생성
      const mealLogs: any[] = []

      const mealTypes = [
        { type: 'breakfast', content: mealData.breakfast, completed: mealData.breakfastCompleted },
        { type: 'lunch', content: mealData.lunch, completed: mealData.lunchCompleted },
        { type: 'dinner', content: mealData.dinner, completed: mealData.dinnerCompleted },
        { type: 'snack', content: mealData.snack, completed: mealData.snackCompleted }
      ]

      mealTypes.forEach(meal => {
        if (meal.content && meal.content.trim()) {
          mealLogs.push({
            user_id: userId,
            date: date,
            meal_type: meal.type,
            eaten: meal.completed || false,
            note: meal.content,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
          })
        }
      })

      if (mealLogs.length > 0) {
        const { error } = await supabase
          .from('meal_log')
          .insert(mealLogs)

        if (error) throw error
      }

      return true
    } catch (error) {
      console.error('식단 저장 실패:', error)
      return false
    }
  }

  /**
   * 식단 데이터 삭제
   */
  static async deleteMeal(date: string, userId: string): Promise<boolean> {
    try {
      if (!userId) {
        throw new Error('로그인이 필요합니다.')
      }

      const { error } = await supabase
        .from('meal_log')
        .delete()
        .eq('date', date)
        .eq('user_id', userId)

      if (error) throw error

      return true
    } catch (error) {
      console.error('식단 삭제 실패:', error)
      return false
    }
  }

  /**
   * 특정 식사 완료 상태 업데이트
   */
  static async updateMealCompletion(date: string, mealType: string, completed: boolean, userId: string): Promise<boolean> {
    try {
      if (!userId) {
        throw new Error('로그인이 필요합니다.')
      }

      const { error } = await supabase
        .from('meal_log')
        .update({
          eaten: completed,
          updated_at: new Date().toISOString()
        })
        .eq('date', date)
        .eq('meal_type', mealType)
        .eq('user_id', userId)

      if (error) throw error

      return true
    } catch (error) {
      console.error('식단 완료 상태 업데이트 실패:', error)
      return false
    }
  }
}

/**
 * LLM 응답에서 식단 JSON 파싱
 */
export interface LLMParsedMeal {
  breakfast: string
  lunch: string
  dinner: string
  snack?: string
  date?: string
}

/**
 * LLM 응답 파싱 유틸리티
 */
export class MealParserService {
  /**
   * 백엔드 ChatResponse에서 식단 데이터 추출
   */
  static parseMealFromBackendResponse(chatResponse: any): LLMParsedMeal | null {
    try {
      console.log('🔍 DEBUG: MealParserService.parseMealFromBackendResponse 시작')
      console.log('🔍 DEBUG: chatResponse 구조:', {
        hasResults: !!chatResponse.results,
        resultsLength: chatResponse.results?.length,
        hasMealPlanData: !!chatResponse.meal_plan_data,
        responseLength: chatResponse.response?.length
      })
      
      // 1. results 배열에서 식단 데이터 찾기
      if (chatResponse.results && Array.isArray(chatResponse.results)) {
        console.log('🔍 DEBUG: results 배열 확인, 길이:', chatResponse.results.length)
        for (let i = 0; i < chatResponse.results.length; i++) {
          const result = chatResponse.results[i]
          console.log(`🔍 DEBUG: results[${i}] 구조:`, {
            type: result.type,
            hasDays: !!result.days,
            daysLength: result.days?.length,
            keys: Object.keys(result)
          })
          
          if (result.type === 'meal_plan' || result.days) {
            console.log('🔍 DEBUG: meal_plan 조건 만족!')
            // 7일 식단표 형태
            if (result.days && Array.isArray(result.days) && result.days.length > 0) {
              const firstDay = result.days[0]
              console.log('🔍 DEBUG: firstDay 구조:', {
                keys: Object.keys(firstDay),
                breakfast: firstDay.breakfast,
                lunch: firstDay.lunch,
                dinner: firstDay.dinner,
                snack: firstDay.snack
              })
              
              const parsedMeal = {
                breakfast: firstDay.breakfast?.title || firstDay.breakfast || '',
                lunch: firstDay.lunch?.title || firstDay.lunch || '',
                dinner: firstDay.dinner?.title || firstDay.dinner || '',
                snack: firstDay.snack?.title || firstDay.snack || ''
              }
              console.log('🔍 DEBUG: 파싱된 식단 데이터:', parsedMeal)
              return parsedMeal
            }
          }

          // 단일 식단 객체
          if (result.breakfast || result.lunch || result.dinner) {
            return this.normalizeKeys(result)
          }
        }
      }

      // 2. response 텍스트에서 JSON 추출
      if (chatResponse.response) {
        return this.parseMealFromResponse(chatResponse.response)
      }

      return null
    } catch (error) {
      console.error('백엔드 응답 파싱 실패:', error)
      return null
    }
  }

  /**
   * LLM 응답 텍스트에서 식단 JSON 추출
   */
  static parseMealFromResponse(response: string): LLMParsedMeal | null {
    try {
      // JSON 패턴 찾기 (다양한 형태의 JSON 지원)
      const jsonPatterns = [
        /```json\s*(\{[\s\S]*?\})\s*```/i,
        /```\s*(\{[\s\S]*?\})\s*```/i,
        /(\{[\s\S]*?"breakfast"[\s\S]*?\})/i,
        /(\{[\s\S]*?"점심"[\s\S]*?\})/i,
      ]

      for (const pattern of jsonPatterns) {
        const match = response.match(pattern)
        if (match) {
          const jsonStr = match[1]
          const parsed = JSON.parse(jsonStr)

          // 한국어 키를 영어로 변환
          const normalized = this.normalizeKeys(parsed)

          if (this.isValidMealData(normalized)) {
            return normalized
          }
        }
      }

      // JSON이 없을 경우 텍스트에서 패턴 추출 시도
      return this.extractMealFromText(response)
    } catch (error) {
      console.error('식단 파싱 실패:', error)
      return null
    }
  }

  /**
   * 한국어 키를 영어로 정규화
   */
  private static normalizeKeys(data: any): LLMParsedMeal {
    const keyMap: Record<string, string> = {
      '아침': 'breakfast',
      '점심': 'lunch',
      '저녁': 'dinner',
      '간식': 'snack',
      '날짜': 'date',
      'breakfast': 'breakfast',
      'lunch': 'lunch',
      'dinner': 'dinner',
      'snack': 'snack',
      'date': 'date'
    }

    const normalized: any = {}

    Object.keys(data).forEach(key => {
      const normalizedKey = keyMap[key] || key
      normalized[normalizedKey] = data[key]
    })

    return normalized as LLMParsedMeal
  }

  /**
   * 유효한 식단 데이터인지 확인
   */
  private static isValidMealData(data: any): boolean {
    return data &&
           typeof data === 'object' &&
           (data.breakfast || data.lunch || data.dinner)
  }

  /**
   * 텍스트에서 식단 정보 추출
   */
  private static extractMealFromText(text: string): LLMParsedMeal | null {
    const mealData: any = {}

    // 마크다운 형태의 7일 식단표에서 첫 번째 날 파싱
    const firstDayMatch = text.match(/\*\*1일차:\*\*([\s\S]*?)(?:\*\*2일차:\*\*|$)/)
    if (firstDayMatch) {
      const firstDayText = firstDayMatch[1]

      // 이모지와 함께된 패턴 매칭
      const patterns = {
        breakfast: /🌅\s*아침:\s*([^\n\r-]+)/i,
        lunch: /🌞\s*점심:\s*([^\n\r-]+)/i,
        dinner: /🌙\s*저녁:\s*([^\n\r-]+)/i,
        snack: /🍎\s*간식:\s*([^\n\r-]+)/i
      }

      Object.entries(patterns).forEach(([key, pattern]) => {
        const match = firstDayText.match(pattern)
        if (match) {
          mealData[key] = match[1].trim()
        }
      })
    }

    // 기본 패턴 매칭 (이모지 없는 경우)
    if (!this.isValidMealData(mealData)) {
      const basicPatterns = {
        breakfast: /(?:아침|breakfast)[:\s]*([^\n\r]+)/i,
        lunch: /(?:점심|lunch)[:\s]*([^\n\r]+)/i,
        dinner: /(?:저녁|dinner)[:\s]*([^\n\r]+)/i,
        snack: /(?:간식|snack)[:\s]*([^\n\r]+)/i
      }

      Object.entries(basicPatterns).forEach(([key, pattern]) => {
        const match = text.match(pattern)
        if (match) {
          mealData[key] = match[1].trim()
        }
      })
    }

    return this.isValidMealData(mealData) ? mealData : null
  }
}

/**
 * 식단 데이터 예시 (LLM 응답 형태)
 */
export const MEAL_JSON_EXAMPLE = {
  breakfast: "아보카도 토스트와 스크램블 에그",
  lunch: "그릴 치킨 샐러드 (올리브오일 드레싱)",
  dinner: "연어 스테이크와 브로콜리",
  snack: "아몬드 한 줌과 치즈 큐브"
}