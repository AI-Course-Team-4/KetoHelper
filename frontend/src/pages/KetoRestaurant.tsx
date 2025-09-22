import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabaseClient'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

function TestPage() {
  const [restaurants, setRestaurants] = useState<Restaurant[]>([])
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  type Restaurant = {
    id: number
    name: string
    addr_road: string | null
    addr_jibun: string | null
    lat: number | null
    lng: number | null
    phone: string | null
    category: string | null
    price_range: string | null
    'hompage-url': string | null
    source: string | null
    source_url: string | null
    place_provider: string | null
    place_id: string | null
    normalized_name: string | null
    created_at: string
    updated_at: string
  }

  useEffect(() => {
    fetchRestaurants()
  }, [])

  async function fetchRestaurants() {
    try {
      setLoading(true)
      setError(null)
      const { data, error } = await supabase
        .from('restaurant')
        .select('*')
        console.log(data)
      if (error) throw error
      setRestaurants((data || []) as Restaurant[])
    } catch (e: any) {
      console.error(e)
      setError(e?.message || '데이터를 불러오지 못했습니다.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-end justify-between">
        <div className="text-sm text-muted-foreground">{restaurants.length.toLocaleString()}개</div>
      </div>

      {loading && (
        <div className="text-sm text-muted-foreground">불러오는 중...</div>
      )}
      {error && (
        <div className="text-sm text-red-600">{error}</div>
      )}

      {!loading && !error && restaurants.length === 0 && (
        <div className="text-sm text-muted-foreground">표시할 식당이 없습니다.</div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {restaurants.map((r) => {
          const address = r.addr_road || r.addr_jibun || ''
          const hasCoord = typeof r.lat === 'number' && typeof r.lng === 'number'
          return (
            <Card key={r.id} className="overflow-hidden">
              <CardHeader className="pb-2">
                <CardTitle className="text-base flex items-center justify-between gap-2">
                  <span className="truncate" title={r.name || undefined}>{r.name || '이름 없음'}</span>
                  <div className="flex items-center gap-2">
                    {r.category && <Badge variant="secondary">{r.category}</Badge>}
                    {r.place_provider && <Badge variant="outline">{r.place_provider}</Badge>}
                  </div>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="text-sm text-muted-foreground truncate" title={address}>{address || '주소 정보 없음'}</div>
                <div className="flex flex-wrap items-center gap-2 text-xs">
                  {/* <Badge variant="outline">위도: {hasCoord ? r.lat : 'N/A'}</Badge>
                  <Badge variant="outline">경도: {hasCoord ? r.lng : 'N/A'}</Badge> */}
                  {r.phone && <div className="bg-secondary">{r.phone}</div>}
                </div>
                <div className="flex items-center gap-3 text-xs text-muted-foreground">
                  {r.source_url && (
                    <a
                      href={r.source_url}
                      target="_blank"
                      rel="noreferrer"
                      className="underline hover:text-foreground"
                    >
                      링크 열기
                    </a>
                  )}
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>
    </div>
  )
}

export default TestPage
