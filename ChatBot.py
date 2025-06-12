import pyttsx3
import os
import tempfile
import platform
import sys
from moviepy import AudioFileClip
import traceback

def diagnose_tts_system():
    """Comprehensive TTS system diagnosis"""
    print("=" * 60)
    print("TTS SYSTEM DIAGNOSTIC")
    print("=" * 60)
    
    # System information
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Python version: {platform.python_version()}")
    print(f"Architecture: {platform.architecture()}")
    
    # Check pyttsx3 installation
    try:
        import pyttsx3
        print(f"✅ pyttsx3 is installed (version: {pyttsx3.__version__ if hasattr(pyttsx3, '__version__') else 'unknown'})")
    except ImportError:
        print("❌ pyttsx3 is not installed")
        return False
    
    # Check moviepy installation
    try:
        from moviepy import AudioFileClip
        print("✅ moviepy is installed")
    except ImportError:
        print("❌ moviepy is not installed")
        return False
    
    # Try to initialize TTS engine
    print("\n" + "-" * 40)
    print("TESTING TTS ENGINE INITIALIZATION")
    print("-" * 40)
    
    engine = None
    try:
        engine = pyttsx3.init()
        print("✅ TTS engine initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize TTS engine: {e}")
        traceback.print_exc()
        return False
    
    # Check available voices
    print("\n" + "-" * 40)
    print("CHECKING AVAILABLE VOICES")
    print("-" * 40)
    
    try:
        voices = engine.getProperty('voices')
        if voices:
            print(f"✅ Found {len(voices)} voices:")
            for i, voice in enumerate(voices):
                if voice:
                    name = getattr(voice, 'name', 'Unknown')
                    id_val = getattr(voice, 'id', 'Unknown')
                    lang = getattr(voice, 'languages', ['Unknown'])
                    print(f"  {i}: {name} (ID: {id_val}, Lang: {lang})")
        else:
            print("⚠️  No voices found")
    except Exception as e:
        print(f"❌ Error checking voices: {e}")
    
    # Check TTS properties
    print("\n" + "-" * 40)
    print("CHECKING TTS PROPERTIES")
    print("-" * 40)
    
    try:
        rate = engine.getProperty('rate')
        volume = engine.getProperty('volume')
        voice = engine.getProperty('voice')
        print(f"✅ Current rate: {rate}")
        print(f"✅ Current volume: {volume}")
        print(f"✅ Current voice: {voice}")
    except Exception as e:
        print(f"❌ Error checking properties: {e}")
    
    # Test audio generation
    print("\n" + "-" * 40)
    print("TESTING AUDIO GENERATION")
    print("-" * 40)
    
    temp_dir = tempfile.mkdtemp()
    test_file = os.path.join(temp_dir, "test_audio.wav")
    test_text = "Hello, this is a test of the text to speech system."
    
    try:
        print(f"Generating audio to: {test_file}")
        engine.save_to_file(test_text, test_file)
        engine.runAndWait()
        
        # Wait for file to be created
        import time
        time.sleep(2)
        
        if os.path.exists(test_file):
            file_size = os.path.getsize(test_file)
            print(f"✅ Audio file created: {file_size} bytes")
            
            if file_size > 100:
                # Test with moviepy
                try:
                    audio_clip = AudioFileClip(test_file)
                    duration = audio_clip.duration
                    audio_clip.close()
                    print(f"✅ Audio duration: {duration} seconds")
                    print("✅ TTS system is working correctly!")
                    return True
                except Exception as e:
                    print(f"❌ Error reading audio with moviepy: {e}")
                    return False
            else:
                print("❌ Audio file is too small (likely empty)")
                return False
        else:
            print("❌ Audio file was not created")
            return False
            
    except Exception as e:
        print(f"❌ Error generating audio: {e}")
        traceback.print_exc()
        return False
    finally:
        try:
            engine.stop()
        except:
            pass

def suggest_fixes():
    """Suggest potential fixes for TTS issues"""
    print("\n" + "=" * 60)
    print("POTENTIAL FIXES")
    print("=" * 60)
    
    system = platform.system()
    
    if system == "Windows":
        print("For Windows:")
        print("1. Install Microsoft Speech Platform:")
        print("   - Download and install Microsoft Speech Platform Runtime")
        print("   - Install Microsoft Speech Platform SDK")
        print("2. Try installing additional voices from Windows Settings")
        print("3. Run as administrator if you have permission issues")
        print("4. Try: pip install --upgrade pyttsx3")
        
    elif system == "Darwin":  # macOS
        print("For macOS:")
        print("1. Make sure you have system voices installed")
        print("2. Check System Preferences > Accessibility > Speech")
        print("3. Try: pip install --upgrade pyttsx3")
        print("4. If using conda, try: conda install -c conda-forge espeak")
        
    elif system == "Linux":
        print("For Linux:")
        print("1. Install espeak: sudo apt-get install espeak espeak-data")
        print("2. Or install festival: sudo apt-get install festival festvox-kallpc16k")
        print("3. Try: pip install --upgrade pyttsx3")
        print("4. For Ubuntu/Debian: sudo apt-get install python3-pyttsx3")
        
    print("\nGeneral troubleshooting:")
    print("1. Restart your Python environment")
    print("2. Try in a fresh virtual environment")
    print("3. Check if antivirus is blocking TTS")
    print("4. Try running with different user permissions")
    print("5. Alternative: Use gTTS (Google Text-to-Speech) instead")

def test_alternative_tts():
    """Test alternative TTS solutions"""
    print("\n" + "=" * 60)
    print("TESTING ALTERNATIVE TTS SOLUTIONS")
    print("=" * 60)
    
    # Test gTTS
    try:
        from gtts import gTTS
        import pygame
        
        print("✅ gTTS is available")
        
        temp_dir = tempfile.mkdtemp()
        temp_file = os.path.join(temp_dir, "gtts_test.mp3")
        
        tts = gTTS("This is a test using Google Text to Speech", lang='en')
        tts.save(temp_file)
        
        if os.path.exists(temp_file) and os.path.getsize(temp_file) > 0:
            print("✅ gTTS audio generation successful")
            return temp_file
        else:
            print("❌ gTTS audio generation failed")
            
    except ImportError:
        print("⚠️  gTTS not installed (pip install gtts)")
    except Exception as e:
        print(f"❌ gTTS error: {e}")
    
    return None

if __name__ == "__main__":
    print("Starting TTS diagnostic...")
    
    success = diagnose_tts_system()
    
    if not success:
        suggest_fixes()
        
        # Test alternative solutions
        alt_file = test_alternative_tts()
        if alt_file:
            print(f"\n✅ Alternative TTS solution works: {alt_file}")
        
    print("\n" + "=" * 60)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 60)
