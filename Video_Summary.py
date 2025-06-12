import tempfile
import moviepy as mp
from moviepy import TextClip, ImageClip, CompositeVideoClip, concatenate_videoclips, AudioFileClip
from PIL import Image, ImageDraw, ImageFont
import traceback
import base64
import requests
import io
import os
import json
import re
import streamlit as st
from translate import Translator
from gtts import gTTS
import threading
import time

def generate_speech_audio(text, output_path, lang='en', slow=False):
    """Generate speech audio from text using gTTS"""
    try:
        # Clean text for speech
        clean_text = re.sub(r'[^\w\s.,!?-]', '', text)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        if not clean_text:
            print("No clean text to convert to speech")
            return None
            
        print(f"Generating speech for: {clean_text[:50]}...")
        
        # Create gTTS object
        tts = gTTS(text=clean_text, lang=lang, slow=slow)
        
        # Save to temporary wav file
        temp_mp3 = output_path.replace('.wav', '.mp3')
        tts.save(temp_mp3)
        
        # Convert MP3 to WAV using moviepy for better compatibility
        try:
            audio_clip = AudioFileClip(temp_mp3)
            audio_clip.write_audiofile(output_path, logger=None)
            audio_clip.close()
            
            # Remove temporary MP3 file
            if os.path.exists(temp_mp3):
                os.remove(temp_mp3)
                
        except Exception as e:
            print(f"Error converting MP3 to WAV: {e}")
            # If conversion fails, use MP3 directly
            if os.path.exists(temp_mp3):
                os.rename(temp_mp3, output_path.replace('.wav', '.mp3'))
                output_path = output_path.replace('.wav', '.mp3')
        
        # Verify file was created and has content
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"Audio file created: {output_path}, size: {file_size} bytes")
            if file_size > 0:
                return output_path
            else:
                print("Audio file is empty")
                return None
        else:
            print("Audio file was not created")
            return None
            
    except Exception as e:
        print(f"Error generating speech with gTTS: {e}")
        traceback.print_exc()
        return None
        
def get_audio_duration(audio_path):
    """Get duration of audio file with better error handling"""
    try:
        if not audio_path or not os.path.exists(audio_path):
            print(f"Audio file does not exist: {audio_path}")
            return 0
            
        file_size = os.path.getsize(audio_path)
        if file_size == 0:
            print(f"Audio file is empty: {audio_path}")
            return 0
            
        print(f"Getting duration for audio file: {audio_path} (size: {file_size} bytes)")
        
        audio_clip = AudioFileClip(audio_path)
        duration = audio_clip.duration
        audio_clip.close()
        
        print(f"Audio duration: {duration} seconds")
        return duration if duration and duration > 0 else 3  # Default to 3 seconds if invalid
        
    except Exception as e:
        print(f"Error getting audio duration for {audio_path}: {e}")
        return 3  # Default duration

def create_audio_for_text_chunks(text_chunks, temp_dir, lang='en'):
    """Create individual audio files for each text chunk with better debugging"""
    audio_files = []
    
    print(f"Creating audio for {len(text_chunks)} text chunks...")
    
    for i, chunk in enumerate(text_chunks):
        if not chunk or not chunk.strip():
            print(f"Chunk {i} is empty, skipping...")
            audio_files.append(None)
            continue
            
        print(f"Processing chunk {i}: {chunk[:100]}...")
        
        audio_filename = f"audio_chunk_{i}.wav"
        audio_path = os.path.join(temp_dir, audio_filename)
        
        # Generate speech for this chunk
        result = generate_speech_audio(chunk, audio_path, lang=lang)
        
        if result and os.path.exists(result):
            print(f"Successfully created audio for chunk {i}")
            audio_files.append(result)
        else:
            print(f"Failed to create audio for chunk {i}")
            audio_files.append(None)
        
        # Small delay to prevent TTS engine issues
        time.sleep(0.2)
    
    print(f"Created {sum(1 for f in audio_files if f is not None)} audio files out of {len(text_chunks)} chunks")
    return audio_files

def create_title_announcement_audio(title, author, temp_dir, lang='en'):
    """Create audio announcement for the book title and author"""
    announcement_text = f"Welcome to the summary of {title} by {author}."
    audio_path = os.path.join(temp_dir, "title_announcement.wav")
    print(f"Creating title announcement: {announcement_text}")
    return generate_speech_audio(announcement_text, audio_path, lang=lang)

def create_outro_audio(temp_dir, lang='en'):
    """Create audio for outro"""
    outro_text = "Happy Reading! This summary was brought to you by Book Wanderer."
    audio_path = os.path.join(temp_dir, "outro_audio.wav")
    print(f"Creating outro audio: {outro_text}")
    eturn generate_speech_audio(outro_text, audio_path, lang=lang)

def generate_book_summary_video(book_data, api_key):
    try:
        temp_dir = tempfile.mkdtemp()
        print(f"Working in temp directory: {temp_dir}")
        
        raw_title = book_data.get('bookname') or book_data.get('bookName', 'Unknown Title')
        raw_author = book_data.get('authors') or book_data.get('author', 'Unknown Author')
        publisher = book_data.get('publisher', 'Unknown Publisher')
        cover_url = book_data.get('bookImageURL', '')

        # Ensure English for summary generation
        title = ensure_english(raw_title)
        author = ensure_english(raw_author)

        print(f"Generating summary for: {title} by {author}")

        # Generate a detailed summary using HyperCLOVA
        summary_text = generate_book_summary_text(title, author, api_key)
        print(f"Generated summary: {summary_text[:200]}...")

        # Split summary into manageable chunks for slides (every 2 sentences)
        sentences = re.split(r'(?<=[.!?]) +', summary_text)
        chunks = [' '.join(sentences[i:i+2]) for i in range(0, len(sentences), 2)]
        
        print(f"Split summary into {len(chunks)} chunks")

        # Create audio for all text chunks
        print("Generating audio for text chunks...")
        chunk_audio_files = create_audio_for_text_chunks(chunks, temp_dir)

        # Create title announcement audio
        print("Creating title announcement audio...")
        title_audio = create_title_announcement_audio(title, author, temp_dir)
        
        # Create outro audio
        print("Creating outro audio...")
        outro_audio = create_outro_audio(temp_dir)

        # Create the main book cover clip and resize
        print("Creating book cover image...")
        cover_image_path = download_book_cover(cover_url, temp_dir)
        if not cover_image_path:
            cover_image_path = create_placeholder_cover(title, author, temp_dir)
        
        # Determine cover clip duration based on title audio
        cover_duration = max(4, get_audio_duration(title_audio) if title_audio else 4)
        print(f"Cover clip duration: {cover_duration} seconds")
        
        cover_clip = ImageClip(cover_image_path).with_duration(cover_duration)
        cover_clip = cover_clip.resized(height=1080)
        if cover_clip.w > 1080:
            cover_clip = cover_clip.resized(width=1080)
        cover_clip = cover_clip.with_position('center')
        
        # Add title audio to cover clip
        if title_audio and os.path.exists(title_audio):
            print("Adding title audio to cover clip...")
            try:
                title_audio_clip = AudioFileClip(title_audio)
                cover_clip = cover_clip.with_audio(title_audio_clip)
                print("Successfully added title audio")
            except Exception as e:
                print(f"Error adding title audio: {e}")
        else:
            print("No title audio to add")

        # Create a slide for each summary chunk with corresponding audio
        print("Creating summary slides...")
        point_clips = []
        for i, chunk in enumerate(chunks):
            print(f"Creating slide {i+1}/{len(chunks)}...")
            
            point_image_path = add_text_to_book_cover(
                cover_image_path, chunk, temp_dir, f"summary_{i}.png"
            )
            
            # Determine clip duration based on audio or default
            audio_duration = get_audio_duration(chunk_audio_files[i]) if chunk_audio_files[i] else 0
            clip_duration = max(6, audio_duration + 1)  # Add 1 second buffer
            
            print(f"Slide {i} duration: {clip_duration} seconds (audio: {audio_duration})")
            
            point_clip = ImageClip(point_image_path).with_duration(clip_duration)
            
            # Add audio if available
            if chunk_audio_files[i] and os.path.exists(chunk_audio_files[i]):
                print(f"Adding audio to slide {i}...")
                try:
                    audio_clip = AudioFileClip(chunk_audio_files[i])
                    point_clip = point_clip.with_audio(audio_clip)
                    print(f"Successfully added audio to slide {i}")
                except Exception as e:
                    print(f"Error adding audio to clip {i}: {e}")
            else:
                print(f"No audio available for slide {i}")
            
            point_clips.append(point_clip)

        # Create outro image with audio
        print("Creating outro slide...")
        outro_text = f"Happy Reading!\n~ Book Wanderer"
        outro_image_path = create_text_image(outro_text, (1080, 1080), 60, temp_dir, "outro.png")
        outro_duration = max(3, get_audio_duration(outro_audio) if outro_audio else 3)
        outro_clip = ImageClip(outro_image_path).with_duration(outro_duration)
        
        # Add outro audio
        if outro_audio and os.path.exists(outro_audio):
            print("Adding outro audio...")
            try:
                outro_audio_clip = AudioFileClip(outro_audio)
                outro_clip = outro_clip.with_audio(outro_audio_clip)
                print("Successfully added outro audio")
            except Exception as e:
                print(f"Error adding outro audio: {e}")
        else:
            print("No outro audio to add")

        # Only include cover, summary slides, and outro
        all_clips = [cover_clip] + point_clips + [outro_clip]
        
        print(f"Concatenating {len(all_clips)} video clips...")
        final_clip = concatenate_videoclips(all_clips, method="compose")

        output_path = os.path.join(temp_dir, "book_summary.mp4")
        print("Writing final video file...")
        
        # Write video with explicit audio codec
        final_clip.write_videofile(
            output_path,
            fps=24,
            codec='libx264',
            preset='medium',
            logger=None,
            audio_codec='aac',
            temp_audiofile=os.path.join(temp_dir, 'temp-audio.m4a'),
            remove_temp=True
        )
        
        # Close all clips to free memory
        for clip in all_clips:
            clip.close()
        final_clip.close()
        
        print(f"Video created successfully: {output_path}")
        
        # Don't clean up audio files immediately for debugging
        # Keep them to check if they were created properly
        
        return output_path

    except Exception as e:
        error_traceback = traceback.format_exc()
        print(f"Full error traceback:\n{error_traceback}")
        return f"Error generating video: {str(e)}\n\nFull traceback:\n{error_traceback}"

# Test function to verify TTS is working
def test_tts(temp_dir):
    """Test function to verify TTS is working"""
    test_text = "This is a test of the text to speech system."
    test_path = os.path.join(temp_dir, "test_audio.wav")
    
    print("Testing gTTS system...")
    result = generate_speech_audio(test_text, test_path)
    
    if result:
        print(f"gTTS test successful: {result}")
        duration = get_audio_duration(result)
        print(f"Test audio duration: {duration} seconds")
        return True
    else:
        print("gTTS test failed")
        return False
