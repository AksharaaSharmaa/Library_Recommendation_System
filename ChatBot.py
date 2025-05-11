import streamlit as st
import requests
from streamlit_extras.colored_header import colored_header
import base64

# Custom CSS for the warm earthy theme
def add_custom_css():
    st.markdown("""
    <style>
    /* Main background and text colors */
    .stApp {
        background: linear-gradient(135deg, #E3D4B9, #D9CBA0, #E3D4B9);
        color: #4B3D2D;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: rgba(75, 61, 45, 0.1);
    }
    
    /* Chat message containers */
    .stChatMessage {
        background: rgba(226, 212, 185, 0.4);
        border-radius: 15px;
        margin-bottom: 12px;
        padding: 10px;
        border-left: none;
        box-shadow: 0 4px 8px rgba(75, 61, 45, 0.1);
    }
    
    /* User message styling */
    [data-testid="stChatMessageContent"] {
        background: rgba(166, 124, 77, 0.1) !important;
        border-radius: 12px !important;
        padding: 10px 15px !important;
        border: none;
        box-shadow: 0 2px 5px rgba(75, 61, 45, 0.1);
    }
    
    /* Chat input box */
    .stChatInputContainer {
        background: rgba(226, 212, 185, 0.6) !important;
        border-radius: 20px !important;
        padding: 5px !important;
        border: 1px solid rgba(139, 91, 41, 0.2);
    }
    
    /* Chat input field */
    .stChatInput {
        background: rgba(255, 255, 255, 0.8) !important;
        color: #4B3D2D !important;
        border-radius: 18px !important;
    }
    
    /* Button styling */
    .stButton button {
        background: linear-gradient(90deg, #8B5B29, #A67C4D) !important;
        color: #E3D4B9 !important;
        border: none !important;
        border-radius: 20px !important;
        padding: 10px 20px !important;
        font-weight: bold !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 10px rgba(139, 91, 41, 0.2) !important;
    }
    
    .stButton button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 15px rgba(139, 91, 41, 0.3) !important;
        background: linear-gradient(90deg, #A67C4D, #8B5B29) !important;
    }
    
    /* API key input */
    [data-testid="stTextInput"] input {
        background: rgba(255, 255, 255, 0.8) !important;
        border: 1px solid rgba(139, 91, 41, 0.3) !important;
        border-radius: 8px !important;
        color: #4B3D2D !important;
    }
    
    /* Header styling */
    h1, h2, h3 {
        color: #8B5B29;
        font-weight: 800 !important;
    }
    
    /* Korean text emphasis */
    .korean-text {
        color: #8B5B29;
        font-weight: 500;
    }
    
    /* Streamlit elements padding reduction */
    [data-testid="stVerticalBlock"] {
        gap: 10px !important;
    }
    
    /* Make header more compact */
    [data-testid="stHeader"] {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
    }

    /* Divider style */
    hr {
        height: 1px;
        background: linear-gradient(90deg, transparent, #A67C4D, transparent);
        border: none;
        margin: 15px 0;
    }

    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }

    ::-webkit-scrollbar-track {
        background: rgba(217, 203, 160, 0.3);
        border-radius: 10px;
    }

    ::-webkit-scrollbar-thumb {
        background: #A67C4D;
        border-radius: 10px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: #8B5B29;
    }
    </style>
    """, unsafe_allow_html=True)

# Function to create a warm title
def warm_title(title):
    html = f'''
    <div style="text-align: center; margin-bottom: 20px;">
        <h1 style="color: #8B5B29; 
                   font-size: 2.6rem;
                   font-weight: 800;
                   text-shadow: 1px 1px 2px rgba(75, 61, 45, 0.2);">
            {title}
        </h1>
        <div style="height: 3px; width: 100px; margin: 0 auto; background: linear-gradient(90deg, transparent, #A67C4D, transparent);"></div>
    </div>
    '''
    st.markdown(html, unsafe_allow_html=True)

# Apply the custom CSS
add_custom_css()

# App layout
st.title=("HyperCLOVA X Bilingual Bot")

# Create columns for layout
col1, col2, col3 = st.columns([1, 3, 1])

with col2:
    warm_title("HyperCLOVA X Bilingual Chatbot")
    
    st.markdown("""
    <div style="text-align: center; margin-bottom: 20px;">
        <p style="font-size: 1.1rem; color: #4B3D2D; margin-bottom: 20px;">
            Experience seamless communication in English and Korean
        </p>
    </div>
    """, unsafe_allow_html=True)

# Initialize session state for storing conversation history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "You are a helpful AI assistant. For EVERY response, you must answer in BOTH English and Korean. First provide the complete answer in English, then provide '한국어 답변:' followed by the complete Korean translation of your answer."}
    ]

# API key input
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

# Sidebar for API key with improved styling
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; margin-bottom: 20px; padding-top: 20px;">
        <h3 style="color: #8B5B29; font-weight: 700;">
            API Configuration
        </h3>
        <div style="height: 2px; width: 80px; margin: 10px auto; background: linear-gradient(90deg, transparent, #A67C4D, transparent);"></div>
    </div>
    """, unsafe_allow_html=True)
    
    api_key = st.text_input("Enter your HyperCLOVA API Key", type="password", value=st.session_state.api_key)
    st.session_state.api_key = api_key
    
    # Fixed settings without sliders
    st.markdown("""
    <div style="text-align: center; margin: 20px 0;">
        <h4 style="color: #8B5B29; font-weight: 600;">
            Model Settings
        </h4>
        <div style="height: 2px; width: 60px; margin: 10px auto; background: linear-gradient(90deg, transparent, #A67C4D, transparent);"></div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background: rgba(226, 212, 185, 0.5); padding: 15px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 2px 6px rgba(75, 61, 45, 0.1);">
        <p style="margin: 8px 0; color: #4B3D2D;"><span style="color: #8B5B29; font-weight: 500;">Temperature:</span> 0.7</p>
        <p style="margin: 8px 0; color: #4B3D2D;"><span style="color: #8B5B29; font-weight: 500;">Max Tokens:</span> 1024</p>
        <p style="margin: 8px 0; color: #4B3D2D;"><span style="color: #8B5B29; font-weight: 500;">Top P:</span> 0.8</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Clear chat button with warm style
    if st.button("Clear Chat ✨"):
        st.session_state.messages = [
            {"role": "system", "content": "You are a helpful AI assistant. For EVERY response, you must answer in BOTH English and Korean. First provide the complete answer in English, then provide '한국어 답변:' followed by the complete Korean translation of your answer."}
        ]
        st.rerun()
    
    st.markdown("""
    <div style="text-align: center; margin-top: 30px; padding: 10px;">
        <p style="color: #4B3D2D; font-size: 0.85rem; font-style: italic;">
            Powered by HyperCLOVA X
        </p>
    </div>
    """, unsafe_allow_html=True)

# Chat container
chat_container = st.container()

with chat_container:
    # Display chat history with custom styling
    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                # Apply custom styling for Korean text
                if message["role"] == "assistant" and "한국어 답변:" in message["content"]:
                    parts = message["content"].split("한국어 답변:", 1)
                    english_part = parts[0].strip()
                    korean_part = parts[1].strip() if len(parts) > 1 else ""
                    
                    st.markdown(english_part)
                    st.markdown(f"""
                    <div style="margin-top: 15px; padding-top: 12px; border-top: 1px solid rgba(166, 124, 77, 0.3);">
                        <span style="color: #8B5B29; font-weight: 500;">한국어 답변:</span><br>
                        {korean_part}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask something in English or Korean..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Display assistant response
        with st.chat_message("assistant"):
            if not st.session_state.api_key:
                st.error("Please enter your HyperCLOVA API Key in the sidebar.")
            else:
                message_placeholder = st.empty()
                
                # Custom loading animation
                st.markdown("""
                <div style="display: flex; justify-content: center; align-items: center; margin: 15px 0;">
                    <div style="color: #8B5B29; font-weight: 500;">Thinking</div>
                    <div class="loading-dots">
                        <style>
                            .loading-dots {
                                display: flex;
                                align-items: center;
                            }
                            .loading-dots::after {
                                content: '...';
                                color: #A67C4D;
                                animation: dots 1.5s infinite;
                                font-weight: bold;
                            }
                            @keyframes dots {
                                0%, 20% { content: '.'; }
                                40% { content: '..'; }
                                60%, 100% { content: '...'; }
                            }
                        </style>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                try:
                    endpoint = "https://clovastudio.stream.ntruss.com/testapp/v1/chat-completions/HCX-003"
                    headers = {
                        "Authorization": f"Bearer {st.session_state.api_key}",
                        "Content-Type": "application/json"
                    }
                    
                    # Add a reminder to respond in both languages for each user query
                    messages_with_reminder = st.session_state.messages.copy()
                    if len(messages_with_reminder) > 1:  # If there's at least one user message
                        messages_with_reminder.append({
                            "role": "system", 
                            "content": "Remember to respond in BOTH English and Korean. First provide the complete answer in English, then write '한국어 답변:' followed by the complete Korean translation."
                        })
                    
                    payload = {
                        "messages": messages_with_reminder,
                        "maxTokens": 1024,  # Fixed value
                        "temperature": 0.7,  # Fixed value
                        "topP": 0.8,        # Fixed value
                    }
                    
                    response = requests.post(endpoint, headers=headers, json=payload)
                    
                    if response.status_code == 200:
                        result = response.json()
                        assistant_response = result['result']['message']['content']
                        
                        # Format the response with custom styling
                        if "한국어 답변:" in assistant_response:
                            parts = assistant_response.split("한국어 답변:", 1)
                            english_part = parts[0].strip()
                            korean_part = parts[1].strip() if len(parts) > 1 else ""
                            
                            formatted_response = f"{english_part}\n\n<div style='margin-top: 15px; padding-top: 12px; border-top: 1px solid rgba(166, 124, 77, 0.3);'><span style='color: #8B5B29; font-weight: 500;'>한국어 답변:</span><br>{korean_part}</div>"
                            message_placeholder.markdown(formatted_response, unsafe_allow_html=True)
                        else:
                            message_placeholder.markdown(assistant_response)
                        
                        # Add assistant response to chat history
                        st.session_state.messages.append({"role": "assistant", "content": assistant_response})
                    else:
                        message_placeholder.error(f"API Error {response.status_code}: {response.text}")
                except Exception as e:
                    message_placeholder.error(f"Request failed: {e}")
