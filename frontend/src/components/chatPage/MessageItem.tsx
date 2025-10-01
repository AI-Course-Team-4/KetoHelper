import { AccessTime, CalendarToday, Save, Person } from '@mui/icons-material'
import { CircularProgress } from '@mui/material'
import { Button } from '@/components/ui/button'
import { ChatMessage, LLMParsedMeal } from '@/store/chatStore'
import { format } from 'date-fns'
import { PlaceCard } from '@/components/PlaceCard'
import KakaoMap from '@/pages/KakaoMap'

interface MessageItemProps {
  msg: ChatMessage
  index: number
  totalMessages: number // 전체 메시지 수
  shouldShowTimestamp: (index: number) => boolean
  shouldShowDateSeparator: (index: number) => boolean
  formatMessageTime: (timestamp: Date) => string
  formatDetailedTime: (timestamp: Date) => string
  formatDateSeparator: (timestamp: Date) => string
  user: any
  profile: any
  isSavingMeal: string | null
  userLocation: { lat: number; lng: number } | null
  selectedPlaceIndexByMsg: Record<string, number | null>
  onSaveMealToCalendar: (messageId: string, mealData: LLMParsedMeal, targetDate?: string) => void
  onPlaceMarkerClick: (messageId: string, index: number) => void
}

export function MessageItem({
  msg,
  index,
  shouldShowTimestamp,
  shouldShowDateSeparator,
  formatMessageTime,
  formatDetailedTime,
  formatDateSeparator,
  user,
  profile,
  isSavingMeal,
  userLocation,
  selectedPlaceIndexByMsg,
  onSaveMealToCalendar,
  onPlaceMarkerClick
}: MessageItemProps) {
  // 타이핑 애니메이션 없이 모든 메시지 즉시 표시
  const displayedText = msg.content
  const isTyping = false

  return (
    <div
      key={msg.id}
      data-msg-id={`msg-${msg.id}`}
      data-msg-role={msg.role}
      className="animate-in slide-in-from-bottom-2 fade-in duration-300"
    >
      {/* 날짜 구분선 */}
      {shouldShowDateSeparator(index) && (
        <div className="flex items-center justify-center my-6">
          <div className="flex items-center gap-3 px-4 py-2 bg-muted/30 rounded-full border border-border/50">
            <AccessTime sx={{ fontSize: 12, color: 'text.secondary' }} />
            <span className="text-xs font-medium text-muted-foreground">
              {formatDateSeparator(msg.timestamp)}
            </span>
          </div>
        </div>
      )}

      <div className={`flex items-start gap-3 lg:gap-4 ${msg.role === 'user' ? 'flex-row-reverse justify-end' : 'justify-start'}`}>
        {/* 아바타 */}
        <div className={`flex-shrink-0 w-10 h-10 lg:w-12 lg:h-12 rounded-full flex items-center justify-center shadow-lg ring-2 overflow-hidden ${msg.role === 'user'
            ? 'bg-gradient-to-r from-blue-500 to-indigo-600 text-white ring-blue-200'
            : 'bg-gradient-to-r from-green-500 to-emerald-500 text-white ring-green-200'
          }`}>
          {msg.role === 'user' ? (
            // 사용자 프로필 이미지 또는 기본 아이콘
            (() => {
              const profileImageUrl = profile?.profile_image_url || user?.profileImage;
              const userName = profile?.nickname || user?.name || '사용자';
              
              
              if (user && profileImageUrl) {
                return (
                  <div className="relative w-full h-full">
                    <img 
                      src={profileImageUrl} 
                      alt={userName} 
                      className="w-full h-full object-cover rounded-full"
                      onError={(e) => {
                        // 이미지 로드 실패 시 fallback div 표시
                        const target = e.currentTarget;
                        target.style.display = 'none';
                        const fallback = target.nextElementSibling as HTMLElement;
                        if (fallback) {
                          fallback.style.display = 'flex';
                        }
                      }}
                    />
                    <div 
                      className="absolute inset-0 flex items-center justify-center bg-gradient-to-r from-blue-500 to-indigo-600 rounded-full"
                      style={{ display: 'none' }}
                    >
                      <Person sx={{ fontSize: { xs: 20, lg: 24 } }} />
                    </div>
                  </div>
                );
              } else if (user) {
                // 로그인했지만 프로필 이미지가 없는 경우 - 이니셜 표시
                const initial = userName.charAt(0).toUpperCase();
                return (
                  <div className="flex items-center justify-center w-full h-full text-white font-bold text-sm lg:text-base">
                    {initial}
                  </div>
                );
              } else {
                // 게스트 사용자
                return <Person sx={{ fontSize: { xs: 20, lg: 24 } }} />;
              }
            })()
          ) : (
            <span className="text-lg lg:text-xl">🥑</span>
          )}
        </div>

        {/* 메시지 내용 */}
        <div className={`flex-1 max-w-3xl ${msg.role === 'user' ? 'text-right' : ''}`}>
          {/* 사용자 프로필 정보 표시 */}
          {msg.role === 'user' && (
            <div className="mb-2 text-right">
              <span className="text-xs lg:text-sm text-gray-600 bg-gray-50 px-3 py-1 rounded-full">
                {user ? 
                  (profile?.nickname || user.name || user.email || '사용자') : 
                  '게스트 사용자'
                }
                {profile && user && (
                  <span className="ml-2 text-green-600">
                    키토 목표: {profile.goals_kcal || 1500}kcal
                    {profile.goals_carbs_g && (
                      <span className="ml-1">/ 탄수화물: {profile.goals_carbs_g}g</span>
                    )}
                  </span>
                )}
                {!user && (
                  <span className="ml-2 text-amber-600">
                    로그인하면 개인화된 추천을 받을 수 있어요
                  </span>
                )}
              </span>
            </div>
          )}
          <div className={`inline-block p-4 lg:p-5 rounded-2xl shadow-lg transition-all duration-300 ease-out ${msg.role === 'user'
              ? 'bg-gradient-to-r from-blue-500 to-indigo-600 text-white max-w-2xl'
              : 'bg-white border-2 border-gray-100 max-w-3xl'
            }`}>
            <p className="text-sm lg:text-base whitespace-pre-wrap leading-relaxed">
              {msg.role === 'assistant' ? displayedText : msg.content}
              {msg.role === 'assistant' && isTyping && (
                <span className="inline-block w-2 h-4 bg-green-500 ml-1 animate-pulse" />
              )}
            </p>
          </div>

          {/* 타임스탬프 */}
          {shouldShowTimestamp(index) && (
            <div className={`mt-1 ${msg.role === 'user' ? 'text-right' : 'text-left'}`}>
              <span
                className="text-xs text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
                title={formatDetailedTime(msg.timestamp)}
              >
                {formatMessageTime(msg.timestamp)}
              </span>
            </div>
          )}

          {/* 식단 저장 버튼 */}
          {msg.role === 'assistant' && msg.mealData && (
            <div className="mt-4 lg:mt-5 p-4 lg:p-5 bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-green-200 rounded-2xl shadow-lg">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-base font-bold text-green-800 flex items-center gap-2">
                  <CalendarToday sx={{ fontSize: 20 }} />
                  추천받은 식단
                </h4>
                <div className="flex flex-wrap gap-2">
                  <Button
                    size="sm"
                    onClick={() => onSaveMealToCalendar(msg.id, msg.mealData!)}
                    disabled={isSavingMeal === msg.id || isSavingMeal === 'auto-save'}
                    className="bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all duration-300"
                  >
                    {isSavingMeal === msg.id ? (
                      <>
                        <CircularProgress size={16} sx={{ mr: 1 }} />
                        저장 중...
                      </>
                    ) : (
                      <>
                        <Save sx={{ fontSize: 16, mr: 1 }} />
                        오늘에 저장
                      </>
                    )}
                  </Button>
                  
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      const tomorrow = format(new Date(Date.now() + 86400000), 'yyyy-MM-dd')
                      onSaveMealToCalendar(msg.id, msg.mealData!, tomorrow)
                    }}
                    disabled={isSavingMeal === msg.id || isSavingMeal === 'auto-save'}
                    className="border-2 border-green-500 text-green-700 hover:bg-green-50 font-semibold rounded-xl transition-all duration-300"
                  >
                    <CalendarToday sx={{ fontSize: 16, mr: 1 }} />
                    내일에 저장
                  </Button>

                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      const dayAfterTomorrow = format(new Date(Date.now() + 172800000), 'yyyy-MM-dd')
                      onSaveMealToCalendar(msg.id, msg.mealData!, dayAfterTomorrow)
                    }}
                    disabled={isSavingMeal === msg.id || isSavingMeal === 'auto-save'}
                    className="border-2 border-green-500 text-green-700 hover:bg-green-50 font-semibold rounded-xl transition-all duration-300"
                  >
                    <CalendarToday sx={{ fontSize: 16, mr: 1 }} />
                    모레에 저장
                  </Button>
                  
                  {isSavingMeal === 'auto-save' && (
                    <div className="flex items-center gap-1 px-3 py-1 bg-blue-100 text-blue-700 rounded-lg text-sm">
                      <CircularProgress size={12} />
                      <span>자동 저장 중...</span>
                    </div>
                  )}
                </div>
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 text-sm">
                {msg.mealData.breakfast && (
                  <div className="bg-white/70 p-3 rounded-xl border border-green-100">
                    <span className="font-bold text-green-700 text-base">🌅 아침</span>
                    <p className="text-green-600 mt-1">{msg.mealData.breakfast}</p>
                  </div>
                )}
                {msg.mealData.lunch && (
                  <div className="bg-white/70 p-3 rounded-xl border border-green-100">
                    <span className="font-bold text-green-700 text-base">☀️ 점심</span>
                    <p className="text-green-600 mt-1">{msg.mealData.lunch}</p>
                  </div>
                )}
                {msg.mealData.dinner && (
                  <div className="bg-white/70 p-3 rounded-xl border border-green-100">
                    <span className="font-bold text-green-700 text-base">🌙 저녁</span>
                    <p className="text-green-600 mt-1">{msg.mealData.dinner}</p>
                  </div>
                )}
                {msg.mealData.snack && (
                  <div className="bg-white/70 p-3 rounded-xl border border-green-100">
                    <span className="font-bold text-green-700 text-base">🍎 간식</span>
                    <p className="text-green-600 mt-1">{msg.mealData.snack}</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* 결과에 좌표가 포함된 장소가 있으면 지도와 카드를 가로로 표시 */}
          {(() => {
            const hasLocationData = msg.results && msg.results.some((r: any) => typeof r.lat === 'number' && typeof r.lng === 'number')
            return hasLocationData
          })() && (
            <div className="mt-4 lg:mt-5">
              <div className="flex flex-col lg:flex-row gap-4 lg:gap-6">
                {/* 지도 영역 */}
                <div className="flex-1">
                  <div className="rounded-2xl overflow-hidden border border-gray-200">
                    <div className="h-[500px] lg:h-[500px]">
                      {(() => {
                        const placeResults = msg.results!.filter((r: any) => typeof r.lat === 'number' && typeof r.lng === 'number')
                        const restaurants = placeResults.map((r: any, i: number) => ({
                          id: r.place_id || String(i),
                          name: r.name || '',
                          address: r.address || '',
                          lat: r.lat,
                          lng: r.lng,
                        }))
                        return (
                          <KakaoMap
                            key={`map-${msg.id}`}
                            lat={userLocation?.lat}
                            lng={userLocation?.lng}
                            level={1}
                            fitToBounds={true}
                            restaurants={restaurants}
                            activeIndex={typeof selectedPlaceIndexByMsg[msg.id] === 'number' ? selectedPlaceIndexByMsg[msg.id]! : null}
                            specialMarker={userLocation ? { lat: userLocation.lat, lng: userLocation.lng, title: '현재 위치' } : undefined}
                            onMarkerClick={({ index }) => {
                              onPlaceMarkerClick(msg.id, index)
                            }}
                          />
                        )
                      })()}
                    </div>
                  </div>
                </div>

                {/* 장소 카드 영역 */}
                <div className="w-full lg:w-80 flex-shrink-0">
                  <div className="overflow-hidden">
                    {(() => {
                      const placeResults = msg.results!.filter((r: any) => typeof r.lat === 'number' && typeof r.lng === 'number')
                      const sel = selectedPlaceIndexByMsg[msg.id]
                      if (typeof sel === 'number' && sel >= 0 && sel < placeResults.length) {
                        const place = placeResults[sel]
                        return <PlaceCard place={place} />
                      }
                      return (
                        <div className="h-[500px] flex items-center justify-center p-6 bg-gray-50 rounded-2xl border border-gray-200">
                          <div className="text-center text-gray-500">
                            <p className="text-sm font-medium">지도에서 장소를 클릭해보세요</p>
                            <p className="text-xs text-gray-400 mt-1">상세 정보를 확인할 수 있습니다</p>
                          </div>
                        </div>
                      )
                    })()}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
