import { useState, useEffect } from 'react'

/**
 * 폼 상태 관리를 위한 커스텀 훅
 * 원본 데이터와 현재 데이터를 비교하여 변경 여부를 감지
 */
export function useFormState<T>(initialValue: T) {
  const [value, setValue] = useState<T>(initialValue)
  const [originalValue, setOriginalValue] = useState<T>(initialValue)

  // 초기값이 변경될 때 상태 업데이트
  useEffect(() => {
    setValue(initialValue)
    setOriginalValue(initialValue)
  }, [initialValue])

  // 변경 여부 계산
  const hasChanged = JSON.stringify(value) !== JSON.stringify(originalValue)

  // 저장 성공 시 호출할 함수 (원본 데이터를 현재 데이터로 업데이트)
  const markAsSaved = () => {
    setOriginalValue(value)
  }

  // 초기값으로 리셋
  const reset = () => {
    setValue(originalValue)
  }

  return {
    value,
    setValue,
    originalValue,
    hasChanged,
    markAsSaved,
    reset
  }
}

/**
 * 여러 필드를 가진 객체 폼 상태 관리 훅
 */
export function useObjectFormState<T extends Record<string, any>>(initialValue: T) {
  const [values, setValues] = useState<T>(initialValue)
  const [originalValues, setOriginalValues] = useState<T>(initialValue)

  // 초기값이 변경될 때 상태 업데이트
  useEffect(() => {
    setValues(initialValue)
    setOriginalValues(initialValue)
  }, [initialValue])

  // 개별 필드 업데이트
  const updateField = <K extends keyof T>(field: K, value: T[K]) => {
    setValues(prev => ({ ...prev, [field]: value }))
  }

  // 변경 여부 계산
  const hasChanged = JSON.stringify(values) !== JSON.stringify(originalValues)

  // 특정 필드의 변경 여부
  const hasFieldChanged = <K extends keyof T>(field: K): boolean => {
    return JSON.stringify(values[field]) !== JSON.stringify(originalValues[field])
  }

  // 저장 성공 시 호출할 함수
  const markAsSaved = () => {
    setOriginalValues(values)
  }

  // 초기값으로 리셋
  const reset = () => {
    setValues(originalValues)
  }

  return {
    values,
    setValues,
    updateField,
    originalValues,
    hasChanged,
    hasFieldChanged,
    markAsSaved,
    reset
  }
}
