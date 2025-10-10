"""
RecipeValidator 간단 테스트 스크립트
"""

import asyncio
import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# .env 파일 로드 (중요!)
from dotenv import load_dotenv
from pathlib import Path

# .env 파일 위치 찾기 (backend/.env 또는 ../env)
backend_env = Path(__file__).parent / '.env'
root_env = Path(__file__).parent.parent / '.env'

if backend_env.exists():
    load_dotenv(backend_env)
    print(f"✅ .env 파일 로드: {backend_env}")
elif root_env.exists():
    load_dotenv(root_env)
    print(f"✅ .env 파일 로드: {root_env}")
else:
    print("⚠️  .env 파일을 찾을 수 없습니다. 환경 변수를 직접 설정하세요.")
    load_dotenv()  # 기본 위치에서 시도

from app.domains.recipe.services.recipe_validator import RecipeValidator


async def test_validator():
    """RecipeValidator 기본 테스트"""
    
    print("=" * 60)
    print("🧪 RecipeValidator 테스트 시작")
    print("=" * 60)
    
    try:
        # RecipeValidator 초기화
        print("\n1️⃣ RecipeValidator 초기화 중...")
        validator = RecipeValidator()
        print("✅ 초기화 완료")
        
        # 테스트 케이스 1: 닭고기 요리
        print("\n2️⃣ 테스트 케이스 1: 닭고기 요리")
        print("-" * 60)
        result = await validator.generate_validated_recipe(
            meal_type='닭고기 요리',
            constraints={
                'allergies': [],
                'dislikes': [],
                'kcal_target': 500,
                'carbs_max': 15
            }
        )
        
        print(f"\n📊 결과:")
        print(f"  - 성공: {result['success']}")
        
        if result['success']:
            recipe = result['recipe']
            print(f"  - 레시피: {recipe['title']}")
            print(f"  - 시도 횟수: {result['attempts']}회")
            print(f"  - 응답 시간: {result['response_time_ms']}ms")
            print(f"  - 출처: {recipe.get('source', 'unknown')}")
            
            # 매크로 정보
            if 'macros' in recipe:
                macros = recipe['macros']
                print(f"\n  📈 영양 정보:")
                print(f"    - 탄수화물: {macros.get('carb_g', 0)}g")
                print(f"    - 단백질: {macros.get('protein_g', 0)}g")
                print(f"    - 지방: {macros.get('fat_g', 0)}g")
                print(f"    - 칼로리: {macros.get('kcal', 0)}kcal")
            
            # 재료 정보
            if 'ingredients' in recipe and recipe['ingredients']:
                print(f"\n  🥘 재료 ({len(recipe['ingredients'])}개):")
                for ing in recipe['ingredients'][:3]:  # 처음 3개만
                    name = ing.get('name_norm', ing.get('name', 'Unknown'))
                    amount = ing.get('amount_g', ing.get('amount', 0))
                    print(f"    - {name}: {amount}g")
                if len(recipe['ingredients']) > 3:
                    print(f"    ... 외 {len(recipe['ingredients']) - 3}개")
            
            # 검증 정보
            if 'validation' in result:
                validation = result['validation']
                print(f"\n  ✅ 검증 정보:")
                print(f"    - 통과: {validation.get('passed', False)}")
                if 'reasons' in validation and validation['reasons']:
                    print(f"    - 사유: {len(validation['reasons'])}개")
                    for reason in validation['reasons'][:2]:
                        print(f"      • {reason}")
        else:
            print(f"  - 오류: {result.get('error', 'Unknown error')}")
            if 'attempts' in result:
                print(f"  - 시도 횟수: {result['attempts']}회")
        
        print("\n" + "=" * 60)
        print("🎉 테스트 완료!")
        print("=" * 60)
        
    except ImportError as e:
        print(f"\n❌ Import 오류: {e}")
        print("\n💡 해결 방법:")
        print("  1. backend 디렉토리에서 실행하세요")
        print("  2. 환경 변수 확인: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY")
        print("  3. LLM API 키 확인: OPENAI_API_KEY 또는 GOOGLE_API_KEY")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        print("\n📋 상세 오류:")
        print(traceback.format_exc())


if __name__ == "__main__":
    print("\n🚀 RecipeValidator 테스트 스크립트")
    print("이 스크립트는 골든셋 기반 레시피 검증 시스템을 테스트합니다.\n")
    
    # 환경 변수 확인
    required_env_vars = [
        'SUPABASE_URL',
        'SUPABASE_SERVICE_ROLE_KEY'
    ]
    
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"⚠️  경고: 다음 환경 변수가 설정되지 않았습니다:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\n.env 파일을 확인하세요.\n")
    
    # LLM API 키 확인
    llm_keys = ['OPENAI_API_KEY', 'GOOGLE_API_KEY']
    has_llm_key = any(os.getenv(key) for key in llm_keys)
    
    if not has_llm_key:
        print(f"⚠️  경고: LLM API 키가 설정되지 않았습니다.")
        print(f"  다음 중 하나를 .env 파일에 설정하세요:")
        for key in llm_keys:
            print(f"  - {key}")
        print()
    
    # 테스트 실행
    asyncio.run(test_validator())

