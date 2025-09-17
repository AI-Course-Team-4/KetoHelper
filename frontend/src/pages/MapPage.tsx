<<<<<<< HEAD
import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Search, MapPin, Filter } from 'lucide-react'
import { PlaceCard } from '@/components/PlaceCard'
import { useSearchPlaces, useNearbyPlaces } from '@/hooks/useApi'

export function MapPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [userLocation, setUserLocation] = useState<{ lat: number; lng: number } | null>(null)
  const [selectedCategory, setSelectedCategory] = useState('')

  const searchPlaces = useSearchPlaces()
  const { data: nearbyPlaces, isLoading: nearbyLoading } = useNearbyPlaces(
    userLocation?.lat || 0,
    userLocation?.lng || 0,
    1000,
    70
  )

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

  const handleSearch = async () => {
    if (!searchQuery.trim() || !userLocation) return

    await searchPlaces.mutateAsync({
      q: searchQuery,
      lat: userLocation.lat,
      lng: userLocation.lng,
      radius: 1000,
      category: selectedCategory || undefined
    })
  }

  const categories = [
    { code: '', name: '전체' },
    { code: 'meat', name: '고기구이' },
    { code: 'shabu', name: '샤브샤브' },
    { code: 'salad', name: '샐러드' },
    { code: 'seafood', name: '해산물' },
    { code: 'western', name: '양식' }
  ]

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
            <Input
              placeholder="식당명이나 음식 종류를 검색하세요..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              className="flex-1"
            />
            <Button onClick={handleSearch} disabled={!userLocation}>
              <Search className="h-4 w-4 mr-2" />
              검색
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

      {/* 지도 영역 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center">
            <MapPin className="h-5 w-5 mr-2" />
            지도
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-96 bg-muted rounded-lg flex items-center justify-center">
            <div className="text-center">
              <MapPin className="h-12 w-12 text-muted-foreground mx-auto mb-2" />
              <p className="text-muted-foreground">
                카카오 지도가 여기에 표시됩니다
              </p>
              <p className="text-sm text-muted-foreground mt-1">
                Kakao Map JS SDK 연동 필요
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

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

      {/* 주변 추천 식당 */}
      {nearbyPlaces && (
        <div>
          <h2 className="text-xl font-semibold mb-4">주변 키토 친화 식당</h2>
          {nearbyLoading ? (
            <div className="text-center py-8">
              <div className="loading-dots">
                <div></div>
                <div></div>
                <div></div>
              </div>
              <p className="text-muted-foreground mt-2">주변 식당을 찾고 있습니다...</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {nearbyPlaces.places?.map((place: any) => (
                <PlaceCard key={place.place_id} place={place} />
              ))}
            </div>
          )}
        </div>
      )}

      {/* 위치 정보가 없는 경우 */}
      {!userLocation && (
        <Card>
          <CardContent className="text-center py-8">
            <MapPin className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
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
=======
import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Search, MapPin, Filter } from 'lucide-react'
import { PlaceCard } from '@/components/PlaceCard'
import { useSearchPlaces, useNearbyPlaces } from '@/hooks/useApi'
import KakaoMap from './KakaoMap'

export function MapPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [userLocation, setUserLocation] = useState<{ lat: number; lng: number } | null>(null)
  const [selectedCategory, setSelectedCategory] = useState('')

  const searchPlaces = useSearchPlaces()
  const { data: nearbyPlaces, isLoading: nearbyLoading } = useNearbyPlaces(
    userLocation?.lat || 0,
    userLocation?.lng || 0,
    1000,
    70
  )

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

  const handleSearch = async () => {
    if (!searchQuery.trim() || !userLocation) return

    await searchPlaces.mutateAsync({
      q: searchQuery,
      lat: userLocation.lat,
      lng: userLocation.lng,
      radius: 1000,
      category: selectedCategory || undefined
    })
  }

  const categories = [
    { code: '', name: '전체' },
    { code: 'meat', name: '고기구이' },
    { code: 'shabu', name: '샤브샤브' },
    { code: 'salad', name: '샐러드' },
    { code: 'seafood', name: '해산물' },
    { code: 'western', name: '양식' }
  ]

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
            <Input
              placeholder="식당명이나 음식 종류를 검색하세요..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              className="flex-1"
            />
            <Button onClick={handleSearch} disabled={!userLocation}>
              <Search className="h-4 w-4 mr-2" />
              검색
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

      {/* 지도 영역 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center">
            <MapPin className="h-5 w-5 mr-2" />
            지도
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-96 bg-muted rounded-lg flex items-center justify-center">
            <KakaoMap
              lat={userLocation?.lat}
              lng={userLocation?.lng}
              level={2}
              height="100%"
              markerSize={64}
              onMarkerClick={() => {}}
              markers={[]}
            />
          </div>
        </CardContent>
      </Card>

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

      {/* 주변 추천 식당 */}
      {nearbyPlaces && (
        <div>
          <h2 className="text-xl font-semibold mb-4">주변 키토 친화 식당</h2>
          {nearbyLoading ? (
            <div className="text-center py-8">
              <div className="loading-dots">
                <div></div>
                <div></div>
                <div></div>
              </div>
              <p className="text-muted-foreground mt-2">주변 식당을 찾고 있습니다...</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {nearbyPlaces.places?.map((place: any) => (
                <PlaceCard key={place.place_id} place={place} />
              ))}
            </div>
          )}
        </div>
      )}

      {/* 위치 정보가 없는 경우 */}
      {!userLocation && (
        <Card>
          <CardContent className="text-center py-8">
            <MapPin className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
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
>>>>>>> de7aaf3f92b9eaeb241486c6d211bba219ec20ec
