import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Message, CalendarToday, LocationOn, FilterList } from '@mui/icons-material'
import { useRef } from 'react'
import { useNavigate } from 'react-router-dom'

export function MainPage() {
    const featuresRef = useRef<HTMLDivElement | null>(null)
    const navigate = useNavigate()

    return (
        <div className="space-y-6">
            {/* 헤더 */}
            <div>
                <h1 className="text-2xl font-bold text-gradient">KetoHelper</h1>
                <p className="text-muted-foreground mt-1">
                    건강한 키토 식단을 위한 AI 어시스턴트
                </p>
            </div>

            {/* 랜딩 히어로 */}
            <Card>
                <CardContent className="p-6 lg:p-8 grid lg:grid-cols-2 gap-8 items-center">
                    <div>
                        <h2 className="text-3xl sm:text-4xl font-extrabold leading-tight">AI가 당신에게 딱 맞는 키토 식단과 식당을 추천해드립니다!</h2>
                        <p className="mt-3 text-muted-foreground">채팅으로 간편하게 추천받고, 캘린더에 바로 등록하세요. 위치 기반 식당 추천과 알레르기 필터까지 제공합니다.</p>
                        <div className="mt-5 flex flex-col sm:flex-row gap-3">
                            <Button onClick={() => featuresRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })}>주요 기능 확인하기</Button>
                            <Button variant="outline" onClick={() => navigate('/subscribe')}>구독하기</Button>
                        </div>
                    </div>
                    <div className="relative">
                        <div className="mb-2"><Badge variant="secondary">예시 프리뷰</Badge></div>
                        <div className="rounded-2xl border border-border bg-background/60 backdrop-blur p-4 shadow-sm">
                            <div className="space-y-3">
                                <div className="flex justify-end">
                                    <div className="max-w-[75%] rounded-2xl px-3 py-2 text-sm text-white bg-gradient-to-r from-green-500 to-emerald-500">
                                        아침 키토 레시피 추천해줘
                                    </div>
                                </div>
                                <div className="flex justify-start">
                                    <div className="max-w-[75%] rounded-2xl px-3 py-2 text-sm bg-card border border-border">
                                        ## ✨ 아침 키토 레시피 추천해줘 (키토 버전)<br /><br />

                                        ### 👨‍🍳 조리법<br />
                                        1. 양파를 잘게 다져 버터 1큰술을 두른 팬에 볶아 향을 냅니다.<br />
                                        2. 베이컨을 넣고 바삭하게 굽습니다.  익은 베이컨은 따로 접시에 덜어둡니다.<br />
                                        3. 베이컨을 굽던 팬에 계란을 깨뜨려 스크램블 에그를 만듭니다.  소금, 후추로 간을 합니다.<br />
                                        4. 아보카도를 반으로 갈라 씨를 제거하고,  스크램블 에그와 구운 베이컨, 다진 체다 치즈를 넣어 섞어 먹거나, 아보카도를 토스트처럼 활용하여 베이컨과 계란을 얹어 먹습니다.... (중략)
                                    </div>
                                </div>
                            </div>
                            <div className="mt-4 flex gap-2">
                                <div className="flex-1 h-10 rounded-full border border-border bg-background/70 px-4 flex items-center text-sm text-muted-foreground">
                                    메시지를 입력하세요...
                                </div>
                                <Button size="sm" className="rounded-full px-4">전송</Button>
                            </div>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* 주요 기능 */}
            <Card ref={featuresRef as any}>
                <CardHeader className="pb-6">
                    <CardTitle className="text-lg">주요 기능</CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
                    <div className="grid md:grid-cols-4 gap-4">
                        <Card>
                            <CardContent className="p-6 text-center hover:scale-[1.02] transition-transform" style={{ cursor: 'pointer' }} onClick={() => navigate('/chat')}>
                                <div className="flex items-center justify-center">
                                    <Message sx={{ fontSize: 28, color: 'green.600' }} />
                                </div>
                                <div className="font-semibold mt-2 cursor-pointer">채팅 기반 추천</div>
                                <div className="text-sm text-muted-foreground mt-1">질문하면 AI가 바로 식단과 식당을 추천합니다.</div>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardContent className="p-6 text-center hover:scale-[1.02] transition-transform" style={{ cursor: 'pointer' }} onClick={() => navigate('/calendar')}>
                                <div className="flex items-center justify-center">
                                    <CalendarToday sx={{ fontSize: 28, color: 'green.600' }} />
                                </div>
                                <div className="font-semibold mt-2">캘린더 등록</div>
                                <div className="text-sm text-muted-foreground mt-1">추천 식단을 클릭하면 캘린더에 자동 등록됩니다.</div>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardContent className="p-6 text-center hover:scale-[1.02] transition-transform" style={{ cursor: 'pointer' }} onClick={() => navigate('/map')}>
                                <div className="flex items-center justify-center">
                                    <LocationOn sx={{ fontSize: 28, color: 'green.600' }} />
                                </div>
                                <div className="font-semibold mt-2">위치 기반 식당</div>
                                <div className="text-sm text-muted-foreground mt-1">현재 위치 주변의 키토 친화 식당을 찾아드립니다.</div>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardContent className="p-6 text-center hover:scale-[1.02] transition-transform" style={{ cursor: 'pointer' }} onClick={() => navigate('/profile')}>
                                <div className="flex items-center justify-center">
                                    <FilterList sx={{ fontSize: 28, color: 'green.600' }} />
                                </div>
                                <div className="font-semibold mt-2">알레르기 & 필터</div>
                                <div className="text-sm text-muted-foreground mt-1">알레르기나 비선호 음식은 추천에서 자동 제외됩니다.</div>
                            </CardContent>
                        </Card>
                    </div>
                </CardContent>
            </Card>

            {/* 피드: 키토제닉 다이어트란? */}
            <Card>
                <CardHeader>
                    <CardTitle className="text-lg">키토제닉 다이어트란?</CardTitle>
                </CardHeader>
                <CardContent>
                    <div>
                        <Card>
                            <CardHeader>
                                <CardTitle className="text-sm font-medium">
                                    키토제닉 다이어트는 탄수화물 섭취를 줄여 몸이 ‘케톤체’를 주요 에너지원으로 사용하도록 유도하는 건강한 식사법입니다.
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="text-sm text-muted-foreground">
                                    탄수화물이 부족할 때 간에서 지방을 분해해 만들어내는 에너지원이 바로 케톤체입니다. 이 과정 덕분에 체지방을 더 효율적으로 태우고, 지속적인 에너지를 공급받아 활력과 집중력이 높아질 수 있습니다. 꾸준히 실천하면 체중 관리뿐만 아니라 생활 전반에서 긍정적인 변화를 기대할 수 있습니다.
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                </CardContent>
                <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="text-center p-4 bg-green-50 rounded-lg">
                            <div className="text-2xl font-bold text-green-600">70-80%</div>
                            <div className="text-sm text-green-700">지방</div>
                            <div className="text-xs text-muted-foreground mt-1">
                                주 에너지원
                            </div>
                        </div>

                        <div className="text-center p-4 bg-blue-50 rounded-lg">
                            <div className="text-2xl font-bold text-blue-600">15-25%</div>
                            <div className="text-sm text-blue-700">단백질</div>
                            <div className="text-xs text-muted-foreground mt-1">
                                근육 유지
                            </div>
                        </div>

                        <div className="text-center p-4 bg-orange-50 rounded-lg">
                            <div className="text-2xl font-bold text-orange-600">5-10%</div>
                            <div className="text-sm text-orange-700">탄수화물</div>
                            <div className="text-xs text-muted-foreground mt-1">
                                최소 섭취
                            </div>
                        </div>
                    </div>

                    <div className="mt-6 space-y-2">
                        <h4 className="font-medium">💡 키토 성공 팁</h4>
                        <ul className="text-sm text-muted-foreground space-y-1">
                            <li>• 충분한 물 섭취 (하루 2-3L)</li>
                            <li>• 전해질 보충 (나트륨, 칼륨, 마그네슘)</li>
                            <li>• 점진적 탄수화물 감소</li>
                            <li>• 규칙적인 식사 시간</li>
                            <li>• 스트레스 관리와 충분한 수면</li>
                        </ul>
                    </div>
                </CardContent>
            </Card>

            {/* 피드: 자주 묻는 질문 */}
            <Card>
                <CardHeader className="pb-2">
                    <CardTitle className="text-lg">자주 묻는 질문</CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
                    <div className="grid gap-4 md:grid-cols-1 mt-4">
                        <details className="group rounded-lg border border-border p-4 bg-card">
                            <summary className="cursor-pointer font-medium text-sm flex items-center justify-between">추천 식단은 반드시 따라야 하나요?
                                <span className="opacity-60 group-open:rotate-180 transition-transform">⌄</span>
                            </summary>
                            <p className="mt-3 text-sm text-muted-foreground">아니요. 생활 패턴에 맞춰 자유롭게 대체할 수 있도록 대안 메뉴도 함께 제안해 드립니다.</p>
                        </details>
                        <details className="group rounded-lg border border-border p-4 bg-card">
                            <summary className="cursor-pointer font-medium text-sm flex items-center justify-between">알레르기/기피 식재료 반영이 되나요?
                                <span className="opacity-60 group-open:rotate-180 transition-transform">⌄</span>
                            </summary>
                            <p className="mt-3 text-sm text-muted-foreground">프로필에서 설정하면 추천 알고리즘에 즉시 반영됩니다.</p>
                        </details>
                        <details className="group rounded-lg border border-border p-4 bg-card">
                            <summary className="cursor-pointer font-medium text-sm flex items-center justify-between">무료인가요, 유료인가요?
                                <span className="opacity-60 group-open:rotate-180 transition-transform">⌄</span>
                            </summary>
                            <p className="mt-3 text-sm text-muted-foreground">핵심 기능은 무료로 제공하며, 프리미엄 구독 시 식단 캘린더/쇼핑리스트 등 부가 기능이 열립니다.</p>
                        </details>
                    </div>
                </CardContent>
            </Card>

            {/* 피드: 오늘의 키토 팁 */}
            {/* <Card>
                <CardHeader>
                    <CardTitle className="text-lg">오늘의 키토 팁</CardTitle>
                </CardHeader>
                <CardContent>
                    <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
                        <li>탄수는 낮게, 단백질은 충분히, 지방은 포만감이 들 정도로.</li>
                        <li>물은 자주 조금씩. 전해질(소금/마그네슘)도 함께 보충하세요.</li>
                        <li>외식 시에는 소스/설탕/빵/면/밥 제외 옵션을 요청하세요.</li>
                    </ul>
                </CardContent>
            </Card> */}
        </div>
    )
}