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
from Discussion_Function import *
from Video_Summary import *

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
    if "selected_category_filter" not in st.session_state:
        st.session_state.selected_category_filter = "All"
    if "show_discussion" not in st.session_state:
        st.session_state.show_discussion = False

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
        
        # Display books
        for i, book in enumerate(st.session_state.books_data[:10]):  # Show top 10 books
            display_book_card(book, i)
        
        # ADD THIS: Book Video Generation Section
        st.header("🎬 Book Summary Videos")
        
        with st.expander("Generate Book Summary Videos", expanded=False):
            st.markdown("### Create engaging video summaries for your recommended books")
            st.markdown("""
            Our AI will create video presentations that:
            - Showcase the book cover prominently
            - Highlight key themes and plot elements
            - Provide engaging summaries for each book
            - Create shareable content for book lovers
            """)
            
            # Let user select which book to create video for
            book_options = []
            for i, book in enumerate(st.session_state.books_data[:10]):  # Limit to first 5 books
                title = book.get('bookname') or book.get('bookName', 'Unknown Title')
                author = book.get('authors') or book.get('author', 'Unknown Author')
                book_options.append(f"{title} by {author}")
            
            if book_options:
                selected_book_index = st.selectbox(
                    "જ⁀➴ Select a book to create a summary video:",
                    range(len(book_options)),
                    format_func=lambda x: book_options[x],
                    key="book_video_selector"
                )
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    if st.button("Generate Book Summary Video", key="generate_book_video"):
                        selected_book = st.session_state.books_data[selected_book_index]
                        
                        with st.spinner("Creating your book summary video... This may take a few minutes."):
                            try:
                                # Generate the video using HyperCLOVA API key
                                video_path = generate_book_summary_video(
                                    selected_book,
                                    HYPERCLOVA_API_KEY
                                )
                                
                                if video_path and not video_path.startswith("Error"):
                                    # Save the path to session state
                                    st.session_state.book_video_path = video_path
                                    st.session_state.book_video_generated = True
                                    st.session_state.selected_book_for_video = selected_book
                                    
                                    st.success("Book summary video generated successfully!")
                                    st.rerun()
                                else:
                                    st.error(f"Error generating video: {video_path}")
                            
                            except Exception as e:
                                st.error(f"Error generating video: {str(e)}")
                
                with col2:
                    # Show book cover preview
                    selected_book = st.session_state.books_data[selected_book_index]
                    cover_url = selected_book.get('bookImageURL', '')
                    if cover_url:
                        try:
                            st.image(cover_url, caption="Book Cover", use_container_width=True)
                        except:
                            st.markdown("""
                            <div style="width: 100%; height: 200px; background: linear-gradient(135deg, #2c3040, #363c4e); 
                                        display: flex; align-items: center; justify-content: center; border-radius: 8px;">
                                <span style="color: #b3b3cc;">No Cover Available</span>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.markdown("""
                        <div style="width: 100%; height: 200px; background: linear-gradient(135deg, #2c3040, #363c4e); 
                                    display: flex; align-items: center; justify-content: center; border-radius: 8px;">
                            <span style="color: #b3b3cc;">No Cover Available</span>
                        </div>
                        """, unsafe_allow_html=True)
            
            # Display the video if it exists
            if hasattr(st.session_state, 'book_video_generated') and st.session_state.book_video_generated:
                st.markdown("### 📺 Your Book Summary Video")
                
                # Show which book the video is for
                if hasattr(st.session_state, 'selected_book_for_video'):
                    book = st.session_state.selected_book_for_video
                    title = book.get('bookname') or book.get('bookName', 'Unknown Title')
                    author = book.get('authors') or book.get('author', 'Unknown Author')
                    st.markdown(f"**Video for:** {title} by {author}")
                
                # Display the video
                try:
                    st.video(st.session_state.book_video_path)
                    
                    # Provide download button
                    with open(st.session_state.book_video_path, "rb") as file:
                        st.download_button(
                            label="📥 Download Video",
                            data=file,
                            file_name=f"book_summary_{title.replace(' ', '_')}.mp4",
                            mime="video/mp4",
                            key="download_book_video"
                        )
                except Exception as e:
                    st.error(f"Error displaying video: {str(e)}")
                    
                    # Clear the video state if there's an error
                    if 'book_video_generated' in st.session_state:
                        del st.session_state.book_video_generated
                    if 'book_video_path' in st.session_state:
                        del st.session_state.book_video_path

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
            # Get liked books from MongoDB
            liked_books = get_liked_books(st.session_state.username)
            
            # Category filter with equal-sized buttons using CSS
            st.markdown("""
            <style>
            div[data-testid="column"] button {
                width: 100% !important;
                min-height: 40px !important;
                white-space: nowrap !important;
                font-size: 14px !important;
            }
            </style>
            """, unsafe_allow_html=True)
            
            col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
            with col1:
                if st.button("전체 도서", key="filter_all", use_container_width=True):
                    st.session_state.selected_category_filter = "All"
                    st.rerun()
            with col2:
                if st.button("읽을 예정", key="filter_to_read", use_container_width=True):
                    st.session_state.selected_category_filter = "To Read"
                    st.rerun()
            with col3:
                if st.button("읽는 중", key="filter_ongoing", use_container_width=True):
                    st.session_state.selected_category_filter = "Currently Reading"
                    st.rerun()
            with col4:
                if st.button("읽기 완료", key="filter_finished", use_container_width=True):
                    st.session_state.selected_category_filter = "Finished"
                    st.rerun()
            
            st.markdown("---")
            
            if liked_books:
                # Filter books based on selected category
                filtered_books = []
                for book in liked_books:
                    book_category = book.get('category', 'To Read')
                    
                    if st.session_state.selected_category_filter == "All" or book_category == st.session_state.selected_category_filter:
                        filtered_books.append(book)
                
                st.markdown(f"**{st.session_state.selected_category_filter}**: {len(filtered_books)} books")
                
                # Display filtered books using the MongoDB-compatible display function
                for i, book in enumerate(filtered_books):
                    display_liked_book_card(book, i)
                    st.markdown("---")
            else:
                st.info("You haven't liked any books yet. Go to recommendations and like some books to see them here!")
                if st.button("Discover Books"):
                    st.session_state.app_stage = "welcome"
                    st.rerun()
        else:
            st.warning("Please log in to view your library.")

    elif st.session_state.app_stage == "discussion_page":
        add_vertical_space(2)
        st.markdown("<h1 style='text-align:center;'>💬 Community Discussion</h1>", unsafe_allow_html=True)
        st.markdown("<div style='text-align:center;'>책에 대한 생각을 동료 독자들과 공유하세요</div>", unsafe_allow_html=True)
        st.markdown("---")
        
        # Check if user is logged in
        if hasattr(st.session_state, 'username') and st.session_state.username:
            # New post section
            st.markdown("### 📝 Share Your Thoughts")
            with st.form("new_discussion_post"):
                post_content = st.text_area(
                    "What's on your mind about books? (책에 대해 무슨 생각을 하고 있나요?)",
                    placeholder="Share your book thoughts, recommendations, or start a discussion...",
                    height=100
                )
                submitted = st.form_submit_button("Post Discussion")
                
                if submitted and post_content.strip():
                    if save_discussion_post(st.session_state.username, post_content.strip()):
                        st.success("Your post has been shared!")
                        st.rerun()
                    else:
                        st.error("Failed to post discussion.")
                elif submitted:
                    st.warning("Please enter some content before posting.")
            
            st.markdown("---")
            
            # Display all discussion posts
            st.markdown("### 📚 Community Posts")
            posts = get_all_discussion_posts()
            
            if posts:
                for i, post in enumerate(posts):
                    display_discussion_post(post, i)
                    st.markdown("---")
            else:
                st.info("No discussions yet. Be the first to start a conversation!")
        
        else:
            st.warning("Please log in to participate in discussions.")
            st.info("You can view discussions, but you need to log in to post or reply.")
            
            # Show discussions in read-only mode
            st.markdown("### 📚 Community Posts")
            posts = get_all_discussion_posts()
            
            if posts:
                for i, post in enumerate(posts):
                    # Display post without reply functionality
                    with st.container():
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"**{post['username']}**")
                        with col2:
                            timestamp = datetime.fromisoformat(post['timestamp'])
                            st.markdown(f"*{timestamp.strftime('%Y-%m-%d %H:%M')}*")
                        
                        st.markdown(f"{post['content']}")
                        
                        if post.get('replies'):
                            st.markdown("**Replies:**")
                            for reply in post['replies']:
                                reply_timestamp = datetime.fromisoformat(reply['timestamp'])
                                st.markdown(f"↳ **{reply['username']}** ({reply_timestamp.strftime('%Y-%m-%d %H:%M')}): {reply['content']}")
                        
                        st.markdown("---")
            else:
                st.info("No discussions yet.")
        
        # Back to recommendations button
        if st.button("← Back to Recommendations", key="back_to_recs_from_library"):
            st.session_state.app_stage = "show_recommendations" if st.session_state.books_data else "welcome"
            st.rerun()

    # Footer
    add_vertical_space(3)
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666; font-size: 14px;'>"
        "📚 한 권의 책은 하나의 세상이다"
        "</div>", 
        unsafe_allow_html=True
    )
