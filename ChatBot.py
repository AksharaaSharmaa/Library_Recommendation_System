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

# --- EMBEDDED API KEYS ---
HYPERCLOVA_API_KEY = "nv-270db94eb8bf42108110b22f551e655axCwf"
LIBRARY_API_KEY = "70b5336f9e785c681d5ff58906e6416124f80f59faa834164d297dcd8db63036"

add_custom_css()

def display_liked_book_card(book, index):
    """Display a liked book card with a remove (cross) button using MongoDB."""
    info = book if isinstance(book, dict) else book.get("doc", {})
    with st.container():
        st.markdown('<div class="book-card" style="border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 8px;">', unsafe_allow_html=True)
        cols = st.columns([1, 3])
        with cols[0]:
            image_url = info.get("bookImageURL", "")
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
            title = info.get('bookname') or info.get('bookName', '제목 없음')
            authors = info.get('authors') or info.get('author', '저자 없음')
            publisher = info.get('publisher', '출판사 없음')
            year = info.get('publication_year') or info.get('publicationYear', '연도 없음')
            loan_count = info.get('loan_count') or info.get('loanCount', 0)
            isbn13 = info.get('isbn13') or info.get('isbn', 'unknown')
            st.markdown(f"""
            <div style="padding-left: 10px;">
                <div style="font-size: 1.2em; font-weight: bold; color: #333; margin-bottom: 8px;">{title}</div>
                <div style="margin-bottom: 4px;"><strong>Author:</strong> {authors}</div>
                <div style="margin-bottom: 4px;"><strong>Publisher:</strong> {publisher}</div>
                <div style="margin-bottom: 4px;"><strong>Year:</strong> {year}</div>
                <div style="margin-bottom: 8px;"><strong>Loan Count:</strong> {loan_count}</div>
            </div>
            """, unsafe_allow_html=True)
            btn_col1, btn_col2 = st.columns([3, 1])
            with btn_col1:
                if st.button(f"Tell me more about this book", key=f"details_liked_{isbn13}_{index}"):
                    st.session_state.selected_book = info
                    st.session_state.app_stage = "discuss_book"
                    st.rerun()
            with btn_col2:
                # Remove (cross) button
                if st.button("❌", key=f"remove_{isbn13}_{index}", help="Remove from My Library"):
                    unlike_book_for_user(st.session_state.username, isbn13)
                    st.success("Removed from your library!")
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


# Add after MongoDB client initialization
def get_user_library_collection():
    client = st.session_state.db_client  # Already set in login.py
    db = client["Login_Credentials"]
    return db["user_libraries"]

def like_book_for_user(username, book_info):
    user_library = get_user_library_collection()
    isbn = book_info.get("isbn13")
    if not isbn:
        return False
    # First, try to add to existing document
    result = user_library.update_one(
        {"username": username},
        {"$addToSet": {"liked_books": book_info}}
    )
    # If no document was modified, create one with an empty array and add the book
    if result.matched_count == 0:
        user_library.update_one(
            {"username": username},
            {"$set": {"liked_books": [book_info], "username": username}},
            upsert=True
        )
    return True

def get_liked_books(username):
    user_library = get_user_library_collection()
    doc = user_library.find_one({"username": username})
    return doc.get("liked_books", []) if doc else []

def unlike_book_for_user(username, isbn):
    user_library = get_user_library_collection()
    user_library.update_one(
        {"username": username},
        {"$pull": {"liked_books": {"isbn13": isbn}}}
    )

def display_message(message):
    if message["role"] != "system":
        if message["role"] == "assistant":
            avatar = "AI"
            avatar_class = "assistant-avatar"
            message_class = "assistant-message"
            
            if "한국어 답변:" in message["content"]:
                parts = message["content"].split("한국어 답변:", 1)
                english_part = parts[0].strip()
                korean_part = parts[1].strip() if len(parts) > 1 else ""
                
                st.markdown(f"""
                <div class="message-with-avatar">
                    <div class="message-avatar {avatar_class}">{avatar}</div>
                    <div class="chat-message {message_class}">
                        {english_part}
                        <div class="korean-text">
                            <span class="korean-label">한국어 답변:</span><br>
                            {korean_part}
                        </div>
                        <div class="message-timestamp">Now</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="message-with-avatar">
                    <div class="message-avatar {avatar_class}">{avatar}</div>
                    <div class="chat-message {message_class}">
                        {message["content"]}
                        <div class="message-timestamp">Now</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            avatar = "You"
            avatar_class = "user-avatar"
            message_class = "user-message"
            
            st.markdown(f"""
            <div class="message-with-avatar">
                <div class="message-avatar {avatar_class}">{avatar}</div>
                <div class="chat-message {message_class}">
                    {message["content"]}
                    <div class="message-timestamp">Now</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

def call_hyperclova_api(messages, api_key):
    """Helper function to call HyperCLOVA API with correct headers"""
    try:
        endpoint = "https://clovastudio.stream.ntruss.com/testapp/v1/chat-completions/HCX-003"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messages": messages,
            "maxTokens": 1024,
            "temperature": 0.7,
            "topP": 0.8,
        }
        
        response = requests.post(endpoint, headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            return result['result']['message']['content']
        else:
            st.error(f"Error connecting to HyperCLOVA API: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error connecting to HyperCLOVA API: {e}")
        return None

def display_book_card(book, index):
    """Display a book card with like and image functionality, using MongoDB for liked books."""
    # Handle both old format (direct keys) and new format (nested in 'doc')
    if "doc" in book:
        info = book["doc"]
    else:
        info = book

    with st.container():
        st.markdown('<div class="book-card" style="border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 8px;">', unsafe_allow_html=True)
        cols = st.columns([1, 3])
        with cols[0]:
            image_url = info.get("bookImageURL", "")
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
            title = info.get('bookname') or info.get('bookName', '제목 없음')
            authors = info.get('authors') or info.get('author', '저자 없음')
            publisher = info.get('publisher', '출판사 없음')
            year = info.get('publication_year') or info.get('publicationYear', '연도 없음')
            loan_count = info.get('loan_count') or info.get('loanCount', 0)
            isbn13 = info.get('isbn13') or info.get('isbn', 'unknown')

            st.markdown(f"""
            <div style="padding-left: 10px;">
                <div style="font-size: 1.2em; font-weight: bold; color: #333; margin-bottom: 8px;">{title}</div>
                <div style="margin-bottom: 4px;"><strong>저자:</strong> {authors}</div>
                <div style="margin-bottom: 4px;"><strong>출판사:</strong> {publisher}</div>
                <div style="margin-bottom: 4px;"><strong>출간년도:</strong> {year}</div>
                <div style="margin-bottom: 8px;"><strong>대출 횟수:</strong> {loan_count}</div>
            </div>
            """, unsafe_allow_html=True)

            btn_col1, btn_col2 = st.columns([2, 1])
            with btn_col1:
                if st.button(f"이 책에 대해 더 알아보기", key=f"details_{isbn13}_{index}"):
                    st.session_state.selected_book = info
                    st.session_state.app_stage = "discuss_book"
                    st.rerun()
            with btn_col2:
                # Check if this book is already liked
                liked_books = get_liked_books(st.session_state.username)
                already_liked = any((b.get("isbn13") or b.get("isbn")) == isbn13 for b in liked_books)
                if already_liked:
                    st.button("❤️", key=f"liked_{isbn13}_{index}", help="내 서재에 추가됨", disabled=True)
                else:
                    if st.button("❤️", key=f"like_{isbn13}_{index}", help="내 서재에 추가"):
                        # Store the book in MongoDB with consistent ISBN field
                        book_data = info.copy()
                        book_data['isbn13'] = isbn13
                        like_book_for_user(st.session_state.username, book_data)
                        st.success("서재에 추가되었습니다!")
                        st.rerun()
                        
# --- Load JSON files ---
@st.cache_resource
def load_dtl_kdc_json():
    """Load only the detailed KDC JSON file"""
    with open("dtl_kdc.json", encoding="utf-8") as f:
        dtl_kdc_dict = json.load(f)
    return dtl_kdc_dict

dtl_kdc_dict = load_dtl_kdc_json()

# --- Enhanced HyperCLOVA API Integration ---
def extract_keywords_with_hyperclova(user_input, api_key):
    """Extract and detect if the user is asking for books by a specific author or a genre"""
    if not api_key:
        return detect_author_or_genre_fallback(user_input)
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Enhanced multi-language author detection prompt
    author_detection_prompt = f"""
사용자 입력 분석: "{user_input}"

다음 기준으로 요청 유형을 정확히 판단해주세요:

**작가 검색 패턴:**
- 한국 작가: "박경리", "김영하", "무라카미 하루키", "황석영 작품", "이문열 소설"
- 외국 작가: "Stephen King", "J.K. Rowling", "Agatha Christie", "셰익스피어", "헤밍웨이"
- 작가 관련 표현: "~의 작품", "~가 쓴", "~저자", "~작가의 책", "books by ~"

**장르/주제 검색 패턴:**
- 문학 장르: "로맨스", "추리소설", "판타지", "SF", "호러", "스릴러"
- 주제 분야: "역사책", "철학서", "과학도서", "경제학", "자기계발"
- 일반적 표현: "~에 관한 책", "~분야", "~관련 도서"

**판단 규칙:**
1. 사람의 이름(성+이름 또는 단일명)이 포함 → 작가 검색
2. 문학 장르나 학문 분야명만 포함 → 장르 검색
3. 애매한 경우 문맥으로 판단

응답 형식:
- 작가 검색: "AUTHOR:작가이름"
- 장르 검색: "GENRE"

예시:
"무라카미 하루키 신작" → AUTHOR:무라카미 하루키
"미스터리 소설 추천해줘" → GENRE
"스티븐 킹" → AUTHOR:스티븐 킹
"철학 관련 서적" → GENRE
"해리포터 작가 책" → AUTHOR:J.K. Rowling
"""
    
    data_detection = {
        "messages": [
            {
                "role": "system",
                "content": "당신은 도서 검색 요청을 정확히 분석하는 전문가입니다. 사용자가 특정 작가의 책을 찾는지, 아니면 특정 장르나 주제의 책을 찾는지 명확하게 구분해야 합니다. 작가 이름이 포함되면 작가 검색, 장르나 주제만 언급되면 장르 검색으로 판단합니다."
            },
            {
                "role": "user", 
                "content": author_detection_prompt
            }
        ],
        "maxTokens": 150,
        "temperature": 0.1,
        "topP": 0.3,
    }
    
    try:
        # API call for request type detection
        response = requests.post(
            "https://clovastudio.stream.ntruss.com/testapp/v1/chat-completions/HCX-003",
            headers=headers,
            json=data_detection,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            detection_result = result['result']['message']['content'].strip()
            
            # Parse the response more robustly
            if "AUTHOR:" in detection_result:
                author_name = detection_result.split("AUTHOR:")[-1].strip()
                # Clean up the author name
                author_name = author_name.replace('"', '').replace("'", '').strip()
                if author_name:
                    return ("AUTHOR", author_name)
            elif "GENRE" in detection_result:
                return ("GENRE", user_input)
            
            # If response format is unexpected, try fallback
            return detect_author_or_genre_fallback(user_input)
        else:
            st.warning(f"HyperCLOVA API error: {response.status_code}")
            return detect_author_or_genre_fallback(user_input)
            
    except Exception as e:
        st.warning(f"Request type detection failed: {e}")
        return detect_author_or_genre_fallback(user_input)

def detect_author_or_genre_fallback(user_input):
    """Enhanced fallback method to detect if input is author name or genre without API"""
    import re
    
    # Normalize input for better matching
    normalized_input = user_input.lower().strip()
    
    # Common author-related keywords in multiple languages
    author_keywords = [
        '작가', '저자', '작품', '소설가', '시인', '문학가',
        'author', 'writer', 'books by', 'novels by', 'works by',
        '가 쓴', '의 작품', '의 책', '의 소설'
    ]
    
    # Common genre keywords
    genre_keywords = [
        '소설', '로맨스', '추리', '미스터리', '판타지', 'sf', '공상과학',
        '역사', '철학', '경제', '과학', '자기계발', '에세이', '시집',
        'romance', 'mystery', 'fantasy', 'thriller', 'horror', 
        'philosophy', 'history', 'economics', 'science'
    ]
    
    # Check for explicit author indicators
    for keyword in author_keywords:
        if keyword in normalized_input:
            # Extract potential author name by removing keywords
            clean_name = user_input
            for remove_word in ['작가', '저자', '작품', '소설', '책', 'author', 'writer', 'books by']:
                clean_name = re.sub(rf'\b{re.escape(remove_word)}\b', '', clean_name, flags=re.IGNORECASE)
            clean_name = clean_name.strip()
            if clean_name:
                return ("AUTHOR", clean_name)
    
    # Enhanced Korean name detection
    korean_surnames = ['김', '박', '이', '최', '정', '강', '조', '윤', '장', '임', '한', '오', '서', '신', '권', '황', '안', '송', '류', '전']
    has_korean_surname = any(surname in user_input for surname in korean_surnames)
    
    # Check for Western name patterns (Title case words)
    words = user_input.split()
    has_western_name_pattern = len(words) >= 2 and any(word[0].isupper() and len(word) > 1 for word in words)
    
    # Famous author name patterns (partial matching)
    famous_authors = [
        '하루키', '헤밍웨이', '톨스토이', '도스토옙스키', '카프카', '조이스',
        'king', 'rowling', 'christie', 'shakespeare', 'hemingway'
    ]
    has_famous_author = any(author.lower() in normalized_input for author in famous_authors)
    
    # If it looks like a person's name
    if has_korean_surname or has_western_name_pattern or has_famous_author:
        # But check if it's clearly a genre request
        genre_indicators = ['추천', '소개', '목록', '리스트', '종류', '분야', '관련']
        is_genre_request = any(indicator in normalized_input for indicator in genre_indicators) and \
                          any(genre in normalized_input for genre in genre_keywords)
        
        if not is_genre_request:
            return ("AUTHOR", user_input.strip())
    
    # Check for clear genre indicators
    if any(genre in normalized_input for genre in genre_keywords):
        return ("GENRE", user_input)
    
    # Default fallback logic
    # If input is very short and looks like a name, assume author
    if len(words) <= 3 and (has_korean_surname or has_western_name_pattern):
        return ("AUTHOR", user_input.strip())
    
    # Otherwise, assume genre request
    return ("GENRE", user_input)

def extract_genre_keywords(user_input, api_key, dtl_kdc_dict, headers):
    """Original genre-based keyword extraction logic"""
    # First attempt - exact keyword matching
    categories_list = []
    for code, label in dtl_kdc_dict.items():
        categories_list.append(f"- {code}: {label}")
    
    categories_text = "\n".join(categories_list)
    
    # First prompt - look for exact keywords
    prompt_exact = f"""
다음은 전체 도서 분류 코드 목록입니다:
{categories_text}

사용자 입력: "{user_input}"

위의 전체 목록에서 사용자 입력과 정확히 일치하는 키워드나 분류명을 찾아주세요.
예를 들어:
- "영문학" → 영미문학 관련 코드
- "역사" → 역사 관련 코드  
- "소설" → 소설 관련 코드
- "철학" → 철학 관련 코드

정확한 일치가 있으면 해당 코드번호만 반환하세요. 정확한 일치가 없으면 "NO_EXACT_MATCH"를 반환하세요.
"""
    
    data_exact = {
        "messages": [
            {
                "role": "system",
                "content": "당신은 도서 분류 전문가입니다. 전체 분류 목록에서 정확한 키워드 일치를 찾아 코드번호만 반환합니다."
            },
            {
                "role": "user", 
                "content": prompt_exact
            }
        ],
        "maxTokens": 50,
        "temperature": 0.1,
        "topP": 0.5,
    }
    
    try:
        # First API call - exact matching
        response = requests.post(
            "https://clovastudio.stream.ntruss.com/testapp/v1/chat-completions/HCX-003",
            headers=headers,
            json=data_exact,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            extracted_code = result['result']['message']['content'].strip()
            extracted_code = extracted_code.replace('"', '').replace("'", '').strip()
            
            # If exact match found and exists in dictionary
            if extracted_code != "NO_EXACT_MATCH" and extracted_code in dtl_kdc_dict:
                return extracted_code, dtl_kdc_dict[extracted_code]
            
            # If no exact match, try second attempt with similarity
            prompt_similar = f"""
사용자 입력: "{user_input}"

다음은 사용할 수 있는 도서 분류 코드들입니다:
{categories_text}

정확한 일치가 없으므로, 사용자 입력의 의미와 가장 유사한 분류 코드를 찾아주세요.
의미상 연관성을 고려하여 가장 적절한 코드를 선택하세요.

예를 들어:
- "책 추천" → 일반적인 문학이나 총류 관련 코드
- "경제 관련" → 경제학 관련 코드
- "건강" → 의학이나 건강 관련 코드
- "요리" → 요리, 음식 관련 코드

가장 유사한 코드번호만 반환하세요.
"""
            
            data_similar = {
                "messages": [
                    {
                        "role": "system",
                        "content": "당신은 도서 분류 전문가입니다. 의미적 유사성을 바탕으로 가장 적절한 분류 코드를 찾아 반환합니다."
                    },
                    {
                        "role": "user", 
                        "content": prompt_similar
                    }
                ],
                "maxTokens": 50,
                "temperature": 0.3,
                "topP": 0.7,
            }
            
            # Second API call - similarity matching
            response2 = requests.post(
                "https://clovastudio.stream.ntruss.com/testapp/v1/chat-completions/HCX-003",
                headers=headers,
                json=data_similar,
                timeout=30
            )
            
            if response2.status_code == 200:
                result2 = response2.json()
                similar_code = result2['result']['message']['content'].strip()
                similar_code = similar_code.replace('"', '').replace("'", '').strip()
                
                if similar_code in dtl_kdc_dict:
                    return similar_code, dtl_kdc_dict[similar_code]
                else:
                    # Try to find partial matches
                    return find_best_dtl_code_fallback(user_input, dtl_kdc_dict, similar_code)
            else:
                return find_best_dtl_code_fallback(user_input, dtl_kdc_dict)
        else:
            st.warning(f"HyperCLOVA API error: {response.status_code}")
            return find_best_dtl_code_fallback(user_input, dtl_kdc_dict)
            
    except Exception as e:
        st.warning(f"Keyword extraction failed: {e}")
        return find_best_dtl_code_fallback(user_input, dtl_kdc_dict)

# --- New function to get books by author ---
def get_books_by_author(author_name, auth_key, page_no=1, page_size=10):
    """Get books by specific author using Library API"""
    url = "http://data4library.kr/api/srchBooks"
    params = {
        "authKey": auth_key,
        "author": author_name,
        "pageNo": page_no,
        "pageSize": page_size,
        "format": "json"
    }
    
    try:
        r = requests.get(url, params=params)
        if r.status_code == 200:
            response_data = r.json()
            
            # Check if response has the expected structure
            if "response" in response_data and "docs" in response_data["response"]:
                docs = response_data["response"]["docs"]
                
                # Handle case where docs might be a single dict instead of list
                if isinstance(docs, dict):
                    docs = [docs]
                elif not isinstance(docs, list):
                    return []
                
                # Extract and clean book data
                books = []
                for doc in docs:
                    # Handle nested 'doc' structure if it exists
                    if "doc" in doc:
                        book_data = doc["doc"]
                    else:
                        book_data = doc
                    
                    # Extract book information with fallback values
                    book_info = {
                        "bookname": book_data.get("bookname", book_data.get("bookName", "Unknown Title")),
                        "authors": book_data.get("authors", book_data.get("author", "Unknown Author")),
                        "publisher": book_data.get("publisher", "Unknown Publisher"),
                        "publication_year": book_data.get("publication_year", book_data.get("publicationYear", "Unknown Year")),
                        "isbn13": book_data.get("isbn13", book_data.get("isbn", "")),
                        "loan_count": int(book_data.get("loan_count", book_data.get("loanCount", 0))),
                        "bookImageURL": book_data.get("bookImageURL", ""),
                        "bookDtlUrl": book_data.get("bookDtlUrl", "")
                    }
                    books.append(book_info)
                
                # Sort by publication year (descending) and then by loan count
                books = sorted(books, key=lambda x: (x.get("publication_year", "0"), x["loan_count"]), reverse=True)
                return books
            else:
                st.error(f"No books found for author: {author_name}")
                return []
    except requests.exceptions.RequestException as e:
        st.error(f"API request failed: {e}")
        return []
    except json.JSONDecodeError as e:
        st.error(f"Failed to parse API response: {e}")
        return []
    except Exception as e:
        st.error(f"Error processing API response: {e}")
        return []
    
    return []
    
def find_best_dtl_code_fallback(user_query, dtl_kdc_dict, ai_suggested_code=None):
    """Fallback method to find the best matching DTL KDC code"""
    best_score = 0
    best_code = None
    best_label = ""
    
    # If AI suggested a code but it wasn't exact, try to find similar codes
    if ai_suggested_code:
        for code, label in dtl_kdc_dict.items():
            if ai_suggested_code in code or code in ai_suggested_code:
                return code, label
    
    # Original similarity matching
    for code, label in dtl_kdc_dict.items():
        # Check similarity with the label
        score = SequenceMatcher(None, user_query.lower(), label.lower()).ratio()
        
        # Also check if any word from user query is in the label
        user_words = user_query.lower().split()
        for word in user_words:
            if len(word) > 1 and word in label.lower():
                score += 0.3  # Boost score for word matches
        
        if score > best_score:
            best_score = score
            best_code = code
            best_label = label
    
    return best_code, best_label if best_score > 0.2 else (None, None)

def get_dtl_kdc_code(user_query, api_key=None):
    """Enhanced DTL KDC code detection with better author/genre classification"""
    if api_key:
        try:
            # Use HyperCLOVA for classification
            result = extract_keywords_with_hyperclova(user_query, api_key)
            
            # Handle author requests
            if isinstance(result, tuple) and len(result) == 2 and result[0] == "AUTHOR":
                author_name = result[1]
                st.info(f"🔍 Searching for books by author: **{author_name}**")
                return "AUTHOR", author_name
            
            # Handle genre requests
            elif isinstance(result, tuple) and len(result) == 2 and result[0] == "GENRE":
                user_input = result[1]
                st.info(f"📚 Searching for books in genre/topic: **{user_input}**")
                
                # Use the existing genre extraction logic
                code, label = extract_genre_keywords(user_input, api_key, dtl_kdc_dict, {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                })
                
                if code and label:
                    st.success(f"✅ Found category: **{label}** (Code: {code})")
                    return code, label
                else:
                    st.warning("⚠️ Could not find a matching category. Please try being more specific with genres like 'romance novels', 'mystery books', or 'philosophy books'.")
                    return None, None
            
            # Fallback if HyperCLOVA result is unexpected
            else:
                st.info("🔄 HyperCLOVA response unclear, using fallback analysis...")
                return handle_fallback_classification(user_query)
                
        except Exception as e:
            st.warning(f"❌ HyperCLOVA processing failed: {e}. Using fallback search...")
            return handle_fallback_classification(user_query)
    
    # No API key available
    else:
        st.info("🔍 Using fallback search without AI assistance...")
        return handle_fallback_classification(user_query)

def handle_fallback_classification(user_query):
    """Handle classification when HyperCLOVA is not available or fails"""
    fallback_result = detect_author_or_genre_fallback(user_query)
    
    if fallback_result[0] == "AUTHOR":
        author_name = fallback_result[1]
        st.info(f"👤 Detected author search: **{author_name}**")
        return "AUTHOR", author_name
    else:
        # Try genre matching with dtl_kdc_dict
        code, label = find_best_dtl_code_fallback(user_query, dtl_kdc_dict)
        if code and label:
            st.success(f"📖 Found category: **{label}** (Code: {code})")
            return code, label
        else:
            st.warning("⚠️ Could not find a matching category. Please try being more specific with:\n"
                      "- **Author names**: 'Stephen King', '무라카미 하루키', 'J.K. Rowling'\n"
                      "- **Genres**: 'romance novels', 'mystery books', 'philosophy', 'history'")
            return None, None

            
# --- Query library API for books by DTL KDC code ---
def get_books_by_dtl_kdc(dtl_kdc_code, auth_key, page_no=1, page_size=10):
    """Get books using DTL KDC code"""
    url = "http://data4library.kr/api/loanItemSrch"
    params = {
        "authKey": auth_key,
        "startDt": "2000-01-01",
        "endDt": datetime.now().strftime("%Y-%m-%d"),
        "format": "json",
        "pageNo": page_no,
        "pageSize": page_size,
        "dtl_kdc": dtl_kdc_code  # Use dtl_kdc parameter
    }
    
    try:
        r = requests.get(url, params=params)
        if r.status_code == 200:
            response_data = r.json()
            
            # Check if response has the expected structure
            if "response" in response_data:
                docs = response_data["response"].get("docs", [])
                
                # Handle case where docs might be a single dict instead of list
                if isinstance(docs, dict):
                    docs = [docs]
                elif not isinstance(docs, list):
                    return []
                
                # Extract and clean book data
                books = []
                for doc in docs:
                    # Handle nested 'doc' structure if it exists
                    if "doc" in doc:
                        book_data = doc["doc"]
                    else:
                        book_data = doc
                    
                    # Extract book information with fallback values
                    book_info = {
                        "bookname": book_data.get("bookname", book_data.get("bookName", "Unknown Title")),
                        "authors": book_data.get("authors", book_data.get("author", "Unknown Author")),
                        "publisher": book_data.get("publisher", "Unknown Publisher"),
                        "publication_year": book_data.get("publication_year", book_data.get("publicationYear", "Unknown Year")),
                        "isbn13": book_data.get("isbn13", book_data.get("isbn", "")),
                        "loan_count": int(book_data.get("loan_count", book_data.get("loanCount", 0))),
                        "bookImageURL": book_data.get("bookImageURL", "")
                    }
                    books.append(book_info)
                
                # Sort by loan count (descending)
                books = sorted(books, key=lambda x: x["loan_count"], reverse=True)
                return books
            else:
                st.error(f"Unexpected API response structure: {response_data}")
                return []
    except requests.exceptions.RequestException as e:
        st.error(f"API request failed: {e}")
        return []
    except json.JSONDecodeError as e:
        st.error(f"Failed to parse API response: {e}")
        return []
    except Exception as e:
        st.error(f"Error processing API response: {e}")
        return []
    
    return []

# --- Sidebar (as provided) ---
import os

def run_location_script(location):
    """Function to run the location-specific Python script"""
    script_name = f"{location.lower()}.py"
    if os.path.exists(script_name):
        try:
            # Read and execute the script content within the current app context
            with open(script_name, "r", encoding="utf-8") as f:
                code = f.read()
            exec(code, globals())
        except Exception as e:
            st.error(f"Error running {script_name}: {str(e)}")
    else:
        st.error(f"Script {script_name} not found!")

def setup_sidebar():
    """Setup sidebar with navigation buttons"""
    with st.sidebar:
        st.markdown("### 📚 Navigation")
        
        # My Library button
        if st.button("📜 좋아하는 책들 (My Library)", use_container_width=True):
            st.session_state.app_stage = "show_liked_books"
            st.rerun()
        
        # Reading Schedule button - Navigate to calendar page
        if st.button("📅 내 독서 일정 (My Reading Schedule)", use_container_width=True):
            st.session_state.app_stage = "calendar"
            st.rerun()
        
        # Back to Book Discovery button (show only when not on main page)
        if st.session_state.get("app_stage") not in ["welcome", "awaiting_user_input", "process_user_input"]:
            if st.button("🔍 책 찾기 (Book Discovery)", use_container_width=True):
                st.session_state.app_stage = "welcome"
                st.rerun()
        
        st.markdown("---")
        
        # Reset/Restart button
        if st.button("✨ 다시 시작하기 (Restart)", use_container_width=True):
            # Clear all session state related to the main app
            st.session_state.messages = [{
                "role": "system",
                "content": (
                    "You are a friendly AI assistant specializing in book recommendations. "
                    "Start by greeting and asking about favorite books/authors/genres/age. "
                    "For EVERY response, answer in BOTH English and Korean. "
                    "First provide complete English answer, then '한국어 답변:' with Korean translation."
                )
            }]
            st.session_state.app_stage = "welcome"
            st.session_state.books_data = []
            st.session_state.user_genre = ""
            st.session_state.user_age = ""
            st.session_state.selected_book = None
            st.session_state.showing_books = False
            st.session_state.book_discussion_messages = []
            st.session_state.book_intro_shown = False
            st.rerun()
        
        st.markdown("---")
        
        # API Configuration Section
        st.markdown("### ⚙️ API Settings")
        
        # HyperCLOVA API Key
        api_key_input = st.text_input(
            "HyperCLOVA API Key:", 
            value=st.session_state.get("api_key", ""),
            type="password",
            help="Enter your HyperCLOVA API key for AI responses"
        )
        
        if api_key_input != st.session_state.get("api_key", ""):
            st.session_state.api_key = api_key_input
        
        # Library API Key
        library_api_key_input = st.text_input(
            "Library API Key:", 
            value=st.session_state.get("library_api_key", ""),
            type="password",
            help="Enter your Korean Library API key"
        )
        
        if library_api_key_input != st.session_state.get("library_api_key", ""):
            st.session_state.library_api_key = library_api_key_input
        
        # API Status indicators
        st.markdown("#### API Status:")
        hyperclova_status = "🟢 Connected" if st.session_state.get("api_key") else "🔴 Not Set"
        library_status = "🟢 Connected" if st.session_state.get("library_api_key") else "🔴 Not Set"
        
        st.markdown(f"**HyperCLOVA:** {hyperclova_status}")
        st.markdown(f"**Library API:** {library_status}")
        
        st.markdown("---")
        
        # User Info Section (if logged in)
        if hasattr(st.session_state, 'username') and st.session_state.username:
            st.markdown("### 👤 User Info")
            st.markdown(f"**Logged in as:** {st.session_state.username}")
            
            # User statistics
            try:
                liked_books_count = len(get_liked_books(st.session_state.username))
                st.markdown(f"**Books in Library:** {liked_books_count}")
                
                # Reading schedule info
                if hasattr(st.session_state, 'reading_schedule') and st.session_state.reading_schedule:
                    schedule_count = len(st.session_state.reading_schedule)
                    st.markdown(f"**Scheduled Books:** {schedule_count}")
            except Exception as e:
                st.markdown("**Books in Library:** Error loading")
        
        st.markdown("---")
        
        # Footer with attribution
        st.markdown("""
        <div style="text-align: center; margin-top: 30px; padding: 15px; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    border-radius: 10px; color: white;">
            <h4 style="margin: 0; font-size: 0.9rem;">Powered by</h4>
            <p style="margin: 5px 0 0 0; font-size: 0.8rem; opacity: 0.9;">
                HyperCLOVA X 🤝 한국 도서관 API
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # App version info
        st.markdown("""
        <div style="text-align: center; margin-top: 10px;">
            <p style="color: #888; font-size: 0.7rem;">
                Book Wanderer v2.0 📚✨
            </p>
        </div>
        """, unsafe_allow_html=True)

        
# --- Process follow-up questions with HyperCLOVA ---
def process_followup_with_hyperclova(user_input, api_key):
    """Process follow-up questions using HyperCLOVA API"""
    if not api_key:
        return "Please provide your HyperCLOVA API key in the sidebar to get detailed responses.\n\n한국어 답변: 자세한 답변을 받으려면 사이드바에서 HyperCLOVA API 키를 제공해 주세요."
    
    # Create context from previous messages
    conversation_context = ""
    recent_messages = st.session_state.messages[-5:]  # Get last 5 messages for context
    for msg in recent_messages:
        if msg["role"] != "system":
            conversation_context += f"{msg['role']}: {msg['content']}\n"
    
    prompt = f"""
이전 대화 내용:
{conversation_context}

사용자의 새로운 질문: "{user_input}"

위의 맥락을 고려하여 사용자의 질문에 대해 도움이 되는 답변을 해주세요. 
만약 새로운 도서 추천을 요청하는 것 같다면, 구체적인 장르나 주제를 제시해주세요.

답변은 영어와 한국어 모두로 제공하되, 먼저 영어로 완전한 답변을 하고, 
그 다음 "한국어 답변:" 이후에 한국어 번역을 제공하세요.
"""
    
    messages = [
        {
            "role": "system",
            "content": "당신은 도서 추천 전문가입니다. 사용자와의 대화 맥락을 이해하고 도움이 되는 답변을 제공합니다. 항상 영어와 한국어로 답변하세요."
        },
        {
            "role": "user", 
            "content": prompt
        }
    ]
    
    return call_hyperclova_api(messages, api_key)

def generate_book_introduction(book, api_key):
    """Generate an introduction about the book when first selected"""
    title = book.get('bookname') or book.get('bookName', 'Unknown Title')
    authors = book.get('authors') or book.get('author', 'Unknown Author')
    publisher = book.get('publisher', 'Unknown Publisher')
    year = book.get('publication_year') or book.get('publicationYear', 'Unknown Year')
    loan_count = book.get('loan_count') or book.get('loanCount', 0)
    
    if not api_key:
        return f"Let's discuss '{title}' by {authors}! This book was published by {publisher} in {year} and has been borrowed {loan_count} times, showing its popularity. What would you like to know about this book - its themes, plot, writing style, or would you like similar recommendations?\n\n한국어 답변: {authors}의 '{title}'에 대해 이야기해 봅시다! 이 책은 {year}년에 {publisher}에서 출간되었으며 {loan_count}번 대출되어 인기를 보여줍니다. 이 책에 대해 무엇을 알고 싶으신가요 - 주제, 줄거리, 문체, 아니면 비슷한 추천을 원하시나요?"
    
    book_context = f"Book: {title} by {authors}, published by {publisher} in {year}, with {loan_count} loans"
    
    messages = [
        {
            "role": "system",
            "content": "You are a knowledgeable book expert. For EVERY response, answer in BOTH English and Korean. First provide complete English answer, then '한국어 답변:' with Korean translation. Provide an engaging introduction about the book."
        },
        {
            "role": "user", 
            "content": f"Please provide an engaging introduction about this book: {book_context}. Talk about what makes this book interesting, its potential themes, and invite the user to ask questions about it. Keep it conversational and welcoming."
        }
    ]
    
    response = call_hyperclova_api(messages, api_key)
    if response:
        return response
    else:
        # Fallback if API fails
        return f"Let's explore '{title}' by {authors}! This book from {publisher} ({year}) has {loan_count} loans, indicating its appeal to readers. I'm here to discuss anything about this book - from plot details to thematic analysis. What aspect interests you most?\n\n한국어 답변: {authors}의 '{title}'을 탐험해 봅시다! {publisher}({year})의 이 책은 {loan_count}번의 대출로 독자들에게 어필하고 있음을 보여줍니다. 줄거리 세부사항부터 주제 분석까지 이 책에 대한 모든 것을 논의할 준비가 되어 있습니다. 어떤 측면에 가장 관심이 있으신가요?"

def process_book_question(book, question, api_key, conversation_history):
    """Process specific questions about a book using HyperCLOVA with improved context handling"""
    if not api_key:
        return "Please provide your HyperCLOVA API key in the sidebar to get detailed responses about this book.\n\n한국어 답변: 이 책에 대한 자세한 답변을 받으려면 사이드바에서 HyperCLOVA API 키를 제공해 주세요."
    
    title = book.get('bookname') or book.get('bookName', 'Unknown Title')
    authors = book.get('authors') or book.get('author', 'Unknown Author')
    publisher = book.get('publisher', 'Unknown Publisher')
    year = book.get('publication_year') or book.get('publicationYear', 'Unknown Year')
    loan_count = book.get('loan_count') or book.get('loanCount', 0)
    
    # Build comprehensive conversation context
    context_string = ""
    if conversation_history:
        # Include more context - last 6 messages for better continuity
        recent_history = conversation_history[-6:] if len(conversation_history) >= 6 else conversation_history
        for msg in recent_history:
            role = "사용자" if msg["role"] == "user" else "AI"
            context_string += f"{role}: {msg['content']}\n\n"
    
    book_info = f"제목: '{title}', 저자: {authors}, 출판사: {publisher}, 출간년도: {year}, 인기도: {loan_count}회 대출"
    
    # Enhanced prompt with better context integration
    enhanced_prompt = f"""
현재 논의 중인 도서 정보:
{book_info}

이전 대화 내용:
{context_string}

사용자의 새로운 질문: "{question}"

위의 도서와 이전 대화 맥락을 모두 고려하여 사용자의 질문에 대해 상세하고 도움이 되는 답변을 제공해주세요.

답변 지침:
1. 이전 대화의 맥락을 참고하여 연속성 있는 답변을 제공하세요
2. 책의 내용, 주제, 등장인물, 문체, 문화적 배경 등에 대해 구체적으로 설명하세요
3. 필요시 유사한 책 추천도 포함하세요
4. 영어로 완전한 답변을 먼저 제공하고, 그 다음 "한국어 답변:" 이후에 한국어 번역을 제공하세요

답변은 상세하고 통찰력 있게 작성해주세요.
"""
    
    messages = [
        {
            "role": "system",
            "content": f"당신은 '{title}' by {authors}에 대해 논의하는 지식이 풍부한 도서 전문가입니다. 이전 대화의 맥락을 기억하고 연속성 있는 답변을 제공합니다. 모든 답변은 영어와 한국어 모두로 제공하며, 먼저 영어로 완전한 답변을 하고 그 다음 '한국어 답변:'으로 한국어 번역을 제공합니다. 도서의 주제, 줄거리 요소, 등장인물 분석, 문체, 문화적 맥락, 유사한 도서 추천 등을 포함한 상세하고 통찰력 있는 정보를 제공합니다."
        },
        {
            "role": "user",
            "content": enhanced_prompt
        }
    ]
    
    try:
        response = call_hyperclova_api(messages, api_key)
        if response:
            return response
        else:
            return f"I'd be happy to continue our discussion about '{title}', but I'm having trouble connecting to the AI service right now. Could you try asking your question again?\n\n한국어 답변: '{title}'에 대한 논의를 계속하고 싶지만 지금 AI 서비스에 연결하는 데 문제가 있습니다. 질문을 다시 해보시겠어요?"
    except Exception as e:
        st.error(f"Error processing question: {e}")
        return f"I encountered an error while processing your question about '{title}'. Please try rephrasing your question or check your API connection.\n\n한국어 답변: '{title}'에 대한 질문을 처리하는 중 오류가 발생했습니다. 질문을 다시 표현하거나 API 연결을 확인해 주세요."

def main():
    # --- Initialize all session state variables before use ---
    if "api_key" not in st.session_state:
        st.session_state.api_key = HYPERCLOVA_API_KEY if 'HYPERCLOVA_API_KEY' in globals() else ""
    if "library_api_key" not in st.session_state:
        st.session_state.library_api_key = LIBRARY_API_KEY if 'LIBRARY_API_KEY' in globals() else ""
    if "messages" not in st.session_state:
        st.session_state.messages = [{
            "role": "system",
            "content": (
                "You are a friendly AI assistant specializing in book recommendations. "
                "Start by greeting and asking about favorite books/authors/genres/age. "
                "For EVERY response, answer in BOTH English and Korean. "
                "First provide complete English answer, then '한국어 답변:' with Korean translation."
            )
        }]
    if "app_stage" not in st.session_state:
        st.session_state.app_stage = "welcome"
    if "books_data" not in st.session_state:
        st.session_state.books_data = []
    if "user_genre" not in st.session_state:
        st.session_state.user_genre = ""
    if "user_age" not in st.session_state:
        st.session_state.user_age = ""
    if "selected_book" not in st.session_state:
        st.session_state.selected_book = None
    if "showing_books" not in st.session_state:
        st.session_state.showing_books = False
    if "book_discussion_messages" not in st.session_state:
        st.session_state.book_discussion_messages = []
    if "book_intro_shown" not in st.session_state:
        st.session_state.book_intro_shown = False
    if "reading_schedule" not in st.session_state:
        st.session_state.reading_schedule = []

    # Setup sidebar first
    setup_sidebar()

    # Main app header
    st.markdown("""
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); 
                   -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
                   font-size: 3rem; margin-bottom: 10px;">
            📚 Book Wanderer / 책방랑자
        </h1>
        <p style="font-size: 1.2rem; color: #666; margin-bottom: 20px;">
            Discover your next favorite read with AI assistance in English and Korean
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    # Check if user is logged in for certain features
    user_logged_in = hasattr(st.session_state, 'username') and st.session_state.username

    # --- Chat history (only show non-book-specific messages in main flow) ---
    for msg in st.session_state.messages:
        if msg["role"] != "system" and not msg.get("book_context"):
            display_message(msg)

    # --- App stages ---
    if st.session_state.app_stage == "welcome":
        # Welcome message with improved styling
        welcome_message = {
            "role": "assistant",
            "content": (
                "Hello! Welcome to Book Wanderer! 🌟 Tell me about your favorite books, authors, "
                "genres, or age group. You can describe what you're looking for in natural language. "
                "I'm here to help you discover amazing books!\n\n"
                "한국어 답변: 안녕하세요! 책방랑자에 오신 것을 환영합니다! 🌟 좋아하는 책, 작가, "
                "장르 또는 연령대에 대해 말씀해 주세요. 자연스러운 언어로 원하는 것을 설명해 주시면 됩니다. "
                "멋진 책들을 발견하실 수 있도록 도와드리겠습니다!"
            )
        }
        st.session_state.messages.append(welcome_message)
        st.session_state.app_stage = "awaiting_user_input"
        st.rerun()

    elif st.session_state.app_stage == "awaiting_user_input":
        # User input section with improved styling
        st.markdown("### 🔍 What kind of books are you looking for?")
        
        col1, col2 = st.columns([4, 1])
        with col1:
            user_input = st.text_input(
                "", 
                placeholder="e.g., 'mystery novels by Korean authors' or '자기계발서'",
                key="user_open_input"
            )
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🚀 보내다", key="send_open_input", use_container_width=True):
                if user_input:
                    st.session_state.messages.append({"role": "user", "content": user_input})
                    st.session_state.app_stage = "process_user_input"
                    st.rerun()

    elif st.session_state.app_stage == "process_user_input":
        user_input = st.session_state.messages[-1]["content"]
        
        # Get API keys from session state
        hyperclova_key = st.session_state.get("api_key", "")
        library_key = st.session_state.get("library_api_key", "")
    
        # Detect if it's author or genre request
        dtl_code, dtl_label = get_dtl_kdc_code(user_input, hyperclova_key)
        
        if dtl_code and library_key:
            if dtl_code == "AUTHOR":
                # Author-based search
                author_name = dtl_label
                books = get_books_by_author(author_name, library_key, page_no=1, page_size=20)
                
                if books:
                    st.session_state.books_data = books
                    
                    # Generate AI response about the author's books
                    if hyperclova_key:
                        ai_response = call_hyperclova_api([
                            {"role": "system", "content": "You are a helpful book recommendation assistant. For EVERY response, answer in BOTH English and Korean. First provide complete English answer, then '한국어 답변:' with Korean translation."},
                            {"role": "user", "content": f"I found {len(books)} books by {author_name}. Tell me about this author and encourage me to explore their works."}
                        ], hyperclova_key)
                        
                        if ai_response:
                            st.session_state.messages.append({"role": "assistant", "content": ai_response})
                        else:
                            st.session_state.messages.append({
                                "role": "assistant", 
                                "content": f"Excellent! I found {len(books)} books by {author_name}. This author has created diverse works that showcase their unique writing style and perspective. Take a look at their collection below!\n\n한국어 답변: 훌륭합니다! {author_name}의 책 {len(books)}권을 찾았습니다. 이 작가는 독특한 글쓰기 스타일과 관점을 보여주는 다양한 작품을 창작했습니다. 아래에서 그들의 컬렉션을 살펴보세요!"
                            })
                    
                    st.session_state.app_stage = "show_recommendations"
                else:
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": f"I couldn't find books by '{author_name}' in the library database. Could you try with a different spelling or another author? You can also try genre-based searches like 'mystery novels' or 'romance books'.\n\n한국어 답변: 도서관 데이터베이스에서 '{author_name}'의 책을 찾을 수 없었습니다. 다른 철자나 다른 작가로 시도해 보시겠어요? '추리소설'이나 '로맨스 소설' 같은 장르 기반 검색도 시도해 볼 수 있습니다."
                    })
                    st.session_state.app_stage = "awaiting_user_input"
            else:
                # Genre-based search (existing functionality)
                books = get_books_by_dtl_kdc(dtl_code, library_key, page_no=1, page_size=20)
                
                if books:
                    st.session_state.books_data = books
                    
                    # Generate AI response about the recommendations using HyperCLOVA
                    if hyperclova_key:
                        ai_response = call_hyperclova_api([
                            {"role": "system", "content": "You are a helpful book recommendation assistant. For EVERY response, answer in BOTH English and Korean. First provide complete English answer, then '한국어 답변:' with Korean translation."},
                            {"role": "user", "content": f"I found {len(books)} books in the {dtl_label} category. Tell me about this category and encourage me to explore these recommendations."}
                        ], hyperclova_key)
                        
                        if ai_response:
                            st.session_state.messages.append({"role": "assistant", "content": ai_response})
                        else:
                            st.session_state.messages.append({
                                "role": "assistant", 
                                "content": f"Great! I found {len(books)} excellent books in the {dtl_label} category. These recommendations are based on popularity and should match your interests perfectly. Take a look at the books below!\n\n한국어 답변: 좋습니다! {dtl_label} 카테고리에서 {len(books)}권의 훌륭한 책을 찾았습니다. 이 추천은 인기도를 바탕으로 하며 당신의 관심사와 완벽하게 일치할 것입니다. 아래 책들을 살펴보세요!"
                            })
                    
                    st.session_state.app_stage = "show_recommendations"
                else:
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": "I couldn't find books in that specific category. Could you try describing your preferences differently? For example, mention specific genres like 'mystery novels', 'self-help books', or 'Korean literature', or try searching by author name.\n\n한국어 답변: 해당 카테고리에서 책을 찾을 수 없었습니다. 다른 방식으로 선호도를 설명해 주시겠어요? 예를 들어 '추리소설', '자기계발서', '한국문학'과 같은 구체적인 장르를 언급하거나 작가 이름으로 검색해 보세요."
                    })
                    st.session_state.app_stage = "awaiting_user_input"
        else:
            missing_items = []
            if not dtl_code:
                missing_items.append("category/author matching")
            if not library_key:
                missing_items.append("Library API key")
            
            error_msg = f"Unable to process your request due to: {', '.join(missing_items)}. Please check your API configuration in the sidebar."
            korean_msg = f"다음 이유로 요청을 처리할 수 없습니다: {', '.join(missing_items)}. 사이드바에서 API 설정을 확인해 주세요."
            
            st.session_state.messages.append({
                "role": "assistant", 
                "content": f"{error_msg}\n\n한국어 답변: {korean_msg}"
            })
            st.session_state.app_stage = "awaiting_user_input"
        
        st.rerun()

    elif st.session_state.app_stage == "show_recommendations":
        add_vertical_space(2)
        st.markdown("""
        <h3 style='text-align:center; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); 
                   -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
            📖 Recommended Books for You
        </h3>
        """, unsafe_allow_html=True)
        
        # Display books
        for i, book in enumerate(st.session_state.books_data[:10]):  # Show top 10 books
            display_book_card(book, i)
        
        # Chat input for follow-up questions
        st.markdown("### 💬 Ask me anything about these books:")
        col1, col2 = st.columns([4, 1])
        with col1:
            user_followup = st.text_input(
                "", 
                placeholder="e.g., 'Tell me more about the first book' or '다른 추천도 있나요?'",
                key="followup_input"
            )
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🚀 보내다", key="send_followup", use_container_width=True):
                if user_followup:
                    st.session_state.messages.append({"role": "user", "content": user_followup})
                    
                    # Check if user wants new recommendations
                    if any(keyword in user_followup.lower() for keyword in ['different', 'other', 'new', 'more', '다른', '새로운', '더']):
                        st.session_state.app_stage = "process_user_input"
                    else:
                        # Process as follow-up question using HyperCLOVA
                        hyperclova_key = st.session_state.get("api_key", "")
                        response = process_followup_with_hyperclova(user_followup, hyperclova_key)
                        if response:
                            st.session_state.messages.append({"role": "assistant", "content": response})
                        else:
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": "I'd be happy to help you with more information about these books or other recommendations. What specific aspect would you like to know more about?\n\n한국어 답변: 이 책들에 대한 더 많은 정보나 다른 추천에 대해 기꺼이 도와드리겠습니다. 어떤 구체적인 측면에 대해 더 알고 싶으신가요?"
                            })
                    st.rerun()

    elif st.session_state.app_stage == "discuss_book":
        if st.session_state.selected_book:
            book = st.session_state.selected_book
            
            # Display selected book details
            add_vertical_space(2)
            st.markdown("""
            <h3 style='text-align:center; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); 
                       -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
                📖 Let's Talk About This Book
            </h3>
            """, unsafe_allow_html=True)
            
            with st.container():
                cols = st.columns([1, 2])
                with cols[0]:
                    image_url = book.get("bookImageURL", "")
                    if image_url:
                        st.image(image_url, width=200)
                    else:
                        st.markdown("""
                        <div style="width: 150px; height: 200px; background: linear-gradient(135deg, #2c3040, #363c4e); 
                                    display: flex; align-items: center; justify-content: center; border-radius: 8px;">
                            <span style="color: #b3b3cc;">No Image</span>
                        </div>
                        """, unsafe_allow_html=True)
                
                with cols[1]:
                    title = book.get('bookname') or book.get('bookName', 'Unknown Title')
                    authors = book.get('authors') or book.get('author', 'Unknown Author')
                    publisher = book.get('publisher', 'Unknown Publisher')
                    year = book.get('publication_year') or book.get('publicationYear', 'Unknown Year')
                    loan_count = book.get('loan_count') or book.get('loanCount', 0)
                    
                    st.markdown(f"""
                    <div style="padding: 20px; background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); 
                                border-radius: 10px; margin: 10px 0;">
                        <h2 style="color: #2c3040; margin-bottom: 15px;">{title}</h2>
                        <div style="margin-bottom: 8px;"><strong>📝 Author:</strong> {authors}</div>
                        <div style="margin-bottom: 8px;"><strong>🏢 Publisher:</strong> {publisher}</div>
                        <div style="margin-bottom: 8px;"><strong>📅 Publication Year:</strong> {year}</div>
                        <div style="margin-bottom: 8px;"><strong>📊 Popularity:</strong> {loan_count} loans</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Show introduction message when first entering book discussion
            if not st.session_state.book_intro_shown:
                hyperclova_key = st.session_state.get("api_key", "")
                intro_message = generate_book_introduction(book, hyperclova_key)
                st.session_state.book_discussion_messages.append({
                    "role": "assistant", 
                    "content": intro_message
                })
                st.session_state.book_intro_shown = True
                st.rerun()
            
            # Display chat history for this specific book
            for msg in st.session_state.book_discussion_messages:
                display_message(msg)
            
            # Chat input for book discussion with improved key management
            st.markdown("### 💭 Ask me anything about this book:")
            col1, col2 = st.columns([4, 1])
            with col1:
                book_question = st.text_input(
                    "", 
                    placeholder="e.g., 'What's the main theme?' or '이 책의 줄거리는?'",
                    key=f"book_discussion_input_{len(st.session_state.book_discussion_messages)}"
                )
            
            with col2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🚀 보내다", key=f"ask_about_book_{len(st.session_state.book_discussion_messages)}", use_container_width=True):
                    if book_question:
                        # Add user message to book discussion
                        user_msg = {"role": "user", "content": book_question}
                        st.session_state.book_discussion_messages.append(user_msg)
                        
                        # Generate AI response about the book using HyperCLOVA
                        hyperclova_key = st.session_state.get("api_key", "")
                        ai_response = process_book_question(
                            book, 
                            book_question, 
                            hyperclova_key,
                            st.session_state.book_discussion_messages
                        )
                        
                        assistant_msg = {"role": "assistant", "content": ai_response}
                        st.session_state.book_discussion_messages.append(assistant_msg)
                        
                        st.rerun()
            
            # Back to recommendations button
            if st.button("← Back to Recommendations", key="back_to_recs"):
                # Clear book discussion messages and intro flag when going back
                st.session_state.book_discussion_messages = []
                st.session_state.book_intro_shown = False
                st.session_state.app_stage = "show_recommendations"
                st.rerun()

    elif st.session_state.app_stage == "show_liked_books":
        add_vertical_space(2)
        st.markdown("""
        <h3 style='text-align:center; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); 
                   -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
            ❤️ My Library
        </h3>
        """, unsafe_allow_html=True)
        
        if user_logged_in:
            liked_books = get_liked_books(st.session_state.username)
            
            if liked_books:
                st.markdown(f"📚 You have **{len(liked_books)}** books in your library:")
                for i, book in enumerate(liked_books):
                    display_liked_book_card(book, i)
                
                # Quick actions
                st.markdown("### 🚀 Quick Actions:")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📅 Create Reading Schedule", use_container_width=True):
                        try:
                            run_location_script("calendar")
                        except Exception as e:
                            st.error(f"Error loading reading schedule: {str(e)}")
                
                with col2:
                    if st.button("🔍 Discover More Books", use_container_width=True):
                        st.session_state.app_stage = "welcome"
                        st.rerun()
            else:
                st.markdown("""
                <div style="text-align: center; padding: 40px; background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); 
                            border-radius: 15px; margin: 20px 0;">
                    <h4>📚 Your library is empty</h4>
                    <p>Start exploring books to add them to your collection!</p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("🔍 Discover Books", use_container_width=True):
                    st.session_state.app_stage = "welcome"
                    st.rerun()
        else:
            st.error("🔐 Please ensure you are logged in to view your library.")
        
        # Back to main app button
        if st.button("← Back to Book Discovery", key="back_to_main"):
            st.session_state.app_stage = "show_recommendations" if st.session_state.books_data else "welcome"
            st.rerun()

    # Add some spacing at the bottom
    add_vertical_space(3)
