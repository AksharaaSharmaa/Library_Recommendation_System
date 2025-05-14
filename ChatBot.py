import streamlit as st
import requests
from streamlit_extras.colored_header import colored_header
import base64

def add_custom_css():
    st.markdown("""
    <style>
        /* Main app background */
        .stApp {
            background: linear-gradient(135deg, #f9f2e7, #f0e4d3, #e6d7c3);
            color: #4a3728;
        }
        
        /* Darker sidebar background */
        [data-testid="stSidebar"] {
            background: linear-gradient(135deg, #e6d7c3, #d2b48c, #c9b18c) !important;
            border-right: 1px solid rgba(139, 90, 43, 0.2);
        }
        
        /* Make all text dark brown */
        p, div, span, label, h1, h2, h3, h4, h5, h6, li, a, .stMarkdown, .stText {
            color: #4a3728 !important;
        }
        
        /* Override any white text in elements */
        .stButton button {
            background: linear-gradient(90deg, #8b5a2b, #d2b48c);
            color: #f5e7d3;
            border: none;
            padding: 10px 15px;
            border-radius: 25px;
            transition: all 0.3s ease;
        }
        
        .stButton button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(139, 90, 43, 0.4);
        }
        
        .stTextInput input, .stNumberInput input, .stSelectbox, .stMultiselect {
            background-color: rgba(245, 231, 211, 0.7);
            color: #4a3728;
            border: 1px solid #a67c52;
            border-radius: 25px;
        }
        
        .stChat .message.user {
            background-color: #d2b48c;
            border-radius: 20px;
        }
        
        .stChat .message.assistant {
            background-color: #b39b7d;
            border-radius: 20px;
        }
        
        div[data-testid="stVerticalBlock"] {
            padding: 0 10px;
        }
        
        .book-title {
            color: #603913;
            font-size: 1.2rem;
            margin-bottom: 10px;
            font-weight: 600;
        }
        
        .book-info {
            margin-bottom: 8px;
            color: #4a3728;
            line-height: 1.5;
        }
        
        .like-button {
            background: linear-gradient(90deg, #8b5a2b, #a67c52);
            color: #f5e7d3;
            border: none;
            padding: 5px 10px;
            border-radius: 20px;
            cursor: pointer;
            font-size: 0.8rem;
            transition: all 0.3s ease;
        }
        
        .like-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 3px 10px rgba(139, 90, 43, 0.4);
        }
        
        .chat-container {
            display: flex;
            flex-direction: column;
            gap: 20px;
            margin-bottom: 30px;
            padding: 15px;
        }
        
        .chat-message {
            padding: 15px 20px;
            border-radius: 20px;
            max-width: 85%;
            box-shadow: 0 3px 10px rgba(74, 55, 40, 0.2);
            line-height: 1.6;
        }
        
        .assistant-message {
            align-self: flex-start;
            background: linear-gradient(to right, #b39b7d, #9e8974);
            border-left: 3px solid #8b5a2b;
            margin-left: 10px;
        }
        
        .user-message {
            align-self: flex-end;
            background: linear-gradient(to right, #c9b18c, #a67c52);
            border-right: 3px solid #603913;
            margin-right: 10px;
        }
        
        .korean-text {
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid rgba(139, 90, 43, 0.3);
        }
        
        .korean-label {
            color: #603913;
            font-weight: 600;
            display: inline-block;
            margin-bottom: 5px;
        }
        
        .message-timestamp {
            font-size: 0.7rem;
            color: #7d5a41;
            margin-top: 8px;
            text-align: right;
        }
        
        .message-avatar {
            width: 28px;
            height: 28px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 5px;
            font-size: 0.8rem;
            font-weight: bold;
        }
        
        .user-avatar {
            background: linear-gradient(135deg, #8b5a2b, #a67c52);
            color: #f5e7d3;
            align-self: flex-end;
            margin-right: 10px;
        }
        
        .assistant-avatar {
            background: linear-gradient(135deg, #603913, #8b5a2b);
            color: #f5e7d3;
            align-self: flex-start;
            margin-left: 10px;
        }
        
        .message-with-avatar {
            display: flex;
            flex-direction: column;
        }
        
        /* Remove container backgrounds */
        .stHeader, div[data-testid="stDecoration"], div[data-testid="stToolbar"] {
            background: none !important;
            border: none !important;
            box-shadow: none !important;
        }
        
        /* Keep the answer container but make it darker */
        .stTextArea textarea {
            background-color: #b39b7d !important;
            color: #4a3728 !important;
            border: 1px solid #8b5a2b !important;
            border-radius: 15px !important;
        }
        
        /* Remove rectangular containers by making them transparent */
        [data-testid="block-container"], [data-testid="stExpander"] {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }
        
        /* Ensure sidebar text is dark brown */
        [data-testid="stSidebar"] p, 
        [data-testid="stSidebar"] div, 
        [data-testid="stSidebar"] span, 
        [data-testid="stSidebar"] label {
            color: #4a3728 !important;
        }
        
        /* Override any white text in inputs or special elements */
        input, textarea, select, .stSelectbox, .stMultiselect {
            color: #4a3728 !important;
        }
        
        /* Menu items and dropdowns */
        .stSelectbox ul li, .stMultiselect ul li {
            color: #4a3728 !important;
        }
        
        /* Gradient divider */
        .gradient-divider {
            height: 3px;
            background: linear-gradient(90deg, transparent, #8b5a2b, #a67c52, transparent);
            margin: 25px 0;
            border-radius: 3px;
        }
        
        /* Footer text */
        footer {
            color: #4a3728 !important;
        }
        
        /* Code blocks */
        code, pre {
            color: #603913 !important;
        }
    </style>
    """, unsafe_allow_html=True)

def gradient_title(title_text):
    st.markdown(f"""
    <h1 style="text-align: center; 
              background: linear-gradient(90deg, #8b5a2b, #a67c52); 
              -webkit-background-clip: text;
              -webkit-text-fill-color: transparent;
              font-weight: 800;
              font-size: 2.5rem;
              margin-bottom: 20px;">
        {title_text}
    </h1>
    """, unsafe_allow_html=True)

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
            return None
    except Exception as e:
        st.error(f"Error connecting to HyperCLOVA API: {e}")
        return None

def setup_sidebar():
    with st.sidebar:
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

def display_book_card(book, index):
    """Helper function to display a book card"""
    info = book.get("doc", {})
    
    col1, col2 = st.columns([1, 3])
    
    with st.container():
        st.markdown('<div class="book-card">', unsafe_allow_html=True)
        
        cols = st.columns([1, 3])
        
        with cols[0]:
            # Display book image if available
            image_url = info.get("bookImageURL", "")
            if image_url:
                st.image(image_url, width=120)
            else:
                # Placeholder for missing image
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
            
            # Select button for this book
            if st.button(f"Tell me more about this book", key=f"like_{info.get('isbn13', 'unknown')}_{index}"):
                st.session_state.selected_book = info
                st.session_state.app_stage = "discuss_book"
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

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

# Main application
def main():
    # Apply the custom CSS
    add_custom_css()

    # Initialize session states
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "system", "content": "You are a helpful AI assistant specializing in book recommendations. For EVERY response, you must answer in BOTH English and Korean. First provide the complete answer in English, then provide '한국어 답변:' followed by the complete Korean translation of your answer."}
        ]
    
    if "api_key" not in st.session_state:
        st.session_state.api_key = ""
        
    if "library_api_key" not in st.session_state:
        st.session_state.library_api_key = "70b5336f9e785c681d5ff58906e6416124f80f59faa834164d297dcd8db63036"
    
    if "app_stage" not in st.session_state:
        st.session_state.app_stage = "welcome"
        
    if "user_genre" not in st.session_state:
        st.session_state.user_genre = ""
        
    if "user_age" not in st.session_state:
        st.session_state.user_age = ""
        
    if "selected_book" not in st.session_state:
        st.session_state.selected_book = None
        
    if "showing_books" not in st.session_state:
        st.session_state.showing_books = False

    # Setup sidebar
    setup_sidebar()

    # Main layout - header
    st.markdown('<div class="app-header">', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col2:
        gradient_title("Book Wanderer | 책방랑자")
        
        st.markdown("""
        <div style="text-align: center; margin-bottom: 20px;">
            <p style="font-size: 1.1rem; color: #d1d1e0; margin-bottom: 20px;">
                Discover your next favorite read with AI assistance in English and Korean
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

    # Chat container - this will display all messages
    chat_container = st.container()
    
    with chat_container:
        # Display chat history
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        
        for msg in st.session_state.messages:
            if msg["role"] != "system":
                display_message(msg)
        
        st.markdown('</div>', unsafe_allow_html=True)

        # Welcome stage - first interaction with HyperCLOVA
        if st.session_state.app_stage == "welcome":
            # Only add welcome message if it's not already in the chat
            if len(st.session_state.messages) == 1:  # Only system message is present
                # Make API call to HyperCLOVA for welcome message
                if st.session_state.api_key:
                    # Add the welcome message instruction
                    messages_with_instruction = st.session_state.messages.copy()
                    messages_with_instruction.append({
                        "role": "user", 
                        "content": f"Generate a friendly welcome message for a book recommendation system. Ask the user what genre of books they're interested in. Remember to respond in both English and Korean as instructed."
                    })
                    
                    welcome_message = call_hyperclova_api(messages_with_instruction, st.session_state.api_key)
                    
                    if not welcome_message:
                        welcome_message = "Hi! Welcome to the Book Recommendation System. I can help you find your next great read based on your preferences. What genre of books are you interested in? For example: mystery, romance, science fiction, fantasy, history, biography, etc.\n\n한국어 답변: 안녕하세요! 도서 추천 시스템에 오신 것을 환영합니다. 여러분의 취향에 맞는 다음 좋은 책을 찾는 데 도움을 드릴 수 있습니다. 어떤 장르의 책에 관심이 있으신가요? 예: 미스터리, 로맨스, SF, 판타지, 역사, 전기 등."
                else:
                    welcome_message = "Hi! Welcome to the Book Recommendation System. I can help you find your next great read based on your preferences. What genre of books are you interested in? For example: mystery, romance, science fiction, fantasy, history, biography, etc.\n\n한국어 답변: 안녕하세요! 도서 추천 시스템에 오신 것을 환영합니다. 여러분의 취향에 맞는 다음 좋은 책을 찾는 데 도움을 드릴 수 있습니다. 어떤 장르의 책에 관심이 있으신가요? 예: 미스터리, 로맨스, SF, 판타지, 역사, 전기 등."
                
                # Add welcome message to chat history
                st.session_state.messages.append({"role": "assistant", "content": welcome_message})
                st.rerun()
            
            # Genre input with improved styling
            st.markdown('<div class="input-container">', unsafe_allow_html=True)
            genre = st.text_input("Enter a book genre you're interested in:", key="genre_input")
            
            if st.button("Submit Genre", key="submit_genre"):
                if genre:
                    st.session_state.user_genre = genre
                    st.session_state.messages.append({"role": "user", "content": f"I'm interested in {genre} books."})
                    st.session_state.app_stage = "ask_age"
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Ask for age stage
        elif st.session_state.app_stage == "ask_age":
            # Generate age question with HyperCLOVA if not already done
            if len(st.session_state.messages) == 3:  # If we just got the genre and haven't asked age yet
                if st.session_state.api_key:
                    # Copy existing messages and add age question instruction
                    messages_for_age_question = st.session_state.messages.copy()
                    messages_for_age_question.append({
                        "role": "system", 
                        "content": f"The user is interested in {st.session_state.user_genre} books. Now ask for their age range to provide age-appropriate recommendations. Remember to respond in both English and Korean."
                    })
                    
                    age_question = call_hyperclova_api(messages_for_age_question, st.session_state.api_key)
                    
                    if not age_question:
                        age_question = f"Great! I'll find some {st.session_state.user_genre} books for you. To help me recommend age-appropriate books, could you tell me your age range? For example: child (0-12), teen (13-17), young adult (18-25), adult (26+).\n\n한국어 답변: 좋습니다! {st.session_state.user_genre} 장르의 책을 찾아드리겠습니다. 연령에 맞는 책을 추천해 드리기 위해, 연령대를 알려주시겠어요? 예: 어린이(0-12세), 청소년(13-17세), 청년(18-25세), 성인(26세 이상)."
                else:
                    age_question = f"Great! I'll find some {st.session_state.user_genre} books for you. To help me recommend age-appropriate books, could you tell me your age range? For example: child (0-12), teen (13-17), young adult (18-25), adult (26+).\n\n한국어 답변: 좋습니다! {st.session_state.user_genre} 장르의 책을 찾아드리겠습니다. 연령에 맞는 책을 추천해 드리기 위해, 연령대를 알려주시겠어요? 예: 어린이(0-12세), 청소년(13-17세), 청년(18-25세), 성인(26세 이상)."
                
                st.session_state.messages.append({"role": "assistant", "content": age_question})
                st.rerun()
            
            # Age input with improved styling
            st.markdown('<div class="input-container">', unsafe_allow_html=True)
            age = st.text_input("Enter your age range:", key="age_input")
            
            if st.button("Submit Age", key="submit_age"):
                if age:
                    st.session_state.user_age = age
                    st.session_state.messages.append({"role": "user", "content": f"My age range is {age}."})
                    st.session_state.app_stage = "show_recommendations"
                    st.session_state.showing_books = False
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Book recommendations stage
        elif st.session_state.app_stage == "show_recommendations":
            if not st.session_state.showing_books:
                # Fetch book recommendations
                if st.session_state.library_api_key:
                    books = get_book_recommendations(st.session_state.user_genre, st.session_state.library_api_key)
                    
                    if not books:
                        st.warning("No books found for this genre.")
                        # Generate HyperCLOVA response for no books found
                        if st.session_state.api_key:
                            messages_for_no_books = st.session_state.messages.copy()
                            messages_for_no_books.append({
                                "role": "system", 
                                "content": f"No books were found for the genre '{st.session_state.user_genre}'. Please suggest to the user that they try a different genre. Remember to respond in both English and Korean."
                            })
                            
                            no_books_message = call_hyperclova_api(messages_for_no_books, st.session_state.api_key)
                            
                            if not no_books_message:
                                no_books_message = f"I'm sorry, but I couldn't find any books in the '{st.session_state.user_genre}' genre. Would you like to try another genre? Perhaps something similar or more common?\n\n한국어 답변: 죄송합니다만, '{st.session_state.user_genre}' 장르의 책을 찾을 수 없었습니다. 다른 장르를 시도해 보시겠어요? 아마도 비슷하거나 더 일반적인 장르가 좋을 것 같습니다."
                            
                            st.session_state.messages.append({"role": "assistant", "content": no_books_message})
                            st.session_state.app_stage = "welcome"
                            st.rerun()
                    else:
                        # Successfully found books, get AI introduction
                        # Successfully found books, get AI introduction
                        if len(st.session_state.messages) == 5:  # Only if we haven't already shown books
                            # Generate AI introduction for book recommendations
                            if st.session_state.api_key:
                                messages_for_recommendation = st.session_state.messages.copy()
                                messages_for_recommendation.append({
                                    "role": "system", 
                                    "content": f"The user is interested in {st.session_state.user_genre} books and is in the age range {st.session_state.user_age}. Tell them you're going to show some recommendations. Keep it brief and friendly. Remember to respond in both English and Korean."
                                })
                                
                                recommendation_intro = call_hyperclova_api(messages_for_recommendation, st.session_state.api_key)
                                
                                if not recommendation_intro:
                                    recommendation_intro = f"Based on your interest in {st.session_state.user_genre} books and your age range ({st.session_state.user_age}), I've found some great recommendations for you. Please take a look at these books and let me know if you'd like more information about any of them!\n\n한국어 답변: {st.session_state.user_genre} 장르에 대한 관심과 귀하의 연령대({st.session_state.user_age})를 바탕으로, 몇 가지 좋은 추천도서를 찾았습니다. 이 책들을 살펴보시고, 더 자세한 정보가 필요하시면 알려주세요!"
                            else:
                                recommendation_intro = f"Based on your interest in {st.session_state.user_genre} books and your age range ({st.session_state.user_age}), I've found some great recommendations for you. Please take a look at these books and let me know if you'd like more information about any of them!\n\n한국어 답변: {st.session_state.user_genre} 장르에 대한 관심과 귀하의 연령대({st.session_state.user_age})를 바탕으로, 몇 가지 좋은 추천도서를 찾았습니다. 이 책들을 살펴보시고, 더 자세한 정보가 필요하시면 알려주세요!"
                            
                            st.session_state.messages.append({"role": "assistant", "content": recommendation_intro})
                            st.rerun()
                        
                        # Display a divider
                        st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)
                        
                        # Display book recommendations
                        st.markdown("""
                        <h3 style="text-align: center; 
                                background: linear-gradient(90deg, #6E48AA, #FF61D2);
                                -webkit-background-clip: text;
                                -webkit-text-fill-color: transparent;
                                font-weight: 700;
                                margin-bottom: 20px;">
                            Recommended Books
                        </h3>
                        """, unsafe_allow_html=True)
                        
                        # Loop through books and display them
                        for i, book in enumerate(books):
                            display_book_card(book, i)
                        
                        st.session_state.showing_books = True
                else:
                    st.error("Library API key is required to fetch book recommendations.")
            
            # Allow user to ask more questions about genres
            st.markdown('<div class="input-container">', unsafe_allow_html=True)
            more_questions = st.text_input("Ask me anything about these books or try another genre:", key="more_questions")
            
            if st.button("Send", key="send_more_questions"):
                if more_questions:
                    # Add user message to chat
                    st.session_state.messages.append({"role": "user", "content": more_questions})
                    
                    # Check if user wants to try a different genre
                    if any(word in more_questions.lower() for word in ["different", "another", "other", "new", "change"]) and "genre" in more_questions.lower():
                        st.session_state.app_stage = "welcome"
                        st.rerun()
                    else:
                        # Otherwise generate response using HyperCLOVA
                        if st.session_state.api_key:
                            response = call_hyperclova_api(st.session_state.messages, st.session_state.api_key)
                            
                            if response:
                                st.session_state.messages.append({"role": "assistant", "content": response})
                            else:
                                st.session_state.messages.append({
                                    "role": "assistant", 
                                    "content": "I'm sorry, I couldn't process your request. Please try again or ask another question.\n\n한국어 답변: 죄송합니다. 요청을 처리할 수 없었습니다. 다시 시도하시거나 다른 질문을 해주세요."
                                })
                            st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Discuss selected book
        elif st.session_state.app_stage == "discuss_book":
            if st.session_state.selected_book:
                # Display detailed view of selected book
                display_detailed_book(st.session_state.selected_book)
                
                # Get book information
                book_info = st.session_state.selected_book
                book_title = book_info.get('bookname', 'Unknown Title')
                
                # If this is the first time showing this book, get AI description
                last_message = st.session_state.messages[-1]
                if last_message["role"] != "assistant" or book_title not in last_message["content"]:
                    if st.session_state.api_key:
                        book_author = book_info.get('authors', 'Unknown Author')
                        book_publisher = book_info.get('publisher', 'Unknown Publisher')
                        book_year = book_info.get('publication_year', 'Unknown Year')
                        
                        book_prompt = f"Tell me about the book '{book_title}' by {book_author}, published by {book_publisher} in {book_year}. Provide a brief description and why someone might enjoy this book. If you don't have specific information about this book, provide general information about this type of book/author/genre. Remember to respond in both English and Korean."
                        
                        messages_for_book = st.session_state.messages.copy()
                        messages_for_book.append({"role": "user", "content": book_prompt})
                        
                        book_description = call_hyperclova_api(messages_for_book, st.session_state.api_key)
                        
                        if not book_description:
                            book_description = f"Here's information about '{book_title}' by {book_author}. This book was published by {book_publisher} in {book_year}. While I don't have detailed plot information about this specific book, books of this type often explore themes related to {st.session_state.user_genre}. Based on your interest in this genre, you might enjoy this book for its storytelling, characters, and exploration of relevant themes.\n\n한국어 답변: {book_author}의 '{book_title}'에 대한 정보입니다. 이 책은 {book_year}년에 {book_publisher}에서 출판되었습니다. 이 특정 책에 대한 자세한 줄거리 정보는 없지만, 이런 유형의 책들은 주로 {st.session_state.user_genre}와 관련된 주제를 탐구합니다. 이 장르에 대한 귀하의 관심을 바탕으로, 이 책의 스토리텔링, 캐릭터, 그리고 관련 주제의 탐구로 인해 이 책을 즐기실 수 있을 것입니다."
                        
                        # Add this as both a user question and assistant response to the chat history
                        st.session_state.messages.append({"role": "user", "content": f"Tell me about '{book_title}'"})
                        st.session_state.messages.append({"role": "assistant", "content": book_description})
                        st.rerun()
                
                # Allow user to ask questions about the book
                st.markdown('<div class="input-container">', unsafe_allow_html=True)
                book_question = st.text_input("Ask specific questions about this book or go back to recommendations:", key="book_question")
                
                if st.button("Send", key="send_book_question"):
                    if book_question:
                        if "back" in book_question.lower() or "recommendations" in book_question.lower():
                            # Go back to recommendations
                            st.session_state.app_stage = "show_recommendations"
                            st.session_state.showing_books = False
                            st.rerun()
                        else:
                            # Add user question to chat
                            st.session_state.messages.append({"role": "user", "content": book_question})
                            
                            # Get AI response using HyperCLOVA
                            if st.session_state.api_key:
                                messages_with_context = st.session_state.messages.copy()
                                messages_with_context.append({
                                    "role": "system", 
                                    "content": f"The user is asking about the book '{book_title}'. Try to provide relevant information based on the genre ({st.session_state.user_genre}) and what you know about literature. Remember to respond in both English and Korean."
                                })
                                
                                book_response = call_hyperclova_api(messages_with_context, st.session_state.api_key)
                                
                                if book_response:
                                    st.session_state.messages.append({"role": "assistant", "content": book_response})
                                else:
                                    st.session_state.messages.append({
                                        "role": "assistant", 
                                        "content": f"I don't have specific details about that aspect of '{book_title}', but books in the {st.session_state.user_genre} genre often explore similar themes. Is there something else about this book or other books you'd like to know about?\n\n한국어 답변: '{book_title}'의 해당 측면에 대한 구체적인 세부 정보는 없지만, {st.session_state.user_genre} 장르의 책들은 종종 비슷한 주제를 탐구합니다. 이 책이나 다른 책에 대해 알고 싶은 다른 내용이 있으신가요?"
                                    })
                                st.rerun()
                
                # Button to go back to recommendations
                if st.button("← Back to All Recommendations", key="back_to_recommendations"):
                    st.session_state.app_stage = "show_recommendations"
                    st.session_state.showing_books = False
                    st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer section
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

# Run the app
if __name__ == "__main__":
    main()
