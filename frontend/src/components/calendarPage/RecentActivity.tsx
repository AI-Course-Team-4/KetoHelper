import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { BarChart } from '@mui/icons-material'

export function RecentActivity() {
  const activities = [
    { date: '오늘', action: '점심 식단 완료', status: 'completed', icon: '✅' },
    { date: '어제', action: '저녁 식단 스킵', status: 'skipped', icon: '⏭️' },
    { date: '2일 전', action: '7일 식단표 생성', status: 'planned', icon: '📋' },
  ]

  return (
    <Card className="border border-gray-200 bg-gradient-to-br from-white to-blue-50/30">
      <CardHeader className="pb-4">
        <CardTitle className="flex items-center text-xl font-bold">
          <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center mr-3">
            <BarChart className="h-5 w-5 text-white" />
          </div>
          최근 활동
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {activities.map((activity, index) => (
            <div key={index} className="flex items-center justify-between p-4 rounded-xl bg-white/60 border border-gray-200 transition-all duration-300">
              <div className="flex items-center gap-3 flex-1 min-w-0">
                <span className="text-2xl flex-shrink-0">{activity.icon}</span>
                <div className="min-w-0 flex-1">
                  <div className="font-semibold text-gray-800 truncate">{activity.action}</div>
                  <div className="text-sm text-gray-500">{activity.date}</div>
                </div>
              </div>
              <div className={`text-sm px-3 py-1 rounded-full font-medium flex-shrink-0 ${
                activity.status === 'completed' ? 'bg-green-100 text-green-700 border border-green-200' :
                activity.status === 'skipped' ? 'bg-red-100 text-red-700 border border-red-200' :
                'bg-blue-100 text-blue-700 border border-blue-200'
              }`}>
                {activity.status === 'completed' ? '완료' :
                 activity.status === 'skipped' ? '스킵' : '계획'}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
