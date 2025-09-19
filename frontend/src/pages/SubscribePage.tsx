import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Calendar, BarChart3, Heart, ShieldCheck } from 'lucide-react'

export function SubscribePage() {
    return (
        <div className="space-y-8">
            {/* Hero */}
            <div>
                <h1 className="text-2xl font-bold text-gradient">구독 관리</h1>
                <p className="text-muted-foreground mt-1">
                    맞춤 식단, 식단 캘린더, 통계 등 프리미엄 기능을 이용해 보세요.
                </p>
            </div>

            {/* Plans */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Basic */}
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-lg">Basic</CardTitle>
                    </CardHeader>
                    <CardContent className="pt-0 space-y-4">
                        <div className="text-3xl font-bold">무료</div>
                        <ul className="text-sm text-muted-foreground space-y-2">
                            <li>• 기본 레시피 추천</li>
                            <li>• 주변 키토 식당 조회</li>
                            <li>• 즐겨찾기 저장(제한)</li>
                        </ul>
                        <Button className="w-full" variant="outline">현재 이용 중</Button>
                    </CardContent>
                </Card>

                {/* Pro (recommended) */}
                <Card className="relative border-2 border-green-500/40">
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                        <Badge className="bg-green-600 text-white">가장 인기</Badge>
                    </div>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-lg">Pro</CardTitle>
                    </CardHeader>
                    <CardContent className="pt-0 space-y-4">
                        <div>
                            <span className="text-3xl font-bold">₩9,900</span>
                            <span className="text-sm text-muted-foreground"> / 월</span>
                        </div>
                        <ul className="text-sm text-muted-foreground space-y-2">
                            <li>• 한 달 맞춤 식단 생성</li>
                            <li>• 캘린더 이용 가능</li>
                            <li>• 원클릭 레시피/식당 일정 추가</li>
                            <li>• 진행률/섭취 통계</li>
                        </ul>
                        <Button className="w-full">Pro 구독하기</Button>
                    </CardContent>
                </Card>

                {/* Premium */}
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-lg">Premium</CardTitle>
                    </CardHeader>
                    <CardContent className="pt-0 space-y-4">
                        <div>
                            <span className="text-3xl font-bold">₩19,900</span>
                            <span className="text-sm text-muted-foreground"> / 월</span>
                        </div>
                        <ul className="text-sm text-muted-foreground space-y-2">
                            <li>• Pro의 모든 기능</li>
                            <li>• 무제한 기록/통계 저장</li>
                            <li>• 우선 지원</li>
                        </ul>
                        <Button className="w-full" variant="outline">Premium 구독하기</Button>
                    </CardContent>
                </Card>
            </div>

            {/* Benefits */}
            <Card>
                <CardHeader className="pb-6">
                    <CardTitle className="text-lg">구독 혜택</CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-2 gap-4">
                        <div className="flex items-center gap-3 p-3 border border-border rounded-lg">
                            <Calendar className="h-5 w-5 text-green-600" />
                            <div className="text-sm">식단 캘린더 & 주간 계획</div>
                        </div>
                        <div className="flex items-center gap-3 p-3 border border-border rounded-lg">
                            <BarChart3 className="h-5 w-5 text-green-600" />
                            <div className="text-sm">섭취/진행 통계</div>
                        </div>
                        <div className="flex items-center gap-3 p-3 border border-border rounded-lg">
                            <Heart className="h-5 w-5 text-green-600" />
                            <div className="text-sm">즐겨찾기 & 기록 보관</div>
                        </div>
                        <div className="flex items-center gap-3 p-3 border border-border rounded-lg">
                            <ShieldCheck className="h-5 w-5 text-green-600" />
                            <div className="text-sm">보안 결제 & 환불 보장</div>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* FAQ */}
            <Card>
                <CardHeader className="pb-2">
                    <CardTitle className="text-lg">자주 묻는 질문</CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
                    <div className="grid gap-4 md:grid-cols-1 mt-4">
                        <details className="group rounded-lg border border-border p-4 bg-card">
                            <summary className="cursor-pointer font-medium text-sm flex items-center justify-between">언제든 해지할 수 있나요?
                                <span className="opacity-60 group-open:rotate-180 transition-transform">⌄</span>
                            </summary>
                            <p className="mt-3 text-sm text-muted-foreground">언제든 즉시 해지되며 다음 결제는 청구되지 않습니다.</p>
                        </details>
                        <details className="group rounded-lg border border-border p-4 bg-card">
                            <summary className="cursor-pointer font-medium text-sm flex items-center justify-between">환불 정책은 어떻게 되나요?
                                <span className="opacity-60 group-open:rotate-180 transition-transform">⌄</span>
                            </summary>
                            <p className="mt-3 text-sm text-muted-foreground">첫 결제 7일 이내 단순 변심 환불을 지원합니다.</p>
                        </details>
                        <details className="group rounded-lg border border-border p-4 bg-card">
                            <summary className="cursor-pointer font-medium text-sm flex items-center justify-between">결제 수단은 무엇을 지원하나요?
                                <span className="opacity-60 group-open:rotate-180 transition-transform">⌄</span>
                            </summary>
                            <p className="mt-3 text-sm text-muted-foreground">국내 신용/체크카드 및 해외 카드 기반 결제를 지원합니다.</p>
                        </details>
                    </div>
                </CardContent>
            </Card>

            {/* Bottom CTA */}
            <Card>
                <CardContent className="py-6 flex items-center justify-between gap-3">
                    <div className="text-sm text-muted-foreground">
                        지금 Pro로 시작하고 모든 프리미엄 기능을 이용해 보세요.
                    </div>
                    <Button>Pro 구독하기</Button>
                </CardContent>
            </Card>
        </div>
    )
}