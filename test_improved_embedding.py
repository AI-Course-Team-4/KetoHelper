"""
개선된 임베딩 텍스트 생성 테스트
"""

from src.data_parser import RestaurantDataParser

def main():
    # 파서 초기화 및 데이터 로드
    parser = RestaurantDataParser('mock_restaurants_50.json')
    parser.load_json_data()

    print('=== 개선된 임베딩 텍스트 생성 테스트 ===\n')

    # 첫 번째 레스토랑의 첫 번째 메뉴로 테스트
    restaurant = parser.raw_data[0]
    menu = restaurant['menus'][0]

    print('원본 데이터:')
    print(f'  레스토랑: {restaurant["restaurant_name"]}')
    print(f'  메뉴: {menu["menu_name"]}')
    print(f'  재료: {menu["key_ingredients"]}')
    print(f'  설명: {menu["short_description"]}')
    print()

    # 개선된 임베딩 텍스트 생성
    combined_text = parser.create_combined_text(
        restaurant['restaurant_name'],
        menu['menu_name'],
        menu['key_ingredients'],
        menu['short_description']
    )

    print(f'개선된 임베딩 텍스트: "{combined_text}"')
    print()

    # 몇 개 더 테스트
    print('=== 추가 테스트 (5개 메뉴) ===')
    count = 0
    for restaurant in parser.raw_data[:3]:
        for menu in restaurant['menus'][:2]:  # 각 레스토랑에서 2개씩
            if count >= 5:
                break
            combined = parser.create_combined_text(
                restaurant['restaurant_name'],
                menu['menu_name'], 
                menu['key_ingredients'],
                menu['short_description']
            )
            print(f'{count+1}. {menu["menu_name"]} → "{combined}"')
            count += 1
        if count >= 5:
            break

if __name__ == "__main__":
    main()
