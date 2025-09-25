import { supabase } from './supabaseClient'
import { MealData } from '@/data/ketoMeals'

export interface MealRecord {
  id: string
  user_id: string
  date: string
  breakfast?: string
  lunch?: string
  dinner?: string
  snack?: string
  breakfast_completed?: boolean
  lunch_completed?: boolean
  dinner_completed?: boolean
  snack_completed?: boolean
  created_at: string
}

/**
 * Supabase 식단 데이터 관리 서비스
 */
export class MealService {
  /**
   * 특정 날짜의 식단 데이터 조회
   */
  static async getMealByDate(date: string, userId: string): Promise<MealData | null> {
    try {
      if (!userId) {
        throw new Error('로그인이 필요합니다.')
      }
      
      const { data, error } = await supabase
        .from('meals')
        .select('*')
        .eq('date', date)
        .eq('user_id', userId)
        .single()

      if (error) {
        if (error.code === 'PGRST116') {
          // 데이터가 없는 경우
          return null
        }
        throw error
      }

      return {
        breakfast: data.breakfast || '',
        lunch: data.lunch || '',
        dinner: data.dinner || '',
        snack: data.snack || '',
        breakfastCompleted: data.breakfast_completed || false,
        lunchCompleted: data.lunch_completed || false,
        dinnerCompleted: data.dinner_completed || false,
        snackCompleted: data.snack_completed || false
      }
    } catch (error) {
      console.error('식단 조회 실패:', error)
      return null
    }
  }

  /**
   * 여러 날짜의 식단 데이터 조회
   */
  static async getMealsByDateRange(startDate: string, endDate: string, userId: string): Promise<Record<string, MealData>> {
    try {
      if (!userId) {
        throw new Error('로그인이 필요합니다.')
      }
      
      const { data, error } = await supabase
        .from('meals')
        .select('*')
        .gte('date', startDate)
        .lte('date', endDate)
        .eq('user_id', userId)

      if (error) throw error

      const mealData: Record<string, MealData> = {}
      
      data?.forEach((meal) => {
        mealData[meal.date] = {
          breakfast: meal.breakfast || '',
          lunch: meal.lunch || '',
          dinner: meal.dinner || '',
          snack: meal.snack || '',
          breakfastCompleted: meal.breakfast_completed || false,
          lunchCompleted: meal.lunch_completed || false,
          dinnerCompleted: meal.dinner_completed || false,
          snackCompleted: meal.snack_completed || false
        }
      })

      return mealData
    } catch (error) {
      console.error('식단 범위 조회 실패:', error)
      return {}
    }
  }

  /**
   * 식단 데이터 저장 (신규/업데이트)
   */
  static async saveMeal(date: string, mealData: MealData, userId: string): Promise<boolean> {
    try {
      if (!userId) {
        throw new Error('로그인이 필요합니다.')
      }
      
      // 기존 데이터 확인
      const existingMeal = await this.getMealByDate(date, userId)
      
      const mealRecord = {
        user_id: userId,
        date,
        breakfast: mealData.breakfast || null,
        lunch: mealData.lunch || null,
        dinner: mealData.dinner || null,
        snack: mealData.snack || null,
        breakfast_completed: mealData.breakfastCompleted || false,
        lunch_completed: mealData.lunchCompleted || false,
        dinner_completed: mealData.dinnerCompleted || false,
        snack_completed: mealData.snackCompleted || false
      }

      let result
      if (existingMeal) {
        // 업데이트
        result = await supabase
          .from('meals')
          .update(mealRecord)
          .eq('date', date)
          .eq('user_id', userId)
      } else {
        // 신규 생성
        result = await supabase
          .from('meals')
          .insert([mealRecord])
      }

      if (result.error) throw result.error
      
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
        .from('meals')
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
      // 1. results 배열에서 식단 데이터 찾기
      if (chatResponse.results && Array.isArray(chatResponse.results)) {
        for (const result of chatResponse.results) {
          if (result.type === 'meal_plan' || result.days) {
            // 7일 식단표 형태
            if (result.days && Array.isArray(result.days) && result.days.length > 0) {
              const firstDay = result.days[0]
              return {
                breakfast: firstDay.breakfast?.title || firstDay.breakfast || '',
                lunch: firstDay.lunch?.title || firstDay.lunch || '',
                dinner: firstDay.dinner?.title || firstDay.dinner || '',
                snack: firstDay.snack?.title || firstDay.snack || ''
              }
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
