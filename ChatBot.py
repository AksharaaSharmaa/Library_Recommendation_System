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
    if "book_categories" not in st.session_state:
        st.session_state.book_categories = {}  # book_id: {category, status}
    if "selected_category_filter" not in st.session_state:
        st.session_state.selected_category_filter = "All"

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
        # Beautiful Library Header
        st.markdown("""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 40px 20px; margin: -20px -20px 30px -20px; text-align: center; border-radius: 0 0 20px 20px;'>
            <h1 style='color: white; margin: 0; font-size: 2.5em; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);'>
                📖 My Personal Library
            </h1>
            <p style='color: rgba(255,255,255,0.9); margin-top: 10px; font-size: 1.2em;'>
                나만의 도서관 • Your Reading Journey
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        if hasattr(st.session_state, 'username') and st.session_state.username:
            liked_books = get_liked_books(st.session_state.username)
            
            # Modern Category Filter Tabs
            st.markdown("""
            <style>
            .category-tabs {
                display: flex;
                justify-content: center;
                margin-bottom: 30px;
                gap: 10px;
            }
            .tab-button {
                padding: 12px 24px;
                border: none;
                border-radius: 25px;
                cursor: pointer;
                font-weight: 500;
                transition: all 0.3s ease;
                font-size: 14px;
            }
            .tab-active {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
            }
            .tab-inactive {
                background: #f8f9fa;
                color: #6c757d;
                border: 2px solid #e9ecef;
            }
            .tab-inactive:hover {
                background: #e9ecef;
                color: #495057;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Category tabs
            col1, col2, col3, col4 = st.columns(4)
            categories = ["All", "To Read", "Ongoing", "Finished"]
            category_icons = {"All": "📚", "To Read": "🔖", "Ongoing": "📖", "Finished": "✅"}
            
            for i, category in enumerate(categories):
                with [col1, col2, col3, col4][i]:
                    is_active = st.session_state.selected_category_filter == category
                    if st.button(
                        f"{category_icons[category]} {category}", 
                        key=f"filter_{category.lower().replace(' ', '_')}",
                        use_container_width=True
                    ):
                        st.session_state.selected_category_filter = category
                        st.rerun()
            
            st.markdown("---")
            
            if liked_books:
                # Filter books based on selected category
                filtered_books = []
                category_counts = {"To Read": 0, "Ongoing": 0, "Finished": 0}
                
                for book in liked_books:
                    book_id = str(book.get('id', '')) or book.get('bookname', '') or book.get('bookName', '')
                    book_category = st.session_state.book_categories.get(book_id, {}).get('category', 'To Read')
                    category_counts[book_category] += 1
                    
                    if st.session_state.selected_category_filter == "All" or book_category == st.session_state.selected_category_filter:
                        filtered_books.append(book)
                
                # Stats Section
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                           padding: 20px; border-radius: 15px; margin-bottom: 30px; color: white; text-align: center;'>
                    <div style='display: flex; justify-content: space-around; align-items: center;'>
                        <div>
                            <h3 style='margin: 0; font-size: 1.8em;'>{len(liked_books)}</h3>
                            <p style='margin: 5px 0 0 0; opacity: 0.9;'>Total Books</p>
                        </div>
                        <div>
                            <h3 style='margin: 0; font-size: 1.8em;'>{category_counts["To Read"]}</h3>
                            <p style='margin: 5px 0 0 0; opacity: 0.9;'>To Read</p>
                        </div>
                        <div>
                            <h3 style='margin: 0; font-size: 1.8em;'>{category_counts["Ongoing"]}</h3>
                            <p style='margin: 5px 0 0 0; opacity: 0.9;'>Reading</p>
                        </div>
                        <div>
                            <h3 style='margin: 0; font-size: 1.8em;'>{category_counts["Finished"]}</h3>
                            <p style='margin: 5px 0 0 0; opacity: 0.9;'>Completed</p>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Books Grid
                st.markdown(f"""
                <h3 style='color: #2c3e50; margin-bottom: 20px; text-align: center;'>
                    {category_icons[st.session_state.selected_category_filter]} {st.session_state.selected_category_filter} 
                    <span style='color: #7f8c8d; font-size: 0.8em;'>({len(filtered_books)} books)</span>
                </h3>
                """, unsafe_allow_html=True)
                
                for i, book in enumerate(filtered_books):
                    book_id = str(book.get('id', '')) or book.get('bookname', '') or book.get('bookName', '')
                    book_info = st.session_state.book_categories.get(book_id, {})
                    current_category = book_info.get('category', 'To Read')
                    
                    # Modern Book Card
                    st.markdown(f"""
                    <div style='background: white; border-radius: 15px; padding: 20px; margin-bottom: 20px; 
                               box-shadow: 0 8px 25px rgba(0,0,0,0.1); border: 1px solid #f0f0f0;
                               transition: transform 0.3s ease;'>
                    """, unsafe_allow_html=True)
                    
                    cols = st.columns([1, 3, 1.5, 0.5])
                    
                    with cols[0]:
                        image_url = book.get("bookImageURL", "")
                        if image_url:
                            st.markdown(f"""
                            <div style='text-align: center;'>
                                <img src='{image_url}' style='width: 120px; height: 160px; object-fit: cover; 
                                     border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);'>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown("""
                            <div style="width: 120px; height: 160px; margin: 0 auto;
                                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                        display: flex; align-items: center; justify-content: center; 
                                        border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
                                <span style="color: white; font-size: 24px;">📚</span>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    with cols[1]:
                        title = book.get('bookname') or book.get('bookName', 'Unknown Title')
                        authors = book.get('authors') or book.get('author', 'Unknown Author')
                        publisher = book.get('publisher', 'Unknown Publisher')
                        year = book.get('publication_year') or book.get('publicationYear', 'Unknown Year')
                        
                        st.markdown(f"""
                        <div style='padding-left: 20px;'>
                            <h3 style='color: #2c3e50; margin-bottom: 10px; font-size: 1.4em; line-height: 1.3;'>{title}</h3>
                            <div style='color: #7f8c8d; margin-bottom: 5px; font-size: 1.1em;'>
                                <strong>✍️ {authors}</strong>
                            </div>
                            <div style='color: #95a5a6; margin-bottom: 5px;'>
                                🏢 {publisher} • 📅 {year}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Enhanced Status Badge
                        status_config = {
                            'To Read': {'color': '#ff9800', 'bg': '#fff3e0', 'icon': '🔖'},
                            'Ongoing': {'color': '#4caf50', 'bg': '#e8f5e8', 'icon': '📖'},
                            'Finished': {'color': '#2196f3', 'bg': '#e3f2fd', 'icon': '✅'}
                        }
                        
                        config = status_config[current_category]
                        st.markdown(f"""
                        <div style='margin-top: 10px; padding-left: 20px;'>
                            <span style='background: {config["bg"]}; color: {config["color"]}; 
                                        padding: 6px 12px; border-radius: 20px; font-size: 12px; font-weight: 600;
                                        border: 2px solid {config["color"]}20;'>
                                {config["icon"]} {current_category}
                            </span>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with cols[2]:
                        st.markdown("<div style='padding: 10px 0;'>", unsafe_allow_html=True)
                        
                        # Modern Status Selector
                        st.markdown("**📊 Update Status:**")
                        new_category = st.selectbox(
                            "", 
                            ["To Read", "Ongoing", "Finished"],
                            index=["To Read", "Ongoing", "Finished"].index(current_category),
                            key=f"category_{book_id}_{i}",
                            label_visibility="collapsed"
                        )
                        
                        # Update category if changed
                        if new_category != current_category:
                            if book_id not in st.session_state.book_categories:
                                st.session_state.book_categories[book_id] = {}
                            
                            st.session_state.book_categories[book_id]['category'] = new_category
                            st.success(f"📝 Updated to {new_category}!")
                            st.rerun()
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    with cols[3]:
                        st.markdown("<div style='text-align: center; padding-top: 20px;'>", unsafe_allow_html=True)
                        
                        # Modern Remove Button
                        if st.button("🗑️", key=f"unlike_{book_id}_{i}", help="Remove from library"):
                            if hasattr(st.session_state, 'username') and st.session_state.username:
                                remove_liked_book(st.session_state.username, book_id)
                                # Also remove from categories
                                if book_id in st.session_state.book_categories:
                                    del st.session_state.book_categories[book_id]
                                st.success("📚 Book removed from your library!")
                                st.rerun()
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    st.markdown("</div>", unsafe_allow_html=True)
            else:
                # Empty State
                st.markdown("""
                <div style='text-align: center; padding: 80px 20px; background: linear-gradient(135deg, #f8f9ff 0%, #e8f2ff 100%); 
                           border-radius: 20px; margin: 40px 0; border: 2px dashed #d1e7ff;'>
                    <div style='font-size: 4em; margin-bottom: 20px; opacity: 0.6;'>📚</div>
                    <h2 style='color: #4a5568; margin-bottom: 15px; font-weight: 300;'>Your Library is Empty</h2>
                    <p style='color: #718096; font-size: 1.1em; margin-bottom: 30px; max-width: 400px; margin-left: auto; margin-right: auto; line-height: 1.6;'>
                        Start building your personal collection by exploring book recommendations and saving your favorites!
                    </p>
                    <div style='display: flex; justify-content: center; gap: 15px; flex-wrap: wrap;'>
                        <div style='background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); min-width: 200px;'>
                            <div style='font-size: 2em; margin-bottom: 10px;'>🔍</div>
                            <h4 style='color: #2d3748; margin-bottom: 8px;'>Discover Books</h4>
                            <p style='color: #718096; font-size: 0.9em; margin: 0;'>Search by genre or author</p>
                        </div>
                        <div style='background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); min-width: 200px;'>
                            <div style='font-size: 2em; margin-bottom: 10px;'>💝</div>
                            <h4 style='color: #2d3748; margin-bottom: 8px;'>Save Favorites</h4>
                            <p style='color: #718096; font-size: 0.9em; margin: 0;'>Build your reading list</p>
                        </div>
                        <div style='background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); min-width: 200px;'>
                            <div style='font-size: 2em; margin-bottom: 10px;'>📖</div>
                            <h4 style='color: #2d3748; margin-bottom: 8px;'>Track Progress</h4>
                            <p style='color: #718096; font-size: 0.9em; margin: 0;'>Organize your reading journey</p>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            # User not logged in - Beautiful login prompt
            st.markdown("""
            <div style='text-align: center; padding: 60px 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                       border-radius: 20px; margin: 40px 0; color: white;'>
                <div style='font-size: 3.5em; margin-bottom: 20px; opacity: 0.9;'>🔐</div>
                <h2 style='margin-bottom: 15px; font-weight: 300;'>Access Your Personal Library</h2>
                <p style='font-size: 1.1em; margin-bottom: 30px; opacity: 0.9; max-width: 500px; margin-left: auto; margin-right: auto; line-height: 1.6;'>
                    Sign in to save your favorite books, track your reading progress, and create your personalized library collection.
                </p>
                <div style='background: rgba(255,255,255,0.2); padding: 25px; border-radius: 15px; max-width: 400px; margin: 0 auto; backdrop-filter: blur(10px);'>
                    <h4 style='margin-bottom: 15px; color: rgba(255,255,255,0.95);'>✨ Library Features</h4>
                    <div style='text-align: left; color: rgba(255,255,255,0.85);'>
                        <div style='margin-bottom: 8px;'>📚 Save unlimited books</div>
                        <div style='margin-bottom: 8px;'>📊 Track reading status</div>
                        <div style='margin-bottom: 8px;'>🏷️ Organize by categories</div>
                        <div style='margin-bottom: 8px;'>💭 Personal book discussions</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Back to recommendations button with beautiful styling
        st.markdown("<div style='text-align: center; margin-top: 40px;'>", unsafe_allow_html=True)
        if st.button("🔍 Discover New Books", key="back_to_search_from_library", use_container_width=False):
            st.session_state.app_stage = "awaiting_user_input"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # Add some beautiful footer spacing
    add_vertical_space(3)
    
    # Beautiful Footer
    st.markdown("""
    <div style='text-align: center; padding: 30px 20px; margin-top: 50px; 
               background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); 
               border-radius: 15px; border-top: 3px solid #667eea;'>
        <div style='color: #6c757d; font-size: 0.9em; margin-bottom: 10px;'>
            📚 Book Wanderer • 책방랑자
        </div>
        <div style='color: #adb5bd; font-size: 0.8em;'>
            Discover your next favorite read with AI assistance
        </div>
    </div>
    """, unsafe_allow_html=True)


def add_vertical_space(lines):
    """Add vertical space"""
    for _ in range(lines):
        st.markdown("<br>", unsafe_allow_html=True)


def display_message(message):
    """Display a chat message with beautiful styling"""
    if message["role"] == "user":
        st.markdown(f"""
        <div style='display: flex; justify-content: flex-end; margin-bottom: 15px;'>
            <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                       color: white; padding: 15px 20px; border-radius: 20px 20px 5px 20px; 
                       max-width: 70%; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);'>
                <div style='font-weight: 500;'>{message["content"]}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style='display: flex; justify-content: flex-start; margin-bottom: 15px;'>
            <div style='background: white; color: #2c3e50; padding: 15px 20px; 
                       border-radius: 20px 20px 20px 5px; max-width: 70%; 
                       box-shadow: 0 4px 15px rgba(0,0,0,0.1); border: 1px solid #f0f0f0;'>
                <div style='line-height: 1.6;'>{message["content"]}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def display_book_card(book, index):
    """Display a beautiful book card with enhanced styling"""
    book_id = str(book.get('id', '')) or book.get('bookname', '') or book.get('bookName', '')
    
    # Enhanced card with modern design
    st.markdown(f"""
    <div style='background: white; border-radius: 20px; padding: 25px; margin-bottom: 25px; 
               box-shadow: 0 10px 30px rgba(0,0,0,0.1); border: 1px solid #f0f0f0;
               transition: all 0.3s ease; position: relative; overflow: hidden;'>
        <div style='position: absolute; top: 0; left: 0; width: 100%; height: 4px; 
                   background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);'></div>
    """, unsafe_allow_html=True)
    
    cols = st.columns([1, 3, 1.5])
    
    with cols[0]:
        image_url = book.get("bookImageURL", "")
        if image_url:
            st.markdown(f"""
            <div style='text-align: center;'>
                <img src='{image_url}' style='width: 140px; height: 180px; object-fit: cover; 
                     border-radius: 12px; box-shadow: 0 6px 20px rgba(0,0,0,0.15);
                     transition: transform 0.3s ease;'>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="width: 140px; height: 180px; margin: 0 auto;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        display: flex; align-items: center; justify-content: center; 
                        border-radius: 12px; box-shadow: 0 6px 20px rgba(0,0,0,0.15);">
                <span style="color: white; font-size: 28px;">📚</span>
            </div>
            """, unsafe_allow_html=True)
    
    with cols[1]:
        title = book.get('bookname') or book.get('bookName', 'Unknown Title')
        authors = book.get('authors') or book.get('author', 'Unknown Author')
        publisher = book.get('publisher', 'Unknown Publisher')
        year = book.get('publication_year') or book.get('publicationYear', 'Unknown Year')
        loan_count = book.get('loan_count') or book.get('loanCount', 0)
        
        st.markdown(f"""
        <div style='padding-left: 25px;'>
            <h3 style='color: #2c3e50; margin-bottom: 12px; font-size: 1.5em; line-height: 1.3; font-weight: 600;'>{title}</h3>
            <div style='color: #34495e; margin-bottom: 8px; font-size: 1.1em; font-weight: 500;'>
                <span style='color: #667eea;'>✍️</span> {authors}
            </div>
            <div style='color: #7f8c8d; margin-bottom: 6px; font-size: 0.95em;'>
                <span style='color: #e74c3c;'>🏢</span> {publisher}
            </div>
            <div style='color: #7f8c8d; margin-bottom: 8px; font-size: 0.95em;'>
                <span style='color: #f39c12;'>📅</span> {year}
            </div>
            <div style='background: linear-gradient(135deg, #ff6b6b, #ee5a52); color: white; 
                       padding: 6px 12px; border-radius: 20px; display: inline-block; font-size: 0.85em; font-weight: 600;'>
                🔥 {loan_count} loans
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with cols[2]:
        st.markdown("<div style='text-align: center; padding-top: 15px;'>", unsafe_allow_html=True)
        
        # Enhanced buttons with beautiful styling
        if st.button("💬 Discuss", key=f"discuss_{index}", use_container_width=True):
            st.session_state.selected_book = book
            st.session_state.app_stage = "discuss_book"
            st.session_state.book_discussion_messages = []
            st.session_state.book_intro_shown = False
            st.rerun()
        
        # Like/Unlike functionality with enhanced styling
        if hasattr(st.session_state, 'username') and st.session_state.username:
            liked_books = get_liked_books(st.session_state.username)
            book_ids = [str(b.get('id', '')) or b.get('bookname', '') or b.get('bookName', '') for b in liked_books]
            
            if book_id in book_ids:
                if st.button("💝 Saved", key=f"unlike_{index}", use_container_width=True):
                    remove_liked_book(st.session_state.username, book_id)
                    st.success("📚 Removed from your library!")
                    st.rerun()
            else:
                if st.button("🤍 Save", key=f"like_{index}", use_container_width=True):
                    add_liked_book(st.session_state.username, book)
                    # Initialize book category
                    if book_id not in st.session_state.book_categories:
                        st.session_state.book_categories[book_id] = {'category': 'To Read'}
                    st.success("💝 Added to your library!")
                    st.rerun()
        else:
            st.markdown("""
            <div style='background: #f8f9fa; padding: 10px; border-radius: 8px; 
                       border: 2px dashed #dee2e6; text-align: center;'>
                <small style='color: #6c757d;'>Sign in to save books</small>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)


def setup_sidebar():
    """Setup the beautiful sidebar with enhanced styling"""
    with st.sidebar:
        st.markdown("""
        <div style='text-align: center; padding: 20px 0; margin-bottom: 30px;
                   background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                   margin: -20px -20px 30px -20px; border-radius: 0 0 15px 15px;'>
            <h2 style='color: white; margin: 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);'>⚙️ Settings</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # User Authentication Section
        st.markdown("### 👤 User Profile")
        
        if not hasattr(st.session_state, 'username') or not st.session_state.username:
            with st.expander("🔐 Sign In", expanded=False):
                username = st.text_input("Username", key="login_username")
                if st.button("Sign In", use_container_width=True):
                    if username:
                        st.session_state.username = username
                        st.success(f"Welcome, {username}! 🎉")
                        st.rerun()
        else:
            st.markdown(f"""
            <div style='background: linear-gradient(135deg, #4CAF50, #45a049); 
                       color: white; padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 15px;'>
                <div style='font-size: 1.2em; margin-bottom: 5px;'>👋 Welcome!</div>
                <div style='font-weight: 600;'>{st.session_state.username}</div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🚪 Sign Out", use_container_width=True):
                st.session_state.username = None
                st.success("Signed out successfully!")
                st.rerun()
        
        st.markdown("---")
        
        # Library Access with beautiful button
        if st.button("📚 My Library", use_container_width=True, key="library_access"):
            st.session_state.app_stage = "show_liked_books"
            st.session_state.selected_category_filter = "All"
            st.rerun()
        
        st.markdown("---")
        
        # API Configuration
        st.markdown("### 🔑 API Configuration")
        
        with st.expander("HyperCLOVA API", expanded=False):
            st.session_state.api_key = st.text_input(
                "API Key", 
                value=st.session_state.api_key, 
                type="password",
                key="hyperclova_key"
            )
        
        with st.expander("Library API", expanded=False):
            st.session_state.library_api_key = st.text_input(
                "Library API Key", 
                value=st.session_state.library_api_key, 
                type="password",
                key="library_key"
            )
        
        st.markdown("---")
        
        # Quick Actions
        st.markdown("### 🚀 Quick Actions")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 New Search", use_container_width=True, key="new_search"):
                st.session_state.app_stage = "awaiting_user_input"
                st.session_state.messages = [{
                    "role": "system",
                    "content": (
                        "You are a friendly AI assistant specializing in book recommendations. "
                        "Start by greeting and asking about favorite books/authors/genres/age. "
                        "For EVERY response, answer in BOTH English and Korean. "
                        "First provide complete English answer, then '한국어 답변:' with Korean translation."
                    )
                }]
                st.rerun()
        
        with col2:
            if st.button("🏠 Home", use_container_width=True, key="go_home"):
                st.session_state.app_stage = "welcome"
                st.rerun()
        
        # Footer
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; color: #7f8c8d; font-size: 0.8em; margin-top: 20px;'>
            📚 Book Wanderer v2.0<br>
            Made with ❤️ for book lovers
        </div>
        """, unsafe_allow_html=True)
