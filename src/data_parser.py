"""
JSON 데이터 파싱 및 전처리 모듈
레스토랑 메뉴 데이터를 파싱하고 벡터화를 위한 텍스트로 변환
"""

import json
import pandas as pd
from typing import List, Dict, Any, Tuple
from loguru import logger
import re


class RestaurantDataParser:
    """레스토랑 메뉴 데이터 파서 클래스"""
    
    def __init__(self, json_file_path: str):
        """
        Args:
            json_file_path: JSON 파일 경로
        """
        self.json_file_path = json_file_path
        self.raw_data: List[Dict] = []
        self.processed_data: List[Dict] = []
        
    def load_json_data(self) -> List[Dict]:
        """JSON 파일에서 데이터 로드"""
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as file:
                self.raw_data = json.load(file)
            
            logger.info(f"JSON 데이터 로드 완료: {len(self.raw_data)}개 레스토랑")
            return self.raw_data
            
        except FileNotFoundError:
            logger.error(f"파일을 찾을 수 없습니다: {self.json_file_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 오류: {e}")
            raise
        except Exception as e:
            logger.error(f"데이터 로드 중 오류 발생: {e}")
            raise
    
    def clean_text(self, text: str) -> str:
        """텍스트 정리 및 정규화"""
        if not text or not isinstance(text, str):
            return ""
        
        # 불필요한 공백 제거
        text = re.sub(r'\s+', ' ', text.strip())
        
        # 특수 문자 정리 (한글, 영문, 숫자, 기본 문장부호만 유지)
        text = re.sub(r'[^\w\s가-힣.,!?()-]', ' ', text)
        
        # 연속된 공백 제거
        text = re.sub(r'\s+', ' ', text.strip())
        
        return text
    
    def combine_ingredients(self, ingredients: List[str]) -> str:
        """재료 리스트를 문자열로 결합"""
        if not ingredients or not isinstance(ingredients, list):
            return ""
        
        # 각 재료를 정리하고 결합
        cleaned_ingredients = [self.clean_text(str(ingredient)) for ingredient in ingredients]
        cleaned_ingredients = [ing for ing in cleaned_ingredients if ing]  # 빈 문자열 제거
        
        return " ".join(cleaned_ingredients)
    
    def create_combined_text(self, restaurant_name: str, menu_name: str, 
                           ingredients: List[str], description: str) -> str:
        """벡터화를 위한 결합 텍스트 생성"""
        
        # 각 필드 정리
        restaurant_clean = self.clean_text(restaurant_name)
        menu_clean = self.clean_text(menu_name)
        ingredients_clean = self.combine_ingredients(ingredients)
        description_clean = self.clean_text(description)
        
        # 결합 텍스트 생성
        combined_parts = []
        
        if restaurant_clean:
            combined_parts.append(restaurant_clean)
        if menu_clean:
            combined_parts.append(menu_clean)
        if ingredients_clean:
            combined_parts.append(ingredients_clean)
        if description_clean:
            combined_parts.append(description_clean)
        
        combined_text = " ".join(combined_parts)
        
        # 최종 정리
        combined_text = re.sub(r'\s+', ' ', combined_text.strip())
        
        return combined_text
    
    def process_restaurant_data(self) -> List[Dict]:
        """레스토랑 데이터를 처리하여 플랫 구조로 변환"""
        if not self.raw_data:
            logger.warning("원본 데이터가 없습니다. 먼저 load_json_data()를 실행하세요.")
            return []
        
        processed_items = []
        total_menus = 0
        
        for restaurant in self.raw_data:
            restaurant_name = restaurant.get("restaurant_name", "")
            menus = restaurant.get("menus", [])
            
            if not restaurant_name:
                logger.warning("레스토랑 이름이 없는 데이터를 건너뜁니다.")
                continue
            
            for menu in menus:
                menu_name = menu.get("menu_name", "")
                key_ingredients = menu.get("key_ingredients", [])
                short_description = menu.get("short_description", "")
                
                if not menu_name:
                    logger.warning(f"메뉴 이름이 없는 항목을 건너뜁니다: {restaurant_name}")
                    continue
                
                # 결합 텍스트 생성
                combined_text = self.create_combined_text(
                    restaurant_name, menu_name, key_ingredients, short_description
                )
                
                if not combined_text:
                    logger.warning(f"결합 텍스트가 생성되지 않았습니다: {restaurant_name} - {menu_name}")
                    continue
                
                processed_item = {
                    "restaurant_name": restaurant_name,
                    "menu_name": menu_name,
                    "key_ingredients": key_ingredients,
                    "short_description": short_description,
                    "combined_text": combined_text
                }
                
                processed_items.append(processed_item)
                total_menus += 1
        
        self.processed_data = processed_items
        logger.info(f"데이터 처리 완료: {len(processed_items)}개 메뉴 항목")
        
        return processed_items
    
    def get_statistics(self) -> Dict[str, Any]:
        """데이터 통계 정보 반환"""
        if not self.processed_data:
            return {}
        
        df = pd.DataFrame(self.processed_data)
        
        stats = {
            "total_restaurants": df['restaurant_name'].nunique(),
            "total_menu_items": len(df),
            "avg_menus_per_restaurant": round(len(df) / df['restaurant_name'].nunique(), 2),
            "restaurants_with_most_menus": df.groupby('restaurant_name').size().nlargest(5).to_dict(),
            "avg_combined_text_length": round(df['combined_text'].str.len().mean(), 2),
            "avg_ingredients_per_menu": round(df['key_ingredients'].apply(len).mean(), 2)
        }
        
        return stats
    
    def validate_data(self) -> Tuple[bool, List[str]]:
        """데이터 유효성 검사"""
        if not self.processed_data:
            return False, ["처리된 데이터가 없습니다."]
        
        errors = []
        
        for i, item in enumerate(self.processed_data):
            # 필수 필드 확인
            required_fields = ["restaurant_name", "menu_name", "combined_text"]
            for field in required_fields:
                if not item.get(field):
                    errors.append(f"항목 {i}: '{field}' 필드가 비어있습니다.")
            
            # 텍스트 길이 확인
            combined_text = item.get("combined_text", "")
            if len(combined_text) < 5:
                errors.append(f"항목 {i}: 결합 텍스트가 너무 짧습니다. ({len(combined_text)}자)")
            
            if len(combined_text) > 1000:
                logger.warning(f"항목 {i}: 결합 텍스트가 매우 깁니다. ({len(combined_text)}자)")
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def save_processed_data(self, output_path: str) -> None:
        """처리된 데이터를 JSON 파일로 저장"""
        if not self.processed_data:
            logger.error("저장할 처리된 데이터가 없습니다.")
            return
        
        try:
            # 디렉토리가 없으면 생성
            import os
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as file:
                json.dump(self.processed_data, file, ensure_ascii=False, indent=2)
            
            logger.info(f"처리된 데이터 저장 완료: {output_path}")
            
        except Exception as e:
            logger.error(f"데이터 저장 중 오류 발생: {e}")
            raise
    
    def get_sample_data(self, n: int = 5) -> List[Dict]:
        """샘플 데이터 반환"""
        if not self.processed_data:
            return []
        
        return self.processed_data[:n]


def main():
    """테스트용 메인 함수"""
    # 로깅 설정
    logger.add("logs/data_parser.log", rotation="10 MB")
    
    try:
        # 데이터 파서 초기화
        parser = RestaurantDataParser("mock_restaurants_50.json")
        
        # 데이터 로드 및 처리
        logger.info("데이터 로드 시작...")
        parser.load_json_data()
        
        logger.info("데이터 처리 시작...")
        processed_data = parser.process_restaurant_data()
        
        # 유효성 검사
        is_valid, errors = parser.validate_data()
        if not is_valid:
            logger.error("데이터 유효성 검사 실패:")
            for error in errors:
                logger.error(f"  - {error}")
        else:
            logger.info("데이터 유효성 검사 통과")
        
        # 통계 정보 출력
        stats = parser.get_statistics()
        logger.info("데이터 통계:")
        for key, value in stats.items():
            logger.info(f"  - {key}: {value}")
        
        # 샘플 데이터 출력
        sample_data = parser.get_sample_data(3)
        logger.info("샘플 데이터:")
        for i, item in enumerate(sample_data):
            logger.info(f"  {i+1}. {item['restaurant_name']} - {item['menu_name']}")
            logger.info(f"     결합텍스트: {item['combined_text'][:100]}...")
        
        # 처리된 데이터 저장
        parser.save_processed_data("processed_restaurant_data.json")
        
        logger.info("데이터 파싱 완료!")
        
    except Exception as e:
        logger.error(f"데이터 파싱 중 오류 발생: {e}")
        raise


if __name__ == "__main__":
    main()
