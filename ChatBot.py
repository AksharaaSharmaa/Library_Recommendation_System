import streamlit as st
import requests
from streamlit_extras.colored_header import colored_header
import base64
from Frontend import add_custom_css
from pymongo.errors import DuplicateKeyError
import streamlit as st
import requests
import json
from datetime import datetime, date
from difflib import SequenceMatcher
from streamlit_extras.add_vertical_space import add_vertical_space
import requests
import os
from PIL import Image, ImageDraw, ImageFont
import io
import hashlib
import random
from Helper_Functions import *
import calendar

# --- EMBEDDED API KEYS ---
HYPERCLOVA_API_KEY = "nv-270db94eb8bf42108110b22f551e655axCwf"
LIBRARY_API_KEY = "70b5336f9e785c681d5ff58906e6416124f80f59faa834164d297dcd8db63036"

add_custom_css()

import streamlit as st
import datetime
import calendar
import json
from datetime import timedelta
import pandas as pd

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
    if "liked_books" not in st.session_state:
        st.session_state.liked_books = {}
    if "reading_schedule" not in st.session_state:
        st.session_state.reading_schedule = {}
    if "selected_library_book" not in st.session_state:
        st.session_state.selected_library_book = None
    if "calendar_view" not in st.session_state:
        st.session_state.calendar_view = datetime.datetime.now().replace(day=1)

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
        
        # Enhanced Library Header with Tabs
        st.markdown("<h3 style='text-align:center;'>❤️ My Reading Library / 나의 독서 도서관</h3>", unsafe_allow_html=True)
        
        # Create tabs for different views
        library_tab1, library_tab2, library_tab3 = st.tabs(["📚 My Books", "📅 Reading Calendar", "📊 Reading Schedule"])
        
        with library_tab1:
            # Category filter
            col1, col2, col3 = st.columns(3)
            with col1:
                show_to_read = st.checkbox("To Be Read / 읽을 예정", value=True)
            with col2:
                show_ongoing = st.checkbox("Currently Reading / 읽는 중", value=True)
            with col3:
                show_finished = st.checkbox("Finished / 완료", value=True)
            
            if hasattr(st.session_state, 'username') and st.session_state.username:
                liked_books = get_liked_books(st.session_state.username)
            else:
                liked_books = list(st.session_state.liked_books.values())
            
            if liked_books:
                # Group books by category
                categories = {
                    "to_read": [book for book in liked_books if book.get('reading_status') == 'to_read'],
                    "ongoing": [book for book in liked_books if book.get('reading_status') == 'ongoing'],
                    "finished": [book for book in liked_books if book.get('reading_status') == 'finished']
                }
                
                # Display books by category
                if show_to_read and categories["to_read"]:
                    st.markdown("### 📖 To Be Read / 읽을 예정")
                    for i, book in enumerate(categories["to_read"]):
                        display_enhanced_library_book_card(book, f"to_read_{i}")
                
                if show_ongoing and categories["ongoing"]:
                    st.markdown("### 📚 Currently Reading / 읽는 중")
                    for i, book in enumerate(categories["ongoing"]):
                        display_enhanced_library_book_card(book, f"ongoing_{i}")
                
                if show_finished and categories["finished"]:
                    st.markdown("### ✅ Finished / 완료")
                    for i, book in enumerate(categories["finished"]):
                        display_enhanced_library_book_card(book, f"finished_{i}")
                
                if not any([categories["to_read"], categories["ongoing"], categories["finished"]]):
                    st.info("No books match the selected filters. / 선택한 필터와 일치하는 책이 없습니다.")
            else:
                st.markdown("Your library is empty. Start exploring books to add them to your collection!")
                st.markdown("도서관이 비어 있습니다. 책을 탐색하여 컬렉션에 추가하세요!")
                if st.button("Discover Books / 책 발견하기"):
                    st.session_state.app_stage = "welcome"
                    st.rerun()
        
        with library_tab2:
            # Reading Calendar View
            st.markdown("### 📅 Reading Calendar / 독서 캘린더")
            
            # Calendar navigation
            col1, col2, col3 = st.columns([1, 2, 1])
            with col1:
                if st.button("◀ Previous Month", key="prev_month"):
                    current_date = st.session_state.calendar_view
                    if current_date.month == 1:
                        st.session_state.calendar_view = current_date.replace(year=current_date.year-1, month=12)
                    else:
                        st.session_state.calendar_view = current_date.replace(month=current_date.month-1)
                    st.rerun()
            
            with col2:
                st.markdown(f"<h4 style='text-align:center;'>{st.session_state.calendar_view.strftime('%B %Y')}</h4>", unsafe_allow_html=True)
            
            with col3:
                if st.button("Next Month ▶", key="next_month"):
                    current_date = st.session_state.calendar_view
                    if current_date.month == 12:
                        st.session_state.calendar_view = current_date.replace(year=current_date.year+1, month=1)
                    else:
                        st.session_state.calendar_view = current_date.replace(month=current_date.month+1)
                    st.rerun()
            
            # Generate calendar
            display_reading_calendar(st.session_state.calendar_view)
        
        with library_tab3:
            # Reading Schedule Management
            st.markdown("### 📊 Reading Schedule / 독서 일정")
            
            # Show current reading schedules
            active_schedules = {k: v for k, v in st.session_state.reading_schedule.items() 
                              if v.get('status') == 'active'}
            
            if active_schedules:
                st.markdown("#### Active Reading Schedules / 활성 독서 일정")
                for book_id, schedule in active_schedules.items():
                    display_reading_schedule_card(schedule, book_id)
            else:
                st.info("No active reading schedules. Set up a reading plan for your books! / 활성 독서 일정이 없습니다. 책에 대한 독서 계획을 세워보세요!")
            
            # Quick stats
            if active_schedules:
                st.markdown("#### Reading Statistics / 독서 통계")
                col1, col2, col3 = st.columns(3)
                
                total_books = len(active_schedules)
                total_hours = sum(schedule.get('total_hours', 0) for schedule in active_schedules.values())
                avg_daily_hours = sum(schedule.get('daily_hours', 0) for schedule in active_schedules.values())
                
                with col1:
                    st.metric("Books in Progress", total_books)
                with col2:
                    st.metric("Total Reading Hours", f"{total_hours:.1f}")
                with col3:
                    st.metric("Daily Reading Time", f"{avg_daily_hours:.1f}h")
        
        # Back to main app button
        if st.button("← Back to Book Discovery", key="back_to_main"):
            st.session_state.app_stage = "show_recommendations" if st.session_state.books_data else "welcome"
            st.rerun()

    # Handle book schedule setup
    elif st.session_state.app_stage == "setup_reading_schedule":
        if st.session_state.selected_library_book:
            setup_reading_schedule_interface(st.session_state.selected_library_book)

def display_enhanced_library_book_card(book, card_key):
    """Display enhanced book card with reading status and schedule options"""
    title = book.get('bookname') or book.get('bookName', 'Unknown Title')
    authors = book.get('authors') or book.get('author', 'Unknown Author')
    status = book.get('reading_status', 'to_read')
    
    # Status colors and icons
    status_config = {
        'to_read': {'color': '#3498db', 'icon': '📖', 'text': 'To Read'},
        'ongoing': {'color': '#f39c12', 'icon': '📚', 'text': 'Reading'},
        'finished': {'color': '#27ae60', 'icon': '✅', 'text': 'Finished'}
    }
    
    config = status_config.get(status, status_config['to_read'])
    
    with st.container():
        col1, col2, col3, col4 = st.columns([1, 3, 2, 1])
        
        with col1:
            image_url = book.get("bookImageURL", "")
            if image_url:
                st.image(image_url, width=80)
            else:
                st.markdown("""
                <div style="width: 60px; height: 80px; background: linear-gradient(135deg, #2c3040, #363c4e); 
                            display: flex; align-items: center; justify-content: center; border-radius: 4px;">
                    <span style="color: #b3b3cc; font-size: 12px;">📚</span>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="padding: 10px;">
                <h4 style="margin: 0; color: #2c3040;">{title}</h4>
                <p style="margin: 5px 0; color: #666; font-size: 14px;">{authors}</p>
                <span style="background-color: {config['color']}; color: white; padding: 2px 8px; 
                      border-radius: 12px; font-size: 12px;">
                    {config['icon']} {config['text']}
                </span>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            # Show schedule info if exists
            book_id = book.get('id', str(hash(title + authors)))
            schedule = st.session_state.reading_schedule.get(book_id)
            
            if schedule and status == 'ongoing':
                progress = calculate_reading_progress(schedule)
                st.markdown(f"""
                <div style="padding: 10px; font-size: 12px;">
                    <div>Progress: {progress:.1f}%</div>
                    <div>Start: {schedule.get('start_date', 'N/A')}</div>
                    <div>End: {schedule.get('end_date', 'N/A')}</div>
                    <div>Daily: {schedule.get('daily_hours', 0):.1f}h</div>
                </div>
                """, unsafe_allow_html=True)
            elif status == 'finished' and schedule:
                st.markdown(f"""
                <div style="padding: 10px; font-size: 12px; color: #27ae60;">
                    <div>✅ Completed</div>
                    <div>Finished: {schedule.get('actual_end_date', 'N/A')}</div>
                </div>
                """, unsafe_allow_html=True)
        
        with col4:
            # Action buttons
            if status == 'to_read':
                if st.button("Start Reading", key=f"start_{card_key}"):
                    book['reading_status'] = 'ongoing'
                    st.session_state.selected_library_book = book
                    st.session_state.app_stage = "setup_reading_schedule"
                    st.rerun()
            elif status == 'ongoing':
                col4a, col4b = st.columns(2)
                with col4a:
                    if st.button("📅", key=f"schedule_{card_key}", help="Manage Schedule"):
                        st.session_state.selected_library_book = book
                        st.session_state.app_stage = "setup_reading_schedule"
                        st.rerun()
                with col4b:
                    if st.button("✅", key=f"finish_{card_key}", help="Mark as Finished"):
                        book['reading_status'] = 'finished'
                        book_id = book.get('id', str(hash(title + authors)))
                        if book_id in st.session_state.reading_schedule:
                            st.session_state.reading_schedule[book_id]['status'] = 'completed'
                            st.session_state.reading_schedule[book_id]['actual_end_date'] = datetime.datetime.now().strftime('%Y-%m-%d')
                        update_liked_book(book)
                        st.rerun()
            else:  # finished
                if st.button("🔄", key=f"reread_{card_key}", help="Read Again"):
                    book['reading_status'] = 'to_read'
                    update_liked_book(book)
                    st.rerun()

def setup_reading_schedule_interface(book):
    """Interface for setting up reading schedule"""
    st.markdown("### 📅 Setup Reading Schedule / 독서 일정 설정")
    
    title = book.get('bookname') or book.get('bookName', 'Unknown Title')
    authors = book.get('authors') or book.get('author', 'Unknown Author')
    book_id = book.get('id', str(hash(title + authors)))
    
    # Display book info
    col1, col2 = st.columns([1, 3])
    with col1:
        image_url = book.get("bookImageURL", "")
        if image_url:
            st.image(image_url, width=150)
        else:
            st.markdown("""
            <div style="width: 120px; height: 160px; background: linear-gradient(135deg, #2c3040, #363c4e); 
                        display: flex; align-items: center; justify-content: center; border-radius: 8px;">
                <span style="color: #b3b3cc;">📚</span>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="padding: 20px;">
            <h3 style="color: #2c3040; margin-bottom: 10px;">{title}</h3>
            <p style="color: #666; margin-bottom: 5px;"><strong>Author:</strong> {authors}</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Get existing schedule if any
    existing_schedule = st.session_state.reading_schedule.get(book_id, {})
    
    # Schedule input form
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Reading Plan / 독서 계획")
        
        # Estimated pages (user input or default)
        estimated_pages = st.number_input(
            "Estimated number of pages / 예상 페이지 수",
            min_value=1,
            max_value=2000,
            value=existing_schedule.get('pages', 300),
            help="Enter the approximate number of pages in this book"
        )
        
        # Daily reading hours
        daily_hours = st.number_input(
            "Daily reading hours / 일일 독서 시간",
            min_value=0.1,
            max_value=12.0,
            value=existing_schedule.get('daily_hours', 1.0),
            step=0.1,
            help="How many hours per day can you dedicate to reading this book?"
        )
        
        # Reading speed (pages per hour)
        reading_speed = st.number_input(
            "Reading speed (pages per hour) / 독서 속도 (시간당 페이지)",
            min_value=1,
            max_value=100,
            value=existing_schedule.get('reading_speed', 20),
            help="On average, how many pages can you read per hour?"
        )
    
    with col2:
        st.markdown("#### Schedule Details / 일정 세부사항")
        
        # Start date
        start_date = st.date_input(
            "Reading start date / 독서 시작일",
            value=datetime.datetime.strptime(existing_schedule.get('start_date', datetime.datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d').date() if existing_schedule.get('start_date') else datetime.datetime.now().date(),
            help="When do you plan to start reading this book?"
        )
        
        # Calculate estimated completion
        total_hours_needed = estimated_pages / reading_speed
        days_needed = total_hours_needed / daily_hours
        estimated_end_date = start_date + timedelta(days=int(days_needed))
        
        st.info(f"""
        **Reading Estimation / 독서 예상:**
        - Total reading time needed: {total_hours_needed:.1f} hours / 총 필요 독서 시간: {total_hours_needed:.1f}시간
        - Estimated completion: {days_needed:.0f} days / 예상 완료: {days_needed:.0f}일
        - Target finish date: {estimated_end_date.strftime('%Y-%m-%d')} / 목표 완료일: {estimated_end_date.strftime('%Y-%m-%d')}
        """)
        
        # Reading preferences
        st.markdown("#### Reading Preferences / 독서 선호도")
        
        reading_days = st.multiselect(
            "Reading days / 독서 요일",
            options=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
            default=existing_schedule.get('reading_days', ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']),
            help="Select the days you plan to read"
        )
        
        reminder_enabled = st.checkbox(
            "Enable reading reminders / 독서 알림 활성화",
            value=existing_schedule.get('reminder_enabled', True),
            help="Get daily reminders for your reading schedule"
        )
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Save Schedule / 일정 저장", type="primary"):
            # Create or update schedule
            schedule_data = {
                'book_id': book_id,
                'book_title': title,
                'book_author': authors,
                'pages': estimated_pages,
                'daily_hours': daily_hours,
                'reading_speed': reading_speed,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': estimated_end_date.strftime('%Y-%m-%d'),
                'total_hours': total_hours_needed,
                'reading_days': reading_days,
                'reminder_enabled': reminder_enabled,
                'status': 'active',
                'created_date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'progress': 0.0
            }
            
            # Save to session state
            st.session_state.reading_schedule[book_id] = schedule_data
            
            # Update book status
            book['reading_status'] = 'ongoing'
            update_liked_book(book)
            
            st.success("Reading schedule saved successfully! / 독서 일정이 성공적으로 저장되었습니다!")
            st.session_state.app_stage = "show_liked_books"
            st.rerun()
    
    with col2:
        if st.button("🗑️ Delete Schedule / 일정 삭제"):
            if book_id in st.session_state.reading_schedule:
                del st.session_state.reading_schedule[book_id]
                st.success("Schedule deleted / 일정이 삭제되었습니다")
                st.session_state.app_stage = "show_liked_books"
                st.rerun()
    
    with col3:
        if st.button("← Back to Library / 도서관으로 돌아가기"):
            st.session_state.app_stage = "show_liked_books"
            st.rerun()

def display_reading_calendar(current_date):
    """Display interactive reading calendar"""
    year = current_date.year
    month = current_date.month
    
    # Get calendar for the month
    cal = calendar.monthcalendar(year, month)
    
    # Days of week headers
    days_of_week = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    
    # Create calendar HTML
    calendar_html = "<table style='width: 100%; border-collapse: collapse; margin: 20px 0;'>"
    
    # Header row
    calendar_html += "<tr>"
    for day in days_of_week:
        calendar_html += f"<th style='padding: 10px; background-color: #f0f0f0; border: 1px solid #ddd; text-align: center;'>{day}</th>"
    calendar_html += "</tr>"
    
    # Calendar rows
    for week in cal:
        calendar_html += "<tr>"
        for day in week:
            if day == 0:
                calendar_html += "<td style='padding: 10px; border: 1px solid #ddd; height: 80px;'></td>"
            else:
                date_str = f"{year}-{month:02d}-{day:02d}"
                scheduled_books = get_books_for_date(date_str)
                
                cell_content = f"<div style='font-weight: bold; margin-bottom: 5px;'>{day}</div>"
                
                if scheduled_books:
                    for book_info in scheduled_books[:2]:  # Show max 2 books per day
                        cell_content += f"<div style='font-size: 10px; background-color: #e3f2fd; padding: 2px 4px; margin: 1px 0; border-radius: 3px; overflow: hidden; white-space: nowrap; text-overflow: ellipsis;'>{book_info}</div>"
                    
                    if len(scheduled_books) > 2:
                        cell_content += f"<div style='font-size: 10px; color: #666;'>+{len(scheduled_books) - 2} more</div>"
                    
                    cell_color = "#e8f5e8"
                else:
                    cell_color = "#ffffff"
                
                calendar_html += f"<td style='padding: 5px; border: 1px solid #ddd; height: 80px; background-color: {cell_color}; vertical-align: top;'>{cell_content}</td>"
        
        calendar_html += "</tr>"
    
    calendar_html += "</table>"
    
    st.markdown(calendar_html, unsafe_allow_html=True)
    
    # Legend
    st.markdown("""
    <div style='margin-top: 20px; padding: 10px; background-color: #f9f9f9; border-radius: 5px;'>
        <strong>Legend / 범례:</strong><br>
        <span style='display: inline-block; width: 15px; height: 15px; background-color: #e8f5e8; margin-right: 5px; border: 1px solid #ddd;'></span> Days with reading scheduled / 독서가 예정된 날<br>
        <span style='display: inline-block; width: 15px; height: 15px; background-color: #ffffff; margin-right: 5px; border: 1px solid #ddd;'></span> Free days / 자유로운 날
    </div>
    """, unsafe_allow_html=True)

def display_reading_schedule_card(schedule, book_id):
    """Display reading schedule card with progress"""
    with st.container():
        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
        
        with col1:
            st.markdown(f"""
            <div style="padding: 10px;">
                <h4 style="margin: 0; color: #2c3040;">{schedule.get('book_title', 'Unknown')}</h4>
                <p style="margin: 5px 0; color: #666; font-size: 12px;">{schedule.get('book_author', 'Unknown Author')}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            progress = calculate_reading_progress(schedule)
            days_elapsed = (datetime.datetime.now().date() - datetime.datetime.strptime(schedule.get('start_date', ''), '%Y-%m-%d').date()).days
            total_days = (datetime.datetime.strptime(schedule.get('end_date', ''), '%Y-%m-%d').date() - datetime.datetime.strptime(schedule.get('start_date', ''), '%Y-%m-%d').date()).days
            
            st.markdown(f"""
            <div style="padding: 10px; font-size: 12px;">
                <div>Progress: {progress:.1f}%</div>
                <div>Day {days_elapsed + 1} of {total_days + 1}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Progress bar
            st.progress(progress / 100.0)
        
        with col3:
            st.markdown(f"""
            <div style="padding: 10px; font-size: 12px;">
                <div>Daily: {schedule.get('daily_hours', 0):.1f}h</div>
                <div>Target: {schedule.get('end_date', 'N/A')}</div>
                <div>Total: {schedule.get('total_hours', 0):.1f}h</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            if st.button("📝", key=f"edit_schedule_{book_id}", help="Edit Schedule"):
                # Find the book and set it for editing
                for book in st.session_state.liked_books.values():
                    if book.get('id', str(hash(book.get('bookname', '') + book.get('authors', '')))) == book_id:
                        st.session_state.selected_library_book = book
                        st.session_state.app_stage = "setup_reading_schedule"
                        st.rerun()
                        break

def get_books_for_date(date_str):
    """Get list of books scheduled for a specific date"""
    books_for_date = []
    
    for schedule in st.session_state.reading_schedule.values():
        if schedule.get('status') != 'active':
            continue
            
        start_date = datetime.datetime.strptime(schedule.get('start_date', ''), '%Y-%m-%d').date()
        end_date = datetime.datetime.strptime(schedule.get('end_date', ''), '%Y-%m-%d').date()
        target_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        
        if start_date <= target_date <= end_date:
            # Check if this day is in reading_days
            reading_days = schedule.get('reading_days', [])
            day_name = target_date.strftime('%A')
            
            if day_name in reading_days:
                book_title = schedule.get('book_title', 'Unknown')
                daily_hours = schedule.get('daily_hours', 0)
                books_for_date.append(f"{book_title[:20]}... ({daily_hours}h)" if len(book_title) > 20 else f"{book_title} ({daily_hours}h)")
    
    return books_for_date

def calculate_reading_progress(schedule):
    """Calculate reading progress based on elapsed time"""
    if not schedule.get('start_date') or not schedule.get('end_date'):
        return 0.0
    
    start_date = datetime.datetime.strptime(schedule.get('start_date'), '%Y-%m-%d').date()
    end_date = datetime.datetime.strptime(schedule.get('end_date'), '%Y-%m-%d').date()
    current_date = datetime.datetime.now().date()
    
    if current_date < start_date:
        return 0.0
    elif current_date > end_date:
        return 100.0
    else:
        total_days = (end_date - start_date).days
        elapsed_days = (current_date - start_date).days
        return (elapsed_days / total_days) * 100.0 if total_days > 0 else 0.0

def update_liked_book(book):
    """Update liked book in session state"""
    book_id = book.get('id', str(hash(book.get('bookname', '') + book.get('authors', ''))))
    st.session_state.liked_books[book_id] = book

def get_liked_books(username):
    """Get liked books for a user (placeholder for actual database integration)"""
    # This would typically query a database
    # For now, return books from session state
    return list(st.session_state.liked_books.values())

# Additional helper functions that would be needed
def add_vertical_space(lines):
    """Add vertical space"""
    for _ in range(lines):
        st.write("")

def display_message(msg):
    """Display chat message"""
    role = msg.get("role", "user")
    content = msg.get("content", "")
    
    if role == "user":
        st.markdown(f"""
        <div style="display: flex; justify-content: flex-end; margin: 10px 0;">
            <div style="background-color: #007bff; color: white; padding: 10px 15px; border-radius: 15px; max-width: 70%;">
                {content}
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="display: flex; justify-content: flex-start; margin: 10px 0;">
            <div style="background-color: #f1f1f1; color: #333; padding: 10px 15px; border-radius: 15px; max-width: 70%;">
                {content}
            </div>
        </div>
        """, unsafe_allow_html=True)

def display_book_card(book, index):
    """Display book recommendation card"""
    title = book.get('bookname') or book.get('bookName', 'Unknown Title')
    authors = book.get('authors') or book.get('author', 'Unknown Author')
    
    with st.container():
        col1, col2, col3 = st.columns([1, 3, 1])
        
        with col1:
            image_url = book.get("bookImageURL", "")
            if image_url:
                st.image(image_url, width=100)
            else:
                st.markdown("📚", unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"**{title}**")
            st.markdown(f"*{authors}*")
        
        with col3:
            if st.button("❤️ Add to Library", key=f"add_to_library_{index}"):
                book['reading_status'] = 'to_read'
                book_id = book.get('id', str(hash(title + authors)))
                book['id'] = book_id
                st.session_state.liked_books[book_id] = book
                st.success("Added to library!")
                st.rerun()
