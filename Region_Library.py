import streamlit as st
import requests
from streamlit_extras.colored_header import colored_header
import base64
from Frontend import add_custom_css
from pymongo.errors import DuplicateKeyError
import streamlit as st
import requests
import json
from datetime import datetime
from difflib import SequenceMatcher
from streamlit_extras.add_vertical_space import add_vertical_space
import requests
import os
from PIL import Image, ImageDraw, ImageFont
import io
import hashlib
import random
from Helper_Functions import *

# --- EMBEDDED API KEYS ---
HYPERCLOVA_API_KEY = "nv-270db94eb8bf42108110b22f551e655axCwf"
LIBRARY_API_KEY = "70b5336f9e785c681d5ff58906e6416124f80f59faa834164d297dcd8db63036"

def load_dtl_region_json():
    """Load the detailed region JSON file"""
    with open("dtl_region.json", encoding="utf-8") as f:
        dtl_region_dict = json.load(f)
    return dtl_region_dict
dtl_region_dict = load_dtl_region_json()

def extract_location_with_hyperclova(user_input, api_key, dtl_region_dict):
    """Extract and match location from user input using HyperCLOVA"""
    if not api_key:
        return find_location_fallback(user_input, dtl_region_dict)
    
    # Create location list for HyperCLOVA
    location_list = []
    for region in dtl_region_dict:
        location_list.append(f"- {region['code']}: {region['city']} {region['district']}")
    
    locations_text = "\n".join(location_list[:50])  # Limit to avoid token overflow
    
    location_prompt = f"""
사용자 입력 분석: "{user_input}"

다음은 사용 가능한 지역 코드 목록입니다:
{locations_text}
... (더 많은 지역이 있음)

사용자 입력에서 지역/위치를 찾아 정확한 지역 코드를 반환해주세요.

**지역 매칭 규칙:**
1. 정확한 구/시 이름 매칭 우선 (예: "강남구" → 11230)
2. 시/도 이름만 있으면 대표 지역 선택 (예: "서울" → 11010)
3. 영어 지역명도 인식 (예: "Seoul" → 11010, "Busan" → 21010)
4. 유명 지역/랜드마크도 매칭 (예: "홍대" → 11140 마포구)

**응답 형식:**
- 지역을 찾았으면: "REGION:지역코드"
- 지역을 찾지 못했으면: "NO_REGION"

예시:
"강남구 도서관" → REGION:11230
"서울 책 추천" → REGION:11010
"부산 미스터리 소설" → REGION:21010
"대구 역사책" → REGION:22010
"인천 아동도서" → REGION:23010
"""
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "messages": [
            {
                "role": "system",
                "content": "당신은 한국 지역 인식 전문가입니다. 사용자 입력에서 지역명을 찾아 정확한 지역 코드를 반환합니다. 반드시 지정된 응답 형식만 사용하세요."
            },
            {
                "role": "user", 
                "content": location_prompt
            }
        ],
        "maxTokens": 100,
        "temperature": 0.1,
        "topP": 0.3,
    }
    
    try:
        response = requests.post(
            "https://clovastudio.stream.ntruss.com/testapp/v1/chat-completions/HCX-003",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            location_result = result['result']['message']['content'].strip()
            
            if "REGION:" in location_result:
                region_code = location_result.split("REGION:")[-1].strip()
                region_code = region_code.replace('"', '').replace("'", '').strip()
                
                # Verify the code exists in our data
                for region in dtl_region_dict:
                    if region['code'] == region_code:
                        return region_code, f"{region['city']} {region['district']}"
                
                # If exact code not found, try fallback
                return find_location_fallback(user_input, dtl_region_dict)
            else:
                return find_location_fallback(user_input, dtl_region_dict)
        else:
            return find_location_fallback(user_input, dtl_region_dict)
            
    except Exception as e:
        st.warning(f"Location extraction failed: {e}")
        return find_location_fallback(user_input, dtl_region_dict)

def find_location_fallback(user_input, dtl_region_dict):
    """Fallback method to find location without API"""
    normalized_input = user_input.lower().strip()
    
    # Direct matching patterns
    location_patterns = {
        '서울': '11010', '강남': '11230', '강북': '11090', '강서': '11160', '강동': '11250',
        '종로': '11010', '중구': '11020', '용산': '11030', '성동': '11040', '광진': '11050',
        '동대문': '11060', '중랑': '11070', '성북': '11080', '도봉': '11100', '노원': '11110',
        '은평': '11120', '서대문': '11130', '마포': '11140', '양천': '11150', '구로': '11170',
        '금천': '11180', '영등포': '11190', '동작': '11200', '관악': '11210', '서초': '11220',
        '송파': '11240', '홍대': '11140', '신촌': '11140', '이태원': '11030',
        
        '부산': '21010', '대구': '22010', '인천': '23010', '광주': '24010', 
        '대전': '25010', '울산': '26010', '세종': '29010',
        
        'seoul': '11010', 'busan': '21010', 'daegu': '22010', 'incheon': '23010',
        'gwangju': '24010', 'daejeon': '25010', 'ulsan': '26010'
    }
    
    # Check for direct matches
    for location, code in location_patterns.items():
        if location in normalized_input:
            # Find the region info
            for region in dtl_region_dict:
                if region['code'] == code:
                    return code, f"{region['city']} {region['district']}"
    
    # If no match found
    return None, None

def get_regional_popular_books(region_code, auth_key, page_no=1, page_size=20):
    """Get popular books by region using the Library API"""
    url = "http://data4library.kr/api/loanItemSrchByLib"
    params = {
        "authKey": auth_key,
        "dtl_region": region_code,
        "pageNo": page_no,
        "pageSize": page_size,
        "format": "json"
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if "response" in data and "docs" in data["response"]:
                docs = data["response"]["docs"]
                if isinstance(docs, dict):
                    docs = [docs]
                
                books = []
                for doc in docs:
                    book_data = doc.get("doc", doc)
                    book_info = {
                        "bookname": book_data.get("bookname", "Unknown Title"),
                        "authors": book_data.get("authors", "Unknown Author"),
                        "publisher": book_data.get("publisher", "Unknown Publisher"),
                        "publication_year": book_data.get("publication_year", "Unknown Year"),
                        "isbn13": book_data.get("isbn13", ""),
                        "loan_count": int(book_data.get("loan_count", 0)),
                        "bookImageURL": book_data.get("bookImageURL", ""),
                        "class_nm": book_data.get("class_nm", "")
                    }
                    books.append(book_info)
                
                return sorted(books, key=lambda x: x["loan_count"], reverse=True)
        return []
    except Exception as e:
        st.error(f"Error fetching regional books: {e}")
        return []

def get_libraries_with_book_availability(isbn, region_code, auth_key):
    """Get libraries in a region that have a specific book"""
    url = "http://data4library.kr/api/libSrchByBook"
    params = {
        "authKey": auth_key,
        "isbn": isbn,
        "dtl_region": region_code,
        "format": "json"
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if "response" in data and "libs" in data["response"]:
                libs = data["response"]["libs"]
                if isinstance(libs, dict):
                    libs = [libs]
                
                libraries = []
                for lib in libs:
                    library_info = {
                        "libCode": lib.get("libCode", ""),
                        "libName": lib.get("libName", "Unknown Library"),
                        "address": lib.get("address", "No address"),
                        "tel": lib.get("tel", "No phone"),
                        "homepage": lib.get("homepage", ""),
                        "operatingTime": lib.get("operatingTime", "Check library"),
                        "closed": lib.get("closed", "Check library")
                    }
                    libraries.append(library_info)
                
                return libraries
        return []
    except Exception as e:
        st.error(f"Error checking book availability: {e}")
        return []

def check_my_library_availability(username, user_region_code):
    """Check availability of user's liked books in their region"""
    liked_books = get_liked_books(username)
    availability_results = []
    
    for book in liked_books:
        isbn = book.get('isbn13') or book.get('isbn')
        if isbn and user_region_code:
            libraries = get_libraries_with_book_availability(isbn, user_region_code, LIBRARY_API_KEY)
            availability_results.append({
                "book": book,
                "available_libraries": libraries,
                "availability_count": len(libraries)
            })
    
    return availability_results

def enhanced_search_with_region(user_query, api_key):
    """Enhanced search that handles both location and book preferences"""
    if not api_key:
        st.warning("HyperCLOVA API key required for regional search")
        return None, None, None, None
    
    # First, try to extract location
    region_code, region_name = extract_location_with_hyperclova(user_query, api_key, dtl_region_dict)
    
    # Then, extract book preferences (author/genre)
    book_result = get_dtl_kdc_code(user_query, api_key)
    
    return region_code, region_name, book_result[0], book_result[1]

def process_regional_search(user_query, api_key):
    """Process user query for regional book search"""
    region_code, region_name, search_type, search_value = enhanced_search_with_region(user_query, api_key)
    
    if region_code:
        st.success(f"📍 **Location detected:** {region_name}")
        
        if search_type == "AUTHOR":
            st.info(f"👤 **Searching for:** Books by {search_value} in {region_name}")
            # Get books by author, then filter by region availability
            author_books = get_books_by_author(search_value, LIBRARY_API_KEY)
            regional_books = []
            for book in author_books[:10]:  # Limit to top 10 for performance
                isbn = book.get('isbn13')
                if isbn:
                    libraries = get_libraries_with_book_availability(isbn, region_code, LIBRARY_API_KEY)
                    if libraries:
                        book['available_libraries'] = len(libraries)
                        regional_books.append(book)
            return regional_books, region_name
            
        elif search_type and search_value:
            st.info(f"📚 **Searching for:** {search_value} books in {region_name}")
            # Get regional popular books and filter by genre
            regional_books = get_regional_popular_books(region_code, LIBRARY_API_KEY)
            return regional_books, region_name
        else:
            st.info(f"📖 **Showing:** Popular books in {region_name}")
            regional_books = get_regional_popular_books(region_code, LIBRARY_API_KEY)
            return regional_books, region_name
    else:
        st.warning("⚠️ No region detected. Please specify a location like '서울 강남구', '부산', or 'Seoul'")
        return [], None

def display_regional_search_interface():
    """Display the regional search interface"""
    st.header("🗺️ 지역별 인기도서 검색")
    st.markdown("지역과 선호하는 책 종류를 입력하세요. 예: '강남구 미스터리 소설', '서울 김영하', '부산 철학책'")
    
    user_query = st.text_input(
        "검색어 입력:",
        placeholder="예: 강남구 추리소설, 서울 무라카미 하루키, 부산 역사책"
    )
    
    if st.button("🔍 지역별 도서 검색") and user_query:
        with st.spinner("지역 및 도서 정보를 분석 중..."):
            books, region_name = process_regional_search(user_query, HYPERCLOVA_API_KEY)
            
            if books and region_name:
                st.success(f"📚 {region_name}에서 {len(books)}권의 도서를 찾았습니다!")
                
                for i, book in enumerate(books):
                    display_regional_book_card(book, i, region_name)
            elif region_name:
                st.warning(f"{region_name}에서 해당 조건의 도서를 찾을 수 없습니다.")
            else:
                st.error("검색 조건을 다시 확인해주세요.")

def display_regional_book_card(book, index, region_name):
    """Display book card with regional availability info"""
    cols = st.columns([1, 3])
    
    with cols[0]:
        image_url = book.get("bookImageURL", "")
        if image_url:
            st.image(image_url, width=120)
        else:
            st.markdown("""
            <div style="width: 100px; height: 150px; background: linear-gradient(135deg, #2c3040, #363c4e); 
                        display: flex; align-items: center; justify-content: center; border-radius: 5px;">
                <span style="color: #b3b3cc;">No Image</span>
            </div>
            """, unsafe_allow_html=True)
    
    with cols[1]:
        title = book.get('bookname', '제목 없음')
        authors = book.get('authors', '저자 없음')
        publisher = book.get('publisher', '출판사 없음')
        year = book.get('publication_year', '연도 없음')
        loan_count = book.get('loan_count', 0)
        isbn13 = book.get('isbn13', 'unknown')
        available_libraries = book.get('available_libraries', 0)
        
        st.markdown(f"""
        <div style="padding-left: 10px; margin-top: 0;">
            <div style="font-size: 1.2em; font-weight: bold; color: #333; margin-bottom: 8px;">{title}</div>
            <div style="margin-bottom: 4px;"><strong>저자:</strong> {authors}</div>
            <div style="margin-bottom: 4px;"><strong>출판사:</strong> {publisher}</div>
            <div style="margin-bottom: 4px;"><strong>출간년도:</strong> {year}</div>
            <div style="margin-bottom: 4px;"><strong>대출 횟수:</strong> {loan_count}</div>
            <div style="margin-bottom: 8px; color: #007bff;"><strong>📍 {region_name} 내 보유 도서관:</strong> {available_libraries}곳</div>
        </div>
        """, unsafe_allow_html=True)
        
        btn_col1, btn_col2, btn_col3 = st.columns([2, 2, 1])
        
        with btn_col1:
            if st.button(f"도서관 위치 보기", key=f"libraries_{isbn13}_{index}"):
                show_library_locations(isbn13, st.session_state.user_region)
        
        with btn_col2:
            if st.button(f"이 책에 대해 더 알아보기", key=f"details_{isbn13}_{index}"):
                st.session_state.selected_book = book
                st.session_state.app_stage = "discuss_book"
                st.rerun()
        
        with btn_col3:
            # Like button functionality
            liked_books = get_liked_books(st.session_state.username)
            already_liked = any((b.get("isbn13") or b.get("isbn")) == isbn13 for b in liked_books)
            if already_liked:
                st.button("❤️", key=f"liked_{isbn13}_{index}", help="내 서재에 추가됨", disabled=True)
            else:
                if st.button("❤️", key=f"like_{isbn13}_{index}", help="내 서재에 추가"):
                    book_data = book.copy()
                    book_data['isbn13'] = isbn13
                    like_book_for_user(st.session_state.username, book_data)
                    st.success("서재에 추가되었습니다!")
                    st.rerun()
    
    st.markdown("<hr style='margin: 10px 0; border: none; border-top: 1px solid #000;'>", unsafe_allow_html=True)

def show_library_locations(isbn, region_code):
    """Show libraries that have the book in the region"""
    libraries = get_libraries_with_book_availability(isbn, region_code, LIBRARY_API_KEY)
    
    if libraries:
        st.subheader("📍 도서 보유 도서관")
        for lib in libraries:
            with st.expander(f"🏛️ {lib['libName']}"):
                st.write(f"**주소:** {lib['address']}")
                st.write(f"**전화:** {lib['tel']}")
                st.write(f"**운영시간:** {lib['operatingTime']}")
                st.write(f"**휴관일:** {lib['closed']}")
                if lib['homepage']:
                    st.markdown(f"[🌐 홈페이지]({lib['homepage']})")
    else:
        st.warning("해당 지역에서 이 도서를 보유한 도서관을 찾을 수 없습니다.")

def display_my_library_availability():
    """Display availability check for user's library"""
    st.header("📚 내 서재 도서 이용 가능 여부")
    
    if not hasattr(st.session_state, 'user_region') or not st.session_state.user_region:
        st.warning("먼저 지역을 설정해주세요.")
        return
    
    with st.spinner("내 서재 도서의 이용 가능 여부를 확인 중..."):
        availability_results = check_my_library_availability(
            st.session_state.username, 
            st.session_state.user_region
        )
    
    if availability_results:
        available_books = [r for r in availability_results if r['availability_count'] > 0]
        unavailable_books = [r for r in availability_results if r['availability_count'] == 0]
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("이용 가능한 도서", len(available_books))
        with col2:
            st.metric("이용 불가능한 도서", len(unavailable_books))
        
        if available_books:
            st.subheader("✅ 이용 가능한 도서")
            for result in available_books:
                book = result['book']
                count = result['availability_count']
                title = book.get('bookname', '제목 없음')
                authors = book.get('authors', '저자 없음')
                
                with st.expander(f"📖 {title} - {count}곳에서 이용 가능"):
                    st.write(f"**저자:** {authors}")
                    st.write(f"**보유 도서관 수:** {count}곳")
                    
                    if st.button("도서관 목록 보기", key=f"show_libs_{book.get('isbn13', 'unknown')}"):
                        show_library_locations(book.get('isbn13'), st.session_state.user_region)
        
        if unavailable_books:
            st.subheader("❌ 현재 지역에서 이용 불가능한 도서")
            for result in unavailable_books:
                book = result['book']
                title = book.get('bookname', '제목 없음')
                authors = book.get('authors', '저자 없음')
                st.write(f"📚 **{title}** - {authors}")
    else:
        st.info("내 서재에 저장된 도서가 없습니다.")

def get_books_by_author_regional(author_name, auth_key, region_code=None, page_no=1, page_size=10):
    """Get books by specific author, optionally filtered by region availability"""
    # First get books by author
    books = get_books_by_author(author_name, auth_key, page_no, page_size)
    
    # If region is specified, filter by regional availability
    if region_code and books:
        regional_books = []
        for book in books:
            isbn = book.get('isbn13')
            if isbn:
                # Check if book is available in the region
                libraries = get_libraries_with_book_availability(isbn, region_code, auth_key)
                if libraries:
                    book['available_libraries'] = len(libraries)
                    book['regional_availability'] = True
                    regional_books.append(book)
        
        if regional_books:
            st.success(f"Found {len(regional_books)} books by {author_name} available in your region!")
            return regional_books
        else:
            st.warning(f"No books by {author_name} found in your region. Showing all books by this author.")
            return books
    
    return books

# Updated function to get books by genre WITH regional filtering  
def get_books_by_dtl_kdc_regional(dtl_kdc_code, auth_key, region_code=None, page_no=1, page_size=10):
    """Get books using DTL KDC code, optionally filtered by region"""
    if region_code:
        # Use regional API endpoint for better results
        url = "http://data4library.kr/api/loanItemSrchByLib"
        params = {
            "authKey": auth_key,
            "dtl_region": region_code,
            "dtl_kdc": dtl_kdc_code,
            "pageNo": page_no,
            "pageSize": page_size,
            "format": "json"
        }
    else:
        # Use general API endpoint
        url = "http://data4library.kr/api/loanItemSrch"
        params = {
            "authKey": auth_key,
            "startDt": "2000-01-01",
            "endDt": datetime.now().strftime("%Y-%m-%d"),
            "format": "json",
            "pageNo": page_no,
            "pageSize": page_size,
            "dtl_kdc": dtl_kdc_code
        }
    
    try:
        r = requests.get(url, params=params)
        if r.status_code == 200:
            response_data = r.json()
            
            if "response" in response_data:
                docs = response_data["response"].get("docs", [])
                
                if isinstance(docs, dict):
                    docs = [docs]
                elif not isinstance(docs, list):
                    return []
                
                books = []
                for doc in docs:
                    if "doc" in doc:
                        book_data = doc["doc"]
                    else:
                        book_data = doc
                    
                    book_info = {
                        "bookname": book_data.get("bookname", "Unknown Title"),
                        "authors": book_data.get("authors", "Unknown Author"),
                        "publisher": book_data.get("publisher", "Unknown Publisher"),
                        "publication_year": book_data.get("publication_year", "Unknown Year"),
                        "isbn13": book_data.get("isbn13", ""),
                        "loan_count": int(book_data.get("loan_count", 0)),
                        "bookImageURL": book_data.get("bookImageURL", ""),
                        "regional_context": bool(region_code)
                    }
                    books.append(book_info)
                
                books = sorted(books, key=lambda x: x["loan_count"], reverse=True)
                return books
            else:
                return []
    except Exception as e:
        st.error(f"Error processing API response: {e}")
        return []
    
    return []

# Updated main search function that handles BOTH classification AND regional context
def enhanced_search_with_classification_and_region(user_query, api_key, region_code=None):
    """Main search function that handles author/genre detection AND regional filtering"""
    
    # Get classification result with regional context
    result = get_dtl_kdc_code(user_query, api_key, region_code)
    
    if result[0] == "AUTHOR":
        author_name = result[1]
        # Get books by author with regional filtering
        books = get_books_by_author_regional(author_name, LIBRARY_API_KEY, region_code)
        return books, "author", author_name
        
    elif result[0] and result[0] != "AUTHOR":
        dtl_kdc_code = result[0]
        category_name = result[1]
        # Get books by genre with regional filtering
        books = get_books_by_dtl_kdc_regional(dtl_kdc_code, LIBRARY_API_KEY, region_code)
        return books, "genre", category_name
    
    else:
        return [], "none", None
