import * as React from "react"

import { cn } from "@/lib/utils"

// 한글(자모/완성형), 문자, 기호 제거 -> 숫자만 남기기
function onlyDigits(v: string) {
  return v
    .replace(/[\u1100-\u11FF\u3130-\u318F\uAC00-\uD7AF]/g, "") // 한글 전부 제거
    .replace(/[^\d]/g, ""); // 숫자 이외 제거
}

// 범위 제한
function clamp(n: number, min?: number, max?: number) {
  if (!Number.isFinite(n)) return NaN;
  if (min != null) n = Math.max(min, n);
  if (max != null) n = Math.min(max, n);
  return n;
}

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  numericOnly?: boolean // 숫자 전용 모드
  min?: number
  max?: number
  useComma?: boolean // 천단위 콤마 사용 여부
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, onBlur, onCompositionEnd, onChange, numericOnly, min, max, useComma, ...props }, ref) => {
    const [isComposing, setIsComposing] = React.useState(false)

    // 숫자 전용 모드일 때 값 정규화
    const normalize = (raw: string, addComma = false) => {
      if (!numericOnly) {
        // 일반 모드: 미완성 한글만 제거
        return raw.replace(/[\u1100-\u11FF\u3130-\u318F]/g, "")
      }
      
      // 숫자 전용 모드
      const digits = onlyDigits(raw)
      if (!digits) return ""
      
      const num = clamp(parseInt(digits, 10), min, max)
      if (Number.isNaN(num)) return ""
      
      // addComma가 true이고 useComma가 true일 때만 콤마 추가
      return (addComma && useComma) ? num.toLocaleString() : num.toString()
    }

    const handleCompositionStart = () => {
      setIsComposing(true)
    }

    const handleCompositionEnd = (e: React.CompositionEvent<HTMLInputElement>) => {
      setIsComposing(false)
      
      const target = e.target as HTMLInputElement
      const normalizedValue = normalize(target.value, false) // 콤마 없이
      
      if (target.value !== normalizedValue) {
        target.value = normalizedValue
        
        // onChange 이벤트 강제 발생
        if (onChange) {
          const syntheticEvent = {
            target: target,
            currentTarget: e.currentTarget,
            type: 'change',
          } as React.ChangeEvent<HTMLInputElement>
          onChange(syntheticEvent)
        }
      }
      
      onCompositionEnd?.(e)
    }

    const handleBlur = (e: React.FocusEvent<HTMLInputElement>) => {
      const target = e.target as HTMLInputElement
      const normalizedValue = normalize(target.value, true) // blur 시에만 콤마 추가
      
      if (target.value !== normalizedValue) {
        target.value = normalizedValue
        
        // onChange 이벤트 강제 발생
        if (onChange) {
          const syntheticEvent = {
            target: target,
            currentTarget: e.currentTarget,
            type: 'change',
          } as React.ChangeEvent<HTMLInputElement>
          onChange(syntheticEvent)
        }
      }
      
      onBlur?.(e)
    }

    const handleFocus = (e: React.FocusEvent<HTMLInputElement>) => {
      // 포커스 시 콤마 제거 (편집하기 쉽게)
      if (numericOnly && useComma) {
        const target = e.target as HTMLInputElement
        const withoutComma = target.value.replace(/,/g, '')
        if (target.value !== withoutComma) {
          target.value = withoutComma
          
          // onChange 이벤트 강제 발생
          if (onChange) {
            const syntheticEvent = {
              target: target,
              currentTarget: e.currentTarget,
              type: 'change',
            } as React.ChangeEvent<HTMLInputElement>
            onChange(syntheticEvent)
          }
        }
      }
    }

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      // 조합 중에는 값을 건드리지 않음 (조합중 보호)
      onChange?.(e)
    }

    // 숫자 전용 모드일 때 추가 props
    const numericProps = numericOnly ? {
      inputMode: "numeric" as const,
      pattern: "\\d*"
    } : {}

    return (
      <input
        type={type}
        className={cn(
          "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
          className
        )}
        ref={ref}
        onChange={handleChange}
        onFocus={handleFocus}
        onBlur={handleBlur}
        onCompositionStart={handleCompositionStart}
        onCompositionEnd={handleCompositionEnd}
        {...numericProps}
        {...props}
      />
    )
  }
)
Input.displayName = "Input"

export { Input }
