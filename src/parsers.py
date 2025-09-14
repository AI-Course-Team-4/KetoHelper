import re
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse

def safe_unicode_decode(text: str) -> str:
    """유니코드 이스케이프 시퀀스가 있는 경우만 변환"""
    if not text:
        return text
    # 유니코드 이스케이프 시퀀스가 있는 경우만 변환
    if '\\u' in text:
        try:
            # 문자열을 바이트로 변환 후 유니코드 이스케이프 디코딩
            return text.encode('utf-8').decode('unicode_escape')
        except (UnicodeDecodeError, UnicodeEncodeError):
            return text
    return text

class RecipeListParser:
    """만개의레시피 검색 결과 목록 파서"""

    def __init__(self, base_url: str):
        self.base_url = base_url

    def parse_recipe_links(self, html_content: str) -> List[str]:
        """레시피 링크 목록 추출"""
        soup = BeautifulSoup(html_content, 'lxml')
        links = []

        # 레시피 링크 추출: .common_sp_thumb a 또는 .rcp_m_list_thumbnail
        recipe_links = soup.select('.common_sp_thumb a')
        if not recipe_links:
            recipe_links = soup.select('.rcp_m_list_thumbnail')

        for link in recipe_links:
            href = link.get('href')
            if href and '/recipe/' in href:
                full_url = urljoin(self.base_url, href)
                links.append(full_url)

        return links

    def has_next_page(self, html_content: str, current_url: str = None) -> bool:
        """다음 페이지가 있는지 확인"""
        soup = BeautifulSoup(html_content, 'lxml')

        # 페이지네이션에서 페이지 번호들 확인
        pagination = soup.select('.pagination a')
        page_numbers = []
        
        for link in pagination:
            text = link.get_text(strip=True)
            if text.isdigit():
                page_numbers.append(int(text))
        
        if page_numbers:
            max_page = max(page_numbers)
            
            # 현재 페이지 번호 추출 (URL에서)
            current_page = 1
            if current_url:
                import re
                page_match = re.search(r'page=(\d+)', current_url)
                if page_match:
                    current_page = int(page_match.group(1))
            
            # 현재 페이지가 최대 페이지보다 작으면 다음 페이지가 있음
            if current_page < max_page:
                return True
            
            # 최대 페이지가 6이면 더 많은 페이지가 있을 수 있음 (226개면 약 6페이지)
            # 실제로는 더 많은 페이지가 있을 수 있으므로 더 확인해보자
            if max_page >= 6:
                return True

        # 다음 페이지 버튼 확인 (기존 로직)
        next_link = soup.select_one('.list_btn_next')
        if next_link and 'disabled' not in next_link.get('class', []):
            return True

        # 페이지네이션에서 다음 페이지 확인 (기존 로직)
        for link in pagination:
            if '다음' in link.get_text() or '>' in link.get_text():
                return True

        return False

class RecipeDetailParser:
    """레시피 상세 페이지 파서"""
    
    def _fix_encoding_issues(self, text: str) -> str:
        """인코딩 문제 수정"""
        if not text:
            return text
        
        # 일반적인 인코딩 문제 패턴 수정
        encoding_fixes = {
            # 아몬드 관련
            'ë¤ì´í¸': '아몬드',
            'ë¤ì´í¸ë¦¿': '아몬드 가루',
            'ë¤ì´í¸ ë¦¿': '아몬드 가루',
            
            # 코코넛 관련
            'ì½ì½ë°ë£¨': '코코넛 가루',
            'ì½ì½ë° ë£¨': '코코넛 가루',
            'ì½ì½ë°ë£¨': '코코넛 가루',
            
            # 계란 관련
            'ë¹ë¨ì': '계란',
            'ë¹ë¨': '계란',
            'ë¹ë¨ì': '계란',
            
            # 닭고기 관련
            'ë­ê°ì´ì´': '닭가슴살',
            'ë­ê°ì´ ì´': '닭가슴살',
            'ë­ê°ì´ì´': '닭가슴살',
            
            # 멸치 관련
            'ìë¦¬ìì¤ê¸°ë¦': '멸치볶음',
            'ìë¦¬ì': '멸치',
            
            # 기타
            'ë§ë°ë£¨': '베이킹파우더',
            'ë§ë° ë£¨': '베이킹파우더',
            'ìê¸': '소금',
            'ëª½í¬í¸ë£»': '당근',
            'ëª½í¬': '당근',
            'ìì¡ì¯': '양파',
            'ìì¡': '양파',
            'ìì¡ì¯': '양파',
        }
        
        # 인코딩 문제 수정
        for broken, fixed in encoding_fixes.items():
            text = text.replace(broken, fixed)
        
        return text

    def parse_recipe(self, html_content: str, source_url: str) -> Dict:
        """레시피 상세 정보 추출"""
        # 인코딩 문제 해결: 더 강력한 인코딩 처리
        try:
            if isinstance(html_content, bytes):
                # 바이트인 경우 UTF-8로 디코딩 시도
                try:
                    html_content = html_content.decode('utf-8')
                except UnicodeDecodeError:
                    # UTF-8 실패 시 다른 인코딩 시도
                    try:
                        html_content = html_content.decode('cp949')
                    except UnicodeDecodeError:
                        html_content = html_content.decode('utf-8', errors='ignore')
            elif isinstance(html_content, str):
                # 이미 문자열인 경우 그대로 사용
                html_content = html_content
            else:
                html_content = str(html_content)
        except (UnicodeDecodeError, UnicodeEncodeError):
            # 인코딩 실패 시 원본 사용
            html_content = str(html_content)
        
        # BeautifulSoup에 인코딩 정보 명시 (경고 제거)
        soup = BeautifulSoup(html_content, 'lxml')
        
        # 인코딩 문제가 있는 경우 강제 수정
        html_content = self._fix_encoding_issues(html_content)
        soup = BeautifulSoup(html_content, 'lxml')

        recipe = {
            'source_site': '10000recipe',
            'source_url': source_url,
            'source_recipe_id': self._extract_recipe_id(source_url),
            'title': self._extract_title(soup),
            'author': self._extract_author(soup),
            'rating': self._extract_rating(soup),
            'views': self._extract_views(soup),
            'servings': self._extract_servings(soup),
            'cook_time': self._extract_cook_time(soup),
            'difficulty': self._extract_difficulty(soup),
            'summary': self._extract_summary(soup),
            'tags': self._extract_tags(soup),
            'ingredients': self._extract_ingredients(soup),
            'steps': self._extract_steps(soup),
            'images': self._extract_images(soup, source_url),
        }

        return recipe

    def _extract_recipe_id(self, url: str) -> str:
        """URL에서 레시피 ID 추출"""
        match = re.search(r'/recipe/(\d+)', url)
        return match.group(1) if match else ''

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """제목 추출"""
        # 먼저 title 태그에서 추출 시도
        title_tag = soup.find('title')
        if title_tag:
            title_text = title_tag.get_text(strip=True)
            if title_text and title_text != '10000recipe':
                # 유니코드 이스케이프 시퀀스를 한글로 변환
                title_text = safe_unicode_decode(title_text)
                return title_text
        
        # 기존 셀렉터들도 시도
        selectors = ['.view_tit_inner h1', '.view_tit h1', '.media-heading']
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                title_text = element.get_text(strip=True)
                # 유니코드 이스케이프 시퀀스를 한글로 변환
                title_text = safe_unicode_decode(title_text)
                return title_text
        return ''

    def _extract_author(self, soup: BeautifulSoup) -> str:
        """작성자 추출"""
        selectors = ['.view_profile_area .profile_name', '.user_info .profile_name', '.rcp_chef']
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        return ''

    def _extract_rating(self, soup: BeautifulSoup) -> Optional[float]:
        """평점 추출"""
        rating_element = soup.select_one('.rating .score')
        if rating_element:
            try:
                return float(rating_element.get_text(strip=True))
            except ValueError:
                pass
        return None

    def _extract_views(self, soup: BeautifulSoup) -> Optional[int]:
        """조회수 추출"""
        views_element = soup.select_one('.view_count')
        if views_element:
            try:
                views_text = views_element.get_text(strip=True)
                views_number = re.search(r'(\d+)', views_text)
                if views_number:
                    return int(views_number.group(1))
            except ValueError:
                pass
        return None

    def _extract_servings(self, soup: BeautifulSoup) -> str:
        """분량 추출"""
        info_text = soup.select_one('.view_tit_inner')
        if info_text:
            text = info_text.get_text()
            servings_match = re.search(r'(\d+인분|\d+~\d+인분)', text)
            if servings_match:
                return servings_match.group(1)
        return ''

    def _extract_cook_time(self, soup: BeautifulSoup) -> str:
        """조리시간 추출"""
        info_text = soup.select_one('.view_tit_inner')
        if info_text:
            text = info_text.get_text()
            time_match = re.search(r'(\d+분|\d+시간|\d+시간 \d+분|\d+분 이내)', text)
            if time_match:
                return time_match.group(1)
        return ''

    def _extract_difficulty(self, soup: BeautifulSoup) -> str:
        """난이도 추출"""
        info_text = soup.select_one('.view_tit_inner')
        if info_text:
            text = info_text.get_text()
            if '아무나' in text:
                return '아무나'
            elif '초급' in text:
                return '초급'
            elif '중급' in text:
                return '중급'
            elif '고급' in text:
                return '고급'
        return ''

    def _extract_summary(self, soup: BeautifulSoup) -> str:
        """요약/설명 추출"""
        selectors = ['.view_summary', '.rcp_summary', '.summary']
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                summary_text = element.get_text(strip=True)
                # 유니코드 이스케이프 시퀀스를 한글로 변환
                summary_text = safe_unicode_decode(summary_text)
                return summary_text
        return ''

    def _extract_tags(self, soup: BeautifulSoup) -> List[str]:
        """태그 추출"""
        tags = []
        tag_elements = soup.select('.tag_list a')
        for tag in tag_elements:
            tag_text = tag.get_text(strip=True)
            if tag_text:
                # 유니코드 이스케이프 시퀀스를 한글로 변환
                tag_text = safe_unicode_decode(tag_text)
                tags.append(tag_text)
        return tags

    def _extract_ingredients(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """재료 추출"""
        ingredients = []

        # 먼저 meta description에서 재료 추출 시도
        meta_desc = soup.find('meta', {'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            desc_content = meta_desc.get('content')
            
            # 인코딩 문제 해결: 더 강력한 인코딩 처리
            try:
                if isinstance(desc_content, str):
                    # 이미 문자열인 경우 그대로 사용
                    desc_content = desc_content
                else:
                    # 바이트인 경우 여러 인코딩 시도
                    try:
                        desc_content = desc_content.decode('utf-8')
                    except UnicodeDecodeError:
                        try:
                            desc_content = desc_content.decode('cp949')
                        except UnicodeDecodeError:
                            desc_content = desc_content.decode('utf-8', errors='ignore')
            except (UnicodeDecodeError, UnicodeEncodeError):
                # 인코딩 실패 시 원본 사용
                desc_content = str(desc_content)
            # 재료 카테고리 패턴 찾기
            import re
            # [가루류], [계란], [유지(액체류)], [토핑] 등의 패턴으로 재료 추출
            category_patterns = [
                r'\[가루류\]\s*([^[]*)',
                r'\[계란\]\s*([^[]*)',
                r'\[유지\(액체류\)\]\s*([^[]*)',
                r'\[토핑\]\s*([^[]*)',
                r'\[재료\]\s*([^[]*)',
                r'\[.*재료.*\]\s*([^[]*)'
            ]
            
            for pattern in category_patterns:
                matches = re.findall(pattern, desc_content)
                for match in matches:
                    # 쉼표로 분리된 재료들 추출
                    ingredient_list = [ing.strip() for ing in match.split(',')]
                    for ing in ingredient_list:
                        # 재료만 추출 (길이 2-50자, 조리순서가 포함된 긴 텍스트는 제외)
                        if (ing and 2 <= len(ing) <= 50 and 
                            not ing.isdigit() and 
                            not re.match(r'^\d+$', ing) and
                            not re.search(r'[가-힣]{10,}', ing)):  # 긴 한국어 문장 제외
                            # 특수 문자 제거
                            ing_clean = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', ing)
                            # 유니코드 이스케이프 시퀀스를 한글로 변환
                            ing_clean = safe_unicode_decode(ing_clean)
                            # 인코딩 문제 수정
                            ing_clean = self._fix_encoding_issues(ing_clean)
                            ingredients.append({
                                'name': ing_clean,
                                'amount': ''
                            })
            
            # 최대 15개까지만 재료로 처리
            if ingredients:
                return ingredients[:15]
            
            # 다양한 재료 패턴 지원
            ingredient_patterns = [
                r'\[재료\]',
                r'\[.*재료.*\]',
                r'\[.*도우.*\]',
                r'\[.*김밥.*재료.*\]',
                r'\[.*피자.*도우.*\]',
                r'\[.*케이크.*재료.*\]',
                r'\[.*빵.*재료.*\]',
                r'\[.*소스.*\]',
                r'\[.*양념.*\]',
                r'\[.*드레싱.*\]'
            ]
            
            for pattern in ingredient_patterns:
                if re.search(pattern, desc_content):
                    # 패턴 다음에 나오는 텍스트를 찾아서 재료 부분만 추출
                    match = re.search(pattern, desc_content)
                    if match:
                        start_idx = match.end()
                        remaining_text = desc_content[start_idx:].strip()
                        
                        # 재료 부분을 찾기 위해 조리순서가 시작되는 부분을 찾음
                        cooking_keywords = ['실온에', '넣고', '섞고', '굽고', '끓이고', '볶고', '찌고', '튀기고', '데치고', '절이고', '무치고', '올리고', '뿌리고', '발라서', '감싸서', '말아서', '썰어서', '다져서', '갈아서', '믹서에', '오븐에', '팬에', '냄비에', '총', '1개당', '너무 맛있어서']
                        
                        ingredients_text = remaining_text
                        for keyword in cooking_keywords:
                            if keyword in remaining_text:
                                keyword_idx = remaining_text.find(keyword)
                                ingredients_text = remaining_text[:keyword_idx].strip()
                                break
                        
                        # 재료들을 쉼표로 분리
                        ingredient_list = [ing.strip() for ing in ingredients_text.split(',')]
                        for ing in ingredient_list:
                            # 불필요한 문자 제거
                            ing = ing.replace(']', '').replace('[', '').strip()
                            if (ing and 2 <= len(ing) <= 30 and 
                                not ing.isdigit() and 
                                not re.match(r'^\d+$', ing)):
                                # 특수 문자 제거
                                ing_clean = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', ing)
                                # 유니코드 이스케이프 시퀀스를 한글로 변환
                                ing_clean = safe_unicode_decode(ing_clean)
                                ingredients.append({
                                    'name': ing_clean,
                                    'amount': ''
                                })
                        if ingredients:
                            return ingredients[:15]
            
            # 패턴이 없으면 meta description에서 재료 관련 키워드가 있는 부분 찾기
            if not ingredients:
                # 재료 관련 키워드가 있는 문장 찾기
                sentences = desc_content.split('.')
                for sentence in sentences:
                    if any(keyword in sentence for keyword in ['g', 'ml', 'T', 't', '큰술', '작은술', '컵', '개', '장', '줄']):
                        # 숫자+단위 패턴이 있는 문장을 재료로 간주
                        if re.search(r'\d+[가-힣]*[gmlTt]', sentence):
                            ingredient_list = [ing.strip() for ing in sentence.split(',')]
                            for ing in ingredient_list:
                                if (ing and 2 <= len(ing) <= 30 and 
                                    not ing.isdigit() and 
                                    not re.match(r'^\d+$', ing)):
                                    # 특수 문자 제거
                                    ing_clean = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', ing)
                                    # 유니코드 이스케이프 시퀀스를 한글로 변환
                                    ing_clean = safe_unicode_decode(ing_clean)
                                    ingredients.append({
                                        'name': ing_clean,
                                        'amount': ''
                                    })
                            if ingredients:
                                return ingredients[:15]

        # 기존 방식으로 재료 목록 추출
        ingredient_elements = soup.select('.rcp_m_ingredients li')
        if not ingredient_elements:
            ingredient_elements = soup.select('.ingredients_list li')

        for ing in ingredient_elements:
            name_elem = ing.select_one('.rcp_m_ingre_title')
            amount_elem = ing.select_one('.rcp_m_ingre_amounts')

            if name_elem:
                # 특수 문자 제거 (제어 문자, 비인쇄 문자)
                name_text = name_elem.get_text(strip=True)
                name_text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', name_text)
                # 유니코드 이스케이프 시퀀스를 한글로 변환
                name_text = safe_unicode_decode(name_text)
                
                amount_text = amount_elem.get_text(strip=True) if amount_elem else ''
                amount_text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', amount_text)
                # 유니코드 이스케이프 시퀀스를 한글로 변환
                amount_text = safe_unicode_decode(amount_text)
                
                ingredient = {
                    'name': name_text,
                    'amount': amount_text
                }
                ingredients.append(ingredient)

        return ingredients

    def _extract_steps(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """조리순서 추출"""
        steps = []

        # 먼저 meta description에서 조리순서 추출 시도
        meta_desc = soup.find('meta', {'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            desc_content = meta_desc.get('content')
            # 재료 부분 이후의 조리순서 추출
            import re
            # [재료] 부분을 제거하고 나머지를 조리순서로 처리
            ingredients_match = re.search(r'\[재료\]\s*([^가-힣]*?)(?=\s*[가-힣]{3,})', desc_content)
            if ingredients_match:
                after_ingredients = desc_content[ingredients_match.end():].strip()
                # 문장 단위로 분리하되, 의미있는 조리순서만 추출
                sentences = re.split(r'[.!?]\s*', after_ingredients)
                for i, sentence in enumerate(sentences, 1):
                    sentence = sentence.strip()
                    # 의미있는 조리순서만 (길이 20자 이상, 조리 관련 키워드 포함)
                    if (sentence and len(sentence) > 20 and 
                        not sentence.isdigit() and 
                        not re.match(r'^\d+$', sentence) and
                        re.search(r'(넣고|섞고|굽고|끓이고|볶고|찌고|튀기고|데치고|절이고|무치고|올리고|뿌리고|발라서|감싸서|말아서|썰어서|다져서|갈아서|믹서에|오븐에|팬에|냄비에)', sentence)):
                        # 유니코드 이스케이프 시퀀스를 한글로 변환
                        sentence = safe_unicode_decode(sentence)
                        steps.append({
                            'step': i,
                            'text': sentence,
                            'image': ''
                        })
                # 최대 15개까지만 조리순서로 처리
                if steps:
                    return steps[:15]
            
            # [재료] 패턴이 없으면 전체 description을 문장 단위로 분리
            sentences = re.split(r'[.!?]\s*', desc_content)
            for i, sentence in enumerate(sentences, 1):
                sentence = sentence.strip()
                # 의미있는 문장만 (길이 40자 이상)
                if sentence and len(sentence) > 40:
                    # 유니코드 이스케이프 시퀀스를 한글로 변환
                    sentence = safe_unicode_decode(sentence)
                    steps.append({
                        'step': i,
                        'text': sentence,
                        'image': ''
                    })
            # 최대 15개까지만 조리순서로 처리
            if steps:
                return steps[:15]
            
            # [재료] 패턴이 없으면 전체 description을 문장 단위로 분리
            sentences = re.split(r'[.!?]\s*', desc_content)
            for i, sentence in enumerate(sentences, 1):
                sentence = sentence.strip()
                # 의미있는 문장만 (길이 40자 이상)
                if sentence and len(sentence) > 40:
                    # 유니코드 이스케이프 시퀀스를 한글로 변환
                    sentence = safe_unicode_decode(sentence)
                    steps.append({
                        'step': i,
                        'text': sentence,
                        'image': ''
                    })
            # 최대 15개까지만 조리순서로 처리
            if steps:
                return steps[:15]

        # 기존 방식으로 조리순서 추출
        step_elements = soup.select('.view_step_cont .view_step')
        if not step_elements:
            step_elements = soup.select('.cooking_step')

        for i, step in enumerate(step_elements, 1):
            text_elem = step.select_one('.view_step_text')
            img_elem = step.select_one('img')

            step_data = {
                'step': i,
                'text': text_elem.get_text(strip=True) if text_elem else '',
                'image': img_elem.get('src') if img_elem else ''
            }
            steps.append(step_data)

        return steps

    def _extract_images(self, soup: BeautifulSoup, source_url: str) -> List[str]:
        """이미지 URL 추출"""
        images = []

        # 대표 이미지
        main_img = soup.select_one('.centeredcrop img')
        if not main_img:
            main_img = soup.select_one('.view_photo img')

        if main_img:
            src = main_img.get('src')
            if src:
                images.append(urljoin(source_url, src))

        # 단계별 이미지
        step_imgs = soup.select('.view_step img')
        for img in step_imgs:
            src = img.get('src')
            if src:
                images.append(urljoin(source_url, src))

        return images