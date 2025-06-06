import tempfile
import moviepy as mp
from moviepy import TextClip, ImageClip, CompositeVideoClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFont
import traceback
import base64
import requests
import io
import os
import json
import re
import streamlit as st
from translate import Translator  # <-- NEW

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

def ensure_english(text):
    """Translate text to English if it's not already in English."""
    try:
        translator = Translator(to_lang="en")
        translated = translator.translate(text)
        return translated
    except Exception as e:
        print(f"Translation error: {e}")
        return text

def generate_book_summary_text(title, author, api_key):
    try:
        prompt = (
            f"Summarize the book '{title}' by {author} in English. "
            "Provide a detailed yet concise summary that covers the main plot, key characters, major themes, and the book's overall impact. "
            "Write in clear, engaging English for a general audience."
        )
        messages = [
            {"role": "system", "content": "You are an expert book reviewer."},
            {"role": "user", "content": prompt}
        ]
        response = call_hyperclova_api(messages, api_key)
        if response:
            return response.strip()
        return f"No summary available for '{title}' by {author}."
    except Exception as e:
        print(f"Error generating summary: {e}")
        return f"Error generating summary for '{title}' by {author}."

def generate_book_summary_video(book_data, api_key):
    try:
        temp_dir = tempfile.mkdtemp()
        raw_title = book_data.get('bookname') or book_data.get('bookName', 'Unknown Title')
        raw_author = book_data.get('authors') or book_data.get('author', 'Unknown Author')
        publisher = book_data.get('publisher', 'Unknown Publisher')
        cover_url = book_data.get('bookImageURL', '')

        # You can still use title/author for the summary generation, but NOT for video slides
        title = ensure_english(raw_title)
        author = ensure_english(raw_author)

        # Generate a detailed summary using HyperCLOVA
        summary_text = generate_book_summary_text(title, author, api_key)

        # Split summary into manageable chunks for slides (every 2 sentences)
        sentences = re.split(r'(?<=[.!?]) +', summary_text)
        chunks = [' '.join(sentences[i:i+2]) for i in range(0, len(sentences), 2)]

        # --- REMOVED: Intro and Author slides ---

        # Create the main book cover clip and resize
        cover_image_path = download_book_cover(cover_url, temp_dir)
        if not cover_image_path:
            cover_image_path = create_placeholder_cover(title, author, temp_dir)
        cover_clip = ImageClip(cover_image_path).with_duration(4)
        cover_clip = cover_clip.resized(height=1080)
        if cover_clip.w > 1080:
            cover_clip = cover_clip.resized(width=1080)
        cover_clip = cover_clip.with_position('center')

        # Create a slide for each summary chunk
        point_clips = []
        for i, chunk in enumerate(chunks):
            point_image_path = add_text_to_book_cover(
                cover_image_path, chunk, temp_dir, f"summary_{i}.png"
            )
            point_clip = ImageClip(point_image_path).with_duration(6)
            point_clips.append(point_clip)

        # Create outro image
        outro_text = f"Happy Reading!\n~ Book Wanderer"
        outro_image_path = create_text_image(outro_text, (1080, 1080), 60, temp_dir, "outro.png")
        outro_clip = ImageClip(outro_image_path).with_duration(3)

        # Only include cover, summary slides, and outro
        all_clips = [cover_clip] + point_clips + [outro_clip]
        final_clip = concatenate_videoclips(all_clips, method="compose")
        final_clip = final_clip.without_audio()

        output_path = os.path.join(temp_dir, "book_summary.mp4")
        final_clip.write_videofile(
            output_path,
            fps=24,
            codec='libx264',
            preset='medium',
            logger=None
        )
        final_clip.close()
        return output_path

    except Exception as e:
        error_traceback = traceback.format_exc()
        print(f"Full error traceback:\n{error_traceback}")
        return f"Error generating video: {str(e)}\n\nFull traceback:\n{error_traceback}"

def download_book_cover(cover_url, temp_dir):
    if not cover_url:
        return None
    try:
        response = requests.get(cover_url, timeout=10)
        response.raise_for_status()
        img = Image.open(io.BytesIO(response.content))
        img = img.convert('RGB')
        img = resize_image_to_fit(img, 1080, 1080)
        cover_path = os.path.join(temp_dir, "book_cover.jpg")
        img.save(cover_path, "JPEG", quality=95)
        return cover_path
    except Exception as e:
        print(f"Error downloading book cover: {e}")
        return None

def create_placeholder_cover(title, author, temp_dir):
    width, height = 800, 1200
    image = Image.new('RGB', (width, height), (60, 80, 120))
    for y in range(height):
        gradient_color = int(60 + (y / height) * 40)
        for x in range(width):
            image.putpixel((x, y), (gradient_color, gradient_color + 20, gradient_color + 60))
    draw = ImageDraw.Draw(image)
    try:
        font_paths = [
            "Arial.ttf",
            "/System/Library/Fonts/Arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "C:/Windows/Fonts/arial.ttf"
        ]
        title_font = None
        author_font = None
        for font_path in font_paths:
            try:
                title_font = ImageFont.truetype(font_path, 60)
                author_font = ImageFont.truetype(font_path, 40)
                break
            except (IOError, OSError):
                continue
        if title_font is None:
            title_font = ImageFont.load_default()
            author_font = ImageFont.load_default()
    except Exception:
        title_font = ImageFont.load_default()
        author_font = ImageFont.load_default()
    wrapped_title = wrap_text_for_cover(title, title_font, width - 100)
    title_bbox = draw.multiline_textbbox((0, 0), wrapped_title, font=title_font)
    title_height = title_bbox[3] - title_bbox[1]
    title_y = height // 3 - title_height // 2
    draw.multiline_text(
        ((width - (title_bbox[2] - title_bbox[0])) // 2, title_y),
        wrapped_title,
        font=title_font,
        fill="white",
        align="center"
    )
    author_bbox = draw.textbbox((0, 0), author, font=author_font)
    author_y = height - 200
    draw.text(
        ((width - (author_bbox[2] - author_bbox[0])) // 2, author_y),
        author,
        font=author_font,
        fill="lightgray",
        align="center"
    )
    draw.rectangle([50, 50, width-50, height-50], outline="white", width=3)
    cover_path = os.path.join(temp_dir, "placeholder_cover.jpg")
    image.save(cover_path, "JPEG", quality=95)
    return cover_path

def resize_image_to_fit(image, max_width, max_height):
    width, height = image.size
    width_ratio = max_width / width
    height_ratio = max_height / height
    scale_factor = min(width_ratio, height_ratio)
    new_width = int(width * scale_factor)
    new_height = int(height * scale_factor)
    return image.resize((new_width, new_height), Image.LANCZOS)

def create_text_image(text, size, font_size, temp_dir, filename):
    width, height = size
    image = Image.new('RGB', (width, height))
    for y in range(height):
        gradient = int(30 + (y / height) * 50)
        for x in range(width):
            image.putpixel((x, y), (gradient, gradient + 10, gradient + 30))
    draw = ImageDraw.Draw(image)
    try:
        font_paths = [
            "Arial.ttf",
            "/System/Library/Fonts/Arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "C:/Windows/Fonts/arial.ttf"
        ]
        font = None
        for font_path in font_paths:
            try:
                font = ImageFont.truetype(font_path, font_size)
                break
            except (IOError, OSError):
                continue
        if font is None:
            font = ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()
    lines = text.split('\n')
    total_height = 0
    line_heights = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_height = bbox[3] - bbox[1]
        total_height += line_height
        line_heights.append(line_height)
    y = (height - total_height) // 2
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        line_width = bbox[2] - bbox[0]
        x = (width - line_width) // 2
        draw.text((x, y), line, font=font, fill="white")
        y += line_heights[i] + 10
    output_path = os.path.join(temp_dir, filename)
    image.save(output_path)
    return output_path

def add_text_to_book_cover(cover_path, text, temp_dir, filename):
    img = Image.open(cover_path)
    img = img.convert('RGB')
    img = resize_image_to_fit(img, 1080, 1080)
    canvas = Image.new('RGB', (1080, 1080), (20, 20, 30))
    x_offset = (1080 - img.width) // 2
    y_offset = (1080 - img.height) // 2
    canvas.paste(img, (x_offset, y_offset))
    overlay = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    try:
        font_paths = [
            "Arial.ttf",
            "/System/Library/Fonts/Arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "C:/Windows/Fonts/arial.ttf"
        ]
        font = None
        for font_path in font_paths:
            try:
                font = ImageFont.truetype(font_path, 36)
                break
            except (IOError, OSError):
                continue
        if font is None:
            font = ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()
    max_width = 900
    wrapped_text = wrap_text_simple(text, font, max_width)
    bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    margin = 25
    rect_height = text_height + (margin * 2)
    rect_width = min(text_width + (margin * 2), 1080 - 40)
    rect_x = (1080 - rect_width) // 2
    rect_y = 1080 - rect_height - 40
    draw.rectangle(
        [rect_x, rect_y, rect_x + rect_width, rect_y + rect_height],
        fill=(0, 0, 0, 200)
    )
    text_x = (1080 - text_width) // 2
    text_y = rect_y + margin
    draw.multiline_text(
        (text_x, text_y),
        wrapped_text,
        font=font,
        fill=(255, 255, 255, 255),
        align="center"
    )
    canvas = canvas.convert('RGBA')
    result = Image.alpha_composite(canvas, overlay)
    result = result.convert('RGB')
    output_path = os.path.join(temp_dir, filename)
    result.save(output_path)
    return output_path

def wrap_text_simple(text, font, max_width):
    words = text.split()
    lines = []
    current_line = []
    for word in words:
        current_line.append(word)
        line_text = ' '.join(current_line)
        temp_img = Image.new('RGB', (1, 1))
        temp_draw = ImageDraw.Draw(temp_img)
        bbox = temp_draw.textbbox((0, 0), line_text, font=font)
        line_width = bbox[2] - bbox[0]
        if line_width > max_width and len(current_line) > 1:
            current_line.pop()
            lines.append(' '.join(current_line))
            current_line = [word]
    if current_line:
        lines.append(' '.join(current_line))
    return '\n'.join(lines)

def wrap_text_for_cover(text, font, max_width):
    words = text.split()
    if len(words) <= 3:
        return text
    lines = []
    current_line = []
    for word in words:
        current_line.append(word)
        line_text = ' '.join(current_line)
        temp_img = Image.new('RGB', (1, 1))
        temp_draw = ImageDraw.Draw(temp_img)
        bbox = temp_draw.textbbox((0, 0), line_text, font=font)
        line_width = bbox[2] - bbox[0]
        if line_width > max_width and len(current_line) > 1:
            current_line.pop()
            lines.append(' '.join(current_line))
            current_line = [word]
    if current_line:
        lines.append(' '.join(current_line))
    return '\n'.join(lines)

# Integration function to add video generation to your main app
def integrate_book_video_generation():
    if st.session_state.app_stage == "show_recommendations" and st.session_state.books_data:
        st.markdown("---")
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
                    format_func=lambda x: book_options[x]
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
                        st.image(cover_url, caption="Book Cover", use_container_width=True)
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
                st.video(st.session_state.book_video_path)
                
                # Provide download button
                try:
                    with open(st.session_state.book_video_path, "rb") as file:
                        btn = st.download_button(
                            label="📥 Download Video",
                            data=file,
                            file_name="book_summary.mp4",
                            mime="video/mp4",
                            key="download_book_video"
                        )
                except Exception as e:
                    st.error(f"Error preparing download: {str(e)}")
