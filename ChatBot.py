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

import streamlit as st
import requests
from datetime import datetime
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.docstore.document import Document
from PyPDF2 import PdfReader

# --- PDF Extraction and Chunking ---
@st.cache_resource
def build_pdf_vectorstore(pdf_path="Codes.pdf"):
    # 1. Extract text from PDF
    reader = PdfReader(pdf_path)
    full_text = ""
    for page in reader.pages:
        full_text += page.extract_text() + "\n"
    # 2. Chunk text (keep chunks small for retrieval accuracy)
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_text(full_text)
    documents = [Document(page_content=chunk) for chunk in chunks]
    # 3. Embed and store in FAISS
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectorstore = FAISS.from_documents(documents, embeddings)
    return vectorstore

pdf_vectorstore = build_pdf_vectorstore()

# --- Utility: Retrieve best chunk and extract KDC code ---
def extract_kdc_code_from_chunk(chunk):
    # Look for KDC/dtl_kdc code patterns in the chunk
    import re
    # Match lines like: "dtl_kdc", "kdc", or "코드값" in tables
    kdc_matches = re.findall(r'(?:kdc|dtl_kdc|코드값)\s*[:=]?\s*([0-9]{1,3}(?:\.[0-9]+)?)', chunk, flags=re.IGNORECASE)
    if kdc_matches:
        return kdc_matches[0]
    # Also try to match lines like "813.7", "81", etc.
    fallback = re.findall(r'\b([0-9]{1,3}(?:\.[0-9]+)?)\b', chunk)
    if fallback:
        return fallback[0]
    return None

def get_relevant_kdc_code(user_query):
    # Retrieve top relevant chunk from the PDF vectorstore
    docs = pdf_vectorstore.similarity_search(user_query, k=2)
    for doc in docs:
        code = extract_kdc_code_from_chunk(doc.page_content)
        if code:
            return code
    return None

# --- Query library API for books by KDC code ---
def get_books_by_kdc(kdc_code, auth_key, page_no=1, page_size=30):
    url = "http://data4library.kr/api/loanltemSrch"
    params = {
        "authKey": auth_key,
        "startDt": "2000-01-01",
        "endDt": datetime.now().strftime("%Y-%m-%d"),
        "format": "json",
        "pageNo": page_no,
        "pageSize": page_size
    }
    # Use kdc or dtl_kdc depending on code length (API docs: dtl_kdc for subcategories)
    if len(kdc_code) <= 2:
        params["kdc"] = kdc_code
    else:
        params["dtl_kdc"] = kdc_code
    r = requests.get(url, params=params)
    if r.status_code == 200:
        docs = r.json().get("response", {}).get("docs", {}).get("doc", [])
        if isinstance(docs, dict):  # only one book
            docs = [docs]
        docs = sorted(docs, key=lambda x: int(x.get("loan_count", 0)), reverse=True)
        return docs
    return []

def main():
    add_custom_css()
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
    if "api_key" not in st.session_state:
        st.session_state.api_key = ""
    if "library_api_key" not in st.session_state:
        st.session_state.library_api_key = ""
    if "app_stage" not in st.session_state:
        st.session_state.app_stage = "init_convo"
    if "books_data" not in st.session_state:
        st.session_state.books_data = []

    setup_sidebar()
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

    chat_container = st.container()
    with chat_container:
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        for msg in st.session_state.messages:
            if msg["role"] != "system":
                display_message(msg)
        st.markdown('</div>', unsafe_allow_html=True)

        if st.session_state.app_stage == "init_convo":
            if len(st.session_state.messages) == 1 and st.session_state.api_key:
                initial_message = call_hyperclova_api(st.session_state.messages, st.session_state.api_key)
                if initial_message:
                    st.session_state.messages.append({"role": "assistant", "content": initial_message})
                else:
                    st.session_state.messages.append({"role": "assistant", "content": "Hello! Tell me about your favourite books, author, genre, or age group.\n\n한국어 답변: 안녕하세요! 좋아하는 책, 작가, 장르 또는 연령대에 대해 말씀해 주세요."})
                st.session_state.app_stage = "awaiting_user_input"
                st.rerun()
            elif not st.session_state.api_key:
                st.warning("Please enter your HyperCLOVA API key in the sidebar to begin.")
            else:
                st.session_state.app_stage = "awaiting_user_input"
                st.rerun()

        elif st.session_state.app_stage == "awaiting_user_input":
            st.markdown('<div class="input-container">', unsafe_allow_html=True)
            user_input = st.text_input("Tell me about your favorite genre, author, or book:", key="user_open_input")
            if st.button("Send", key="send_open_input"):
                if user_input:
                    st.session_state.messages.append({"role": "user", "content": user_input})
                    st.session_state.app_stage = "process_user_input"
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        elif st.session_state.app_stage == "process_user_input":
            user_query = st.session_state.messages[-1]["content"]
            # Use HyperCLOVA to extract intent (simulate or call API as needed)
            # Use RAG (vector search) to find KDC code from documentation
            kdc_code = get_relevant_kdc_code(user_query)
            if not kdc_code:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "Sorry, I could not find a matching KDC code for your query. Please try a different genre or keyword.\n\n한국어 답변: 죄송합니다. 입력하신 내용과 일치하는 KDC 코드를 찾지 못했습니다. 다른 장르나 키워드로 시도해 주세요."
                })
                st.session_state.app_stage = "awaiting_user_input"
                st.rerun()
            if st.session_state.library_api_key:
                books = get_books_by_kdc(kdc_code, st.session_state.library_api_key)
                if books:
                    st.session_state.books_data = books
                    intro_msg = f"I found these books for KDC code '{kdc_code}', sorted by loan count.\n\n한국어 답변: KDC 코드 '{kdc_code}'에 해당하는 도서를 대출 건수 내림차순으로 찾았습니다."
                    st.session_state.messages.append({"role": "assistant", "content": intro_msg})
                    st.session_state.app_stage = "show_recommendations"
                else:
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"Sorry, no books found for KDC code '{kdc_code}'.\n\n한국어 답변: KDC 코드 '{kdc_code}'에 해당하는 도서를 찾을 수 없습니다."
                    })
                    st.session_state.app_stage = "awaiting_user_input"
            else:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "Library API key required. Please check sidebar.\n\n한국어 답변: 라이브러리 API 키가 필요합니다. 사이드바를 확인해 주세요."
                })
                st.session_state.app_stage = "awaiting_user_input"
            st.rerun()

        elif st.session_state.app_stage == "show_recommendations":
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
            st.markdown('<div class="input-container">', unsafe_allow_html=True)
            follow_up = st.text_input("Ask about these books, or tell me another genre/author:", key="follow_up_input")
            if st.button("Send", key="send_follow_up"):
                if follow_up:
                    st.session_state.messages.append({"role": "user", "content": follow_up})
                    st.session_state.app_stage = "process_user_input"
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

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

if __name__ == "__main__":
    main()


