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

add_custom_css()

# --- Load JSON files ---
@st.cache_resource
def load_dtl_kdc_json():
    """Load only the detailed KDC JSON file"""
    with open("dtl_kdc.json", encoding="utf-8") as f:
        dtl_kdc_dict = json.load(f)
    return dtl_kdc_dict

dtl_kdc_dict = load_dtl_kdc_json()

def main():
    # --- Initialize all session state variables before use ---
    if "api_key" not in st.session_state:
        st.session_state.api_key = HYPERCLOVA_API_KEY
    if "library_api_key" not in st.session_state:
        st.session_state.library_api_key = LIBRARY_API_KEY
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
        st.session_state.reading_schedule = {}
    if "reading_goals" not in st.session_state:
        st.session_state.reading_goals = {}

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
        col1, col2 = st.columns([4, 1])
        with col1:
            user_input = st.text_input("", key="user_open_input")
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("보내다 ᯓ➤", key="send_open_input"):
                if user_input:
                    st.session_state.messages.append({"role": "user", "content": user_input})
                    st.session_state.app_stage = "process_user_input"
                    st.rerun()

    elif st.session_state.app_stage == "process_user_input":
        user_input = st.session_state.messages[-1]["content"]
    
        # Detect if it's author or genre request
        dtl_code, dtl_label = get_dtl_kdc_code(user_input, HYPERCLOVA_API_KEY)
        
        if dtl_code and LIBRARY_API_KEY:
            if dtl_code == "AUTHOR":
                # Author-based search
                author_name = dtl_label
                books = get_books_by_author(author_name, LIBRARY_API_KEY, page_no=1, page_size=20)
                
                if books:
                    st.session_state.books_data = books
                    
                    # Generate AI response about the author's books
                    if HYPERCLOVA_API_KEY:
                        ai_response = call_hyperclova_api([
                            {"role": "system", "content": "You are a helpful book recommendation assistant. For EVERY response, answer in BOTH English and Korean. First provide complete English answer, then '한국어 답변:' with Korean translation."},
                            {"role": "user", "content": f"I found {len(books)} books by {author_name}. Tell me about this author and encourage me to explore their works."}
                        ], HYPERCLOVA_API_KEY)
                        
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
                books = get_books_by_dtl_kdc(dtl_code, LIBRARY_API_KEY, page_no=1, page_size=20)
                
                if books:
                    st.session_state.books_data = books
                    
                    # Generate AI response about the recommendations using HyperCLOVA
                    if HYPERCLOVA_API_KEY:
                        ai_response = call_hyperclova_api([
                            {"role": "system", "content": "You are a helpful book recommendation assistant. For EVERY response, answer in BOTH English and Korean. First provide complete English answer, then '한국어 답변:' with Korean translation."},
                            {"role": "user", "content": f"I found {len(books)} books in the {dtl_label} category. Tell me about this category and encourage me to explore these recommendations."}
                        ], HYPERCLOVA_API_KEY)
                        
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
            if not LIBRARY_API_KEY:
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
        st.markdown("<h3 style='text-align:center;'>📖 Recommended Books for You</h3>", unsafe_allow_html=True)
        
        # Display books
        for i, book in enumerate(st.session_state.books_data[:10]):  # Show top 10 books
            display_book_card(book, i)
        
        # Chat input for follow-up questions
        col1, col2 = st.columns([4, 1])
        with col1:
            user_followup = st.text_input("Ask me anything about these books or request different recommendations:", key="followup_input")
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("보내다 ᯓ➤", key="send_followup"):
                if user_followup:
                    st.session_state.messages.append({"role": "user", "content": user_followup})
                    
                    # Check if user wants new recommendations
                    if any(keyword in user_followup.lower() for keyword in ['different', 'other', 'new', 'more', '다른', '새로운', '더']):
                        st.session_state.app_stage = "process_user_input"
                    else:
                        # Process as follow-up question using HyperCLOVA
                        response = process_followup_with_hyperclova(user_followup, HYPERCLOVA_API_KEY)
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
            st.markdown("<h3 style='text-align:center;'>📖 Let's Talk About This Book</h3>", unsafe_allow_html=True)
            
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
                intro_message = generate_book_introduction(book, HYPERCLOVA_API_KEY)
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
            col1, col2 = st.columns([4, 1])
            with col1:
                book_question = st.text_input(
                    "Ask me anything about this book (plot, themes, similar books, etc.):", 
                    key=f"book_discussion_input_{len(st.session_state.book_discussion_messages)}"
                )
            
            with col2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("보내다 ᯓ➤", key=f"ask_about_book_{len(st.session_state.book_discussion_messages)}"):
                    if book_question:
                        # Add user message to book discussion
                        user_msg = {"role": "user", "content": book_question}
                        st.session_state.book_discussion_messages.append(user_msg)
                        
                        # Generate AI response about the book using HyperCLOVA
                        ai_response = process_book_question(
                            book, 
                            book_question, 
                            HYPERCLOVA_API_KEY,
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
        st.markdown("<h3 style='text-align:center;'>❤️ My Library</h3>", unsafe_allow_html=True)
        
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

    elif st.session_state.app_stage == "calendar":
        # Reading Calendar and Goals Feature
        add_vertical_space(2)
        st.markdown("<h3 style='text-align:center;'>📅 Reading Calendar & Goals</h3>", unsafe_allow_html=True)
        
        # Navigation tabs
        cal_tab1, cal_tab2 = st.tabs(["📅 Reading Schedule", "🎯 Reading Goals"])
        
        with cal_tab1:
            st.markdown("### Plan Your Reading Journey")
            
            # Add book to schedule
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.session_state.books_data:
                    book_options = [f"{book.get('bookname', 'Unknown')} - {book.get('authors', 'Unknown Author')}" 
                                  for book in st.session_state.books_data[:10]]
                    selected_book_idx = st.selectbox("Select a book to schedule:", 
                                                   range(len(book_options)), 
                                                   format_func=lambda x: book_options[x])
                else:
                    st.info("No books available. Please search for books first.")
                    selected_book_idx = None
            
            with col2:
                target_date = st.date_input("Target completion date:")
            
            if st.button("Add to Schedule") and selected_book_idx is not None:
                book = st.session_state.books_data[selected_book_idx]
                schedule_key = str(target_date)
                if schedule_key not in st.session_state.reading_schedule:
                    st.session_state.reading_schedule[schedule_key] = []
                st.session_state.reading_schedule[schedule_key].append({
                    'book': book,
                    'status': 'planned',
                    'added_date': str(datetime.date.today())
                })
                st.success(f"Added to your reading schedule for {target_date}")
                st.rerun()
            
            # Display current schedule
            if st.session_state.reading_schedule:
                st.markdown("### Your Reading Schedule")
                
                for date_str, books in sorted(st.session_state.reading_schedule.items()):
                    with st.expander(f"📅 {date_str} ({len(books)} books)"):
                        for i, entry in enumerate(books):
                            book = entry['book']
                            status = entry['status']
                            
                            col1, col2, col3 = st.columns([3, 1, 1])
                            with col1:
                                st.write(f"**{book.get('bookname', 'Unknown')}**")
                                st.write(f"*by {book.get('authors', 'Unknown Author')}*")
                            
                            with col2:
                                status_options = ['planned', 'reading', 'completed', 'paused']
                                current_status = st.selectbox(
                                    "Status", 
                                    status_options, 
                                    index=status_options.index(status),
                                    key=f"status_{date_str}_{i}"
                                )
                                if current_status != status:
                                    st.session_state.reading_schedule[date_str][i]['status'] = current_status
                                    st.rerun()
                            
                            with col3:
                                if st.button("Remove", key=f"remove_{date_str}_{i}"):
                                    st.session_state.reading_schedule[date_str].pop(i)
                                    if not st.session_state.reading_schedule[date_str]:
                                        del st.session_state.reading_schedule[date_str]
                                    st.rerun()
            else:
                st.info("No books scheduled yet. Add some books to your reading schedule!")
        
        with cal_tab2:
            st.markdown("### Set Your Reading Goals")
            
            # Monthly reading goal
            col1, col2 = st.columns(2)
            with col1:
                current_month = datetime.date.today().strftime("%Y-%m")
                monthly_goal = st.number_input(
                    f"Books to read this month ({current_month}):", 
                    min_value=0, 
                    max_value=50, 
                    value=st.session_state.reading_goals.get(f"monthly_{current_month}", 3)
                )
                
                if st.button("Set Monthly Goal"):
                    st.session_state.reading_goals[f"monthly_{current_month}"] = monthly_goal
                    st.success(f"Monthly goal set to {monthly_goal} books!")
                    st.rerun()
            
            with col2:
                # Calculate progress
                completed_this_month = 0
                for date_str, books in st.session_state.reading_schedule.items():
                    if date_str.startswith(current_month):
                        completed_this_month += sum(1 for entry in books if entry['status'] == 'completed')
                
                current_goal = st.session_state.reading_goals.get(f"monthly_{current_month}", 3)
                progress = min(completed_this_month / current_goal * 100, 100) if current_goal > 0 else 0
                
                st.metric("This Month's Progress", f"{completed_this_month}/{current_goal}", f"{progress:.1f}%")
                st.progress(progress / 100)
            
            # Yearly reading goal
            current_year = datetime.date.today().year
            yearly_goal = st.number_input(
                f"Books to read in {current_year}:", 
                min_value=0, 
                max_value=365, 
                value=st.session_state.reading_goals.get(f"yearly_{current_year}", 24)
            )
            
            if st.button("Set Yearly Goal"):
                st.session_state.reading_goals[f"yearly_{current_year}"] = yearly_goal
                st.success(f"Yearly goal set to {yearly_goal} books!")
                st.rerun()
            
            # Yearly progress
            completed_this_year = 0
            for date_str, books in st.session_state.reading_schedule.items():
                if date_str.startswith(str(current_year)):
                    completed_this_year += sum(1 for entry in books if entry['status'] == 'completed')
            
            yearly_current_goal = st.session_state.reading_goals.get(f"yearly_{current_year}", 24)
            yearly_progress = min(completed_this_year / yearly_current_goal * 100, 100) if yearly_current_goal > 0 else 0
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("This Year's Progress", f"{completed_this_year}/{yearly_current_goal}", f"{yearly_progress:.1f}%")
            with col2:
                st.progress(yearly_progress / 100)
            
            # Reading statistics
            if st.session_state.reading_schedule:
                st.markdown("### Reading Statistics")
                
                total_books = sum(len(books) for books in st.session_state.reading_schedule.values())
                completed_books = sum(sum(1 for entry in books if entry['status'] == 'completed') 
                                    for books in st.session_state.reading_schedule.values())
                reading_books = sum(sum(1 for entry in books if entry['status'] == 'reading') 
                                  for books in st.session_state.reading_schedule.values())
                planned_books = sum(sum(1 for entry in books if entry['status'] == 'planned') 
                                  for books in st.session_state.reading_schedule.values())
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Scheduled", total_books)
                with col2:
                    st.metric("Completed", completed_books)
                with col3:
                    st.metric("Currently Reading", reading_books)
                with col4:
                    st.metric("Planned", planned_books)
        
        # Back to main app button
        if st.button("← Back to Book Discovery", key="back_to_main_from_calendar"):
            st.session_state.app_stage = "show_recommendations" if st.session_state.books_data else "welcome"
            st.rerun()
