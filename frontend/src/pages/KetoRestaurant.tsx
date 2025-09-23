import { useEffect, useMemo, useRef, useState } from 'react'
import { supabase } from '@/lib/supabaseClient'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

type KetoRestaurantProps = {
  onCountChange?: (count: number) => void
  restaurants?: Array<{ id: string | number; name: string; address?: string; addr_road?: string | null; addr_jibun?: string | null }>
  activeIndex?: number
  scrollContainerRef?: { current: HTMLElement | null } | null
}

function KetoRestaurant({ onCountChange, restaurants: restaurantsProp, activeIndex, scrollContainerRef }: KetoRestaurantProps) {
  const [restaurants, setRestaurants] = useState<Restaurant[]>([])
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const itemRefs = useRef<Array<HTMLDivElement | null>>([])

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
    if (!restaurantsProp) {
      fetchRestaurants()
    } else {
      try { onCountChange?.(restaurantsProp.length) } catch {}
    }
  }, [restaurantsProp])

  async function fetchRestaurants() {
    try {
      setLoading(true)
      setError(null)
      const { data, error } = await supabase
        .from('restaurant')
        .select('*')
      
      if (error) throw error
      console.log(data)
      const list = (data || []) as Restaurant[]
      setRestaurants(list)
      try { onCountChange?.(list.length) } catch {}
    } catch (e: any) {
      console.error(e)
      setError(e?.message || '데이터를 불러오지 못했습니다.')
      try { onCountChange?.(0) } catch {}
    } finally {
      setLoading(false)
    }
  }

  const displayList = useMemo(() => {
    if (restaurantsProp) {
      return (restaurantsProp.map((r) => ({
        id: r.id as number,
        name: r.name as string,
        addr_road: (r as any).addr_road ?? (r as any).address ?? null,
        addr_jibun: (r as any).addr_jibun ?? null,
        lat: null,
        lng: null,
        phone: null,
        category: null,
        price_range: null,
        'hompage-url': null as any,
        source: null,
        source_url: null,
        place_provider: null,
        place_id: null,
        normalized_name: null,
        created_at: '',
        updated_at: '',
      })) as Restaurant[])
    }
    return restaurants
  }, [restaurantsProp, restaurants])

  useEffect(() => {
    if (typeof activeIndex === 'number' && activeIndex >= 0) {
      const el = itemRefs.current[activeIndex]
      const container = scrollContainerRef?.current || (el?.parentElement?.parentElement as HTMLElement | null)
      if (el && container) {
        const containerRect = container.getBoundingClientRect()
        const elRect = el.getBoundingClientRect()
        const offset = elRect.top - containerRect.top + container.scrollTop - containerRect.height / 2 + elRect.height / 2
        container.scrollTo({ top: offset, behavior: 'smooth' })
      }
    }
  }, [activeIndex, scrollContainerRef])

  return (
    <div className="space-y-4">
      {/* <div className="flex items-end justify-between">
        <div className="text-sm text-muted-foreground">{restaurants.length.toLocaleString()}개</div>
      </div> */}

      {loading && (
        <div className="text-sm text-muted-foreground">불러오는 중...</div>
      )}
      {error && (
        <div className="text-sm text-red-600">{error}</div>
      )}

      {!loading && !error && displayList.length === 0 && (
        <div className="text-sm text-muted-foreground">표시할 식당이 없습니다.</div>
      )}

      <div className="grid grid-cols-1 gap-4">
        {displayList.map((r, index) => {
          const address = r.addr_road || r.addr_jibun || ''
          const active = typeof activeIndex === 'number' && activeIndex === index
          const url = (r as any).source_url || `https://map.kakao.com/?q=${encodeURIComponent((r.name || '') + ' ' + (address || ''))}`
          return (
            <div key={r.id} ref={(el) => (itemRefs.current[index] = el)}>
              <Card className={`overflow-hidden transition-[box-shadow,background-color] ${active ? 'ring-2 ring-inset ring-primary/60 bg-primary/5' : ''}`}>
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
                  <a
                    href={url}
                    target="_blank"
                    rel="noreferrer"
                    className="underline hover:text-foreground"
                  >
                    링크 열기
                  </a>
                </div>
                </CardContent>
              </Card>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default KetoRestaurant
