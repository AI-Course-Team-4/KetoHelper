"""
단일 레시피 생성용 프롬프트
사용자 요청에 맞는 개별 키토 레시피 생성 템플릿
"""

SINGLE_RECIPE_GENERATION_PROMPT = """
<<<<<<< HEAD
당신은 키토 식단 전문가입니다냥~ '{message}'에 맞는 맞춤 키토 레시피를 만들어주세요냥~

<b>사용자 정보:</b> {profile_context}
=======
당신은 키토 식단 전문가입니다. '{message}'에 대한 맞춤 키토 레시피를 생성해주세요.
>>>>>>> 89ecc00aa37a7104ab3df07b72b49573ad200a6a

<hr>

<span style="font-weight: bold; font-size: 1.3em;">✨ {message} (키토 버전)</span>

<table style="width: 100%; border-collapse: collapse; font-size: 0.95rem; margin-top: 10px;">
  <tr style="background-color: #f3f4f6;">
    <th colspan="2" style="text-align: left; padding: 8px; border: 1px solid #ddd;">📋 재료 (2인분)</th>
  </tr>
  <tr>
    <td style="width: 25%; font-weight: bold; padding: 8px; border: 1px solid #ddd;">주재료</td>
    <td style="padding: 8px; border: 1px solid #ddd;">[구체적인 재료와 정확한 분량]</td>
  </tr>
  <tr>
    <td style="font-weight: bold; padding: 8px; border: 1px solid #ddd;">부재료</td>
    <td style="padding: 8px; border: 1px solid #ddd;">[구체적인 재료와 정확한 분량]</td>
  </tr>
  <tr>
    <td style="font-weight: bold; padding: 8px; border: 1px solid #ddd;">키토 대체재</td>
    <td style="padding: 8px; border: 1px solid #ddd;">[일반 재료 → 키토 재료로 변경 설명]</td>
  </tr>
</table>

<br>

<b>👨‍🍳 조리법</b><br>
1. [첫 번째 단계 - 구체적이고 명확하게]<br>
2. [두 번째 단계 - 구체적이고 명확하게]<br>
3. [세 번째 단계 - 구체적이고 명확하게]<br>
4. [완성 및 마무리 단계]<br>

<br>

<b>📊 영양 정보 (1인분 기준)</b><br>
- 칼로리: 000 kcal<br>
- 탄수화물: 0 g<br>
- 단백질: 00 g<br>
- 지방: 00 g<br>

<br>

<b>💡 키토 성공 팁</b><br>
- [키토 식단에 맞는 구체적 조언]<br>
- [조리 시 주의사항]<br>
- [보관 및 활용 팁]<br>

<br><hr>

<i style="color: gray; font-size: 0.9em;">
※ 내부 지침: 탄수화물 5‑10g, 단백질 20‑30g, 지방 30‑40g, 총 400‑600 kcal 기준으로 계산하되  
이 기준은 사용자에게 표시하지 마세요냥~
</i>
"""

RECIPE_FALLBACK_PROMPT = """
✨ {message} (키토 버전) 기본 가이드냥~

<table style="width: 100%; border-collapse: collapse; font-size: 0.95rem; margin-top: 10px;">
  <tr style="background-color: #f3f4f6;">
    <th colspan="2" style="text-align: left; padding: 8px; border: 1px solid #ddd;">📋 재료 (2인분)</th>
  </tr>
  <tr>
    <td style="width: 25%; font-weight: bold; padding: 8px; border: 1px solid #ddd;">주재료</td>
    <td style="padding: 8px; border: 1px solid #ddd;">키토 친화적 재료들</td>
  </tr>
  <tr>
    <td style="font-weight: bold; padding: 8px; border: 1px solid #ddd;">키토 대체재</td>
    <td style="padding: 8px; border: 1px solid #ddd;">
      설탕 → 에리스리톨 또는 스테비아<br>
      밀가루 → 아몬드 가루 또는 코코넛 가루
    </td>
  </tr>
</table>

<br>

<b>👨‍🍳 조리법</b><br>
1. 재료를 준비합니다냥~<br>
2. 키토 원칙에 맞게 조리합니다냥~<br>
3. 탄수화물을 최소화하여 완성합니다냥~<br>

<br>

<b>📊 영양 정보 (1인분 기준)</b><br>
- 칼로리: 450 kcal<br>
- 탄수화물: 8 g<br>
- 단백질: 25 g<br>
- 지방: 35 g<br>

<br>

<b>💡 키토 성공 팁</b><br>
- 탄수화물 함량을 꼼꼼히 확인하세요냥~<br>
- 충분한 지방 섭취로 포만감을 유지하세요냥~<br>
- 개인 취향에 맞게 조절하세요냥~<br>

<br>

<i style="color: gray; font-size: 0.9em;">
⚠️ AI 서비스 오류로 기본 가이드를 제공했습니다냥~ 구체적인 레시피는 키토 레시피 사이트를 참고해주세요냥~
</i>
"""

PROMPT = SINGLE_RECIPE_GENERATION_PROMPT
FALLBACK_PROMPT = RECIPE_FALLBACK_PROMPT
