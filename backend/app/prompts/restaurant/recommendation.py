"""
식당 추천용 프롬프트
팀원들이 복사하여 개인화할 수 있는 템플릿
"""

RESTAURANT_RECOMMENDATION_PROMPT = """
키토 식당을 추천해주세요.

사용자 요청: "{message}"
식당 목록:
{restaurants}

사용자 프로필: {profile}

추천 가이드라인:
1. 각 식당의 키토 친화도를 0-100점으로 평가하고 그 이유 설명
2. 키토 식단에 적합한 메뉴나 주문 팁 제공
3. 사용자 프로필(알레르기, 비선호 음식)을 고려한 개인화 조언
4. 식당별로 키토 관점에서의 장점과 주의사항 명시
5. 친근하고 실용적인 톤으로 작성

키토 친화도 평가 기준 요약:
- 재료/조리법의 탄수화물·당분 수준 평가
- 커스터마이징 용이성(밥→야채, 소스 선택/제외 가능 여부)
- 단백질·지방 중심 메뉴 가용성 및 선택 폭

알레르기 표시 지침:
- 추천 메뉴 텍스트에 알레르기 경고를 괄호로 붙이지 말 것
- 식당별 블록 하단에 별도 경고 줄로 표시 (있을 때만 노출)
- 형식 예시:
  - <div style='color: #8b4513; font-size: 0.9em; margin-top: 4px;'>⚠️ 알레르기 주의: [알레르기 항목] 제외</div>
  - <div style='color: #8b4513; font-size: 0.9em; margin-top: 2px;'>🚫 비선호 음식: [비선호 항목] 피하기</div>

응답 형식:
안녕하세요! 키토 식단에 알레르기까지 고려해서 식당을 찾으시는군요. 걱정 마세요, 사용자님의 조건에 딱 맞는 키토 식당들을 추천해 드릴게요!

<hr>

<span style="font-weight: bold;"><b>추천 식당 TOP 3</b></span>

<span style="color: #16a34a; font-weight: bold;"><b>1. [식당명]</b></span>
<div style="font-size: 0.95rem; line-height: 1.6; margin: 6px 0; color: #444;">
  <b>키토 친화도: [점수]/100</b><br>
  [한두 문장 설명: 메뉴 구성, 커스터마이징 가능 여부(밥→야채, 소스 당분 조절), 알레르기 안전성 등 핵심 근거를 간결히 요약]
</div>
<table style="border-collapse: collapse; width: 100%; margin: 10px 0;">
  <tr>
    <td style="border: 1px solid #ddd; padding: 8px; background-color: #f8f9fa; font-weight: bold; width: 25%;">추천 메뉴</td>
    <td style="border: 1px solid #ddd; padding: 8px;">[메뉴명]</td>
  </tr>
  <tr>
    <td style="border: 1px solid #ddd; padding: 8px; background-color: #f8f9fa; font-weight: bold;">주문 팁</td>
    <td style="border: 1px solid #ddd; padding: 8px;">[팁]</td>
  </tr>
  <tr>
    <td style="border: 1px solid #ddd; padding: 8px; background-color: #f8f9fa; font-weight: bold;">위치</td>
    <td style="border: 1px solid #ddd; padding: 8px;">[주소] <a href="https://map.kakao.com/link/search/[주소]" target="_blank" style="color: #2563eb; text-decoration: underline; font-size: 0.9em;">[길찾기]</a></td>
  </tr>
</table>

[알레르기/비선호 정보가 있으면 아래 줄 추가]
<div style="color: #8b4513; font-size: 0.9em; margin-top: 4px;">⚠️ 알레르기 주의: [알레르기 항목] 제외</div>
<div style="color: #8b4513; font-size: 0.9em; margin-top: 2px;">🚫 비선호 음식: [비선호 항목] 피하기</div>

<span style="color: #16a34a; font-weight: bold;"><b>2. [식당명]</b></span>
<div style="font-size: 0.95rem; line-height: 1.6; margin: 6px 0; color: #444;">
  <b>키토 친화도: [점수]/100</b><br>
  [한두 문장 설명: 메뉴 구성, 커스터마이징 가능 여부(밥→야채, 소스 당분 조절), 알레르기 안전성 등 핵심 근거를 간결히 요약]
</div>
<table style="border-collapse: collapse; width: 100%; margin: 10px 0;">
  <tr>
    <td style="border: 1px solid #ddd; padding: 8px; background-color: #f8f9fa; font-weight: bold; width: 25%;">추천 메뉴</td>
    <td style="border: 1px solid #ddd; padding: 8px;"><b>[메뉴명]</b></td>
  </tr>
  <tr>
    <td style="border: 1px solid #ddd; padding: 8px; background-color: #f8f9fa; font-weight: bold; width: 25%;">주문 팁</td>
    <td style="border: 1px solid #ddd; padding: 8px;">[팁]</td>
  </tr>
  <tr>
    <td style="border: 1px solid #ddd; padding: 8px; background-color: #f8f9fa; font-weight: bold;">위치</td>
    <td style="border: 1px solid #ddd; padding: 8px;">[주소] <a href="https://map.kakao.com/link/search/[주소]" target="_blank" style="color: #2563eb; text-decoration: underline; font-size: 0.9em;">[길찾기]</a></td>
  </tr>
</table>

[알레르기/비선호 정보가 있으면 아래 줄 추가]
<div style="color: #8b4513; font-size: 0.9em; margin-top: 4px;">⚠️ 알레르기 주의: [알레르기 항목] 제외</div>
<div style="color: #8b4513; font-size: 0.9em; margin-top: 2px;">🚫 비선호 음식: [비선호 항목] 피하기</div>

<span style="color: #16a34a; font-weight: bold;"><b>3. [식당명]</b></span>
<div style="font-size: 0.95rem; line-height: 1.6; margin: 6px 0; color: #444;">
  <b>키토 친화도: [점수]/100</b><br>
  [한두 문장 설명: 메뉴 구성, 커스터마이징 가능 여부(밥→야채, 소스 당분 조절), 알레르기 안전성 등 핵심 근거를 간결히 요약]
</div>
<table style="border-collapse: collapse; width: 100%; margin: 10px 0;">
  <tr>
    <td style="border: 1px solid #ddd; padding: 8px; background-color: #f8f9fa; font-weight: bold; width: 25%;">추천 메뉴</td>
    <td style="border: 1px solid #ddd; padding: 8px;"><b>[메뉴명]</b></td>
  </tr>
  <tr>
    <td style="border: 1px solid #ddd; padding: 8px; background-color: #f8f9fa; font-weight: bold;">주문 팁</td>
    <td style="border: 1px solid #ddd; padding: 8px;">[팁]</td>
  </tr>
  <tr>
    <td style="border: 1px solid #ddd; padding: 8px; background-color: #f8f9fa; font-weight: bold;">위치</td>
    <td style="border: 1px solid #ddd; padding: 8px;">[주소] <a href="https://map.kakao.com/link/search/[주소]" target="_blank" style="color: #2563eb; text-decoration: underline; font-size: 0.9em;">[길찾기]</a></td>
  </tr>
</table>

[알레르기/비선호 정보가 있으면 아래 줄 추가]
<div style="color: #8b4513; font-size: 0.9em; margin-top: 4px;">⚠️ 알레르기 주의: [알레르기 항목] 제외</div>
<div style="color: #8b4513; font-size: 0.9em; margin-top: 2px;">🚫 비선호 음식: [비선호 항목] 피하기</div>

<b>개인 맞춤 조언</b>
[추가 조언]

[개인 맞춤 조언: 사용자의 취향/목표/상황에 맞춘 추가 조언을 간결히 작성]

실용적이고 친근한 톤으로 작성해주세요.
"""

# Restaurant Agent에서 분리된 기본 프롬프트
DEFAULT_RECOMMENDATION_PROMPT = """
검색된 식당들을 바탕으로 개인화된 추천을 생성하세요.

사용자 요청: "{message}"
식당 목록: {restaurants}
사용자 프로필: {profile}

키토 관점에서 각 식당의 장점과 주문 팁을 포함한 추천을 제공해주세요.
"""

# 대안 접근용
RECOMMENDATION_PROMPT = RESTAURANT_RECOMMENDATION_PROMPT
PROMPT = RESTAURANT_RECOMMENDATION_PROMPT
