import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Sparkles } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { RecipeCard } from '@/components/RecipeCard'

export function MainPage() {
    const { user } = useAuthStore()

    const sampleRecipes = [
        { id: 'r1', title: '연어 아보카도 샐러드', tags: ['저탄수', '오메가3'], ketoized: true },
        { id: 'r2', title: '버섯 크림 오믈렛', tags: ['고단백', '간단'], ketoized: true },
        { id: 'r3', title: '닭가슴살 스테이크 & 버터야채', tags: ['저탄수', '고지방'], ketoized: true },
    ]
    const ketoProgress = 75
    const recipesTried = 12
    const recipesTotal = 20
    const recipesPct = Math.round((recipesTried / recipesTotal) * 100)

    return (
        <div className="space-y-6">
            {/* 헤더 */}
            <div>
                <h1 className="text-2xl font-bold text-gradient">KetoHelper</h1>
                <p className="text-muted-foreground mt-1">
                    건강한 키토 식단을 위한 AI 어시스턴트
                </p>
            </div>

            <Card>
                <CardHeader className="pb-2">
                    <CardTitle className="text-lg">진행도</CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
                    <p className="text-sm text-muted-foreground mb-4">{user?.name ? `${user.name}님, ` : ''}오늘도 건강한 키토 라이프를 이어가세요!</p>
                    <div className="grid gap-4 md:grid-cols-3">
                        <Card>
                            <CardHeader className="pb-2">
                                <CardTitle className="text-sm font-medium">키토 진행률</CardTitle>
                            </CardHeader>
                            <CardContent className="pt-0">
                                <div className="text-3xl font-bold">{ketoProgress}%</div>
                                <div className="mt-3 h-2 bg-border rounded-full overflow-hidden">
                                    <div className="h-full bg-green-500" style={{ width: `${ketoProgress}%` }} />
                                </div>
                                <div className="text-sm text-muted-foreground mt-1">목표 대비 진행률</div>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardHeader className="pb-2">
                                <CardTitle className="text-sm font-medium">시도한 레시피</CardTitle>
                            </CardHeader>
                            <CardContent className="pt-0">
                                <div className="flex items-center gap-3 mt-2">
                                    <svg width="72" height="72" viewBox="0 0 100 100" className="shrink-0">
                                        <circle cx="50" cy="50" r="42" strokeWidth="8" className="stroke-border" fill="none" />
                                        <circle
                                            cx="50"
                                            cy="50"
                                            r="42"
                                            strokeWidth="8"
                                            className="stroke-green-500"
                                            fill="none"
                                            strokeDasharray={264}
                                            strokeDashoffset={264 * (1 - recipesPct / 100)}
                                            transform="rotate(-90 50 50)"
                                            strokeLinecap="round"
                                        />
                                    </svg>
                                    <div>
                                        <div className="text-3xl font-bold leading-none">{recipesTried}</div>
                                        <div className="text-sm text-muted-foreground mt-1">전체 {recipesTotal}개 중 · {recipesPct}%</div>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardHeader className="pb-2">
                                <CardTitle className="text-sm font-medium">즐겨찾기한 식당</CardTitle>
                            </CardHeader>
                            <CardContent className="pt-0">
                                <div className="flex items-center gap-3 mt-2">
                                    <div className="w-16 h-16 flex items-center justify-center rounded-full bg-green-100 dark:bg-green-700 mb-3">
                                        <svg className="w-8 h-8 text-green-600 dark:text-green-300" fill="currentColor" viewBox="0 0 20 20">
                                            <path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
                                        </svg>
                                    </div>
                                    <div>
                                        <div className="text-3xl font-bold leading-none">8</div>
                                        <div className="text-sm text-muted-foreground mt-1">즐겨찾기한 식당 수</div>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                </CardContent>
            </Card>

            {/* 피드: 오늘의 추천 레시피 (추후 랜덤 3개로 나오게끔 변경) */}
            <Card>
                <CardHeader>
                    <CardTitle className="text-lg flex items-center gap-2">
                        <Sparkles className="h-5 w-5 text-green-600" /> 오늘의 추천 레시피
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid gap-4 md:grid-cols-3">
                        {sampleRecipes.map((r) => (
                            <RecipeCard key={r.id} recipe={r as any} />
                        ))}
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
                    <div className="grid gap-4 md:grid-cols-3">
                        <Card>
                            <CardHeader>
                                <CardTitle className="text-sm font-medium">탄수화물 5–10%</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="text-sm text-muted-foreground">
                                    정제 탄수화물은 최소화하고, 채소 위주로 섭취.
                                </div>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardHeader>
                                <CardTitle className="text-sm font-medium">단백질 15–25%</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="text-sm text-muted-foreground">
                                    닭가슴살, 달걀, 두부 등으로 균형 있게.
                                </div>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardHeader>
                                <CardTitle className="text-sm font-medium">지방 70–80%</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="text-sm text-muted-foreground">
                                    아보카도, 올리브오일, 견과류처럼 좋은 지방 위주.
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                    <div className="mt-6 text-sm text-muted-foreground">
                        해당 정보는 일반적 안내이며, 건강 상태에 따라 조정이 필요할 수 있습니다.
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