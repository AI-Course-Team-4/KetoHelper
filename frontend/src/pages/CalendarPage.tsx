import { useState } from 'react'
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  Chip,
  IconButton,
  Select,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Checkbox,
  FormControlLabel,
  LinearProgress,
} from '@mui/material'
import {
  ChevronLeft,
  ChevronRight,
  CheckCircle,
  CheckCircleOutline,
  Restaurant,
  AccessTime,
  CalendarMonth,
} from '@mui/icons-material'
import { useAuthStore } from '@store/authStore'
import type { MealPlan, Recipe } from '../types/index'

const CalendarPage = () => {
  const { user, isAuthenticated } = useAuthStore()
  const [currentDate, setCurrentDate] = useState(new Date(2025, 8, 1)) // 2025년 9월로 설정
  const [selectedDate, setSelectedDate] = useState<string | null>(null)
  const [mealDetailOpen, setMealDetailOpen] = useState(false)
  const [selectedMeal, setSelectedMeal] = useState<Recipe | null>(null)
  const [monthPickerOpen, setMonthPickerOpen] = useState(false)
  const [tempYear, setTempYear] = useState<number>(new Date().getFullYear())

  // 구독 확인
  const hasSubscription = user?.subscription?.isActive || false

  if (!isAuthenticated || !hasSubscription) {
    return (
      <Box sx={{ textAlign: 'center', py: 8 }}>
        <Typography variant="h4" sx={{ mb: 2 }}>
          🗓️ 캘린더는 프리미엄 전용 기능입니다
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
          개인 맞춤 식단 캘린더를 사용하려면 프리미엄 구독이 필요합니다.
        </Typography>
        <Button variant="contained" size="large" href="/subscription">
          프리미엄 구독하기
        </Button>
      </Box>
    )
  }

  // 임시 식단 데이터 (실제로는 API에서 가져옴)
  const mockMealPlans: MealPlan[] = [
    {
      id: '1',
      date: '2025-09-20',
      meals: {
        breakfast: {
          id: '1',
          title: '아보카도 토스트',
          description: '키토 친화적인 아침 식사',
          imageUrl: 'https://via.placeholder.com/150x100',
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
          createdAt: '2025-09-20',
        },
        lunch: {
          id: '2',
          title: '치킨 샐러드',
          description: '신선한 채소와 그릴드 치킨',
          imageUrl: 'https://via.placeholder.com/150x100',
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
          createdAt: '2025-09-20',
        },
        dinner: {
          id: '3',
          title: '연어 스테이크',
          description: '오메가3가 풍부한 저녁 식사',
          imageUrl: 'https://via.placeholder.com/150x100',
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
          createdAt: '2025-09-20',
        },
      },
      completed: {
        breakfast: true,
        lunch: false,
        dinner: false,
      },
      totalNutrition: { calories: 1220, carbs: 26, protein: 89, fat: 83, fiber: 16 },
    },
    {
      id: '2',
      date: '2025-09-23',
      meals: {
        breakfast: {
          id: '4',
          title: '베이컨 에그',
          description: '고단백 키토 아침',
          imageUrl: 'https://via.placeholder.com/150x100',
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
          createdAt: '2025-09-23',
        },
        lunch: {
          id: '5',
          title: '연어 샐러드',
          description: '오메가3 풍부한 점심',
          imageUrl: 'https://via.placeholder.com/150x100',
          cookingTime: 12,
          difficulty: '쉬움',
          servings: 1,
          ingredients: [],
          instructions: [],
          nutrition: { calories: 350, carbs: 8, protein: 28, fat: 22, fiber: 4 },
          tags: ['키토', '점심'],
          rating: 4.6,
          reviewCount: 28,
          isKetoFriendly: true,
          createdAt: '2025-09-23',
        },
        dinner: {
          id: '6',
          title: '스테이크',
          description: '고단백 저녁 식사',
          imageUrl: 'https://via.placeholder.com/150x100',
          cookingTime: 20,
          difficulty: '중간',
          servings: 1,
          ingredients: [],
          instructions: [],
          nutrition: { calories: 520, carbs: 4, protein: 45, fat: 35, fiber: 1 },
          tags: ['키토', '저녁'],
          rating: 4.8,
          reviewCount: 56,
          isKetoFriendly: true,
          createdAt: '2025-09-23',
        },
      },
      completed: {
        breakfast: true,
        lunch: true,
        dinner: false,
      },
      totalNutrition: { calories: 1250, carbs: 14, protein: 93, fat: 89, fiber: 5 },
    },
    {
      id: '3',
      date: '2025-09-22',
      meals: {
        breakfast: {
          id: '7',
          title: '그릭 요거트',
          description: '프로틴이 풍부한 아침',
          imageUrl: 'https://via.placeholder.com/150x100',
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
          createdAt: '2025-09-22',
        },
        lunch: {
          id: '8',
          title: '치킨 스테이크',
          description: '단백질 풍부한 점심',
          imageUrl: 'https://via.placeholder.com/150x100',
          cookingTime: 18,
          difficulty: '중간',
          servings: 1,
          ingredients: [],
          instructions: [],
          nutrition: { calories: 450, carbs: 5, protein: 40, fat: 30, fiber: 2 },
          tags: ['키토', '점심'],
          rating: 4.5,
          reviewCount: 38,
          isKetoFriendly: true,
          createdAt: '2025-09-22',
        },
        dinner: {
          id: '9',
          title: '새우 볶음',
          description: '고단백 저녁',
          imageUrl: 'https://via.placeholder.com/150x100',
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
          createdAt: '2025-09-22',
        },
      },
      completed: {
        breakfast: false,
        lunch: false,
        dinner: true,
      },
      totalNutrition: { calories: 970, carbs: 19, protein: 90, fat: 60, fiber: 5 },
    },
    {
      id: '4',
      date: '2025-09-23',
      meals: {
        breakfast: {
          id: '10',
          title: '계란 스크램블',
          description: '버터와 함께하는 부드러운 아침',
          imageUrl: 'https://via.placeholder.com/150x100',
          cookingTime: 8,
          difficulty: '쉬움',
          servings: 1,
          ingredients: [],
          instructions: [],
          nutrition: { calories: 280, carbs: 3, protein: 18, fat: 22, fiber: 0 },
          tags: ['키토', '아침'],
          rating: 4.4,
          reviewCount: 52,
          isKetoFriendly: true,
          createdAt: '2025-09-23',
        },
        lunch: {
          id: '11',
          title: '연어 구이',
          description: '레몬과 허브로 맛을 낸 점심',
          imageUrl: 'https://via.placeholder.com/150x100',
          cookingTime: 20,
          difficulty: '중간',
          servings: 1,
          ingredients: [],
          instructions: [],
          nutrition: { calories: 420, carbs: 4, protein: 38, fat: 28, fiber: 1 },
          tags: ['키토', '점심'],
          rating: 4.7,
          reviewCount: 41,
          isKetoFriendly: true,
          createdAt: '2025-09-23',
        },
        dinner: {
          id: '12',
          title: '치킨 윙',
          description: '바삭한 키토 친화적 저녁',
          imageUrl: 'https://via.placeholder.com/150x100',
          cookingTime: 30,
          difficulty: '어려움',
          servings: 1,
          ingredients: [],
          instructions: [],
          nutrition: { calories: 380, carbs: 2, protein: 32, fat: 26, fiber: 0 },
          tags: ['키토', '저녁'],
          rating: 4.6,
          reviewCount: 38,
          isKetoFriendly: true,
          createdAt: '2025-09-23',
        },
      },
      completed: {
        breakfast: true,
        lunch: true,
        dinner: true,
      },
      totalNutrition: { calories: 1080, carbs: 9, protein: 88, fat: 76, fiber: 1 },
    },
  ]

  const getMealPlanForDate = (date: string) => {
    const mealPlan = mockMealPlans.find(plan => plan.date === date)
    console.log('Looking for date:', date, 'Found meal plan:', mealPlan)
    return mealPlan
  }

  const getDaysInMonth = (date: Date) => {
    const year = date.getFullYear()
    const month = date.getMonth()
    const firstDay = new Date(year, month, 1)
    const lastDay = new Date(year, month + 1, 0)
    const daysInMonth = lastDay.getDate()
    const startingDayOfWeek = firstDay.getDay()

    const days = []
    
    // 이전 달의 빈 날들
    for (let i = 0; i < startingDayOfWeek; i++) {
      days.push(null)
    }
    
    // 현재 달의 날들
    for (let day = 1; day <= daysInMonth; day++) {
      days.push(new Date(year, month, day))
    }
    
    return days
  }

  const formatDate = (date: Date) => {
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    return `${year}-${month}-${day}`
  }

  const navigateMonth = (direction: 'prev' | 'next') => {
    const newDate = new Date(currentDate)
    if (direction === 'prev') {
      newDate.setMonth(newDate.getMonth() - 1)
    } else {
      newDate.setMonth(newDate.getMonth() + 1)
    }
    setCurrentDate(newDate)
  }

  const handleSelectMonth = (monthIndex: number) => {
    setCurrentDate(new Date(tempYear, monthIndex, 1))
    setMonthPickerOpen(false)
  }

  const handleMealClick = (meal: Recipe) => {
    setSelectedMeal(meal)
    setMealDetailOpen(true)
  }

  const handleMealComplete = (mealType: 'breakfast' | 'lunch' | 'dinner', date: string) => {
    // TODO: API 호출로 완료 상태 업데이트
    console.log(`Completing ${mealType} for ${date}`)
  }

  const days = getDaysInMonth(currentDate)
  const monthName = currentDate.toLocaleDateString('ko-KR', { year: 'numeric', month: 'long' })

  return (
    <Box>
      {/* 헤더 */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Typography variant="h3" sx={{ fontWeight: 700 }}>
          🗓️ 식단 캘린더
        </Typography>
        
        {/* 진행률 표시 */}
        <Box sx={{ minWidth: 200 }}>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            이번 주 실천률: 75%
          </Typography>
          <LinearProgress variant="determinate" value={75} sx={{ height: 8, borderRadius: 4 }} />
        </Box>
      </Box>

      {/* 월 네비게이션 */}
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', mb: 4 }}>
        <IconButton onClick={() => navigateMonth('prev')}>
          <ChevronLeft />
        </IconButton>
        <Typography
          variant="h5"
          sx={{ mx: 4, fontWeight: 600, cursor: 'pointer', '&:hover': { textDecoration: 'underline' } }}
          onClick={() => {
            setTempYear(currentDate.getFullYear())
            setMonthPickerOpen(true)
          }}
        >
          {monthName}
        </Typography>
        <IconButton onClick={() => navigateMonth('next')}>
          <ChevronRight />
        </IconButton>
      </Box>

      {/* 요일 헤더 */}
      <Grid container spacing={1} sx={{ mb: 2 }}>
        {['일', '월', '화', '수', '목', '금', '토'].map((day) => (
          <Grid item xs={12/7} key={day}>
            <Box sx={{ textAlign: 'center', py: 1, fontWeight: 600, color: 'text.secondary' }}>
              {day}
            </Box>
          </Grid>
        ))}
      </Grid>

      {/* 캘린더 그리드 */}
      <Grid container spacing={1}>
        {days.map((day, index) => {
          if (!day) {
            return <Grid item xs={12/7} key={index}><Box sx={{ height: 120 }} /></Grid>
          }

          const dateString = formatDate(day)
          const mealPlan = getMealPlanForDate(dateString)
          const isToday = dateString === formatDate(new Date())
          const completedMeals = mealPlan ? Object.values(mealPlan.completed).filter(Boolean).length : 0
          const totalMeals = 3

          return (
            <Grid item xs={12/7} key={dateString}>
              <Card
                sx={{
                  height: 160,
                  cursor: 'pointer',
                  border: isToday ? 2 : 1,
                  borderColor: isToday ? 'primary.main' : 'divider',
                  backgroundColor: selectedDate === dateString ? 'action.selected' : 'background.paper',
                  '&:hover': {
                    backgroundColor: 'action.hover',
                  },
                }}
                onClick={() => setSelectedDate(dateString)}
              >
                <CardContent sx={{ p: 1, height: '100%', display: 'flex', flexDirection: 'column' }}>
                  <Typography variant="body2" sx={{ fontWeight: isToday ? 700 : 400, mb: 1 }}>
                    {day.getDate()}
                  </Typography>
                  
                  {mealPlan && (
                    <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5, mb: 1 }}>
                        {(['breakfast', 'lunch', 'dinner'] as const).map((mt) => {
                          const meal = mealPlan.meals[mt]
                          if (!meal) return null
                          const mealTypeMap = { breakfast: '아침', lunch: '점심', dinner: '저녁' } as const
                          const isCompleted = mealPlan.completed[mt]
                          return (
                            <Box key={mt} sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                              <Typography variant="caption" sx={{ mr: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                <strong>{mealTypeMap[mt]}:</strong> {meal.title}
                              </Typography>
                              {isCompleted ? (
                                <CheckCircle color="success" sx={{ fontSize: 16 }} />
                              ) : (
                                <CheckCircleOutline sx={{ fontSize: 16, color: 'text.disabled' }} />
                              )}
                            </Box>
                          )
                        })}
                      </Box>
                      <Box>
                        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                          실행 현황: {completedMeals}/{totalMeals}
                        </Typography>
                        <LinearProgress
                          variant="determinate"
                          value={(completedMeals / totalMeals) * 100}
                          sx={{ height: 6, borderRadius: 1 }}
                        />
                      </Box>
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Grid>
          )
        })}
      </Grid>



      {/* 식단 상세 모달 다이얼로그 */}
      <Dialog
        open={!!selectedDate}
        onClose={() => setSelectedDate(null)}
        maxWidth="lg"
        fullWidth
      >
        {selectedDate && (() => {
          const mealPlan = getMealPlanForDate(selectedDate)
          if (!mealPlan) {
            return (
              <>
                <DialogTitle>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <CalendarMonth sx={{ mr: 1 }} />
                    {selectedDate} 식단
                  </Box>
                </DialogTitle>
                <DialogContent>
                  <Box sx={{ textAlign: 'center', py: 4 }}>
                    <Typography variant="h6" color="text.secondary" sx={{ mb: 2 }}>
                      📅
                    </Typography>
                    <Typography color="text.secondary">
                      이 날짜에는 식단이 등록되어 있지 않습니다.
                    </Typography>
                  </Box>
                </DialogContent>
                <DialogActions>
                  <Button onClick={() => setSelectedDate(null)}>닫기</Button>
                </DialogActions>
              </>
            )
          }

          return (
            <>
              <DialogTitle>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <CalendarMonth sx={{ mr: 1 }} />
                    {selectedDate} 식단
                  </Box>
                  <Chip
                    label={`${Object.values(mealPlan.completed).filter(Boolean).length}/3 완료`}
                    color={Object.values(mealPlan.completed).filter(Boolean).length === 3 ? 'success' : 'default'}
                    size="small"
                  />
                </Box>
              </DialogTitle>
              <DialogContent>
                <Grid container spacing={3}>
                  {Object.entries(mealPlan.meals).map(([mealType, meal]) => {
                    if (!meal) return null
                    
                    const mealTypeMap = {
                      breakfast: '아침',
                      lunch: '점심',
                      dinner: '저녁'
                    } as const
                    
                    const mealTypeKorean = mealTypeMap[mealType as keyof typeof mealTypeMap]
                    const isCompleted = mealPlan.completed[mealType as keyof typeof mealPlan.completed]

                    return (
                      <Grid item xs={12} md={4} key={mealType}>
                        <Card sx={{ height: '100%', border: isCompleted ? 2 : 1, borderColor: isCompleted ? 'success.main' : 'divider' }}>
                          <Box
                            component="img"
                            src={meal.imageUrl}
                            alt={meal.title}
                            sx={{
                              width: '100%',
                              height: 150,
                              objectFit: 'cover',
                              cursor: 'pointer',
                            }}
                            onClick={() => handleMealClick(meal)}
                          />
                          <CardContent>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                                {mealTypeKorean}
                              </Typography>
                              <FormControlLabel
                                control={
                                  <Checkbox
                                    checked={isCompleted}
                                    onChange={() => handleMealComplete(mealType as any, selectedDate)}
                                    icon={<CheckCircleOutline />}
                                    checkedIcon={<CheckCircle />}
                                  />
                                }
                                label=""
                              />
                            </Box>
                            
                            <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>
                              {meal.title}
                            </Typography>
                            
                            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                              {meal.description}
                            </Typography>
                            
                            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                              <AccessTime sx={{ fontSize: 16, mr: 0.5, color: 'text.secondary' }} />
                              <Typography variant="body2" color="text.secondary">
                                {meal.cookingTime}분
                              </Typography>
                            </Box>
                            
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                              <Typography variant="caption">칼로리: {meal.nutrition.calories}</Typography>
                              <Typography variant="caption">탄수화물: {meal.nutrition.carbs}g</Typography>
                            </Box>
                            
                            <Button
                              fullWidth
                              variant="outlined"
                              size="small"
                              onClick={() => handleMealClick(meal)}
                            >
                              레시피 보기
                            </Button>
                          </CardContent>
                        </Card>
                      </Grid>
                    )
                  })}
                </Grid>
                
                {/* 총 영양소 정보 */}
                <Box sx={{ mt: 3, p: 2, backgroundColor: 'grey.50', borderRadius: 1 }}>
                  <Typography variant="h6" sx={{ mb: 1, fontWeight: 600 }}>
                    📊 하루 총 영양소
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={3}>
                      <Typography variant="body2" color="text.secondary">칼로리</Typography>
                      <Typography variant="h6" color="primary.main">{mealPlan.totalNutrition.calories}</Typography>
                    </Grid>
                    <Grid item xs={3}>
                      <Typography variant="body2" color="text.secondary">탄수화물</Typography>
                      <Typography variant="h6" color="warning.main">{mealPlan.totalNutrition.carbs}g</Typography>
                    </Grid>
                    <Grid item xs={3}>
                      <Typography variant="body2" color="text.secondary">단백질</Typography>
                      <Typography variant="h6" color="success.main">{mealPlan.totalNutrition.protein}g</Typography>
                    </Grid>
                    <Grid item xs={3}>
                      <Typography variant="body2" color="text.secondary">지방</Typography>
                      <Typography variant="h6" color="info.main">{mealPlan.totalNutrition.fat}g</Typography>
                    </Grid>
                  </Grid>
                </Box>
              </DialogContent>
              <DialogActions>
                <Button onClick={() => setSelectedDate(null)}>닫기</Button>
              </DialogActions>
            </>
          )
        })()}
      </Dialog>

      {/* 월/년도 빠른 이동 다이얼로그 */}
      <Dialog open={monthPickerOpen} onClose={() => setMonthPickerOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>날짜 이동</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <Typography sx={{ mr: 2 }}>년도</Typography>
            <Select
              size="small"
              value={tempYear}
              onChange={(e) => setTempYear(Number(e.target.value))}
            >
              {Array.from({ length: 21 }, (_, i) => currentDate.getFullYear() - 10 + i).map((year) => (
                <MenuItem key={year} value={year}>{year}년</MenuItem>
              ))}
            </Select>
          </Box>
          <Grid container spacing={1}>
            {Array.from({ length: 12 }, (_, idx) => idx).map((idx) => (
              <Grid item xs={3} key={idx}>
                <Button
                  fullWidth
                  variant={currentDate.getMonth() === idx && currentDate.getFullYear() === tempYear ? 'contained' : 'outlined'}
                  onClick={() => handleSelectMonth(idx)}
                >
                  {idx + 1}월
                </Button>
              </Grid>
            ))}
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setMonthPickerOpen(false)}>닫기</Button>
        </DialogActions>
      </Dialog>

      {/* 식사 상세 다이얼로그 */}
      <Dialog
        open={mealDetailOpen}
        onClose={() => setMealDetailOpen(false)}
        maxWidth="md"
        fullWidth
      >
        {selectedMeal && (
          <>
            <DialogTitle>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Restaurant sx={{ mr: 1 }} />
                {selectedMeal.title}
              </Box>
            </DialogTitle>
            <DialogContent>
              <Box
                component="img"
                src={selectedMeal.imageUrl}
                alt={selectedMeal.title}
                sx={{
                  width: '100%',
                  height: 200,
                  objectFit: 'cover',
                  borderRadius: 1,
                  mb: 2,
                }}
              />
              
              <Typography variant="body1" sx={{ mb: 2 }}>
                {selectedMeal.description}
              </Typography>
              
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="body2">
                    <strong>조리 시간:</strong> {selectedMeal.cookingTime}분
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2">
                    <strong>난이도:</strong> {selectedMeal.difficulty}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2">
                    <strong>칼로리:</strong> {selectedMeal.nutrition.calories}kcal
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2">
                    <strong>탄수화물:</strong> {selectedMeal.nutrition.carbs}g
                  </Typography>
                </Grid>
              </Grid>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setMealDetailOpen(false)}>
                닫기
              </Button>
              <Button variant="contained">
                요리 시작하기
              </Button>
            </DialogActions>
          </>
        )}
      </Dialog>
    </Box>
  )
}

export default CalendarPage
