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

**Book Wanderer** is an intelligent, bilingual book recommendation system that bridges the gap between Korean and English literature. Powered by AI and integrated with comprehensive library databases, it offers personalized book discoveries, community discussions, reading management tools, and now features an innovative **AI-powered video summary generator** that brings books to life through engaging visual content.

<div align="center">

### ✨ What Makes Book Wanderer Special?

🤖 **AI-Powered Recommendations** • 🌐 **Bilingual Support** • 📚 **Library Integration**

👥 **Community Features** • 📱 **Personal Library** • 🎥 **Video Summaries** • 🎨 **Beautiful UI**

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

### 🎥 **AI Video Summary Generator** ⭐ NEW!

![Video Creation GIF](https://media.giphy.com/media/xT9IgzoKnwFNmISR8I/giphy.gif)

</div>

Transform your book recommendations into engaging visual stories! Our latest feature automatically generates professional 1080x1080 summary videos using:

| Component | Technology | Purpose |
|-----------|------------|---------|
| 🧠 **AI Content** | HyperCLOVA API | Intelligent summary generation |
| 🖼️ **Image Processing** | PIL (Python Imaging Library) | Dynamic visual composition |
| 🎬 **Video Assembly** | MoviePy | Professional video rendering |
| 📊 **Progress Tracking** | Real-time UI Updates | Live rendering feedback |

**Key Capabilities:**
- End-to-end automation from text to video
- Intelligent text overlay system for clear, professional visuals
- Real-time progress tracking and instant video preview
- Robust error handling and optimized resource management
- Shareable 1080x1080 format perfect for social media

<div align="center">

### 🤖 **AI Assistant Integration**

![Library GIF](https://media.giphy.com/media/l2Je66zG6mAAZxgqI/giphy.gif)

</div>

Experience the power of **HyperCLOVA API** with advanced Korean language processing, bilingual responses that adapt to your preferences, context-aware conversations that understand your reading journey, deep book analysis with insights into themes and plots, and now **automated video summary creation** that brings recommendations to life.

<div align="center">

### 📚 **Personal Library Management**

![Reading GIF](https://media.giphy.com/media/WoWm8YzFQJg5i/giphy.gif)

</div>

| Feature | Description |
|---------|-------------|
| 📖 **Reading Status** | Track books as "To Read", "Currently Reading", "Finished" |
| ❤️ **Favorites** | Save and organize your beloved books |
| 🎥 **Video Collection** | Generate and save book summary videos |
| 📊 **Reading Stats** | Visualize your reading journey |
| 🏷️ **Smart Categories** | Auto-organize by genre and preferences |

<div align="center">

### 💬 **Community Hub**

![Community GIF](https://media.giphy.com/media/3oKIPnAiaMCws8nOsE/giphy.gif)

</div>

Connect with fellow book lovers through discussion forums where you can share thoughts and reviews, join book clubs to connect with like-minded readers, communicate in your preferred language with multilingual post support, **share AI-generated book videos** to spark discussions, and stay connected with real-time community updates.

<div align="center">

### 🎨 **User Experience**

</div>

```css
✨ Modern Design          🌙 Dark/Light Modes
📱 Responsive Layout      🚀 Fast Performance
🎭 Custom Animations      🔍 Intuitive Search
🎥 Video Integration      📊 Progress Indicators
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

# Video Generation Settings (Optional)
VIDEO_OUTPUT_PATH=./generated_videos/
MAX_VIDEO_DURATION=60
VIDEO_QUALITY=high
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
# Start exploring books and creating videos in your preferred language!
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
    E --> F[Generate Video Summary]
    F --> G[Add to Library]
    G --> H[Share in Community]
```

<div align="center">

### Key Interactions

</div>

| Action | English | Korean |
|--------|---------|--------|
| Search | "Find mystery novels" | "추리소설 찾아줘" |
| Author | "Books by Haruki Murakami" | "무라카미 하루키 책들" |
| Genre | "Romance books" | "로맨스 소설" |
| Video | "Create video summary" | "비디오 요약 만들어줘" |
| Discussion | "What do you think about..." | "이 책에 대해 어떻게 생각해?" |

---

## 📁 Project Structure

```
book-wanderer/
├── 📄 main.py                 # Main Streamlit application
├── 🎨 Frontend.py             # UI components and styling  
├── 🛠️ Helper_Functions.py     # Core utility functions
├── 💬 Discussion_Function.py  # Community features
├── 🎥 Video_Generator.py      # AI video summary system
├── 📚 requirements.txt        # Python dependencies
├── 🔧 .env.example           # Environment template
├── 📖 README.md              # This file
├── 📁 assets/                # Static resources
│   ├── 🖼️ images/
│   ├── 🎨 styles/
│   └── 🎬 video_templates/
└── 📁 generated_videos/      # AI-generated video outputs
```

<div align="center">

## 🔧 Technical Architecture

### **Core Components**

</div>

```python
# AI Integration
HyperCLOVA API → Natural Language Processing + Video Content
Library API → Book Data Retrieval
MongoDB → User Data Management

# Video Processing Pipeline
PIL → Image Processing + Text Overlays
MoviePy → Video Assembly + Rendering
FFmpeg → Video Optimization

# Frontend Stack
Streamlit → Web Interface + Video Preview
CSS/HTML → Custom Styling
JavaScript → Interactive Elements + Progress Tracking
```

<div align="center">

### **Enhanced Data Flow**

</div>

```
User Input → AI Processing → API Calls → Data Processing → UI Rendering
     ↓                                        ↓
Video Generation ← HyperCLOVA ← Book Analysis ← Content Processing
     ↓
Community Sharing ← MongoDB ← User Management
```

---

## 🎬 Video Generation Workflow

<div align="center">

### **AI-Powered Video Pipeline**

</div>

```python
# Step 1: Content Generation
Book Data → HyperCLOVA API → AI Summary

# Step 2: Visual Processing  
Summary Text → PIL → Dynamic Image Composition

# Step 3: Video Assembly
Images + Text → MoviePy → Professional Video

# Step 4: Optimization
Raw Video → FFmpeg → Optimized 1080x1080 Output
```

<div align="center">

### **Video Features**

</div>

| Feature | Implementation | Benefit |
|---------|----------------|---------|
| 🎯 **Smart Layouts** | Dynamic text positioning | Clear, readable content |
| 🎨 **Visual Themes** | Genre-based styling | Engaging, themed videos |
| ⚡ **Real-time Preview** | Progressive rendering | Instant user feedback |
| 📱 **Social Ready** | 1080x1080 format | Perfect for sharing |
| 🔄 **Batch Processing** | Queue management | Efficient resource usage |

---

## 🌐 API Integrations

<div align="center">

### **Korean Library API**

</div>

Access to extensive Korean book database with search capabilities by genre, author, title, and ISBN. Get comprehensive book metadata, cover images, popularity metrics, and **rich content for video generation** to enhance your reading experience.

<div align="center">

### **HyperCLOVA API**

</div>

Advanced Korean language AI processing with natural language understanding and bilingual responses. Enjoy sophisticated book analysis, intelligent recommendation generation, and **automated video script creation** tailored to your preferences.

<div align="center">

### **MongoDB Integration**

</div>

Secure user management with authentication and profiles, personal library storage for your book collections, community data management for discussion posts and interactions, and **video metadata storage** for generated content.

---

## 🚀 Recent Updates

<div align="center">

### **🎥 AI Video Summary Generator** - *Latest Release*

</div>

This week's major feature addition brings book recommendations to life through AI-generated videos:

**✨ Key Highlights:**
- **End-to-end automation**: From book selection to final video output
- **Intelligent processing**: HyperCLOVA-powered content generation  
- **Professional visuals**: Dynamic image handling with PIL
- **Seamless integration**: Real-time progress tracking within the UI
- **Robust performance**: Advanced error handling and resource optimization

**🎯 Impact:**
Enhanced user engagement through visually rich, shareable content that transforms static book recommendations into dynamic, social-media-ready videos.

---

<div align="center">

### **Development Setup**

</div>

```bash
# Fork the repository
git fork https://github.com/yourusername/book-wanderer

# Create feature branch
git checkout -b feature/amazing-feature

# Make changes and commit
git commit -m "Add amazing feature"

# Push and create pull request
git push origin feature/amazing-feature
```

---

## 📜 License

<div align="center">

This project is licensed under the MIT License - see the LICENSE file for details.

</div>

---
