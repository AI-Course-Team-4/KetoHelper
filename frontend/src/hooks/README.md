# Custom Hooks

## useFormState

폼 상태 관리를 위한 커스텀 훅입니다. 원본 데이터와 현재 데이터를 비교하여 변경 여부를 자동으로 감지합니다.

### 기본 사용법

```typescript
import { useFormState } from '@/hooks/useFormState'

function MyComponent() {
  const {
    value,
    setValue,
    hasChanged,
    markAsSaved,
    reset
  } = useFormState('초기값')

  const handleSave = async () => {
    // 저장 로직
    await saveData(value)
    
    // 저장 성공 시 원본 데이터 업데이트
    markAsSaved()
  }

  return (
    <div>
      <input 
        value={value} 
        onChange={(e) => setValue(e.target.value)} 
      />
      <Button 
        onClick={handleSave}
        disabled={!hasChanged}
        variant="contained"
      >
        저장
      </Button>
      <button onClick={reset}>
        초기화
      </button>
    </div>
  )
}
```

### 객체 폼 사용법

```typescript
import { useObjectFormState } from '@/hooks/useFormState'

interface UserProfile {
  name: string
  email: string
  age: number
}

function ProfileForm() {
  const {
    values,
    updateField,
    hasChanged,
    hasFieldChanged,
    markAsSaved,
    reset
  } = useObjectFormState<UserProfile>({
    name: '',
    email: '',
    age: 0
  })

  const handleSave = async () => {
    await saveProfile(values)
    markAsSaved()
  }

  return (
    <div>
      <input 
        value={values.name}
        onChange={(e) => updateField('name', e.target.value)}
      />
      
      <input 
        value={values.email}
        onChange={(e) => updateField('email', e.target.value)}
      />
      
      <input 
        type="number"
        value={values.age}
        onChange={(e) => updateField('age', Number(e.target.value))}
      />
      
      <button 
        onClick={handleSave}
        disabled={!hasChanged}
      >
        저장 ({hasFieldChanged('name') ? '이름 변경됨' : ''})
      </button>
    </div>
  )
}
```

### API

#### useFormState(initialValue)

**Parameters:**
- `initialValue`: 초기값

**Returns:**
- `value`: 현재 값
- `setValue`: 값 업데이트 함수
- `originalValue`: 원본 값
- `hasChanged`: 변경 여부 (boolean)
- `markAsSaved`: 저장 완료 표시 함수
- `reset`: 초기값으로 리셋 함수

#### useObjectFormState(initialValue)

**Parameters:**
- `initialValue`: 초기 객체

**Returns:**
- `values`: 현재 객체 값들
- `setValues`: 전체 객체 업데이트 함수
- `updateField`: 개별 필드 업데이트 함수
- `originalValues`: 원본 객체 값들
- `hasChanged`: 전체 변경 여부 (boolean)
- `hasFieldChanged`: 특정 필드 변경 여부 확인 함수
- `markAsSaved`: 저장 완료 표시 함수
- `reset`: 초기값으로 리셋 함수

### 사용 예시

1. **프로필 페이지**: 사용자 정보 수정 시 변경된 필드만 저장 버튼 활성화
2. **설정 페이지**: 여러 설정 항목 중 변경된 것만 저장
3. **글 작성/수정**: 내용이 변경되었을 때만 저장 버튼 활성화
4. **필터/검색**: 검색 조건 변경 시에만 검색 버튼 활성화
