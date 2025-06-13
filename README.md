<div align="center">

# 📚 Book Wanderer / 책방랑자


*Discover your next favorite read with AI assistance in English and Korean*

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Korean Support](https://img.shields.io/badge/Language-English%20%2B%20Korean-purple.svg)]()

🚀 **[Experience Book Wanderer Live](https://genta-library-recommendation.streamlit.app/)**

</div>

---

## 🌟 Overview

**Book Wanderer** is an intelligent, bilingual book recommendation system that bridges the gap between Korean and English literature. Powered by AI and integrated with comprehensive library databases, it offers personalized book discoveries, community discussions, reading management tools, and now features an innovative **AI-powered video summary generator with voice narration** that brings books to life through engaging audiovisual content.

<div align="center">

### ✨ What Makes Book Wanderer Special?

🤖 **AI-Powered Recommendations** • 🌐 **Bilingual Support** • 📚 **Library Integration**

👥 **Community Features** • 📱 **Personal Library** • 🎥 **Video Summaries** • 🎙️ **Voice Narration** • 🎨 **Beautiful UI**

</div>

---

## 🎯 Features

<div align="center">

### 🔍 **Smart Book Discovery**

</div>

```
🎭 Genre-Based Search        📝 Author-Specific Search
🏷️ Category Filtering        ⭐ Popularity Rankings
🔄 Dynamic Recommendations   🎯 Personalized Suggestions
```

<div align="center">

### 🎥 **AI Video Summary Generator with Voice** ⭐ ENHANCED!

![Video Creation GIF](https://media.giphy.com/media/xT9IgzoKnwFNmISR8I/giphy.gif)

</div>

Transform your book recommendations into captivating audiovisual experiences! Our enhanced feature now includes professional voice narration alongside stunning visuals:

| Component | Technology | Purpose |
|-----------|------------|---------|
| 🧠 **AI Content** | HyperCLOVA API | Intelligent summary generation |
| 🎙️ **Voice Synthesis** | Text-to-Speech Engine | Natural voice narration |
| 🖼️ **Image Processing** | PIL (Python Imaging Library) | Dynamic visual composition |
| 🎬 **Video Assembly** | MoviePy | Professional audiovisual rendering |
| 🔊 **Audio Processing** | Advanced audio mixing | Crystal-clear voice output |
| 📊 **Progress Tracking** | Real-time UI Updates | Live rendering feedback |

**Key Capabilities:**
- **Full audiovisual experience** with synchronized voice narration
- **Bilingual voice support** for Korean and English content
- **Professional audio quality** with clear, engaging narration
- **Intelligent text-to-speech** that adapts to book content and tone
- End-to-end automation from text to complete audiovisual content
- Intelligent text overlay system for visual reinforcement
- Real-time progress tracking and instant video preview
- Robust error handling and optimized resource management
- Shareable 1080x1080 format perfect for social media platforms

<div align="center">

### 🤖 **AI Assistant Integration**

![Library GIF](https://media.giphy.com/media/l2Je66zG6mAAZxgqI/giphy.gif)

</div>

Experience the power of **HyperCLOVA API** with advanced Korean language processing, bilingual responses that adapt to your preferences, context-aware conversations that understand your reading journey, deep book analysis with insights into themes and plots, and now **automated audiovisual summary creation** that brings recommendations to life with both voice and visuals.

<div align="center">

### 📚 **Personal Library Management**

![Reading GIF](https://media.giphy.com/media/WoWm8YzFQJg5i/giphy.gif)

</div>

| Feature | Description |
|---------|-------------|
| 📖 **Reading Status** | Track books as "To Read", "Currently Reading", "Finished" |
| ❤️ **Favorites** | Save and organize your beloved books |
| 🎥 **Video Collection** | Generate and save book summary videos with voice |
| 📊 **Reading Stats** | Visualize your reading journey |
| 🏷️ **Smart Categories** | Auto-organize by genre and preferences |
| 🎙️ **Audio Library** | Collection of narrated book summaries |

<div align="center">

### 💬 **Community Hub**

![Community GIF](https://media.giphy.com/media/3oKIPnAiaMCws8nOsE/giphy.gif)

</div>

Connect with fellow book lovers through discussion forums where you can share thoughts and reviews, join book clubs to connect with like-minded readers, communicate in your preferred language with multilingual post support, **share AI-generated audiovisual book content** to spark discussions, and stay connected with real-time community updates.

<div align="center">

### 🎨 **User Experience**

</div>

```css
✨ Modern Design          🌙 Dark/Light Modes
📱 Responsive Layout      🚀 Fast Performance
🎭 Custom Animations      🔍 Intuitive Search
🎥 Video Integration      🎙️ Voice Controls
📊 Progress Indicators    🔊 Audio Preview
```

---

## 🛠️ Installation

<div align="center">

### Prerequisites

</div>

```bash
Python 3.8+
pip package manager
MongoDB (for user data)
FFmpeg (for video processing)
Audio drivers (for voice synthesis)
```

<div align="center">

### Quick Start

</div>

```bash
# Clone the repository
git clone https://github.com/yourusername/book-wanderer.git
cd book-wanderer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install FFmpeg for video processing
# Ubuntu/Debian: sudo apt install ffmpeg
# macOS: brew install ffmpeg
# Windows: Download from https://ffmpeg.org/

# Install additional audio dependencies
pip install pydub gTTS pygame

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Run the application
streamlit run main.py
```

<div align="center">

### 🔑 API Configuration

</div>

```env
# Required API Keys
HYPERCLOVA_API_KEY=your_hyperclova_key
LIBRARY_API_KEY=your_korean_library_key
MONGODB_URI=your_mongodb_connection_string

# Voice & Video Generation Settings
VIDEO_OUTPUT_PATH=./generated_videos/
AUDIO_OUTPUT_PATH=./generated_audio/
MAX_VIDEO_DURATION=60
VIDEO_QUALITY=high
VOICE_LANGUAGE=auto  # auto, ko, en
VOICE_SPEED=1.0
AUDIO_QUALITY=high
```

---

## 🎮 Usage

<div align="center">

### Getting Started

</div>

```python
# Launch the app
streamlit run main.py

# Navigate to http://localhost:8501
# Start exploring books and creating audiovisual content in your preferred language!
```

<div align="center">

### Enhanced Book Discovery Flow

</div>

```mermaid
graph LR
    A[Welcome] --> B[Describe Preferences]
    B --> C[AI Analysis]
    C --> D[Book Recommendations]
    D --> E[Book Details]
    E --> F[Generate Audiovisual Summary]
    F --> G[Voice Narration + Visuals]
    G --> H[Add to Library]
    H --> I[Share in Community]
```

<div align="center">

### Key Interactions

</div>

| Action | English | Korean |
|--------|---------|--------|
| Search | "Find mystery novels" | "추리소설 찾아줘" |
| Author | "Books by Haruki Murakami" | "무라카미 하루키 책들" |
| Genre | "Romance books" | "로맨스 소설" |
| Video | "Create video with voice summary" | "음성 요약 비디오 만들어줘" |
| Audio | "Generate narrated summary" | "나레이션 요약 생성해줘" |
| Discussion | "What do you think about..." | "이 책에 대해 어떻게 생각해?" |

---

## 📁 Project Structure

```
book-wanderer/
├── 📄 main.py                 # Main Streamlit application
├── 🎨 Frontend.py             # UI components and styling  
├── 🛠️ Helper_Functions.py     # Core utility functions
├── 💬 Discussion_Function.py  # Community features
├── 🎥 Video_Generator.py      # AI audiovisual summary system
├── 🎙️ Voice_Processor.py     # Voice synthesis and audio processing
├── 📚 requirements.txt        # Python dependencies
├── 🔧 .env.example           # Environment template
├── 📖 README.md              # This file
├── 📁 assets/                # Static resources
│   ├── 🖼️ images/
│   ├── 🎨 styles/
│   ├── 🎬 video_templates/
│   └── 🎙️ voice_profiles/
├── 📁 generated_videos/      # AI-generated video outputs
└── 📁 generated_audio/       # Voice narration files
```

<div align="center">

## 🔧 Technical Architecture

### **Core Components**

</div>

```python
# AI Integration
HyperCLOVA API → Natural Language Processing + Content Generation
Text-to-Speech Engine → Voice Synthesis + Audio Processing
Library API → Book Data Retrieval
MongoDB → User Data Management

# Audiovisual Processing Pipeline
PIL → Image Processing + Text Overlays
MoviePy → Video Assembly + Audio Sync
pydub → Audio Processing + Voice Enhancement
FFmpeg → Video Optimization + Audio Mixing

# Frontend Stack
Streamlit → Web Interface + Media Preview
CSS/HTML → Custom Styling + Audio Controls
JavaScript → Interactive Elements + Progress Tracking
```

<div align="center">

### **Enhanced Data Flow**

</div>

```
User Input → AI Processing → API Calls → Data Processing → UI Rendering
     ↓                                        ↓
Audiovisual Generation ← Voice Synthesis ← HyperCLOVA ← Book Analysis
     ↓                        ↓
Video Assembly ← Audio Processing ← Content Processing
     ↓
Community Sharing ← MongoDB ← User Management
```

---

## 🎬 Audiovisual Generation Workflow

<div align="center">

### **AI-Powered Audiovisual Pipeline**

</div>

```python
# Step 1: Content Generation
Book Data → HyperCLOVA API → AI Summary

# Step 2: Voice Synthesis
Summary Text → Text-to-Speech → Natural Voice Narration

# Step 3: Visual Processing  
Summary Text → PIL → Dynamic Image Composition

# Step 4: Audio Processing
Voice Audio → pydub → Enhanced Audio Quality

# Step 5: Audiovisual Assembly
Images + Enhanced Audio → MoviePy → Professional Audiovisual Content

# Step 6: Optimization
Raw Video → FFmpeg → Optimized 1080x1080 Output with Crystal Audio
```

<div align="center">

### **Audiovisual Features**

</div>

| Feature | Implementation | Benefit |
|---------|----------------|---------|
| 🎙️ **Natural Voice** | Advanced TTS engine | Engaging audio narration |
| 🌐 **Bilingual Audio** | Korean + English synthesis | Localized experience |
| 🎯 **Smart Layouts** | Dynamic text positioning | Clear, readable content |
| 🎨 **Visual Themes** | Genre-based styling | Cohesive audiovisual themes |
| 🔊 **Audio Sync** | Precise timing alignment | Perfect voice-visual sync |
| ⚡ **Real-time Preview** | Progressive rendering | Instant user feedback |
| 📱 **Social Ready** | 1080x1080 format | Perfect for sharing |
| 🔄 **Batch Processing** | Queue management | Efficient resource usage |

---

## 🌐 API Integrations

<div align="center">

### **Korean Library API**

</div>

Access to extensive Korean book database with search capabilities by genre, author, title, and ISBN. Get comprehensive book metadata, cover images, popularity metrics, and **rich content for audiovisual generation** to enhance your reading experience.

<div align="center">

### **HyperCLOVA API**

</div>

Advanced Korean language AI processing with natural language understanding and bilingual responses. Enjoy sophisticated book analysis, intelligent recommendation generation, and **automated audiovisual script creation** with voice-optimized content tailored to your preferences.

<div align="center">

### **Text-to-Speech Integration**

</div>

Professional voice synthesis with natural-sounding Korean and English narration, adjustable speech parameters for optimal listening experience, context-aware pronunciation for book titles and author names, and **emotion-aware delivery** that matches book genres and themes.

<div align="center">

### **MongoDB Integration**

</div>

Secure user management with authentication and profiles, personal library storage for your book collections, community data management for discussion posts and interactions, **audiovisual content metadata storage** for generated videos and audio files, and **voice preference tracking** for personalized narration settings.

---

## 🚀 Recent Updates

<div align="center">

### **🎙️ Voice-Enhanced Video Summaries** - *Latest Release*

</div>

This week's major enhancement brings professional voice narration to our AI-generated video summaries:

**✨ Key Highlights:**
- **Full audiovisual experience**: Synchronized voice narration with dynamic visuals
- **Bilingual voice support**: Native Korean and English text-to-speech capabilities
- **Intelligent audio processing**: Enhanced voice quality with pydub integration
- **Perfect synchronization**: Precise timing alignment between voice and visuals
- **Professional audio quality**: Crystal-clear narration optimized for engagement
- **Seamless integration**: Voice controls and audio preview within the existing UI
- **Advanced customization**: Adjustable voice parameters for personalized experience

**🎯 Impact:**
Revolutionary enhancement in user engagement through immersive audiovisual content that transforms static book recommendations into compelling, podcast-like experiences perfect for modern content consumption and social sharing.

**🔧 Technical Improvements:**
- Enhanced MoviePy integration for seamless audio-video synchronization
- Optimized audio processing pipeline for consistent quality
- Real-time audio preview functionality
- Robust error handling for voice synthesis failures
- Memory-efficient audio processing for large-scale generation

---

<div align="center">

### **Development Setup**

</div>

```bash
# Fork the repository
git fork https://github.com/yourusername/book-wanderer

# Create feature branch
git checkout -b feature/amazing-feature

# Install audio development dependencies
pip install pydub gTTS pygame librosa

# Make changes and commit
git commit -m "Add amazing audiovisual feature"

# Push and create pull request
git push origin feature/amazing-feature
```

---

## 📜 License

<div align="center">

This project is licensed under the MIT License - see the LICENSE file for details.

</div>

---
