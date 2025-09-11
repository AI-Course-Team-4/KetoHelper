import { Box, Typography, Button, Grid, Container, Paper, Avatar, LinearProgress, CircularProgress, Accordion, AccordionSummary, AccordionDetails } from '@mui/material'
import { Link } from 'react-router-dom'
import { Restaurant, MenuBook, Settings, LocationOn, Grain, Egg, Spa, CheckCircle, ExpandMore } from '@mui/icons-material'
import { useAuthStore } from '@store/authStore'

const HomePage = () => {
  const { isAuthenticated, user } = useAuthStore()
  const displayName = user?.name || user?.id || ''

  const quickAccessCards = [
    {
      title: '식단 추천',
      description: 'AI가 추천하는 맞춤형 키토 레시피를 확인해보세요',
      icon: <MenuBook sx={{ fontSize: 40 }} />,
      path: '/meals',
      color: 'primary.main',
    },
    {
      title: '식당 추천',
      description: '근처 키토 친화적인 식당을 찾아보세요',
      icon: <Restaurant sx={{ fontSize: 40 }} />,
      path: '/restaurants',
      color: 'secondary.main',
    },
    {
      title: '설정',
      description: '개인 선호도와 알레르기 정보를 관리하세요',
      icon: <Settings sx={{ fontSize: 40 }} />,
      path: '/settings',
      color: 'success.main',
    },
  ]

  return (
    <Box>
      {/* 히어로 섹션 */}
      <Box
        sx={{
          background: 'linear-gradient(135deg, rgba(52,211,153,0.7) 0%, rgba(132,204,22,0.7) 100%)',
          color: '#ffffff',
          mb: 6,
          textAlign: 'center',
        }}
      >
        <Container maxWidth="lg" sx={{ py: { xs: 8, md: 16 } }}>
          <Grid container spacing={10} alignItems="center">
            {/* 왼쪽 텍스트 영역 */}
            <Grid item xs={12} md={5}>
              <Box
                display="inline-flex"
                alignItems="center"
                gap={1}
                px={2}
                py={0.5}
                borderRadius="9999px"
                bgcolor="rgba(255,255,255,0.7)"
                border="1px solid rgba(0,0,0,0.05)"
                mb={2}
              >
                <Box width={8} height={8} borderRadius="50%" bgcolor="#34d399" />
                <Typography variant="caption" fontWeight={500} color={"black"}>
                  AI 기반 개인 맞춤
                </Typography>
              </Box>

              <Typography variant="h1" fontWeight={700} mb={2} color={"black"}>
                나만의 <span style={{ color: "#16a34a" }}>키토 식단</span>, 30초 만에 받아보세요
              </Typography>
              <Typography variant="body1" mb={4} color={"black"}>
                알레르기, 선호식재료, 외식 패턴까지 반영해 AI가 하루 식단을 구성합니다. 건강한 저탄고지 라이프를 쉽게 시작하세요.
              </Typography>

              <Box display="flex" gap={2} flexWrap="wrap" mb={2} justifyContent={"center"}>
                <Button variant="contained" sx={{
                  bgcolor: "white",
                  color: "primary.main",
                  '&:hover': {
                    bgcolor: "grey.100", // hover 시 배경색
                    color: "primary.dark", // 필요하면 글자색도 변경 가능
                  },
                }}>
                  둘러보기
                </Button>
                <Button variant="contained" sx={{
                  bgcolor: "black",
                  color: "white",
                  '&:hover': {
                    bgcolor: "grey.800", // hover 시 배경색
                    color: "white", // 필요하면 글자색도 변경 가능
                  },
                }}>
                  지금 시작
                </Button>
              </Box>

              <Typography variant="caption" color={"black"}>
                의료적 조언이 아닌 참고 정보이며, 특이 증상 시 전문의 상담을 권장합니다.
              </Typography>
            </Grid>

            {/* 오른쪽 추천 식단 영역 */}
            <Grid item xs={12} md={7}>
              <Paper sx={{ p: 3, borderRadius: 4, backdropFilter: "blur(10px)", border: "1px solid rgba(0,0,0,0.1)" }}>
                <Typography variant="h5" fontWeight={700} mb={1}>
                  오늘의 추천 식단
                </Typography>
                <Typography variant="caption" color="text.secondary" mb={2}>
                  예시 프리뷰
                </Typography>

                <Grid container spacing={2} alignItems="stretch" mt={1}>
                  {[
                    {
                      title: "아보카도 베이컨 샐러드",
                      tag: "키토 친화적",
                      desc: "신선한 아보카도와 바삭한 베이컨이 만나는 완벽한 키토 샐러드",
                      img: "/images/avocado-salad.jpg",
                    },
                    {
                      title: "치킨 크림 스프",
                      tag: "키토 친화적",
                      desc: "부드럽고 진한 크림 스프로 포만감을 주는 키토 요리",
                      img: "/images/chicken-cream-soup.jpg",
                    },
                    {
                      title: "연어 스테이크",
                      tag: "키토 친화적",
                      desc: "오메가3이 풍부한 연어로 만든 고급 키토 요리",
                      img: "/images/salmon-steak.jpg",
                    },
                  ].map((meal) => (
                    <Grid item xs={12} sm={6} lg={4} key={meal.title} sx={{ display: 'flex' }}>
                      <Paper
                        sx={{
                          borderRadius: 3,
                          overflow: "hidden",
                          "&:hover": { transform: "scale(1.02)", transition: "all 0.3s" },
                          height: '100%',
                          flex: 1,
                          display: 'flex',
                          flexDirection: 'column',
                        }}
                      >
                        <Box component="img" src={meal.img} alt={meal.title} width="100%" height={160} sx={{ objectFit: "cover" }} />
                        <Box p={2} display="flex" flexDirection="column" gap={1} sx={{ flex: 1 }}>
                          <Typography variant="caption" color={"white"} fontWeight={600} px={1} py={0.5} bgcolor="success.light" borderRadius={2}>
                            {meal.tag}
                          </Typography>
                          <Typography variant="subtitle1" fontWeight={700}>
                            {meal.title}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {meal.desc}
                          </Typography>
                        </Box>
                      </Paper>
                    </Grid>
                  ))}
                </Grid>
              </Paper>
            </Grid>
          </Grid>
        </Container>
      </Box>

      {/* 사용자 환영 메시지 (로그인 시) */}
      {isAuthenticated && user && (
        <Box sx={{ mb: 6 }}>
          <Typography variant="h4" sx={{ fontWeight: 600, mb: 2 }}>
            안녕하세요, {displayName}님! 👋
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
            오늘도 건강한 키토 라이프를 이어가세요.
          </Typography>

          <Grid container spacing={3} sx={{ mb: 4, alignItems: "stretch" }}>
            {/* 1번 카드: 키토 진행률 */}
            <Grid item xs={12} md={4}>
              <Paper
                elevation={0}
                sx={{
                  p: 3,
                  height: "100%",
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "center",
                  textAlign: "center",
                  borderRadius: 2,
                  bgcolor: "rgba(255,255,255,0.9)",
                  backdropFilter: "blur(10px)",
                  boxShadow: 3,
                  transition: "transform .3s, box-shadow .3s",
                  "&:hover": { transform: "translateY(-4px)", boxShadow: 6 },
                }}
              >
                <Typography variant="h4" sx={{ fontWeight: 800, color: "primary.main" }}>
                  75%
                </Typography>
                <Typography sx={{ mt: 1, opacity: 0.7 }}>키토 진행률</Typography>
                <LinearProgress
                  variant="determinate"
                  value={75}
                  sx={{
                    mt: 3,
                    height: 10,
                    borderRadius: 5,
                    bgcolor: "grey.200",
                    "& .MuiLinearProgress-bar": {
                      background: "linear-gradient(90deg, #34d399, #84cc16)",
                      borderRadius: 5,
                    },
                  }}
                />
              </Paper>
            </Grid>

            {/* 2번 카드: 시도한 레시피 (원형 진행률) */}
            <Grid item xs={12} md={4}>
              <Paper
                elevation={0}
                sx={{
                  p: 3,
                  height: "100%",
                  textAlign: "center",
                  borderRadius: 2,
                  bgcolor: "rgba(255,255,255,0.9)",
                  backdropFilter: "blur(10px)",
                  boxShadow: 3,
                  transition: "transform .3s, box-shadow .3s",
                  "&:hover": { transform: "translateY(-4px)", boxShadow: 6 },
                }}
              >
                <Box sx={{ position: "relative", display: "inline-flex", mb: 2 }}>
                  <CircularProgress
                    variant="determinate"
                    value={100}
                    size={96}
                    thickness={6}
                    sx={{ color: "#E5E7EB" }}
                  />
                  <CircularProgress
                    variant="determinate"
                    value={60}
                    size={96}
                    thickness={6}
                    sx={{ color: "#F97316", position: "absolute", left: 0 }}
                  />
                  <Box
                    sx={{
                      position: "absolute",
                      inset: 0,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                    }}
                  >
                    <Typography sx={{ fontWeight: 700, fontSize: "1.25rem" }}>12</Typography>
                  </Box>
                </Box>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
                  시도한 레시피
                </Typography>
                <Typography variant="body2" sx={{ color: "text.secondary" }}>
                  전체 20개 중
                </Typography>
              </Paper>
            </Grid>

            {/* 3번 카드: 방문한 식당 (아이콘 원형 배경) */}
            <Grid item xs={12} md={4}>
              <Paper
                elevation={0}
                sx={{
                  p: 3,
                  height: "100%",
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "center",
                  textAlign: "center",
                  borderRadius: 2,
                  bgcolor: "rgba(255,255,255,0.9)",
                  backdropFilter: "blur(10px)",
                  boxShadow: 3,
                  transition: "transform .3s, box-shadow .3s",
                  "&:hover": { transform: "translateY(-4px)", boxShadow: 6 },
                }}
              >
                <Avatar sx={{ width: 64, height: 64, bgcolor: "white", color: "success.dark", mx: "auto", mb: 1.5 }}>
                  <LocationOn sx={{ fontSize: 32 }} />
                </Avatar>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
                  즐겨찾기한 식당
                </Typography>
                <Typography variant="body2" sx={{ color: "text.secondary" }}>
                  총 8곳
                </Typography>
              </Paper>
            </Grid>
          </Grid>

        </Box>
      )
      }

      {/* 퀵 액세스 카드 */}
      <Box sx={{ mb: 6 }}>
        <Typography variant="h4" sx={{ fontWeight: 600, mb: 4, textAlign: 'left' }}>
          무엇을 도와드릴까요?
        </Typography>

        <Grid container spacing={3}>
          {quickAccessCards.map((card, index) => (
            <Grid item xs={12} md={4} key={index}>
              <Paper
                component={Link}
                to={card.path}
                sx={{
                  textDecoration: 'none',
                  p: 3,
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'center',
                  textAlign: 'center',
                  borderRadius: 2,
                  minHeight: '220px',
                  bgcolor: 'rgba(255,255,255,0.9)',
                  backdropFilter: 'blur(10px)',
                  boxShadow: 3,
                  transition: 'transform .3s, box-shadow .3s',
                  cursor: 'pointer',
                  '&:hover': { transform: 'translateY(-4px)', boxShadow: 6 },
                }}
              >
                <Box sx={{ color: card.color, mb: 2 }}>
                  {card.icon}
                </Box>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                  {card.title}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {card.description}
                </Typography>
              </Paper>
            </Grid>
          ))}
        </Grid>
      </Box>

      {/* 키토 다이어트 소개 섹션 */}
      {/* Guide / Info 섹션 (HTML 스니펫을 MUI로 변환) */}
      <Box sx={{ mb: 6 }}>
        <Typography variant="h4" sx={{ fontWeight: 600, textAlign: 'left', mb: 4 }}>
          키토제닉 다이어트란?
        </Typography>
        <Grid container spacing={3} alignItems="stretch">
          <Grid item xs={12} md={4} sx={{ display: 'flex' }}>
            <Paper sx={{
              p: 3,
              borderRadius: 2,
              bgcolor: 'rgba(255,255,255,0.9)',
              backdropFilter: 'blur(10px)',
              transition: 'transform .3s',
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
              textAlign: 'center',
              minHeight: '220px'
            }}>
              <Box sx={{ color: 'warning.main', mb: 1.5, display: 'flex', justifyContent: 'center' }}>
                <Grain sx={{ fontSize: 40 }} />
              </Box>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>탄수화물 5–10%</Typography>
              <Typography variant="body2" sx={{ mt: 1, opacity: 0.8 }}>
                정제 탄수화물은 최소화하고, 채소 위주로 섭취.
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} md={4} sx={{ display: 'flex' }}>
            <Paper sx={{
              p: 3,
              borderRadius: 2,
              bgcolor: 'rgba(255,255,255,0.9)',
              backdropFilter: 'blur(10px)',
              transition: 'transform .3s',
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
              textAlign: 'center',
              minHeight: '220px'
            }}>
              <Box sx={{ color: 'info.main', mb: 1.5, display: 'flex', justifyContent: 'center' }}>
                <Egg sx={{ fontSize: 40 }} />
              </Box>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>단백질 15–25%</Typography>
              <Typography variant="body2" sx={{ mt: 1, opacity: 0.8 }}>
                닭가슴살, 달걀, 두부 등으로 균형 있게.
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} md={4} sx={{ display: 'flex' }}>
            <Paper sx={{
              p: 3,
              borderRadius: 2,
              bgcolor: 'rgba(255,255,255,0.9)',
              backdropFilter: 'blur(10px)',
              transition: 'transform .3s',
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
              textAlign: 'center',
              minHeight: '220px'
            }}>
              <Box sx={{ color: 'success.main', mb: 1.5, display: 'flex', justifyContent: 'center' }}>
                <Spa sx={{ fontSize: 40 }} />
              </Box>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>지방 70–80%</Typography>
              <Typography variant="body2" sx={{ mt: 1, opacity: 0.8 }}>
                아보카도, 올리브오일, 견과류처럼 좋은 지방 위주.
              </Typography>
            </Paper>
          </Grid>
        </Grid>
        <Typography variant="body2" sx={{ mt: 2, opacity: 0.7 }}>
          해당 정보는 일반적 안내이며, 건강 상태에 따라 조정이 필요할 수 있습니다.
        </Typography>
      </Box>
      <Grid container spacing={3} alignItems="stretch">
        <Grid item xs={12}>
          <Paper
            sx={{
              p: 3,
              borderRadius: 2,
              bgcolor: 'rgba(255,255,255,0.9)',
              backdropFilter: 'blur(10px)',
            }}
          >
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 2, textAlign: 'left' }}>
              KetoHelper의 장점
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                <CheckCircle color="success" fontSize="small" />
                <Typography variant="body2">AI 기반 개인화 추천</Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                <CheckCircle color="success" fontSize="small" />
                <Typography variant="body2">알레르기 및 선호도 고려</Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                <CheckCircle color="success" fontSize="small" />
                <Typography variant="body2">영양 성분 자동 계산</Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                <CheckCircle color="success" fontSize="small" />
                <Typography variant="body2">키토 친화적 식당 정보</Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                <CheckCircle color="success" fontSize="small" />
                <Typography variant="body2">지속적인 학습 및 개선</Typography>
              </Box>
            </Box>
          </Paper>
        </Grid>
      </Grid>

      {/* FAQ 섹션 */}
      <Box component="section" id="faq" sx={{ mt: 6, mb: 8 }}>
        <Typography variant="h4" sx={{ fontWeight: 600, textAlign: 'left', mb: 3 }}>
          자주 묻는 질문
        </Typography>
        <Box sx={{ width: '100%' }}>
          <Accordion sx={{ borderRadius: 2, bgcolor: 'rgba(255,255,255,0.9)', backdropFilter: 'blur(10px)', '&::before': { display: 'none' }, mb: 1 }}>
            <AccordionSummary expandIcon={<ExpandMore />} sx={{ py: 2 }}>
              <Typography sx={{ fontWeight: 500 }}>추천 식단은 반드시 따라야 하나요?</Typography>
            </AccordionSummary>
            <AccordionDetails sx={{ py: 2 }}>
              <Typography variant="body2" sx={{ opacity: 0.8, pb: 2 }}>
                아니요. 생활 패턴에 맞춰 자유롭게 대체할 수 있도록 대안 메뉴도 함께 제안해 드립니다.
              </Typography>
            </AccordionDetails>
          </Accordion>

          <Accordion sx={{ borderRadius: 2, bgcolor: 'rgba(255,255,255,0.9)', backdropFilter: 'blur(10px)', '&::before': { display: 'none' }, mb: 1 }}>
            <AccordionSummary expandIcon={<ExpandMore />} sx={{ py: 2 }}>
              <Typography sx={{ fontWeight: 500 }}>알레르기/기피 식재료 반영이 되나요?</Typography>
            </AccordionSummary>
            <AccordionDetails sx={{ py: 2 }}>
              <Typography variant="body2" sx={{ opacity: 0.8, pb: 2 }}>
                프로필에서 설정하면 추천 알고리즘에 즉시 반영됩니다.
              </Typography>
            </AccordionDetails>
          </Accordion>

          <Accordion sx={{ borderRadius: 2, bgcolor: 'rgba(255,255,255,0.9)', backdropFilter: 'blur(10px)', '&::before': { display: 'none' } }}>
            <AccordionSummary expandIcon={<ExpandMore />} sx={{ py: 2 }}>
              <Typography sx={{ fontWeight: 500 }}>무료인가요, 유료인가요?</Typography>
            </AccordionSummary>
            <AccordionDetails sx={{ py: 2 }}>
              <Typography variant="body2" sx={{ opacity: 0.8, pb: 2 }}>
                핵심 기능은 무료로 제공하며, 프리미엄 구독 시 식단 캘린더/쇼핑리스트 등 부가 기능이 열립니다.
              </Typography>
            </AccordionDetails>
          </Accordion>
        </Box>
      </Box>

    </Box >
  )
}

export default HomePage
