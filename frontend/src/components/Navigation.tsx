import { NavLink } from 'react-router-dom'
import { 
  Message, 
  CalendarToday, 
  Person, 
  BarChart,
  Restaurant,
  LocationOn as MapPin,
  CreditCard
} from '@mui/icons-material'
import { cn } from '@/lib/utils'
import { useAuthStore } from '@/store/authStore'
import { toast } from 'react-hot-toast'

const navigationItems = [
  {
    title: '채팅',
    href: '/chat',
    icon: Message,
    description: 'AI와 대화하며 추천받기'
  },
  {
    title: '지도',
    href: '/map',
    icon: MapPin,
    description: '주변 키토 친화 식당'
  },
  {
    title: '캘린더',
    href: '/calendar',
    icon: CalendarToday,
    description: '식단 계획 관리'
  },
  {
    title: '프로필',
    href: '/profile',
    icon: Person,
    description: '개인 설정 및 목표'
  },
  {
    title: '구독',
    href: '/subscribe',
    icon: CreditCard,
    description: '구독 관리'
  }
]

export function Navigation() {
  const { user } = useAuthStore()
  const items = user ? navigationItems : navigationItems.filter((i) => i.href !== '/profile' && i.href !== '/calendar')
  return (
    <nav className="w-64 bg-muted/30 border-r border-border min-h-screen p-4">
      <div className="space-y-2">
        {items.map((item) => (
          <NavLink
            key={item.href}
            to={item.href}
            onClick={(e) => {
              if (!user && item.href === '/profile') {
                e.preventDefault()
                toast.error('로그인해야 이용할 수 있는 기능입니다')
              }
            }}
            className={({ isActive }) =>
              cn(
                "flex items-center space-x-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground hover:bg-muted"
              )
            }
          >
            <item.icon className="h-5 w-5" />
            <div className="flex-1">
              <div>{item.title}</div>
              <div className="text-xs opacity-70">{item.description}</div>
            </div>
          </NavLink>
        ))}
      </div>

      {/* 빠른 액션 */}
      <div className="mt-8 pt-4 border-t border-border">
        <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
          빠른 액션
        </h3>
        <div className="space-y-1">
          <button className="flex items-center space-x-2 w-full px-3 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-muted rounded-lg transition-colors">
            <Restaurant sx={{ fontSize: 16 }} />
            <span>오늘 식단 추가</span>
          </button>
          <button className="flex items-center space-x-2 w-full px-3 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-muted rounded-lg transition-colors">
            <MapPin sx={{ fontSize: 16 }} />
            <span>주변 식당 찾기</span>
          </button>
          <button className="flex items-center space-x-2 w-full px-3 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-muted rounded-lg transition-colors">
            <BarChart sx={{ fontSize: 16 }} />
            <span>이번 주 통계</span>
          </button>
        </div>
      </div>

      {/* 키토 팁 */}
      <div className="mt-8 p-3 bg-keto-primary/10 rounded-lg">
        <h4 className="text-sm font-semibold text-keto-primary mb-1">
          오늘의 키토 팁 💡
        </h4>
        <p className="text-xs text-muted-foreground">
          탄수화물은 하루 20-30g 이하로 유지하고, 충분한 물을 섭취하세요!
        </p>
      </div>
    </nav>
  )
}