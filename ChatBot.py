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

# --- EMBEDDED API KEYS ---
HYPERCLOVA_API_KEY = "nv-270db94eb8bf42108110b22f551e655axCwf"
LIBRARY_API_KEY = "70b5336f9e785c681d5ff58906e6416124f80f59faa834164d297dcd8db63036"

add_custom_css()

import datetime
import streamlit as st
import calendar

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
    if "liked_books" not in st.session_state:
        st.session_state.liked_books = []

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

    elif st.session_state.app_stage == "show_library_and_calendar":
        add_vertical_space(2)
        st.markdown("<h3 style='text-align:center;'>📚 My Library & Reading Calendar</h3>", unsafe_allow_html=True)
        
        # Create tabs for Library and Calendar
        lib_tab, cal_tab, goals_tab = st.tabs(["📚 My Library", "📅 Reading Calendar", "🎯 Reading Goals"])
        
        with lib_tab:
            st.markdown("### ❤️ My Favorite Books")
            
            # Get liked books
            if hasattr(st.session_state, 'username') and st.session_state.username:
                liked_books = get_liked_books(st.session_state.username)
                if liked_books:
                    st.session_state.liked_books = liked_books
            
            if st.session_state.liked_books:
                st.markdown(f"**You have {len(st.session_state.liked_books)} books in your library:**")
                
                for i, book in enumerate(st.session_state.liked_books):
                    with st.container():
                        col1, col2, col3 = st.columns([1, 3, 1])
                        
                        with col1:
                            image_url = book.get("bookImageURL", "")
                            if image_url:
                                st.image(image_url, width=100)
                            else:
                                st.markdown("""
                                <div style="width: 80px; height: 100px; background: linear-gradient(135deg, #2c3040, #363c4e); 
                                            display: flex; align-items: center; justify-content: center; border-radius: 4px;">
                                    <span style="color: #b3b3cc; font-size: 10px;">No Image</span>
                                </div>
                                """, unsafe_allow_html=True)
                        
                        with col2:
                            title = book.get('bookname') or book.get('bookName', 'Unknown Title')
                            authors = book.get('authors') or book.get('author', 'Unknown Author')
                            
                            st.markdown(f"**{title}**")
                            st.markdown(f"*by {authors}*")
                            
                            # Check if book is already scheduled
                            book_scheduled = False
                            scheduled_date = None
                            for date_str, scheduled_books in st.session_state.reading_schedule.items():
                                for entry in scheduled_books:
                                    if (entry['book'].get('bookname') == title or 
                                        entry['book'].get('bookName') == title):
                                        book_scheduled = True
                                        scheduled_date = date_str
                                        break
                                if book_scheduled:
                                    break
                            
                            if book_scheduled:
                                st.success(f"📅 Scheduled for {scheduled_date}")
                            else:
                                st.info("📅 Not scheduled yet")
                        
                        with col3:
                            if st.button("💬 Discuss", key=f"discuss_liked_{i}"):
                                st.session_state.selected_book = book
                                st.session_state.book_discussion_messages = []
                                st.session_state.book_intro_shown = False
                                st.session_state.app_stage = "discuss_book"
                                st.rerun()
                            
                            if st.button("📅 Schedule", key=f"schedule_liked_{i}"):
                                st.session_state.selected_book_for_scheduling = book
                                st.session_state.show_scheduling_form = True
                                st.rerun()
                    
                    st.markdown("---")
                
                # Scheduling form
                if st.session_state.get('show_scheduling_form', False):
                    selected_book = st.session_state.get('selected_book_for_scheduling')
                    if selected_book:
                        st.markdown("### 📅 Schedule Reading")
                        
                        col1, col2, col3 = st.columns([2, 2, 1])
                        with col1:
                            target_date = st.date_input("Target completion date:", key="schedule_date")
                        
                        with col2:
                            reading_status = st.selectbox(
                                "Reading status:", 
                                ['planned', 'reading', 'completed', 'paused'],
                                key="schedule_status"
                            )
                        
                        with col3:
                            st.markdown("<br>", unsafe_allow_html=True)
                            if st.button("Add to Calendar", key="add_to_calendar"):
                                schedule_key = target_date.strftime("%Y-%m-%d")
                                if schedule_key not in st.session_state.reading_schedule:
                                    st.session_state.reading_schedule[schedule_key] = []
                                
                                # Check if book is already scheduled for this date
                                book_exists = False
                                for entry in st.session_state.reading_schedule[schedule_key]:
                                    if (entry['book'].get('bookname') == selected_book.get('bookname') or 
                                        entry['book'].get('bookName') == selected_book.get('bookName')):
                                        book_exists = True
                                        break
                                
                                if not book_exists:
                                    st.session_state.reading_schedule[schedule_key].append({
                                        'book': selected_book,
                                        'status': reading_status,
                                        'added_date': datetime.date.today().strftime("%Y-%m-%d")
                                    })
                                    st.success(f"✅ Added to your reading schedule for {target_date}")
                                else:
                                    st.warning("📚 This book is already scheduled for this date")
                                
                                st.session_state.show_scheduling_form = False
                                st.session_state.selected_book_for_scheduling = None
                                st.rerun()
                        
                        if st.button("Cancel", key="cancel_scheduling"):
                            st.session_state.show_scheduling_form = False
                            st.session_state.selected_book_for_scheduling = None
                            st.rerun()
            else:
                st.info("📚 Your library is empty. Start exploring books and add them to your favorites!")
                if st.button("🔍 Discover Books"):
                    st.session_state.app_stage = "welcome"
                    st.rerun()
        
        with cal_tab:
            st.markdown("### 📅 Your Reading Calendar")
            
            # Display calendar view
            today = datetime.date.today()
            
            # Month navigation
            col1, col2, col3 = st.columns([1, 2, 1])
            with col1:
                if st.button("◀ Previous Month", key="prev_month"):
                    if 'calendar_month' not in st.session_state:
                        st.session_state.calendar_month = today.month
                        st.session_state.calendar_year = today.year
                    
                    st.session_state.calendar_month -= 1
                    if st.session_state.calendar_month < 1:
                        st.session_state.calendar_month = 12
                        st.session_state.calendar_year -= 1
                    st.rerun()
            
            with col2:
                if 'calendar_month' not in st.session_state:
                    st.session_state.calendar_month = today.month
                    st.session_state.calendar_year = today.year
                
                st.markdown(f"<h4 style='text-align:center;'>{calendar.month_name[st.session_state.calendar_month]} {st.session_state.calendar_year}</h4>", unsafe_allow_html=True)
            
            with col3:
                if st.button("Next Month ▶", key="next_month"):
                    if 'calendar_month' not in st.session_state:
                        st.session_state.calendar_month = today.month
                        st.session_state.calendar_year = today.year
                    
                    st.session_state.calendar_month += 1
                    if st.session_state.calendar_month > 12:
                        st.session_state.calendar_month = 1
                        st.session_state.calendar_year += 1
                    st.rerun()
            
            # Generate calendar
            cal = calendar.monthcalendar(st.session_state.calendar_year, st.session_state.calendar_month)
            
            # Days of week header
            days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            cols = st.columns(7)
            for i, day in enumerate(days):
                with cols[i]:
                    st.markdown(f"<div style='text-align:center; font-weight:bold; padding: 10px;'>{day}</div>", unsafe_allow_html=True)
            
            # Calendar days
            for week in cal:
                cols = st.columns(7)
                for i, day in enumerate(week):
                    with cols[i]:
                        if day == 0:
                            st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)
                        else:
                            # Check if this date has scheduled books
                            date_str = f"{st.session_state.calendar_year}-{st.session_state.calendar_month:02d}-{day:02d}"
                            scheduled_books = st.session_state.reading_schedule.get(date_str, [])
                            
                            # Determine if this is today
                            is_today = (day == today.day and 
                                       st.session_state.calendar_month == today.month and 
                                       st.session_state.calendar_year == today.year)
                            
                            # Create day cell
                            if scheduled_books:
                                book_count = len(scheduled_books)
                                completed_count = sum(1 for entry in scheduled_books if entry['status'] == 'completed')
                                
                                color = "#4CAF50" if completed_count == book_count else "#2196F3"
                                border = "3px solid #FF9800" if is_today else "1px solid #ddd"
                                
                                st.markdown(f"""
                                <div style="height: 80px; border: {border}; border-radius: 4px; padding: 5px; 
                                           background-color: {color}; color: white; text-align: center;">
                                    <div style="font-weight: bold;">{day}</div>
                                    <div style="font-size: 12px;">📚 {book_count} book{'s' if book_count > 1 else ''}</div>
                                    <div style="font-size: 10px;">✅ {completed_count} done</div>
                                </div>
                                """, unsafe_allow_html=True)
                            else:
                                border = "3px solid #FF9800" if is_today else "1px solid #ddd"
                                background = "#f5f5f5" if is_today else "white"
                                
                                st.markdown(f"""
                                <div style="height: 80px; border: {border}; border-radius: 4px; padding: 5px; 
                                           background-color: {background}; text-align: center;">
                                    <div style="font-weight: bold; color: #333;">{day}</div>
                                </div>
                                """, unsafe_allow_html=True)
            
            # Schedule summary
            if st.session_state.reading_schedule:
                st.markdown("### 📋 Reading Schedule Summary")
                
                for date_str, books in sorted(st.session_state.reading_schedule.items()):
                    with st.expander(f"📅 {date_str} ({len(books)} book{'s' if len(books) > 1 else ''})"):
                        for i, entry in enumerate(books):
                            book = entry['book']
                            status = entry['status']
                            
                            col1, col2, col3 = st.columns([3, 1, 1])
                            with col1:
                                title = book.get('bookname') or book.get('bookName', 'Unknown Title')
                                authors = book.get('authors') or book.get('author', 'Unknown Author')
                                st.write(f"**{title}**")
                                st.write(f"*by {authors}*")
                            
                            with col2:
                                status_options = ['planned', 'reading', 'completed', 'paused']
                                status_emoji = {'planned': '📋', 'reading': '📖', 'completed': '✅', 'paused': '⏸️'}
                                
                                current_status = st.selectbox(
                                    "Status", 
                                    status_options, 
                                    index=status_options.index(status),
                                    key=f"status_{date_str}_{i}",
                                    format_func=lambda x: f"{status_emoji[x]} {x.title()}"
                                )
                                if current_status != status:
                                    st.session_state.reading_schedule[date_str][i]['status'] = current_status
                                    st.rerun()
                            
                            with col3:
                                if st.button("🗑️ Remove", key=f"remove_{date_str}_{i}"):
                                    st.session_state.reading_schedule[date_str].pop(i)
                                    if not st.session_state.reading_schedule[date_str]:
                                        del st.session_state.reading_schedule[date_str]
                                    st.rerun()
            else:
                st.info("📅 No books scheduled yet. Add books from your library to your reading schedule!")
        
        with goals_tab:
            st.markdown("### 🎯 Set Your Reading Goals")
            
            # Get current date info
            current_month = datetime.date.today().strftime("%Y-%m")
            current_year = datetime.date.today().year
            
            # Monthly reading goal
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### 📅 Monthly Goal")
                monthly_goal = st.number_input(
                    f"Books to read this month ({current_month}):", 
                    min_value=0, 
                    max_value=50, 
                    value=st.session_state.reading_goals.get(f"monthly_{current_month}", 3)
                )
                
                if st.button("Set Monthly Goal"):
                    st.session_state.reading_goals[f"monthly_{current_month}"] = monthly_goal
                    st.success(f"📅 Monthly goal set to {monthly_goal} books!")
                    st.rerun()
            
            with col2:
                st.markdown("#### 📊 Monthly Progress")
                # Calculate progress
                completed_this_month = 0
                for date_str, books in st.session_state.reading_schedule.items():
                    if date_str.startswith(current_month):
                        completed_this_month += sum(1 for entry in books if entry['status'] == 'completed')
                
                current_goal = st.session_state.reading_goals.get(f"monthly_{current_month}", 3)
                progress = min(completed_this_month / current_goal * 100, 100) if current_goal > 0 else 0
                
                st.metric("This Month's Progress", f"{completed_this_month}/{current_goal}", f"{progress:.1f}%")
                st.progress(progress / 100)
                
                if progress >= 100:
                    st.balloons()
                    st.success("🎉 Congratulations! You've reached your monthly goal!")
            
            # Yearly reading goal
            st.markdown("#### 📅 Yearly Goal")
            col1, col2 = st.columns(2)
            
            with col1:
                yearly_goal = st.number_input(
                    f"Books to read in {current_year}:", 
                    min_value=0, 
                    max_value=365, 
                    value=st.session_state.reading_goals.get(f"yearly_{current_year}", 24)
                )
                
                if st.button("Set Yearly Goal"):
                    st.session_state.reading_goals[f"yearly_{current_year}"] = yearly_goal
                    st.success(f"📅 Yearly goal set to {yearly_goal} books!")
                    st.rerun()
            
            with col2:
                # Yearly progress
                completed_this_year = 0
                for date_str, books in st.session_state.reading_schedule.items():
                    if date_str.startswith(str(current_year)):
                        completed_this_year += sum(1 for entry in books if entry['status'] == 'completed')
                
                yearly_current_goal = st.session_state.reading_goals.get(f"yearly_{current_year}", 24)
                yearly_progress = min(completed_this_year / yearly_current_goal * 100, 100) if yearly_current_goal > 0 else 0
                
                st.metric("This Year's Progress", f"{completed_this_year}/{yearly_current_goal}", f"{yearly_progress:.1f}%")
                st.progress(yearly_progress / 100)
                
                if yearly_progress >= 100:
                    st.balloons()
                    st.success("🎉 Amazing! You've reached your yearly reading goal!")
            
            # Reading statistics
            if st.session_state.reading_schedule:
                st.markdown("#### 📈 Reading Statistics")
                
                total_books = sum(len(books) for books in st.session_state.reading_schedule.values())
                completed_books = sum(sum(1 for entry in books if entry['status'] == 'completed') 
                                    for books in st.session_state.reading_schedule.values())
                reading_books = sum(sum(1 for entry in books if entry['status'] == 'reading') 
                                  for books in st.session_state.reading_schedule.values())
                planned_books = sum(sum(1 for entry in books if entry['status'] == 'planned') 
                                  for books in st.session_state.reading_schedule.values())
                paused_books = sum(sum(1 for entry in books if entry['status'] == 'paused') 
                                 for books in st.session_state.reading_schedule.values())
                
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    st.metric("📚 Total Scheduled", total_books)
                with col2:
                    st.metric("✅ Completed", completed_books)
                with col3:
                    st.metric("📖 Currently Reading", reading_books)
                with col4:
                    st.metric("📋 Planned", planned_books)
                with col5:
                    st.metric("⏸️ Paused", paused_books)
                
                # Reading completion rate
                if total_books > 0:
                    completion_rate = (completed_books / total_books) * 100
                    st.markdown(f"**Overall Completion Rate: {completion_rate:.1f}%**")
                    st.progress(completion_rate / 100)
                
                # Monthly breakdown
                st.markdown("#### 📊 Monthly Reading Breakdown")
                monthly_stats = {}
                for date_str, books in st.session_state.reading_schedule.items():
                    month_key = date_str[:7]  # YYYY-MM
                    if month_key not in monthly_stats:
                        monthly_stats[month_key] = {'total': 0, 'completed': 0}
                    
                    monthly_stats[month_key]['total'] += len(books)
                    monthly_stats[month_key]['completed'] += sum(1 for entry in books if entry['status'] == 'completed')
                
                if monthly_stats:
                    for month, stats in sorted(monthly_stats.items()):
                        completion_pct = (stats['completed'] / stats['total'] * 100) if stats['total'] > 0 else 0
                        st.write(f"**{month}**: {stats['completed']}/{stats['total']} books completed ({completion_pct:.1f}%)")
        
        # Back to main app button
        if st.button("← Back to Book Discovery", key="back_to_main_from_library"):
            st.session_state.app_stage = "show_recommendations" if st.session_state.books_data else "welcome"
            st.rerun()

    # Legacy calendar stage (keeping for backward compatibility)
    elif st.session_state.app_stage == "calendar":
        # Redirect to new merged library and calendar
        st.session_state.app_stage = "show_library_and_calendar"
        st.rerun()

    # Legacy liked books stage (keeping for backward compatibility)  
    elif st.session_state.app_stage == "show_liked_books":
        # Redirect to new merged library and calendar
        st.session_state.app_stage = "show_library_and_calendar"
        st.rerun()


# Helper function to add liked books (you may need to implement this based on your database)
def get_liked_books(username):
    """
    Retrieve liked books for a user from database
    This is a placeholder - implement based on your database structure
    """
    # Example implementation - replace with your actual database logic
    if hasattr(st.session_state, 'liked_books') and st.session_state.liked_books:
        return st.session_state.liked_books
    return []


def display_liked_book_card(book, index):
    """
    Display a liked book card with options
    """
    with st.container():
        col1, col2, col3 = st.columns([1, 3, 1])
        
        with col1:
            image_url = book.get("bookImageURL", "")
            if image_url:
                st.image(image_url, width=100)
            else:
                st.markdown("""
                <div style="width: 80px; height: 100px; background: linear-gradient(135deg, #2c3040, #363c4e); 
                            display: flex; align-items: center; justify-content: center; border-radius: 4px;">
                    <span style="color: #b3b3cc; font-size: 10px;">No Image</span>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            title = book.get('bookname') or book.get('bookName', 'Unknown Title')
            authors = book.get('authors') or book.get('author', 'Unknown Author')
            publisher = book.get('publisher', 'Unknown Publisher')
            
            st.markdown(f"**{title}**")
            st.markdown(f"*by {authors}*")
            st.markdown(f"Publisher: {publisher}")
        
        with col3:
            if st.button("💬 Discuss", key=f"discuss_liked_{index}"):
                st.session_state.selected_book = book
                st.session_state.book_discussion_messages = []
                st.session_state.book_intro_shown = False
                st.session_state.app_stage = "discuss_book"
                st.rerun()
            
            if st.button("📅 Schedule", key=f"schedule_liked_{index}"):
                st.session_state.selected_book_for_scheduling = book
                st.session_state.show_scheduling_form = True
                st.rerun()
    
    st.markdown("---")
