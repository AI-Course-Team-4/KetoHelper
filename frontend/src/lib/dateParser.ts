import { format, addDays, isValid } from 'date-fns'
import { ko } from 'date-fns/locale'

export interface ParsedDateInfo {
  date: Date
  description: string
  isRelative: boolean
  confidence: number // 0-1, 파싱 신뢰도
  method: 'rule-based' | 'llm-assisted' | 'fallback'
}

/**
 * 자연어 날짜 표현을 파싱하여 Date 객체로 변환
 * 예: "오늘", "내일", "다음주 월요일", "12월 25일" 등
 */
export class DateParser {
  private today: Date

  constructor() {
    this.today = new Date()
    // 오늘 날짜를 자정으로 설정
    this.today.setHours(0, 0, 0, 0)
  }

  /**
   * 하이브리드 자연어 날짜 파싱 (규칙 기반 + LLM 보조)
   */
  parseNaturalDate(input: string): ParsedDateInfo | null {
    const normalized = input.trim().toLowerCase()

    // 1단계: 규칙 기반 파싱 (높은 신뢰도)
    const ruleBasedResult = this.parseWithRules(normalized)
    if (ruleBasedResult) {
      return ruleBasedResult
    }

    // 2단계: 복잡한 경우 LLM 보조 (향후 구현)
    // const llmAssistedResult = await this.parseWithLLM(normalized)
    // if (llmAssistedResult) {
    //   return llmAssistedResult
    // }

    // 3단계: 폴백 (기본값)
    return this.getFallbackDate(normalized)
  }

  /**
   * 규칙 기반 날짜 파싱
   */
  private parseWithRules(normalized: string): ParsedDateInfo | null {
    // 오늘 관련
    if (this.containsWords(normalized, ['오늘', '오늘날', '지금', '현재'])) {
      return {
        date: new Date(this.today),
        description: '오늘',
        isRelative: true,
        confidence: 1.0,
        method: 'rule-based'
      }
    }

    // 내일 관련
    if (this.containsWords(normalized, ['내일', '다음날', '명일'])) {
      return {
        date: addDays(this.today, 1),
        description: '내일',
        isRelative: true,
        confidence: 1.0,
        method: 'rule-based'
      }
    }

    // 모레
    if (this.containsWords(normalized, ['모레', '글피'])) {
      return {
        date: addDays(this.today, 2),
        description: '모레',
        isRelative: true,
        confidence: 1.0,
        method: 'rule-based'
      }
    }

    // 다음주 관련
    const nextWeekMatch = this.parseNextWeek(normalized)
    if (nextWeekMatch) {
      return { ...nextWeekMatch, confidence: 0.9, method: 'rule-based' as const }
    }

    // 이번주 관련
    const thisWeekMatch = this.parseThisWeek(normalized)
    if (thisWeekMatch) {
      return { ...thisWeekMatch, confidence: 0.9, method: 'rule-based' as const }
    }

    // 특정 날짜 (예: "12월 25일", "25일")
    const specificDateMatch = this.parseSpecificDate(normalized)
    if (specificDateMatch) {
      return { ...specificDateMatch, confidence: 0.8, method: 'rule-based' as const }
    }

    // N일 후
    const daysLaterMatch = this.parseDaysLater(normalized)
    if (daysLaterMatch) {
      return { ...daysLaterMatch, confidence: 0.8, method: 'rule-based' as const }
    }

    return null
  }

  /**
   * 폴백 날짜 처리 (기본값 또는 추론)
   */
  private getFallbackDate(normalized: string): ParsedDateInfo | null {
    // 식단 관련 키워드가 있으면 오늘 날짜로 기본 설정
    if (normalized.includes('식단') || normalized.includes('저장') || normalized.includes('추가')) {
      return {
        date: new Date(this.today),
        description: '오늘 (추론)',
        isRelative: true,
        confidence: 0.3,
        method: 'fallback'
      }
    }

    return null
  }

  private containsWords(text: string, words: string[]): boolean {
    return words.some(word => text.includes(word))
  }

  private parseNextWeek(text: string): Omit<ParsedDateInfo, 'confidence' | 'method'> | null {
    if (!text.includes('다음주') && !text.includes('담주')) {
      return null
    }

    // 요일 매핑
    const dayMap: Record<string, number> = {
      '월요일': 1, '월': 1,
      '화요일': 2, '화': 2,
      '수요일': 3, '수': 3,
      '목요일': 4, '목': 4,
      '금요일': 5, '금': 5,
      '토요일': 6, '토': 6,
      '일요일': 0, '일': 0
    }

    // 다음주의 시작 (월요일) 구하기
    const today = new Date(this.today)
    const currentDay = today.getDay()
    const daysToNextMonday = currentDay === 0 ? 1 : 8 - currentDay
    const nextMonday = addDays(today, daysToNextMonday)

    // 특정 요일이 언급되었는지 확인
    for (const [dayName, dayNumber] of Object.entries(dayMap)) {
      if (text.includes(dayName)) {
        const targetDate = addDays(nextMonday, dayNumber - 1)
        return {
          date: targetDate,
          description: `다음주 ${this.getDayName(dayNumber)}`,
          isRelative: true
        }
      }
    }

    // 요일이 명시되지 않았으면 다음주 월요일
    return {
      date: nextMonday,
      description: '다음주 월요일',
      isRelative: true
    }
  }

  private parseThisWeek(text: string): Omit<ParsedDateInfo, 'confidence' | 'method'> | null {
    if (!text.includes('이번주')) {
      return null
    }

    const dayMap: Record<string, number> = {
      '월요일': 1, '월': 1,
      '화요일': 2, '화': 2,
      '수요일': 3, '수': 3,
      '목요일': 4, '목': 4,
      '금요일': 5, '금': 5,
      '토요일': 6, '토': 6,
      '일요일': 0, '일': 0
    }

    // 이번주의 시작 (월요일) 구하기
    const today = new Date(this.today)
    const currentDay = today.getDay()
    const daysToThisMonday = currentDay === 0 ? -6 : 1 - currentDay
    const thisMonday = addDays(today, daysToThisMonday)

    // 특정 요일이 언급되었는지 확인
    for (const [dayName, dayNumber] of Object.entries(dayMap)) {
      if (text.includes(dayName)) {
        const targetDate = addDays(thisMonday, dayNumber - 1)
        return {
          date: targetDate,
          description: `이번주 ${this.getDayName(dayNumber)}`,
          isRelative: true
        }
      }
    }

    return null
  }

  private parseSpecificDate(text: string): Omit<ParsedDateInfo, 'confidence' | 'method'> | null {
    const currentYear = this.today.getFullYear()

    // "12월 25일" 형태
    const monthDayMatch = text.match(/(\d{1,2})월\s*(\d{1,2})일/)
    if (monthDayMatch) {
      const month = parseInt(monthDayMatch[1])
      const day = parseInt(monthDayMatch[2])
      const date = new Date(currentYear, month - 1, day)

      if (isValid(date)) {
        // 과거 날짜라면 내년으로 설정
        if (date < this.today) {
          date.setFullYear(currentYear + 1)
        }

        return {
          date,
          description: `${month}월 ${day}일`,
          isRelative: false
        }
      }
    }

    // "25일" 형태 (이번 달)
    const dayOnlyMatch = text.match(/(\d{1,2})일/)
    if (dayOnlyMatch) {
      const day = parseInt(dayOnlyMatch[1])
      const currentMonth = this.today.getMonth()
      const date = new Date(currentYear, currentMonth, day)

      if (isValid(date)) {
        // 과거 날짜라면 다음 달로 설정
        if (date < this.today) {
          date.setMonth(currentMonth + 1)
        }

        return {
          date,
          description: `${day}일`,
          isRelative: false
        }
      }
    }

    return null
  }

  private parseDaysLater(text: string): Omit<ParsedDateInfo, 'confidence' | 'method'> | null {
    // "3일 후", "5일뒤" 등
    const daysLaterMatch = text.match(/(\d+)일\s*[후뒤]/)
    if (daysLaterMatch) {
      const days = parseInt(daysLaterMatch[1])
      const targetDate = addDays(this.today, days)

      return {
        date: targetDate,
        description: `${days}일 후`,
        isRelative: true
      }
    }

    return null
  }

  private getDayName(dayNumber: number): string {
    const days = ['일요일', '월요일', '화요일', '수요일', '목요일', '금요일', '토요일']
    return days[dayNumber] || '월요일'
  }

  /**
   * 채팅 메시지에서 날짜 관련 표현을 찾아 파싱
   */
  extractDateFromMessage(message: string): ParsedDateInfo | null {
    // 식단 저장과 관련된 키워드와 함께 날짜 표현을 찾음
    const saveKeywords = ['저장', '추가', '계획', '등록', '넣어']
    const hasSaveKeyword = saveKeywords.some(keyword => message.includes(keyword))

    if (!hasSaveKeyword) {
      return null
    }

    // 메시지에서 날짜 표현 추출
    const dateExpressions = [
      '오늘', '내일', '모레', '글피',
      '다음주', '담주', '이번주',
      /\d{1,2}월\s*\d{1,2}일/,
      /\d{1,2}일(?![일월화수목금토])/,
      /\d+일\s*[후뒤]/
    ]

    for (const expression of dateExpressions) {
      if (typeof expression === 'string' && message.includes(expression)) {
        return this.parseNaturalDate(expression)
      } else if (expression instanceof RegExp) {
        const match = message.match(expression)
        if (match) {
          return this.parseNaturalDate(match[0])
        }
      }
    }

    return null
  }

  /**
   * 파싱된 날짜를 ISO 형식으로 변환
   */
  toISOString(parsedDate: ParsedDateInfo): string {
    return format(parsedDate.date, 'yyyy-MM-dd')
  }

  /**
   * 파싱된 날짜를 사용자 친화적 형식으로 변환
   */
  toDisplayString(parsedDate: ParsedDateInfo): string {
    if (parsedDate.isRelative) {
      return parsedDate.description
    }

    return format(parsedDate.date, 'M월 d일 (eee)', { locale: ko })
  }
}

// 싱글톤 인스턴스 생성
export const dateParser = new DateParser()

// 유틸리티 함수들
export function parseDate(input: string): ParsedDateInfo | null {
  return dateParser.parseNaturalDate(input)
}

export function extractDateFromMessage(message: string): ParsedDateInfo | null {
  return dateParser.extractDateFromMessage(message)
}

export function formatDateForDisplay(parsedDate: ParsedDateInfo): string {
  return dateParser.toDisplayString(parsedDate)
}

export function formatDateForAPI(parsedDate: ParsedDateInfo): string {
  return dateParser.toISOString(parsedDate)
}