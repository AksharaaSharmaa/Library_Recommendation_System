import streamlit as st
import requests
from streamlit_extras.colored_header import colored_header
import base64
from Frontend import add_custom_css, gradient_title
from pymongo.errors import DuplicateKeyError

# Override button text color to white
st.markdown("""
<style>
    /* Make all button text white */
    .stButton button, .stButton button:focus, .stButton button:active {
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# Add after MongoDB client initialization
def get_user_library_collection():
    client = st.session_state.db_client  # Already set in login.py
    db = client["Login_Credentials"]
    return db["user_libraries"]

def like_book_for_user(username, book_info):
    user_library = get_user_library_collection()
    # Use ISBN as unique book identifier
    isbn = book_info.get("isbn13")
    if not isbn:
        return False
    # Upsert: Add the book if not already liked
    user_library.update_one(
        {"username": username},
        {"$addToSet": {"liked_books": book_info}},
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
    """Helper function to call HyperCLOVA API"""
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



def get_book_recommendations(genre, api_key):
    """Helper function to get book recommendations from library API"""
    try:
        BASE_URL = "http://data4library.kr/api/srchBooks"
        
        params = {
            "authKey": api_key,
            "keyword": genre,
            "format": "json",
            "pageNo": 1,
            "pageSize": 10
        }
        
        response = requests.get(BASE_URL, params=params)
        
        if response.status_code == 200:
            data = response.json()
            books = data.get("response", {}).get("docs", [])
            return books
        else:
            st.error(f"Failed to fetch data from API. Status code: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Error connecting to Library API: {e}")
        return []
    
def build_book_context(book_info, book_details):
    """Build a rich context for HyperCLOVA about the book"""
    context = f"Title: {book_info.get('bookname', 'Unknown')}\n"
    context += f"Author: {book_info.get('authors', 'Unknown')}\n"
    context += f"Publisher: {book_info.get('publisher', 'Unknown')}\n"
    context += f"Publication Year: {book_info.get('publication_year', 'Unknown')}\n"
    context += f"Genre: {st.session_state.user_genre}\n"
    
    # Add details if available
    if book_details:
        if 'description' in book_details:
            context += f"\nDescription: {book_details.get('description', '')}\n"
        if 'contents' in book_details:
            context += f"\nContents: {book_details.get('contents', '')}\n"
        if 'subjects' in book_details:
            context += f"\nSubjects: {book_details.get('subjects', '')}\n"
    
    return context

def display_book_card(book, index):
    """Helper function to display a book card with like functionality"""
    info = book.get("doc", {})
    
    with st.container():
        st.markdown('<div class="book-card">', unsafe_allow_html=True)
        
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
            st.markdown(f"""
            <div style="padding-left: 10px;">
                <div class="book-title">{info.get('bookname', '제목 없음')}</div>
                <div class="book-info"><strong>Author:</strong> {info.get('authors', '저자 없음')}</div>
                <div class="book-info"><strong>Publisher:</strong> {info.get('publisher', '출판사 없음')}</div>
                <div class="book-info"><strong>Year:</strong> {info.get('publication_year', '연도 없음')}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Create columns for buttons
            btn_col1, btn_col2 = st.columns([3, 1])
            
            with btn_col1:
                if st.button(f"Tell me more about this book", key=f"details_{info.get('isbn13', 'unknown')}_{index}"):
                    st.session_state.selected_book = info
                    st.session_state.app_stage = "discuss_book"
                    st.rerun()
            
            with btn_col2:
                # Like button with heart icon
                if st.button("❤️", 
                            key=f"like_{info.get('isbn13', 'unknown')}_{index}",
                            help="Add to My Library"):
                    if like_book_for_user(st.session_state.username, info):
                        st.success("Added to your library!")
                    else:
                        st.error("Could not add to library")
        
        st.markdown('</div>', unsafe_allow_html=True)


def get_book_details(isbn, api_key):
    """Get detailed information about a specific book using its ISBN"""
    try:
        DETAIL_URL = "http://data4library.kr/api/srchDtlList"
        
        params = {
            "authKey": api_key,
            "isbn13": isbn,
            "format": "json"
        }
        
        response = requests.get(DETAIL_URL, params=params)
        
        if response.status_code == 200:
            data = response.json()
            details = data.get("response", {}).get("detail", [])
            return details[0] if details else None
        else:
            st.error(f"Failed to fetch book details. Status code: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error connecting to Library API for book details: {e}")
        return None

def display_detailed_book(book_info):
    """Helper function to display detailed book information"""
    st.markdown('<div class="book-card" style="margin-bottom: 30px;">', unsafe_allow_html=True)
    
    cols = st.columns([1, 3])
    
    with cols[0]:
        # Display book image if available
        image_url = book_info.get("bookImageURL", "")
        if image_url:
            st.image(image_url, width=150)
        else:
            # Placeholder for missing image
            st.markdown("""
            <div style="width: 140px; height: 200px; background: linear-gradient(135deg, #2c3040, #363c4e); 
                        display: flex; align-items: center; justify-content: center; border-radius: 8px;">
                <span style="color: #b3b3cc;">No Image Available</span>
            </div>
            """, unsafe_allow_html=True)
    
    with cols[1]:
        st.markdown(f"""
        <div style="padding-left: 15px;">
            <div class="book-title" style="font-size: 1.5rem;">{book_info.get('bookname', '제목 없음')}</div>
            <div class="book-info"><strong>Author:</strong> {book_info.get('authors', '저자 없음')}</div>
            <div class="book-info"><strong>Publisher:</strong> {book_info.get('publisher', '출판사 없음')}</div>
            <div class="book-info"><strong>Year:</strong> {book_info.get('publication_year', '연도 없음')}</div>
            <div class="book-info"><strong>ISBN:</strong> {book_info.get('isbn13', 'N/A')}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def fetch_and_enrich_books_data(books, api_key):
    """Fetch detailed information for each book and add it to the data"""
    enriched_books = []
    for book in books:
        book_info = book.get("doc", {})
        book_isbn = book_info.get("isbn13", "")
        
        if book_isbn:
            details = get_book_details(book_isbn, api_key)
            if details:
                # Add details to the book info
                book["details"] = details
        
        enriched_books.append(book)
    
    return enriched_books

def build_recommendations_context(books_data):
    """Build a rich context from all recommended books"""
    context = "Here are summaries of the recommended books:\n\n"
    
    for i, book in enumerate(books_data, 1):
        book_info = book.get("doc", {})
        book_details = book.get("details", {})
        
        context += f"{i}. '{book_info.get('bookname', 'Unknown Title')}' by {book_info.get('authors', 'Unknown Author')}\n"
        context += f"   Published by {book_info.get('publisher', 'Unknown Publisher')} in {book_info.get('publication_year', 'Unknown Year')}\n"
        
        # Add description if available
        if book_details and 'description' in book_details:
            # Truncate description if too long
            description = book_details.get('description', '')
            if len(description) > 300:
                description = description[:300] + "..."
            context += f"   Description: {description}\n"
        
        context += "\n"
    
    return context

def main():
    # Apply the custom CSS
    add_custom_css()

    # --- Session State Initialization ---
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "system", "content": "You are a helpful AI assistant specializing in book recommendations. For EVERY response, you must answer in BOTH English and Korean. First provide the complete answer in English, then provide '한국어 답변:' followed by the complete Korean translation of your answer."}
        ]
    if "api_key" not in st.session_state:
        st.session_state.api_key = ""
    if "library_api_key" not in st.session_state:
        st.session_state.library_api_key = ""
    if "app_stage" not in st.session_state:
        st.session_state.app_stage = "init_convo"
    if "user_genre" not in st.session_state:
        st.session_state.user_genre = ""
    if "selected_book" not in st.session_state:
        st.session_state.selected_book = None
    if "books_data" not in st.session_state:
        st.session_state.books_data = []
    if "enriched_books" not in st.session_state:
        st.session_state.enriched_books = False
    if "shown_book_info" not in st.session_state:
        st.session_state.shown_book_info = set()
    if "book_details" not in st.session_state:
        st.session_state.book_details = {}
    if "username" not in st.session_state:
        st.session_state.username = "guest"  # or set from your login logic

    # --- Sidebar ---
    setup_sidebar()

    # --- Header ---
    st.markdown('<div class="app-header">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        gradient_title("Book Wanderer")
        gradient_title("책방랑자")
        st.markdown("""
        <div style="text-align: center; margin-bottom: 20px;">
            <p style="font-size: 1.1rem; color: #d1d1e0; margin-bottom: 20px;">
                Discover your next favorite read with AI assistance in English and Korean
            </p>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # --- Chat Container ---
    chat_container = st.container()
    with chat_container:
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        for msg in st.session_state.messages:
            if msg["role"] != "system":
                display_message(msg)
        st.markdown('</div>', unsafe_allow_html=True)

        # --- APP STAGES ---
        # 1. Initial dynamic HyperCLOVA prompt
        if st.session_state.app_stage == "init_convo":
            if len(st.session_state.messages) == 1 and st.session_state.api_key:
                # Get the initial prompt from HyperCLOVA
                initial_message = call_hyperclova_api(st.session_state.messages, st.session_state.api_key)
                if initial_message:
                    st.session_state.messages.append({"role": "assistant", "content": initial_message})
                else:
                    st.session_state.messages.append({"role": "assistant", "content": "Hello! Tell me about your favourite books, author or genre.\n\n한국어 답변: 안녕하세요! 좋아하는 책, 작가 또는 장르에 대해 말씀해 주세요."})
                st.session_state.app_stage = "awaiting_user_input"
                st.rerun()
            elif not st.session_state.api_key:
                st.warning("Please enter your HyperCLOVA API key in the sidebar to begin.")
            else:
                st.session_state.app_stage = "awaiting_user_input"
                st.rerun()

        # 2. Awaiting user free-form input
        elif st.session_state.app_stage == "awaiting_user_input":
            user_input = st.chat_input("Tell me about your favorite books, authors, or genres:")
            if user_input:
                st.session_state.messages.append({"role": "user", "content": user_input})
                st.session_state.app_stage = "process_user_input"
                st.rerun()

        # 3. Extract keywords and fetch recommendations
        elif st.session_state.app_stage == "process_user_input":
            # Use HyperCLOVA to extract genre/author
            extraction_prompt = [
                {"role": "system", "content": "Extract the main book genre or author mentioned in this user message. Respond ONLY with the genre or author name."},
                {"role": "user", "content": st.session_state.messages[-1]["content"]}
            ]
            extracted = call_hyperclova_api(extraction_prompt, st.session_state.api_key)
            if extracted:
                st.session_state.user_genre = extracted.strip()
                if st.session_state.library_api_key:
                    books = get_book_recommendations(st.session_state.user_genre, st.session_state.library_api_key)
                    if books:
                        st.session_state.books_data = books
                        st.session_state.enriched_books = False
                        intro_msg = f"I found these books related to {st.session_state.user_genre}.\n\n한국어 답변: {st.session_state.user_genre} 관련 도서를 찾았습니다."
                        st.session_state.messages.append({"role": "assistant", "content": intro_msg})
                        st.session_state.app_stage = "show_recommendations"
                    else:
                        error_msg = f"Couldn't find books for '{st.session_state.user_genre}'. Try different keywords?\n\n한국어 답변: '{st.session_state.user_genre}' 관련 도서를 찾을 수 없습니다. 다른 키워드를 시도해 보시겠어요?"
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})
                        st.session_state.app_stage = "awaiting_user_input"
                else:
                    api_error = "Library API key required. Please check sidebar.\n\n한국어 답변: 라이브러리 API 키가 필요합니다. 사이드바를 확인해 주세요."
                    st.session_state.messages.append({"role": "assistant", "content": api_error})
                    st.session_state.app_stage = "awaiting_user_input"
            else:
                st.session_state.messages.append({"role": "assistant", "content": "Sorry, I couldn't understand your preferences. Please try again.\n\n한국어 답변: 죄송합니다. 선호도를 이해하지 못했습니다. 다시 시도해 주세요."})
                st.session_state.app_stage = "awaiting_user_input"
            st.rerun()

        # 4. Show book recommendations and handle follow-up
        elif st.session_state.app_stage == "show_recommendations":
            if not st.session_state.enriched_books:
                with st.spinner("Enriching book data..."):
                    st.session_state.books_data = fetch_and_enrich_books_data(
                        st.session_state.books_data, 
                        st.session_state.library_api_key
                    )
                    st.session_state.enriched_books = True
            st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)
            st.markdown("""
            <h3 style="text-align: center; 
                    background: linear-gradient(90deg, #221409, #3b2314);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    font-weight: 700;
                    margin-bottom: 20px;">
                Recommended Books
            </h3>
            """, unsafe_allow_html=True)
            for i, book in enumerate(st.session_state.books_data):
                display_book_card(book, i)

            # --- Follow-up input using st.chat_input ---
            follow_up = st.chat_input("Ask about these books, or tell me another genre/author:")
            if follow_up:
                st.session_state.messages.append({"role": "user", "content": follow_up})
                # Detect if user wants to change topic/genre/author
                change_keywords = ["different", "another", "other", "new", "change", "genre", "author", "topic"]
                if any(word in follow_up.lower() for word in change_keywords):
                    # Extract new genre/author from follow-up message
                    extraction_prompt = [
                        {"role": "system", "content": "Extract the main book genre or author mentioned in this user message. Respond ONLY with the genre or author name."},
                        {"role": "user", "content": follow_up}
                    ]
                    extracted = call_hyperclova_api(extraction_prompt, st.session_state.api_key)
                    if extracted:
                        st.session_state.user_genre = extracted.strip()
                        if st.session_state.library_api_key:
                            books = get_book_recommendations(st.session_state.user_genre, st.session_state.library_api_key)
                            if books:
                                st.session_state.books_data = books
                                st.session_state.enriched_books = False
                                intro_msg = f"I found these books related to {st.session_state.user_genre}.\n\n한국어 답변: {st.session_state.user_genre} 관련 도서를 찾았습니다."
                                st.session_state.messages.append({"role": "assistant", "content": intro_msg})
                                st.session_state.app_stage = "show_recommendations"
                            else:
                                error_msg = f"Couldn't find books for '{st.session_state.user_genre}'. Try different keywords?\n\n한국어 답변: '{st.session_state.user_genre}' 관련 도서를 찾을 수 없습니다. 다른 키워드를 시도해 보시겠어요?"
                                st.session_state.messages.append({"role": "assistant", "content": error_msg})
                                st.session_state.app_stage = "show_recommendations"
                        else:
                            api_error = "Library API key required. Please check sidebar.\n\n한국어 답변: 라이브러리 API 키가 필요합니다. 사이드바를 확인해 주세요."
                            st.session_state.messages.append({"role": "assistant", "content": api_error})
                            st.session_state.app_stage = "show_recommendations"
                    else:
                        st.session_state.messages.append({"role": "assistant", "content": "Sorry, I couldn't understand your new preference. Please try again.\n\n한국어 답변: 죄송합니다. 새로운 선호도를 이해하지 못했습니다. 다시 시도해 주세요."})
                        st.session_state.app_stage = "show_recommendations"
                    st.rerun()
                else:
                    # Regular follow-up: ask about current recommendations
                    books_context = build_recommendations_context(st.session_state.books_data)
                    enhanced_system_msg = {
                        "role": "system",
                        "content": f"{st.session_state.messages[0]['content']}\n\n{books_context}"
                    }
                    messages_with_context = [enhanced_system_msg] + st.session_state.messages[1:]
                    response = call_hyperclova_api(messages_with_context, st.session_state.api_key)
                    if response:
                        st.session_state.messages.append({"role": "assistant", "content": response})
                    st.rerun()

        # 5. Book details discussion (unchanged)
        elif st.session_state.app_stage == "discuss_book":
            if st.session_state.selected_book:
                display_detailed_book(st.session_state.selected_book)
                book_info = st.session_state.selected_book
                book_title = book_info.get('bookname', 'Unknown Title')
                book_isbn = book_info.get('isbn13', '')
                if "book_details" not in st.session_state or st.session_state.book_details.get('isbn13') != book_isbn:
                    if st.session_state.library_api_key and book_isbn:
                        book_details = get_book_details(book_isbn, st.session_state.library_api_key)
                        st.session_state.book_details = book_details if book_details else {}
                    else:
                        st.session_state.book_details = {}
                if book_isbn not in st.session_state.shown_book_info:
                    st.session_state.shown_book_info.add(book_isbn)
                    book_author = book_info.get('authors', 'Unknown Author')
                    book_publisher = book_info.get('publisher', 'Unknown Publisher')
                    book_year = book_info.get('publication_year', 'Unknown Year')
                    initial_description = f"Here's information about '{book_title}' by {book_author}. This book was published by {book_publisher} in {book_year}."
                    if st.session_state.book_details and 'description' in st.session_state.book_details:
                        initial_description += f"\n\nDescription: {st.session_state.book_details.get('description')}"
                    else:
                        initial_description += f"\n\nWhile I don't have detailed plot information about this specific book, {st.session_state.user_genre} books often explore themes related to this genre."
                    initial_description += f"\n\nBased on your interest in {st.session_state.user_genre}, you might enjoy this book for its storytelling, characters, and exploration of relevant themes."
                    korean_description = f"{book_author}의 '{book_title}'에 대한 정보입니다. 이 책은 {book_year}년에 {book_publisher}에서 출판되었습니다."
                    if st.session_state.book_details and 'description' in st.session_state.book_details:
                        korean_description += f"\n\n설명: {st.session_state.book_details.get('description')}"
                    else:
                        korean_description += f"\n\n이 특정 책에 대한 자세한 줄거리 정보는 없지만, {st.session_state.user_genre} 책들은 주로 이 장르와 관련된 주제를 탐구합니다."
                    korean_description += f"\n\n{st.session_state.user_genre}에 대한 귀하의 관심을 바탕으로, 이 책의 스토리텔링, 캐릭터, 그리고 관련 주제의 탐구로 인해 이 책을 즐기실 수 있을 것입니다."
                    st.session_state.messages.append({"role": "user", "content": f"Tell me about '{book_title}'"})
                    st.session_state.messages.append({"role": "assistant", "content": f"{initial_description}\n\n한국어 답변: {korean_description}"})
                    st.rerun()
                book_question = st.chat_input("Ask specific questions about this book or go back to recommendations:")
                if book_question:
                    if "back" in book_question.lower() or "recommendations" in book_question.lower():
                        st.session_state.app_stage = "show_recommendations"
                        st.rerun()
                    else:
                        st.session_state.messages.append({"role": "user", "content": book_question})
                        if st.session_state.api_key:
                            book_context = build_book_context(book_info, st.session_state.book_details)
                            messages_with_context = st.session_state.messages.copy()
                            system_message = {
                                "role": "system", 
                                "content": f"""You are a helpful AI assistant specializing in book recommendations. 
                                The user is asking about the book '{book_title}'. Below is detailed information about the book:
                                {book_context}
                                Try to provide relevant information based on these details. 
                                For EVERY response, you must answer in BOTH English and Korean.
                                First provide the complete answer in English, then provide '한국어 답변:' 
                                followed by the complete Korean translation of your answer."""
                            }
                            messages_with_context[0] = system_message
                            book_response = call_hyperclova_api(messages_with_context, st.session_state.api_key)
                            if book_response:
                                st.session_state.messages.append({"role": "assistant", "content": book_response})
                            else:
                                fallback_response = f"I don't have specific details about that aspect of '{book_title}', but books in the {st.session_state.user_genre} genre often explore themes like character development, world-building, and thematic elements relevant to the genre. Is there something else about this book or other books you'd like to know about?\n\n한국어 답변: '{book_title}'의 해당 측면에 대한 구체적인 세부 정보는 없지만, {st.session_state.user_genre} 장르의 책들은 종종 캐릭터 발전, 세계관 구축, 그리고 장르와 관련된 주제적 요소와 같은 주제를 탐구합니다. 이 책이나 다른 책에 대해 알고 싶은 다른 내용이 있으신가요?"
                                st.session_state.messages.append({"role": "assistant", "content": fallback_response})
                        else:
                            default_response = f"To provide detailed information about '{book_title}', I need access to the HyperCLOVA API. Please enter your API key in the sidebar.\n\n한국어 답변: '{book_title}'에 대한 자세한 정보를 제공하기 위해서는 HyperCLOVA API에 접근해야 합니다. 사이드바에 API 키를 입력해 주세요."
                            st.session_state.messages.append({"role": "assistant", "content": default_response})
                        st.rerun()

        # 6. Liked books library (unchanged)
        elif st.session_state.app_stage == "show_liked_books":
            st.markdown("<h3 style='text-align:center;'>Your Liked Books</h3>", unsafe_allow_html=True)
            liked_books = get_liked_books(st.session_state.username)
            if not liked_books:
                st.info("You have not liked any books yet.")
            else:
                for idx, book in enumerate(liked_books):
                    st.markdown('<div class="book-card" style="margin-bottom: 30px;">', unsafe_allow_html=True)
                    cols = st.columns([1, 3, 1])  # Add a third column for the Remove button
                    with cols[0]:
                        image_url = book.get("bookImageURL", "")
                        if image_url:
                            st.image(image_url, width=120)
                        else:
                            st.markdown(
                                "<div style='width:100px;height:150px;background:linear-gradient(135deg,#2c3040,#363c4e);display:flex;align-items:center;justify-content:center;border-radius:5px;'><span style='color:#b3b3cc;'>No Image</span></div>",
                                unsafe_allow_html=True
                            )
                    with cols[1]:
                        st.markdown(f"""
                            <div style="padding-left: 10px;">
                                <div class="book-title">{book.get('bookname', 'No Title')}</div>
                                <div class="book-info"><strong>Author:</strong> {book.get('authors', 'Unknown')}</div>
                                <div class="book-info"><strong>Publisher:</strong> {book.get('publisher', 'Unknown')}</div>
                                <div class="book-info"><strong>Year:</strong> {book.get('publication_year', 'Unknown')}</div>
                            </div>
                        """, unsafe_allow_html=True)
                    with cols[2]:
                        if st.button("Remove", key=f"remove_{book.get('isbn13', idx)}"):
                            unlike_book_for_user(st.session_state.username, book.get('isbn13'))
                            st.success(f"Removed '{book.get('bookname', 'No Title')}' from your liked books.")
                            st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

            if st.button("← Back", key="back_from_liked_books_btn"):
                st.session_state.app_stage = "awaiting_user_input"
                st.rerun()

    # --- Footer ---
    st.markdown('<div class="app-footer">', unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align: center; margin: 10px 0;">
        <p style="color: #d1d1e0;">
            This application provides book recommendations based on your preferences using AI assistance.
            All recommendations are available in both English and Korean.
        </p>
        <p style="color: #b3b3cc; font-size: 0.8rem; margin-top: 15px;">
            Powered by Streamlit • HyperCLOVA X • Korean Library API
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
