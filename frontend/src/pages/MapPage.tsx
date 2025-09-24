import { useState, useEffect, useRef } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Search, LocationOn, Restaurant, Clear } from '@mui/icons-material'
import { CircularProgress } from '@mui/material'
import { PlaceCard } from '@/components/PlaceCard'
import { useSearchPlaces, api } from '@/hooks/useApi'
import KakaoMap from './KakaoMap'

export function MapPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [userLocation, setUserLocation] = useState<{ lat: number; lng: number } | null>(null)
  const [selectedCategory, setSelectedCategory] = useState('')
  const [mapRestaurants, setMapRestaurants] = useState<Array<{ 
    id: string; 
    name: string; 
    address: string; 
    lat?: number; 
    lng?: number; 
    keto_score?: number;
    why?: string[];
    tips?: string[];
    category?: string;
  }>>([])
  const [listRestaurants, setListRestaurants] = useState<Array<{ 
    id: string; 
    name: string; 
    address: string; 
    lat?: number; 
    lng?: number; 
    keto_score?: number;
    why?: string[];
    tips?: string[];
    category?: string;
  }>>([])
  const [nearbyCount, setNearbyCount] = useState<number>(0)
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const listContainerRef = useRef<HTMLDivElement | null>(null)
  const itemRefs = useRef<Array<HTMLDivElement | null>>([])

  const searchPlaces = useSearchPlaces()

  // 카테고리 목록을 백엔드에서 로드
  const [categories, setCategories] = useState<Array<{ code: string; name: string }>>([
    { code: '', name: '전체' }
  ])

  useEffect(() => {
    const loadCategories = async () => {
      try {
        const res = await api.get('/places/categories')
        const arr = Array.isArray(res.data?.categories) ? res.data.categories : []
        const mapped = arr.map((c: any) => ({ code: String(c.code || ''), name: String(c.name || '') }))
        setCategories([{ code: '', name: '전체' }, ...mapped])
      } catch (e) {
        console.error('카테고리 로드 실패:', e)
      }
    }
    loadCategories()
  }, [])

  // 위치 정보 가져오기
  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setUserLocation({
            lat: position.coords.latitude,
            lng: position.coords.longitude
          })
        },
        (error) => {
          console.error('위치 정보를 가져올 수 없습니다:', error)
          // 기본 위치 (강남역)
          setUserLocation({ lat: 37.4979, lng: 127.0276 })
        }
      )
    } else {
      // 기본 위치 (강남역)
      setUserLocation({ lat: 37.4979, lng: 127.0276 })
    }
  }, [])

  // 백엔드에서 키토 식당 데이터 로드
  useEffect(() => {
    const loadRestaurants = async () => {
      if (!userLocation) return
      setIsLoading(true)
      try {
        const res = await api.get('/places/high-keto-score', {
          params: {
            lat: userLocation.lat,
            lng: userLocation.lng,
            radius: 2000,
            min_score: 30,
            max_results: 20,
          },
        })
        console.log('백엔드 응답:', res.data)
        const places = res.data?.places || []
        console.log('places 배열:', places)
        const mapped = places.map((p: any) => ({
          id: String(p.place_id || ''),
          name: p.name || '',
          address: p.address || '',
          lat: typeof p.lat === 'number' ? p.lat : undefined,
          lng: typeof p.lng === 'number' ? p.lng : undefined,
          keto_score: typeof p.keto_score === 'number' ? p.keto_score : undefined,
          why: Array.isArray(p.why) ? p.why : undefined,
          tips: Array.isArray(p.tips) ? p.tips : undefined,
          category: p.category || undefined,
        }))
        console.log('매핑된 데이터:', mapped)
        setMapRestaurants(mapped)
        setListRestaurants(mapped)
        setNearbyCount(mapped.length)
      } catch (e) {
        console.error('백엔드 식당 로드 중 에러:', e)
      } finally {
        setIsLoading(false)
      }
    }
    loadRestaurants()
  }, [userLocation])

  // 마커 선택 시 리스트 자동 스크롤
  useEffect(() => {
    if (typeof selectedIndex === 'number' && selectedIndex >= 0) {
      const el = itemRefs.current[selectedIndex]
      const container = listContainerRef?.current || (el?.parentElement?.parentElement as HTMLElement | null)
      if (el && container) {
        const containerRect = container.getBoundingClientRect()
        const elRect = el.getBoundingClientRect()
        const offset = elRect.top - containerRect.top + container.scrollTop - containerRect.height / 2 + elRect.height / 2
        container.scrollTo({ top: offset, behavior: 'smooth' })
      }
    }
  }, [selectedIndex, listContainerRef])

  const handleSearch = async () => {
    if (!userLocation) return
    setIsLoading(true)
    try {
      const hasKeyword = searchQuery.trim().length > 0
      const hasCategory = !!selectedCategory

      if (hasKeyword || hasCategory) {
        const categoryName = categories.find(c => c.code === selectedCategory)?.name
        const queryForBackend = hasKeyword ? searchQuery.trim() : (categoryName || '키토')

        const res = await api.get('/places', {
          params: {
            q: queryForBackend,
            lat: userLocation.lat,
            lng: userLocation.lng,
            radius: 2000,
            category: hasCategory ? selectedCategory : undefined,
          },
        })
        const places = res.data || []
        const mapped = places.map((p: any) => ({
          id: String(p.place_id || ''),
          name: p.name || '',
          address: p.address || '',
          lat: typeof p.lat === 'number' ? p.lat : undefined,
          lng: typeof p.lng === 'number' ? p.lng : undefined,
          keto_score: typeof p.keto_score === 'number' ? p.keto_score : undefined,
          why: Array.isArray(p.why) ? p.why : undefined,
          tips: Array.isArray(p.tips) ? p.tips : undefined,
          category: p.category || undefined,
        }))
        setMapRestaurants(mapped)
        setListRestaurants(mapped)
        setNearbyCount(mapped.length)
        setSelectedIndex(null)
      } else {
        const res = await api.get('/places/high-keto-score', {
          params: {
            lat: userLocation.lat,
            lng: userLocation.lng,
            radius: 2000,
            min_score: 30,
            max_results: 50,
          },
        })
        const places = res.data?.places || []
        const mapped = places.map((p: any) => ({
          id: String(p.place_id || ''),
          name: p.name || '',
          address: p.address || '',
          lat: typeof p.lat === 'number' ? p.lat : undefined,
          lng: typeof p.lng === 'number' ? p.lng : undefined,
          keto_score: typeof p.keto_score === 'number' ? p.keto_score : undefined,
          why: Array.isArray(p.why) ? p.why : undefined,
          tips: Array.isArray(p.tips) ? p.tips : undefined,
          category: p.category || undefined,
        }))
        setMapRestaurants(mapped)
        setListRestaurants(mapped)
        setNearbyCount(mapped.length)
        setSelectedIndex(null)
      }
    } catch (e) {
      console.error('검색 중 에러:', e)
    } finally {
      setIsLoading(false)
    }
  }

  // 전체 페이지 로딩 화면: 위치 획득 중 또는 리스트 로딩 중
  if (!userLocation || isLoading) {
    return (
      <div className="min-h-[80vh] flex flex-col items-center justify-center gap-3">
        <CircularProgress size={40} />
        <div className="text-sm text-muted-foreground">
          {!userLocation ? '위치 정보를 가져오는 중...' : '식당 목록을 불러오는 중...'}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div>
        <h1 className="text-2xl font-bold text-gradient">키토 친화 식당 지도</h1>
        <p className="text-muted-foreground mt-1">
          주변의 키토 친화적인 식당을 찾아보세요
        </p>
      </div>

      {/* 검색 및 필터 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">검색 및 필터</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Input
                placeholder="식당명이나 음식 종류를 검색하세요..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => {
                  const anyEvt = e as any
                  const composing = anyEvt?.nativeEvent?.isComposing || anyEvt?.keyCode === 229
                  if (!composing && e.key === 'Enter') handleSearch()
                }}
                className="pr-8"
              />
              {searchQuery && !isLoading && (
                <button
                  type="button"
                  onMouseDown={(e) => e.preventDefault()}
                  onClick={() => setSearchQuery('')}
                  className="absolute inset-y-0 right-2 my-auto h-6 w-6 flex items-center justify-center rounded hover:bg-muted/70 text-muted-foreground"
                  aria-label="입력 삭제"
                >
                  <Clear sx={{ fontSize: 16 }} />
                </button>
              )}
            </div>
            <Button onClick={handleSearch} disabled={!userLocation || isLoading}>
              {isLoading ? (
                <>
                  <CircularProgress size={16} sx={{ mr: 1 }} />
                  검색 중...
                </>
              ) : (
                <>
                  <Search sx={{ fontSize: 16, mr: 1 }} />
                  검색
                </>
              )}
            </Button>
          </div>

          {/* 카테고리 필터 */}
          <div className="flex flex-wrap gap-2">
            {categories.map((category) => (
              <Button
                key={category.code}
                variant={selectedCategory === category.code ? "default" : "outline"}
                size="sm"
                onClick={() => setSelectedCategory(category.code)}
              >
                {category.name}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <Card className="lg:col-span-8">
          <CardHeader>
            <CardTitle className="text-lg flex items-center">
              <LocationOn sx={{ fontSize: 20, mr: 1 }} />
              지도
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[800px] bg-muted rounded-lg flex items-center justify-center">
              <KakaoMap
                lat={userLocation?.lat}
                lng={userLocation?.lng}
                level={2}
                fitToBounds={false}
                onMarkerClick={(payload) => {
                  const source = (listRestaurants.length ? listRestaurants : mapRestaurants)
                  const matched = typeof payload.index === 'number' ? source[payload.index] : undefined
                  console.log('Marker clicked:', payload, 'matched list item:', matched)
                  if (typeof payload.index === 'number') setSelectedIndex(payload.index)
                }}
                markers={[]}
                restaurants={listRestaurants.length ? listRestaurants : mapRestaurants}
                specialMarker={userLocation
                  ? { lat: userLocation.lat, lng: userLocation.lng, title: '현재 위치' }
                  : { lat: 37.4979, lng: 127.0276, title: '강남역' }}
                activeIndex={selectedIndex}
              />
            </div>
          </CardContent>
        </Card>

        <Card className="lg:col-span-4">
          <CardHeader>
            <CardTitle className="text-lg flex items-center">
              <Restaurant sx={{ fontSize: 20, mr: 1 }} />
              주변 키토 친화 식당
              <span className="ml-auto text-muted-foreground text-sm">{nearbyCount.toLocaleString()}개</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[800px] overflow-auto pr-4 md:pr-6" ref={listContainerRef}>
              {isLoading ? (
                <div className="flex items-center justify-center h-full">
                  <CircularProgress size={32} />
                  <span className="ml-2">로딩 중...</span>
                </div>
              ) : (
                <div className="grid grid-cols-1 gap-4">
                  {(listRestaurants.length ? listRestaurants : mapRestaurants).map((r, index) => {
                    const address = (r as any).addr_road || (r as any).address || (r as any).addr_jibun || ''
                    const active = typeof selectedIndex === 'number' && selectedIndex === index
                    const ketoScore = (r as any).keto_score
                    const why = (r as any).why || []
                    const tips = (r as any).tips || []
                    const category = (r as any).category
                    
                    return (
                      <div key={(r as any).id} ref={(el) => (itemRefs.current[index] = el)}>
                        <Card onClick={() => setSelectedIndex(index)} className={`overflow-hidden transition-[box-shadow,background-color] ${active ? 'ring-2 ring-inset ring-primary/60 bg-primary/5' : ''}`}>
                          <CardHeader className="pb-2">
                            <CardTitle className="text-base flex items-center justify-between gap-2">
                              <span className="truncate" title={(r as any).name || undefined}>{(r as any).name || '이름 없음'}</span>
                              <div className="flex items-center gap-2">
                                {ketoScore && (
                                  <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                                    ketoScore >= 80 ? 'bg-green-100 text-green-800' :
                                    ketoScore >= 60 ? 'bg-blue-100 text-blue-800' :
                                    ketoScore >= 40 ? 'bg-yellow-100 text-yellow-800' :
                                    'bg-red-100 text-red-800'
                                  }`}>
                                    키토 {ketoScore}점
                                  </span>
                                )}
                                {category && (
                                  <span className="px-2 py-1 text-xs bg-gray-100 text-gray-800 rounded-full">
                                    {category}
                                  </span>
                                )}
                              </div>
                            </CardTitle>
                          </CardHeader>
                          <CardContent className="space-y-3">
                            <div className="text-[0.95rem] text-muted-foreground truncate" title={address}>{address || '주소 정보 없음'}</div>
                            
                            {why.length > 0 && (
                              <div className="space-y-1">
                                <ul className="text-sm text-gray-700 space-y-1">
                                  {why.map((reason: string, idx: number) => (
                                    <li key={idx} className="flex items-start">
                                      <span className="text-green-500 mr-1">•</span>
                                      <span>{reason}</span>
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}
                            
                            {tips.length > 0 && (
                              <div className="space-y-1">
                                <ul className="text-sm text-gray-700 space-y-1">
                                  {tips.map((tip: string, idx: number) => (
                                    <li key={idx} className="flex items-start">
                                      <span className="text-blue-500 mr-1">💡</span>
                                      <span>{tip}</span>
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}
                            
                          </CardContent>
                        </Card>
                      </div>
                    )
                  })}
                  {(listRestaurants.length ? listRestaurants : mapRestaurants).length === 0 && (
                    <div className="text-sm text-muted-foreground">표시할 식당이 없습니다.</div>
                  )}
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 검색 결과 */}
      {searchPlaces.data && (
        <div>
          <h2 className="text-xl font-semibold mb-4">검색 결과</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {searchPlaces.data.map((place: any) => (
              <PlaceCard key={place.place_id} place={place} />
            ))}
          </div>
        </div>
      )}

      

      {/* 위치 정보가 없는 경우 */}
      {!userLocation && (
        <Card>
          <CardContent className="text-center py-8">
            <LocationOn sx={{ fontSize: 48, color: 'text.secondary', mx: 'auto', mb: 2 }} />
            <h3 className="text-lg font-semibold mb-2">위치 정보 필요</h3>
            <p className="text-muted-foreground">
              주변 식당을 찾기 위해 위치 정보 접근을 허용해주세요.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}