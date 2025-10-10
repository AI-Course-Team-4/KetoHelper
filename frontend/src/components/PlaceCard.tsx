import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { LocationOn, Phone, OpenInNew, CalendarToday } from '@mui/icons-material'
import { getKetoScoreColor, getKetoScoreText } from '@/lib/utils'

interface PlaceCardProps {
  place: {
    place_id: string
    name: string
    address: string
    category?: string
    lat: number
    lng: number
    keto_score?: number
    why?: string[]
    tips?: string[]
    phone?: string
    distance?: number
    source_url?: string
  }
  onAddToPlan?: (place: any) => void
}

export function PlaceCard({ place, onAddToPlan }: PlaceCardProps) {
  const scoreColor = place.keto_score ? getKetoScoreColor(place.keto_score) : 'keto-score-poor'
  const scoreText = place.keto_score ? getKetoScoreText(place.keto_score) : '정보 없음'

  return (
    <Card className="place-card rounded-2xl overflow-hidden h-[500px] flex flex-col">
      <CardHeader>
        <div className="flex items-start justify-between">
          <CardTitle className="text-lg">{place.name}</CardTitle>
          {place.keto_score && (
            <Badge className={`${scoreColor} font-semibold`}>
              {place.keto_score}점 · {scoreText}
            </Badge>
          )}
        </div>
        
        <div className="flex items-center text-sm text-muted-foreground">
          <LocationOn sx={{ fontSize: 16, mr: 0.5 }} />
          {place.address}
        </div>

        {place.category && (
          <Badge variant="outline" className="w-fit">
            {place.category}
          </Badge>
        )}
      </CardHeader>

      <CardContent className="flex-1 flex flex-col p-6">
        {/* 상단 콘텐츠 영역 */}
        <div className="flex-1 space-y-4">
          {/* 키토 점수 이유 */}
          <div>
            <h4 className="text-sm font-medium mb-2">🎯 키토 친화 이유</h4>
            {place.why && place.why.length > 0 ? (
              <ul className="text-sm text-muted-foreground space-y-1">
                {place.why.slice(0, 2).map((reason, index) => (
                  <li key={index} className="flex items-start">
                    <span className="w-2 h-2 bg-green-500 rounded-full mt-2 mr-2 flex-shrink-0" />
                    {reason}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-gray-400">등록된 정보가 없습니다</p>
            )}
          </div>

          {/* 주문 팁 */}
          <div>
            <h4 className="text-sm font-medium mb-2">💡 주문 팁</h4>
            {place.tips && place.tips.length > 0 ? (
              <div className="text-sm text-muted-foreground">
                {place.tips[0]}
              </div>
            ) : (
              <p className="text-sm text-gray-400">등록된 정보가 없습니다</p>
            )}
          </div>

          {/* 추가 정보 */}
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <span>
              {place.distance ? `${place.distance}m` : '거리 정보 없음'}
            </span>
            <span>
              {place.phone ? place.phone : '전화번호 없음'}
            </span>
          </div>
        </div>

        {/* 하단 버튼 영역 - 고정 */}
        <div className="space-y-3 mt-4">
          {/* 액션 버튼 */}
          <div className="flex gap-2">
            <Button variant="outline" size="sm" className="flex-1">
              <LocationOn sx={{ fontSize: 16, mr: 0.5 }} />
              지도에서 보기
            </Button>
            
            {onAddToPlan && (
              <Button 
                size="sm" 
                onClick={() => onAddToPlan(place)}
                className="flex items-center"
              >
                <CalendarToday sx={{ fontSize: 16, mr: 0.5 }} />
                일정 추가
              </Button>
            )}
          </div>

          {/* 외부 링크 (카카오맵 등) */}
          <div className="flex gap-2">
            <Button 
              variant="ghost" 
              size="sm" 
              className="flex-1 text-xs"
              onClick={() => window.open(`https://map.kakao.com/link/map/${place.place_id}`, '_blank')}
            >
              <OpenInNew sx={{ fontSize: 12, mr: 0.5 }} />
              카카오맵
            </Button>
            
            {place.phone && (
              <Button 
                variant="ghost" 
                size="sm" 
                className="flex-1 text-xs"
                onClick={() => window.open(`tel:${place.phone}`)}
              >
                <Phone sx={{ fontSize: 12, mr: 0.5 }} />
                전화걸기
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}