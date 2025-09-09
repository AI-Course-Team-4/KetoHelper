import { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  IconButton,
  LinearProgress,
  Divider,
} from '@mui/material'
import {
  ChevronLeft,
  ChevronRight,
  Refresh,
  Save,
  CalendarMonth,
  CheckCircle,
  CheckCircleOutline,
} from '@mui/icons-material'
// import { useAuthStore } from '@store/authStore' // 개발용으로 임시 비활성화
import RecipeCard from '../components/RecipeCard'
import MealSelectionModal from '../components/MealSelectionModal'
import MealDetailModal from '../components/MealDetailModal'
import type { Recipe } from '../types/index'

// TODO: 백엔드 연동 시 사용 - API 서비스 import
// import { mealPlanService } from '../services/mealPlanService'
// import { recipeService } from '../services/recipeService'
// import { userService } from '../services/userService'

// TODO: 백엔드 연동 시 사용 - API 서비스 예제 구조
// interface MealPlanService {
//   getWeeklyMealPlan(weekStart: string, weekEnd: string): Promise<WeeklyMealPlan>
//   updateMeal(date: string, mealType: string, recipeId: string): Promise<void>
//   updateMealCompletion(date: string, mealType: string, completed: boolean): Promise<void>
//   saveWeeklyPlan(weeklyPlan: WeeklyMealPlan): Promise<void>
//   generateRandomWeekPlan(weekStart: string, weekEnd: string): Promise<WeeklyMealPlan>
//   getMealDetails(mealId: string): Promise<Recipe>
// }
//
// interface RecipeService {
//   getFavoriteRecipes(): Promise<Recipe[]>
//   toggleFavorite(recipeId: string): Promise<void>
//   searchRecipes(query: string): Promise<Recipe[]>
// }
//
// interface UserService {
//   getMealPreferences(): Promise<any>
//   updateMealPreferences(preferences: any): Promise<void>
// }

interface WeeklyMealPlan {
  [date: string]: {
    breakfast?: Recipe | null
    lunch?: Recipe | null
    dinner?: Recipe | null
    completed: {
      breakfast: boolean
      lunch: boolean
      dinner: boolean
    }
  }
}

// 날짜 포맷 헬퍼 함수
const formatDateHelper = (date: Date) => {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const CalendarPage = () => {
  // const { user, isAuthenticated } = useAuthStore() // 개발용으로 임시 비활성화

  // 더미 식단 데이터
  const dummyMeals: Recipe[] = [
    {
          id: '1',
          title: '아보카도 토스트',
          description: '키토 친화적인 아침 식사',
      imageUrl: 'https://via.placeholder.com/300x200?text=아보카도+토스트',
          cookingTime: 10,
          difficulty: '쉬움',
          servings: 1,
          ingredients: [],
          instructions: [],
          nutrition: { calories: 320, carbs: 8, protein: 12, fat: 26, fiber: 6 },
          tags: ['키토', '아침'],
          rating: 4.5,
          reviewCount: 45,
          isKetoFriendly: true,
      createdAt: '2025-01-01',
        },
    {
          id: '2',
          title: '치킨 샐러드',
          description: '신선한 채소와 그릴드 치킨',
      imageUrl: 'https://via.placeholder.com/300x200?text=치킨+샐러드',
          cookingTime: 15,
          difficulty: '쉬움',
          servings: 1,
          ingredients: [],
          instructions: [],
          nutrition: { calories: 420, carbs: 12, protein: 35, fat: 25, fiber: 8 },
          tags: ['키토', '점심'],
          rating: 4.7,
          reviewCount: 67,
          isKetoFriendly: true,
      createdAt: '2025-01-01',
        },
    {
          id: '3',
          title: '연어 스테이크',
          description: '오메가3가 풍부한 저녁 식사',
      imageUrl: 'https://via.placeholder.com/300x200?text=연어+스테이크',
          cookingTime: 25,
          difficulty: '중간',
          servings: 1,
          ingredients: [],
          instructions: [],
          nutrition: { calories: 480, carbs: 6, protein: 42, fat: 32, fiber: 2 },
          tags: ['키토', '저녁'],
          rating: 4.9,
          reviewCount: 89,
          isKetoFriendly: true,
      createdAt: '2025-01-01',
    },
    {
          id: '4',
          title: '베이컨 에그',
          description: '고단백 키토 아침',
      imageUrl: 'https://via.placeholder.com/300x200?text=베이컨+에그',
          cookingTime: 8,
          difficulty: '쉬움',
          servings: 1,
          ingredients: [],
          instructions: [],
          nutrition: { calories: 380, carbs: 2, protein: 20, fat: 32, fiber: 0 },
          tags: ['키토', '아침'],
          rating: 4.3,
          reviewCount: 32,
          isKetoFriendly: true,
      createdAt: '2025-01-01',
    },
    {
      id: '5',
          title: '새우 볶음',
          description: '고단백 저녁',
      imageUrl: 'https://via.placeholder.com/300x200?text=새우+볶음',
          cookingTime: 15,
          difficulty: '쉬움',
          servings: 1,
          ingredients: [],
          instructions: [],
          nutrition: { calories: 320, carbs: 8, protein: 35, fat: 18, fiber: 3 },
          tags: ['키토', '저녁'],
          rating: 4.4,
          reviewCount: 29,
          isKetoFriendly: true,
      createdAt: '2025-01-01',
    },
    {
      id: '6',
      title: '그릭 요거트 볼',
      description: '프로틴이 풍부한 아침',
      imageUrl: 'https://via.placeholder.com/300x200?text=그릭+요거트',
      cookingTime: 5,
          difficulty: '쉬움',
          servings: 1,
          ingredients: [],
          instructions: [],
      nutrition: { calories: 200, carbs: 6, protein: 15, fat: 12, fiber: 0 },
          tags: ['키토', '아침'],
      rating: 4.2,
          reviewCount: 41,
          isKetoFriendly: true,
      createdAt: '2025-01-01',
    },
  ]
  
  // 현재 주의 시작 날짜 (월요일)
  const [currentWeekStart, setCurrentWeekStart] = useState(() => {
    const today = new Date()
    const day = today.getDay()
    const diff = today.getDate() - day + (day === 0 ? -6 : 1) // 월요일로 조정
    return new Date(today.setDate(diff))
  })
  
  const [weeklyMealPlan, setWeeklyMealPlan] = useState<WeeklyMealPlan>(() => {
    // 더미 데이터 - 일주일 중 3일만 식단이 있도록 초기화
    const today = new Date()
    const initialPlan: WeeklyMealPlan = {}
    
    // 월요일부터 3일간만 식단 데이터 추가
    for (let i = 0; i < 3; i++) {
      const date = new Date(today)
      const day = date.getDay()
      const diff = date.getDate() - day + (day === 0 ? -6 : 1) + i // 월요일부터
      date.setDate(diff)
      const dateString = formatDateHelper(date)
      
      initialPlan[dateString] = {
        breakfast: dummyMeals[i * 2],
        lunch: dummyMeals[i * 2 + 1],
        dinner: dummyMeals[i * 2 + 2] || dummyMeals[0],
        completed: {
          breakfast: false,
          lunch: false,
          dinner: false
        }
      }
    }
    
    return initialPlan
  })
  const [selectedDate, setSelectedDate] = useState<string | null>(null)
  const [mealSelectionOpen, setMealSelectionOpen] = useState(false)
  const [mealDetailOpen, setMealDetailOpen] = useState(false)
  const [selectedMealType, setSelectedMealType] = useState<'breakfast' | 'lunch' | 'dinner'>('breakfast')
  const [selectedDateForMeal, setSelectedDateForMeal] = useState<string>('')
  const [selectedMealForDetail, setSelectedMealForDetail] = useState<Recipe | null>(null)

  // TODO: 프로덕션에서는 구독 확인 로직 활성화
  // const hasSubscription = user?.subscription?.isActive || false
  // if (!isAuthenticated || !hasSubscription) {
  //   return (
  //     <Box sx={{ textAlign: 'center', py: 8 }}>
  //       <Typography variant="h4" sx={{ mb: 2 }}>
  //         🗓️ 캘린더는 프리미엄 전용 기능입니다
  //       </Typography>
  //       <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
  //         개인 맞춤 식단 캘린더를 사용하려면 프리미엄 구독이 필요합니다.
  //       </Typography>
  //       <Button variant="contained" size="large" href="/subscription">
  //         프리미엄 구독하기
  //       </Button>
  //     </Box>
  //   )
  // }

  // 주간 날짜 배열 생성
  const getWeekDates = (startDate: Date) => {
    const dates = []
    for (let i = 0; i < 7; i++) {
      const date = new Date(startDate)
      date.setDate(startDate.getDate() + i)
      dates.push(date)
    }
    return dates
  }

  const formatDate = (date: Date) => {
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    return `${year}-${month}-${day}`
  }

  const navigateWeek = (direction: 'prev' | 'next') => {
    const newDate = new Date(currentWeekStart)
    newDate.setDate(newDate.getDate() + (direction === 'prev' ? -7 : 7))
    setCurrentWeekStart(newDate)
  }


  const handleMealComplete = (mealType: 'breakfast' | 'lunch' | 'dinner', date: string, completed: boolean) => {
    setWeeklyMealPlan(prev => ({
      ...prev,
      [date]: {
        ...prev[date],
        completed: {
          ...prev[date]?.completed,
          [mealType]: completed
        }
      }
    }))
    // TODO: API 호출로 완료 상태 업데이트
    console.log(`Updating ${mealType} completion for ${date}: ${completed}`)
  }

  const handleMealSelection = (meal: Recipe) => {
    setWeeklyMealPlan(prev => ({
      ...prev,
      [selectedDateForMeal]: {
        ...prev[selectedDateForMeal],
        [selectedMealType]: meal,
        completed: prev[selectedDateForMeal]?.completed || {
          breakfast: false,
          lunch: false,
          dinner: false
        }
      }
    }))
    
    // TODO: 백엔드 연동 시 사용 - 식단 추가/변경 API 호출
    // try {
    //   await mealPlanService.updateMeal(selectedDateForMeal, selectedMealType, meal.id)
    //   console.log('식단이 성공적으로 저장되었습니다.')
    // } catch (error) {
    //   console.error('식단 저장 중 오류가 발생했습니다:', error)
    // }
    
    // 모달 닫기
    setMealSelectionOpen(false)
  }

  const handleMealDetailEditRequest = () => {
    // 상세정보 모달 닫고 선택 모달 열기
    setMealDetailOpen(false)
    setMealSelectionOpen(true)
  }

  const handleMealDetailClose = () => {
    setMealDetailOpen(false)
    setSelectedMealForDetail(null)
  }

  const handleToggleMealComplete = () => {
    if (!selectedDate || !selectedMealType) return
    
    const currentStatus = weeklyMealPlan[selectedDate]?.completed[selectedMealType] || false
    const newStatus = !currentStatus
    
    handleMealComplete(selectedMealType, selectedDate, newStatus)
    
    // TODO: 백엔드 연동 시 사용 - 완료 상태 업데이트 API 호출
    // try {
    //   await mealPlanService.updateMealCompletion(selectedDate, selectedMealType, newStatus)
    //   console.log('완료 상태가 업데이트되었습니다.')
    // } catch (error) {
    //   console.error('완료 상태 업데이트 중 오류가 발생했습니다:', error)
    // }
  }

  const handleRandomize = () => {
    const newWeekPlan: WeeklyMealPlan = {}
    const weekDates = getWeekDates(currentWeekStart)
    
    weekDates.forEach(date => {
      const dateString = formatDate(date)
      const shuffled = [...dummyMeals].sort(() => 0.5 - Math.random())
      
      newWeekPlan[dateString] = {
        breakfast: shuffled.find(meal => meal.tags.includes('아침')) || shuffled[0],
        lunch: shuffled.find(meal => meal.tags.includes('점심')) || shuffled[1],
        dinner: shuffled.find(meal => meal.tags.includes('저녁')) || shuffled[2],
        completed: {
          breakfast: false,
          lunch: false,
          dinner: false
        }
      }
    })
    
    setWeeklyMealPlan(newWeekPlan)
    
    // TODO: 백엔드 연동 시 사용 - 랜덤 식단 생성 API 호출
    // try {
    //   const weekStart = formatDate(currentWeekStart)
    //   const weekEnd = formatDate(weekDates[6])
    //   const randomMealPlan = await mealPlanService.generateRandomWeekPlan(weekStart, weekEnd)
    //   setWeeklyMealPlan(randomMealPlan)
    //   console.log('랜덤 식단이 성공적으로 생성되었습니다.')
    // } catch (error) {
    //   console.error('랜덤 식단 생성 중 오류가 발생했습니다:', error)
    // }
  }

  const handleApply = () => {
    // TODO: 백엔드 연동 시 사용 - 주간 식단 저장 API 호출
    // try {
    //   await mealPlanService.saveWeeklyPlan(weeklyMealPlan)
    //   alert('식단이 성공적으로 적용되었습니다!')
    //   console.log('주간 식단이 저장되었습니다.')
    // } catch (error) {
    //   console.error('식단 저장 중 오류가 발생했습니다:', error)
    //   alert('식단 저장 중 오류가 발생했습니다. 다시 시도해 주세요.')
    // }
    
    // 현재는 목 데이터로 동작
    console.log('Saving weekly meal plan:', weeklyMealPlan)
    alert('식단이 적용되었습니다!')
  }

  const handleDateClick = (dateString: string) => {
    setSelectedDate(dateString)
  }

  // TODO: 백엔드 연동 시 사용 - 주간 식단 데이터 로딩
  const loadWeeklyMealPlan = async (weekStartDate: Date) => {
    // try {
    //   const weekDates = getWeekDates(weekStartDate)
    //   const weekStart = formatDate(weekStartDate)
    //   const weekEnd = formatDate(weekDates[6])
    //   const mealPlan = await mealPlanService.getWeeklyMealPlan(weekStart, weekEnd)
    //   setWeeklyMealPlan(mealPlan)
    //   console.log('주간 식단 데이터가 로드되었습니다.')
    // } catch (error) {
    //   console.error('주간 식단 데이터 로딩 중 오류가 발생했습니다:', error)
    //   // 에러 시 빈 식단으로 초기화
    //   setWeeklyMealPlan({})
    // }
    
    console.log('Loading weekly meal plan for week starting:', formatDate(weekStartDate))
  }

  // TODO: 백엔드 연동 시 사용 - 개별 식단 상세정보 로딩
  // const loadMealDetails = async (mealId: string) => {
  //   try {
  //     const mealDetails = await mealPlanService.getMealDetails(mealId)
  //     return mealDetails
  //   } catch (error) {
  //     console.error('식단 상세정보 로딩 중 오류가 발생했습니다:', error)
  //     return null
  //   }
  // }

  // 주간이 변경될 때마다 데이터 로딩
  useEffect(() => {
    loadWeeklyMealPlan(currentWeekStart)
  }, [currentWeekStart])

  // TODO: 백엔드 연동 시 사용 - 컴포넌트 마운트 시 초기 데이터 로딩
  // useEffect(() => {
  //   const initializeData = async () => {
  //     try {
  //       // 사용자 식단 설정 로드
  //       const userPreferences = await userService.getMealPreferences()
  //       
  //       // 즐겨찾기 식단 로드
  //       const favoriteRecipes = await recipeService.getFavoriteRecipes()
  //       
  //       // 현재 주간 식단 로드
  //       await loadWeeklyMealPlan(currentWeekStart)
  //       
  //       console.log('초기 데이터 로딩이 완료되었습니다.')
  //     } catch (error) {
  //       console.error('초기 데이터 로딩 중 오류가 발생했습니다:', error)
  //     }
  //   }
  //   
  //   initializeData()
  // }, [])

  const weekDates = getWeekDates(currentWeekStart)
  const weekStart = currentWeekStart.toLocaleDateString('ko-KR', { month: 'long', day: 'numeric' })
  const weekEnd = weekDates[6].toLocaleDateString('ko-KR', { month: 'long', day: 'numeric' })

  // 주간 완료율 계산
  const totalMeals = weekDates.length * 3
  const completedMeals = weekDates.reduce((total, date) => {
    const dateString = formatDate(date)
    const dayPlan = weeklyMealPlan[dateString]
    if (dayPlan) {
      return total + Object.values(dayPlan.completed).filter(Boolean).length
    }
    return total
  }, 0)
  const weeklyProgress = totalMeals > 0 ? (completedMeals / totalMeals) * 100 : 0

  return (
    <Box>
      {/* 헤더 */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Typography variant="h3" sx={{ fontWeight: 700 }}>
          🗓️ 주간 식단 캘린더
        </Typography>
        
        {/* 진행률 표시 */}
        <Box sx={{ minWidth: 200 }}>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            이번 주 실천률: {Math.round(weeklyProgress)}%
          </Typography>
          <LinearProgress variant="determinate" value={weeklyProgress} sx={{ height: 8, borderRadius: 4 }} />
        </Box>
      </Box>

      {/* 랜덤 버튼 */}
      <Box sx={{ display: 'flex', justifyContent: 'center', mb: 3 }}>
        <Button
          variant="outlined"
          startIcon={<Refresh />}
          onClick={handleRandomize}
          sx={{ mr: 2 }}
        >
          랜덤 식단 생성
        </Button>
      </Box>

      {/* 주간 네비게이션 */}
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', mb: 4 }}>
        <IconButton onClick={() => navigateWeek('prev')}>
          <ChevronLeft />
        </IconButton>
        <Typography variant="h5" sx={{ mx: 4, fontWeight: 600 }}>
          {weekStart} - {weekEnd}
        </Typography>
        <IconButton onClick={() => navigateWeek('next')}>
          <ChevronRight />
        </IconButton>
      </Box>

      {/* 주간 캘린더 그리드 */}
      <Grid container spacing={2} sx={{ mb: 4 }}>
        {weekDates.map((date, index) => {
          const dateString = formatDate(date)
          const dayPlan = weeklyMealPlan[dateString]
          const isToday = dateString === formatDate(new Date())
          const isSelected = selectedDate === dateString
          const dayNames = ['월', '화', '수', '목', '금', '토', '일']

          return (
            <Grid item xs={12/7} key={dateString}>
              <Card
                sx={{
                  cursor: 'pointer',
                  border: isToday ? 2 : isSelected ? 2 : 1,
                  borderColor: isToday ? 'primary.main' : isSelected ? 'secondary.main' : 'divider',
                  backgroundColor: isSelected ? 'action.selected' : 'background.paper',
                  '&:hover': {
                    backgroundColor: 'action.hover',
                  },
                  minHeight: 120
                }}
                onClick={() => handleDateClick(dateString)}
              >
                <CardContent sx={{ p: 2 }}>
                  <Box sx={{ textAlign: 'center', mb: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                      {dayNames[index]}
                    </Typography>
                    <Typography variant="h6" sx={{ fontWeight: isToday ? 700 : 400 }}>
                      {date.getDate()}
                  </Typography>
                  </Box>
                  
                  {/* 간단한 식단 정보 표시 */}
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                    {(['breakfast', 'lunch', 'dinner'] as const).map((mealType) => {
                      const meal = dayPlan?.[mealType]
                          const mealTypeMap = { breakfast: '아침', lunch: '점심', dinner: '저녁' } as const
                      const isCompleted = dayPlan?.completed[mealType] || false
                      
                          return (
                        <Box key={mealType} sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 0.5 }}>
                          <Typography 
                            variant="caption" 
                            sx={{ 
                              overflow: 'hidden', 
                              textOverflow: 'ellipsis', 
                              whiteSpace: 'nowrap',
                              color: meal ? 'text.primary' : 'text.disabled',
                              flex: 1,
                              mr: 0.5
                            }}
                          >
                            {mealTypeMap[mealType]}: {meal ? meal.title : '미설정'}
                              </Typography>
                          {meal && (
                            <IconButton 
                              size="small"
                              sx={{ 
                                ml: 0.5, 
                                p: 0.25,
                                '&:hover': {
                                  backgroundColor: 'action.hover'
                                }
                              }}
                              onClick={(e) => {
                                e.stopPropagation()
                                handleMealComplete(mealType, dateString, !isCompleted)
                              }}
                            >
                              {isCompleted ? (
                                <CheckCircle sx={{ fontSize: 16, color: 'success.main' }} />
                              ) : (
                                <CheckCircleOutline sx={{ fontSize: 16, color: 'text.disabled' }} />
                              )}
                            </IconButton>
                              )}
                            </Box>
                          )
                        })}
                      </Box>
                </CardContent>
              </Card>
            </Grid>
          )
        })}
      </Grid>

      {/* 선택된 날짜의 상세 정보 */}
      {selectedDate && (
        <Box sx={{ mb: 4 }}>
          <Divider sx={{ mb: 3 }} />
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                    <CalendarMonth sx={{ mr: 1 }} />
            <Typography variant="h5" sx={{ fontWeight: 600 }}>
              {new Date(selectedDate).getMonth() + 1}월 {new Date(selectedDate).getDate()}일 ({['일', '월', '화', '수', '목', '금', '토'][new Date(selectedDate).getDay()]}) 식단
                    </Typography>
                  </Box>
          
                <Grid container spacing={3}>
            {(['breakfast', 'lunch', 'dinner'] as const).map((mealType) => {
              const dayPlan = weeklyMealPlan[selectedDate]
              const meal = dayPlan?.[mealType]

                    return (
                      <Grid item xs={12} md={4} key={mealType}>
                  <RecipeCard
                    recipe={meal}
                    variant={meal ? 'default' : 'add'}
                    mealType={mealType}
                    isFavorite={false} // TODO: 즐겨찾기 상태 관리
                    isCompleted={dayPlan?.completed[mealType] || false}
                    onRecipeClick={(recipe) => {
                      setSelectedMealForDetail(recipe)
                      setMealDetailOpen(true)
                    }}
                    onCompletionToggle={(completed) => {
                      handleMealComplete(mealType, selectedDate, completed)
                    }}
                    onAddClick={() => {
                      setSelectedMealType(mealType)
                      setSelectedDateForMeal(selectedDate)
                      setMealSelectionOpen(true)
                    }}
                    actionLabel="상세 보기"
                  />
                      </Grid>
                    )
                  })}
                </Grid>
                
          {/* 영양소 정보 */}
          {weeklyMealPlan[selectedDate] && (
            <Box sx={{ mt: 3, p: 3, backgroundColor: 'grey.50', borderRadius: 2 }}>
              <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
                    📊 하루 총 영양소
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={3}>
                      <Typography variant="body2" color="text.secondary">칼로리</Typography>
                  <Typography variant="h6" color="primary.main">
                    {[weeklyMealPlan[selectedDate].breakfast, weeklyMealPlan[selectedDate].lunch, weeklyMealPlan[selectedDate].dinner]
                      .filter(Boolean)
                      .reduce((total, meal) => total + (meal?.nutrition.calories || 0), 0)}
                  </Typography>
                </Grid>
                <Grid item xs={3}>
                  <Typography variant="body2" color="text.secondary">탄수화물</Typography>
                  <Typography variant="h6" color="warning.main">
                    {[weeklyMealPlan[selectedDate].breakfast, weeklyMealPlan[selectedDate].lunch, weeklyMealPlan[selectedDate].dinner]
                      .filter(Boolean)
                      .reduce((total, meal) => total + (meal?.nutrition.carbs || 0), 0)}g
                  </Typography>
                </Grid>
                <Grid item xs={3}>
                  <Typography variant="body2" color="text.secondary">단백질</Typography>
                  <Typography variant="h6" color="success.main">
                    {[weeklyMealPlan[selectedDate].breakfast, weeklyMealPlan[selectedDate].lunch, weeklyMealPlan[selectedDate].dinner]
                      .filter(Boolean)
                      .reduce((total, meal) => total + (meal?.nutrition.protein || 0), 0)}g
                  </Typography>
                </Grid>
                <Grid item xs={3}>
                  <Typography variant="body2" color="text.secondary">지방</Typography>
                  <Typography variant="h6" color="info.main">
                    {[weeklyMealPlan[selectedDate].breakfast, weeklyMealPlan[selectedDate].lunch, weeklyMealPlan[selectedDate].dinner]
                      .filter(Boolean)
                      .reduce((total, meal) => total + (meal?.nutrition.fat || 0), 0)}g
                  </Typography>
                </Grid>
              </Grid>
            </Box>
          )}
        </Box>
      )}

      {/* 적용 버튼 */}
      <Box sx={{ display: 'flex', justifyContent: 'center', mb: 4 }}>
        <Button
          variant="contained"
          size="large"
          startIcon={<Save />}
          onClick={handleApply}
        >
          식단 적용
              </Button>
      </Box>

      {/* 식사 선택 모달 */}
      <MealSelectionModal
        open={mealSelectionOpen}
        onClose={() => setMealSelectionOpen(false)}
        mealType={selectedMealType}
        onMealSelect={handleMealSelection}
      />

      {/* 식사 상세정보 모달 */}
      <MealDetailModal
        open={mealDetailOpen}
        onClose={handleMealDetailClose}
        meal={selectedMealForDetail}
        mealType={selectedMealType}
        onEditRequest={handleMealDetailEditRequest}
        isCompleted={selectedDate ? weeklyMealPlan[selectedDate]?.completed[selectedMealType] || false : false}
        onToggleComplete={handleToggleMealComplete}
      />
    </Box>
  )
}

export default CalendarPage