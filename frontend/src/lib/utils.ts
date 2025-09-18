import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(date: Date): string {
  return new Intl.DateTimeFormat('ko-KR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    weekday: 'long'
  }).format(date)
}

export function formatMacros(macros: any) {
  if (!macros) return null
  
  return {
    kcal: macros.kcal || 0,
    carb: macros.carb || 0,
    protein: macros.protein || 0,
    fat: macros.fat || 0
  }
}

export function getKetoScoreColor(score: number): string {
  if (score >= 80) return 'keto-score-excellent'
  if (score >= 60) return 'keto-score-good'
  if (score >= 40) return 'keto-score-fair'
  return 'keto-score-poor'
}

export function getKetoScoreText(score: number): string {
  if (score >= 80) return '매우 적합'
  if (score >= 60) return '적합'
  if (score >= 40) return '보통'
  return '부적합'
}

export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength) + '...'
}

export function debounce<T extends (...args: any[]) => any>(
  func: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: NodeJS.Timeout
  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId)
    timeoutId = setTimeout(() => func(...args), delay)
  }
}
