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
    """Display a book card with like functionality, using MongoDB for liked books."""
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
                <div style="margin-bottom: 4px;"><strong>Author:</strong> {authors}</div>
                <div style="margin-bottom: 4px;"><strong>Publisher:</strong> {publisher}</div>
                <div style="margin-bottom: 4px;"><strong>Year:</strong> {year}</div>
                <div style="margin-bottom: 8px;"><strong>Loan Count:</strong> {loan_count}</div>
            </div>
            """, unsafe_allow_html=True)

            btn_col1, btn_col2 = st.columns([3, 1])
            with btn_col1:
                if st.button(f"Tell me more about this book", key=f"details_{isbn13}_{index}"):
                    st.session_state.selected_book = info
                    st.session_state.app_stage = "discuss_book"
                    st.rerun()
            with btn_col2:
                # Check if this book is already liked
                liked_books = get_liked_books(st.session_state.username)
                already_liked = any((b.get("isbn13") or b.get("isbn")) == isbn13 for b in liked_books)
                if already_liked:
                    st.button("❤️", key=f"liked_{isbn13}_{index}", help="Already in My Library", disabled=True)
                else:
                    if st.button("❤️", key=f"like_{isbn13}_{index}", help="Add to My Library"):
                        # Store the book in MongoDB with consistent ISBN field
                        book_data = info.copy()
                        book_data['isbn13'] = isbn13
                        like_book_for_user(st.session_state.username, book_data)
                        st.success("Added to your library!")
                        st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- Load JSON files ---
@st.cache_resource
def load_dtl_kdc_json():
    """Load only the detailed KDC JSON file"""
    with open("dtl_kdc.json", encoding="utf-8") as f:
        dtl_kdc_dict = json.load(f)
    return dtl_kdc_dict

dtl_kdc_dict = load_dtl_kdc_json()

# --- Enhanced HyperCLOVA API Integration ---
def extract_keywords_with_hyperclova(user_input, api_key, dtl_kdc_dict):
    """Extract and match the most appropriate DTL KDC code using HyperCLOVA"""
    if not api_key:
        return find_best_dtl_code_fallback(user_input, dtl_kdc_dict)
    
    # Create a list of available categories for the AI to reference
    categories_list = []
    for code, label in list(dtl_kdc_dict.items())[:50]:  # Show first 50 as examples
        categories_list.append(f"- {code}: {label}")
    
    categories_text = "\n".join(categories_list)
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""
사용자의 요청에서 가장 적합한 도서 분류 코드를 찾아주세요.

사용자 입력: "{user_input}"

다음은 사용할 수 있는 도서 분류 코드들의 예시입니다:
{categories_text}

지시사항:
1. 사용자의 입력을 분석하여 가장 관련성이 높은 분류 코드를 찾으세요
2. 만약 정확한 일치가 없다면, 의미상 가장 가까운 코드를 선택하세요
3. 예를 들어:
   - "영문학 책 추천해 줘" → "영미문학" 관련 코드
   - "역사책 읽고 싶어" → "역사" 관련 코드
   - "소설 추천" → "소설" 관련 코드
   - "자기계발서" → "자기계발" 관련 코드

답변 형식: 오직 코드번호만 반환해주세요 (예: "843" 또는"911.05")
코드번호가 확실하지 않으면 가장 가까운 의미의 코드를 선택하세요.
"""
    
    data = {
        "messages": [
            {
                "role": "system",
                "content": "당신은 도서 분류 전문가입니다. 사용자의 요청을 분석하여 가장 적합한 DTL KDC 코드를 찾아 반환합니다. 반드시 코드번호만 반환하세요."
            },
            {
                "role": "user", 
                "content": prompt
            }
        ],
        "maxTokens": 50,
        "temperature": 0.3,
        "topP": 0.7,
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
            extracted_code = result['result']['message']['content'].strip()
            
            # Clean the response to get just the code
            extracted_code = extracted_code.replace('"', '').replace("'", '').strip()
            
            # Verify if the extracted code exists in our dictionary
            if extracted_code in dtl_kdc_dict:
                return extracted_code, dtl_kdc_dict[extracted_code]
            else:
                # If exact code not found, try to find partial matches or similar codes
                return find_best_dtl_code_fallback(user_input, dtl_kdc_dict, extracted_code)
                
        else:
            st.warning(f"HyperCLOVA API error: {response.status_code}")
            return find_best_dtl_code_fallback(user_input, dtl_kdc_dict)
            
    except Exception as e:
        st.warning(f"Keyword extraction failed: {e}")
        return find_best_dtl_code_fallback(user_input, dtl_kdc_dict)

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
    """Get DTL KDC code using HyperCLOVA or fallback method"""
    if api_key:
        try:
            code, label = extract_keywords_with_hyperclova(user_query, api_key, dtl_kdc_dict)
            if code and label:
                st.info(f"Found category: {label} (Code: {code})")
                return code, label
        except Exception as e:
            st.warning(f"HyperCLOVA extraction failed, using fallback: {e}")
    
    # Fallback to similarity matching
    code, label = find_best_dtl_code_fallback(user_query, dtl_kdc_dict)
    if code and label:
        st.info(f"Found category: {label} (Code: {code})")
        return code, label
    
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
def setup_sidebar():
    with st.sidebar:
        if st.button("My Liked Books"):
            st.session_state.app_stage = "show_liked_books"
            st.rerun()

        st.markdown("""
        <div style="text-align: center; margin-bottom: 20px;">
            <h3 style="background: linear-gradient(90deg, #3b2314, #221409);
                      -webkit-background-clip: text;
                      -webkit-text-fill-color: transparent;
                      font-weight: 700;">
                API Configuration
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        # API Keys section
        with st.container():
            st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
            
            # HyperCLOVA API Key
            hyperclova_api_key = st.text_input("Enter your HyperCLOVA API Key", 
                                              type="password", 
                                              value=st.session_state.api_key)
            st.session_state.api_key = hyperclova_api_key
            
            # Library API Key
            library_api_key = st.text_input("Enter Library API Key", 
                                            type="password", 
                                            value=st.session_state.library_api_key)
            st.session_state.library_api_key = library_api_key
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Reset button
        if st.button("Start Over 💫"):
            st.session_state.messages = [
                {"role": "system", "content": "You are a helpful AI assistant specializing in book recommendations. For EVERY response, you must answer in BOTH English and Korean. First provide the complete answer in English, then provide '한국어 답변:' followed by the complete Korean translation of your answer."}
            ]
            st.session_state.app_stage = "welcome"
            st.session_state.user_genre = ""
            st.session_state.user_age = ""
            st.session_state.selected_book = None
            st.session_state.showing_books = False
            st.rerun()
        
        st.markdown("""
        <div style="text-align: center; margin-top: 30px; padding: 10px;">
            <p style="color: #b3b3cc; font-size: 0.8rem;">
                Powered by HyperCLOVA X & Korean Library API
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
    """Process specific questions about a book using HyperCLOVA"""
    if not api_key:
        return "Please provide your HyperCLOVA API key in the sidebar to get detailed responses about this book.\n\n한국어 답변: 이 책에 대한 자세한 답변을 받으려면 사이드바에서 HyperCLOVA API 키를 제공해 주세요."
    
    title = book.get('bookname') or book.get('bookName', 'Unknown Title')
    authors = book.get('authors') or book.get('author', 'Unknown Author')
    publisher = book.get('publisher', 'Unknown Publisher')
    year = book.get('publication_year') or book.get('publicationYear', 'Unknown Year')
    loan_count = book.get('loan_count') or book.get('loanCount', 0)
    
    # Build conversation context from recent messages
    context_messages = []
    if conversation_history:
        # Get last 4 messages for context (2 user + 2 assistant)
        recent_history = conversation_history[-4:]
        for msg in recent_history:
            context_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
    
    # Add the current question
    book_info = f"Book: '{title}' by {authors}, published by {publisher} in {year}, popularity: {loan_count} loans"
    
    # Create the system message
    system_message = {
        "role": "system",
        "content": f"You are a knowledgeable book expert discussing '{title}' by {authors}. For EVERY response, answer in BOTH English and Korean. First provide complete English answer, then '한국어 답변:' with Korean translation. Provide detailed, insightful information about books including themes, plot elements, character analysis, writing style, cultural context, and similar book recommendations when appropriate."
    }
    
    # Create the user message with context
    user_message = {
        "role": "user",
        "content": f"Book Information: {book_info}\n\nUser Question: {question}\n\nPlease provide a detailed and helpful response about this book based on the question asked."
    }
    
    # Combine all messages
    messages = [system_message] + context_messages + [user_message]
    
    try:
        response = call_hyperclova_api(messages, api_key)
        if response:
            return response
        else:
            return f"I'd be happy to discuss '{title}' further, but I'm having trouble connecting to the AI service right now. Could you try asking your question again?\n\n한국어 답변: '{title}'에 대해 더 자세히 논의하고 싶지만 지금 AI 서비스에 연결하는 데 문제가 있습니다. 질문을 다시 해보시겠어요?"
    except Exception as e:
        return f"I encountered an error while processing your question about '{title}'. Please try rephrasing your question or check your API connection.\n\n한국어 답변: '{title}'에 대한 질문을 처리하는 중 오류가 발생했습니다. 질문을 다시 표현하거나 API 연결을 확인해 주세요."

def main():
    # --- Initialize all session state variables before use ---
    if "api_key" not in st.session_state:
        st.session_state.api_key = ""
    if "library_api_key" not in st.session_state:
        st.session_state.library_api_key = ""
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

    setup_sidebar()

    st.markdown("<h1 style='text-align:center;'>📚 Book Wanderer / 책방랑자</h1>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center;'>Discover your next favorite read with AI assistance in English and Korean</div>", unsafe_allow_html=True)
    st.markdown("---")

    # --- Chat history (only show non-book-specific messages in main flow) ---
    for msg in st.session_state.messages:
        if msg["role"] != "system" and not msg.get("book_context"):
            display_message(msg)

    # --- App stages ---
    if st.session_state.app_stage == "welcome":
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Hello! Tell me about your favourite books, author, genre, or age group. You can describe what you're looking for in natural language.\n\n한국어 답변: 안녕하세요! 좋아하는 책, 작가, 장르 또는 연령대에 대해 말씀해 주세요. 자연스러운 언어로 원하는 것을 설명해 주시면 됩니다."
        })
        st.session_state.app_stage = "awaiting_user_input"
        st.rerun()

    elif st.session_state.app_stage == "awaiting_user_input":
        user_input = st.text_input("Tell me about your favorite genre, author, or book (in Korean or English):", key="user_open_input")
        if st.button("Send", key="send_open_input"):
            if user_input:
                st.session_state.messages.append({"role": "user", "content": user_input})
                st.session_state.app_stage = "process_user_input"
                st.rerun()

    elif st.session_state.app_stage == "process_user_input":
        user_input = st.session_state.messages[-1]["content"]
        
        # Only use Library API for book fetching, HyperCLOVA only for category matching
        dtl_code, dtl_label = get_dtl_kdc_code(user_input, st.session_state.api_key)
        
        if dtl_code and st.session_state.library_api_key:
            # Fetch books using the DTL KDC code (Library API only)
            books = get_books_by_dtl_kdc(dtl_code, st.session_state.library_api_key, page_no=1, page_size=20)
            
            if books:
                st.session_state.books_data = books
                
                # Generate AI response about the recommendations using HyperCLOVA
                if st.session_state.api_key:
                    ai_response = call_hyperclova_api([
                        {"role": "system", "content": "You are a helpful book recommendation assistant. For EVERY response, answer in BOTH English and Korean. First provide complete English answer, then '한국어 답변:' with Korean translation."},
                        {"role": "user", "content": f"I found {len(books)} books in the {dtl_label} category. Tell me about this category and encourage me to explore these recommendations."}
                    ], st.session_state.api_key)
                    
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
                    "content": "I couldn't find books in that specific category. Could you try describing your preferences differently? For example, mention specific genres like 'mystery novels', 'self-help books', or 'Korean literature'.\n\n한국어 답변: 해당 카테고리에서 책을 찾을 수 없었습니다. 다른 방식으로 선호도를 설명해 주시겠어요? 예를 들어 '추리소설', '자기계발서', '한국문학'과 같은 구체적인 장르를 언급해 주세요."
                })
                st.session_state.app_stage = "awaiting_user_input"
        else:
            missing_items = []
            if not dtl_code:
                missing_items.append("category matching")
            if not st.session_state.library_api_key:
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
        st.markdown("### 📖 Recommended Books for You")
        
        # Display books
        for i, book in enumerate(st.session_state.books_data[:10]):  # Show top 10 books
            display_book_card(book, i)
        
        # Chat input for follow-up questions
        user_followup = st.text_input("Ask me anything about these books or request different recommendations:", key="followup_input")
        if st.button("Send", key="send_followup"):
            if user_followup:
                st.session_state.messages.append({"role": "user", "content": user_followup})
                
                # Check if user wants new recommendations
                if any(keyword in user_followup.lower() for keyword in ['different', 'other', 'new', 'more', '다른', '새로운', '더']):
                    st.session_state.app_stage = "process_user_input"
                else:
                    # Process as follow-up question using HyperCLOVA
                    response = process_followup_with_hyperclova(user_followup, st.session_state.api_key)
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
            st.markdown("### 📖 Let's Talk About This Book")
            
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
                    <div style="padding: 20px;">
                        <h2 style="color: #2c3040; margin-bottom: 15px;">{title}</h2>
                        <div style="margin-bottom: 8px;"><strong>Author:</strong> {authors}</div>
                        <div style="margin-bottom: 8px;"><strong>Publisher:</strong> {publisher}</div>
                        <div style="margin-bottom: 8px;"><strong>Publication Year:</strong> {year}</div>
                        <div style="margin-bottom: 8px;"><strong>Popularity:</strong> {loan_count} loans</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Show introduction message when first entering book discussion
            if not st.session_state.book_intro_shown:
                intro_message = generate_book_introduction(book, st.session_state.api_key)
                st.session_state.book_discussion_messages.append({
                    "role": "assistant", 
                    "content": intro_message
                })
                st.session_state.book_intro_shown = True
                st.rerun()
            
            # Display chat history for this specific book
            for msg in st.session_state.book_discussion_messages:
                display_message(msg)
            
            # Chat input for book discussion
            book_question = st.text_input("Ask me anything about this book (plot, themes, similar books, etc.):", key="book_discussion_input")
            if st.button("Ask", key="ask_about_book"):
                if book_question:
                    # Add user message to book discussion
                    user_msg = {"role": "user", "content": book_question}
                    st.session_state.book_discussion_messages.append(user_msg)
                    
                    # Generate AI response about the book using HyperCLOVA
                    ai_response = process_book_question(
                        book, 
                        book_question, 
                        st.session_state.api_key,
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
        st.markdown("### ❤️ My Library")
        
        if hasattr(st.session_state, 'username') and st.session_state.username:
            liked_books = get_liked_books(st.session_state.username)
            
            if liked_books:
                st.markdown(f"You have {len(liked_books)} books in your library:")
                for i, book in enumerate(liked_books):
                    display_liked_book_card(book, i)
            else:
                st.markdown("Your library is empty. Start exploring books to add them to your collection!")
                if st.button("Discover Books"):
                    st.session_state.app_stage = "welcome"
                    st.rerun()
        else:
            st.error("Please ensure you are logged in to view your library.")
        
        # Back to main app button
        if st.button("← Back to Book Discovery", key="back_to_main"):
            st.session_state.app_stage = "show_recommendations" if st.session_state.books_data else "welcome"
            st.rerun()

if __name__ == "__main__":
    main()
