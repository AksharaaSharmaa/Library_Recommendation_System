import streamlit as st
import requests
from streamlit_extras.colored_header import colored_header
import base64

# Custom CSS for an elegant brown-themed aesthetic
def add_custom_css():
    st.markdown("""
    <style>
    /* Main background with subtle gradient */
    .stApp {
        background: linear-gradient(145deg, #f5efe6, #e8dbc5, #f0e6d2);
        color: #3a2f24;
        font-family: 'Crimson Text', 'Georgia', serif;
    }
    
    /* Remove all container boxes */
    div.block-container {
        padding-top: 1rem;
        padding-bottom: 0;
        max-width: 850px;
    }
    
    /* Elegant typography */
    body, p, div {
        font-size: 1.05rem;
        line-height: 1.6;
    }
    
    /* Removal of default Streamlit padding */
    .main .block-container {
        padding: 1rem 0;
    }
    
    /* Chat history styling - removing container boxes */
    .stChatMessage {
        background: transparent !important;
        border-radius: 0;
        margin-bottom: 1.5rem;
        padding: 0;
        border-left: none;
        box-shadow: none;
    }
    
    /* User message styling */
    [data-testid="stChatMessageContent"] {
        background: linear-gradient(90deg, rgba(210, 184, 156, 0.07), rgba(181, 145, 106, 0.15)) !important;
        border-radius: 18px !important;
        padding: 12px 18px !important;
        border: none;
        box-shadow: 0 1px 3px rgba(121, 85, 47, 0.05);
        font-size: 1.02rem;
    }
    
    /* Chat input box - elegant minimalist design */
    .stChatInputContainer {
        background: transparent !important;
        padding: 5px !important;
        border: none;
    }
    
    /* Chat input field */
    .stChatInput {
        background: rgba(255, 252, 247, 0.85) !important;
        color: #563b25 !important;
        border-radius: 24px !important;
        border: 1px solid rgba(159, 118, 75, 0.25) !important;
        padding: 10px 20px !important;
        box-shadow: 0 2px 6px rgba(121, 85, 47, 0.05);
        font-style: italic;
    }
    
    .stChatInput:focus {
        border: 1px solid rgba(159, 118, 75, 0.5) !important;
        box-shadow: 0 2px 8px rgba(159, 118, 75, 0.15);
    }
    
    /* Button styling */
    .stButton button {
        background: linear-gradient(90deg, #9c7a54, #b38e65) !important;
        color: #fff6ea !important;
        border: none !important;
        border-radius: 24px !important;
        padding: 10px 22px !important;
        font-weight: 500 !important;
        letter-spacing: 0.5px;
        transition: all 0.3s ease !important;
        box-shadow: 0 3px 8px rgba(121, 85, 47, 0.15) !important;
    }
    
    .stButton button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 5px 12px rgba(121, 85, 47, 0.25) !important;
        background: linear-gradient(90deg, #b38e65, #9c7a54) !important;
    }
    
    /* API key input */
    [data-testid="stTextInput"] input {
        background: rgba(255, 252, 247, 0.8) !important;
        border: 1px solid rgba(159, 118, 75, 0.2) !important;
        border-radius: 12px !important;
        color: #563b25 !important;
        padding: 8px 16px !important;
    }
    
    [data-testid="stTextInput"] input:focus {
        border: 1px solid rgba(159, 118, 75, 0.5) !important;
        box-shadow: 0 0 0 1px rgba(159, 118, 75, 0.2);
    }
    
    /* Header styling */
    h1, h2, h3 {
        font-family: 'Playfair Display', 'Times New Roman', serif;
        color: #6b4423;
        font-weight: 700 !important;
        letter-spacing: 0.5px;
    }
    
    /* Korean text styling */
    .korean-text {
        color: #8a5d3b;
        font-weight: 500;
    }
    
    /* Elegant divider */
    hr {
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(159, 118, 75, 0.5), transparent);
        border: none;
        margin: 20px 0;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(165deg, #f2e9dd, #f8f3e9);
        border-right: 1px solid rgba(159, 118, 75, 0.1);
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 5px;
        height: 5px;
    }

    ::-webkit-scrollbar-track {
        background: rgba(217, 203, 160, 0.1);
    }

    ::-webkit-scrollbar-thumb {
        background: rgba(159, 118, 75, 0.3);
        border-radius: 10px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: rgba(159, 118, 75, 0.5);
    }
    
    /* Elegant notification styling */
    .stAlert {
        background: linear-gradient(90deg, #f7f0e6, #f2e9dd) !important;
        border: 1px solid rgba(159, 118, 75, 0.2) !important;
        border-left: 3px solid #9c7a54 !important;
    }
    
    .stAlert > div {
        color: #6b4423 !important;
    }
    
    /* Chat messages separation */
    .stChatMessage {
        position: relative;
    }
    
    .stChatMessage:not(:last-child)::after {
        content: '';
        position: absolute;
        bottom: -0.75rem;
        left: 10%;
        right: 10%;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(159, 118, 75, 0.15), transparent);
    }
    
    /* Message content styling */
    [data-testid="stChatMessageContent"] {
        font-size: 1.02rem;
        line-height: 1.6;
    }
    
    /* Color for links */
    a {
        color: #9c7a54 !important;
        text-decoration: none !important;
        border-bottom: 1px dotted rgba(159, 118, 75, 0.5);
        transition: all 0.2s ease;
    }
    
    a:hover {
        color: #6b4423 !important;
        border-bottom: 1px solid rgba(159, 118, 75, 0.8);
    }
    </style>
    """, unsafe_allow_html=True)

# Function to create an elegant title
def elegant_title(title):
    html = f'''
    <div style="text-align: center; margin: 1.8rem 0 2.2rem;">
        <h1 style="color: #6b4423; 
                   font-size: 2.5rem;
                   font-weight: 700;
                   font-family: 'Playfair Display', serif;
                   letter-spacing: 1px;
                   margin-bottom: 0.5rem;
                   text-shadow: 1px 1px 1px rgba(159, 118, 75, 0.1);">
            {title}
        </h1>
        <div style="height: 1px; width: 120px; margin: 0.8rem auto 1rem; background: linear-gradient(90deg, transparent, rgba(159, 118, 75, 0.6), transparent);"></div>
    </div>
    '''
    st.markdown(html, unsafe_allow_html=True)

# Apply the custom CSS
add_custom_css()

# Hide Streamlit's default header and footer
hide_st_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)

# Create a centered layout
col1, col2, col3 = st.columns([1, 10, 1])

with col2:
    elegant_title("HyperCLOVA X Bilingual Chatbot")
    
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <p style="font-size: 1.1rem; color: #8a5d3b; font-style: italic; letter-spacing: 0.3px;">
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

# Elegant sidebar
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; margin-bottom: 1.5rem; padding-top: 1.5rem;">
        <h3 style="color: #6b4423; font-weight: 700; font-family: 'Playfair Display', serif; letter-spacing: 0.5px;">
            API Configuration
        </h3>
        <div style="height: 1px; width: 80px; margin: 0.6rem auto; background: linear-gradient(90deg, transparent, rgba(159, 118, 75, 0.5), transparent);"></div>
    </div>
    """, unsafe_allow_html=True)
    
    api_key = st.text_input("Enter your HyperCLOVA API Key", type="password", value=st.session_state.api_key, placeholder="Your secret key...")
    st.session_state.api_key = api_key
    
    # Model settings section
    st.markdown("""
    <div style="text-align: center; margin: 2rem 0 1rem;">
        <h4 style="color: #6b4423; font-weight: 600; font-family: 'Playfair Display', serif; letter-spacing: 0.3px;">
            Model Settings
        </h4>
        <div style="height: 1px; width: 60px; margin: 0.5rem auto; background: linear-gradient(90deg, transparent, rgba(159, 118, 75, 0.4), transparent);"></div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="padding: 0.5rem 0.2rem; margin-bottom: 1.5rem;">
        <p style="margin: 0.6rem 0; color: #563b25; font-size: 0.95rem;"><span style="color: #8a5d3b; font-weight: 500;">Temperature:</span> 0.7</p>
        <p style="margin: 0.6rem 0; color: #563b25; font-size: 0.95rem;"><span style="color: #8a5d3b; font-weight: 500;">Max Tokens:</span> 1024</p>
        <p style="margin: 0.6rem 0; color: #563b25; font-size: 0.95rem;"><span style="color: #8a5d3b; font-weight: 500;">Top P:</span> 0.8</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Clear chat button
    if st.button("Clear Conversation"):
        st.session_state.messages = [
            {"role": "system", "content": "You are a helpful AI assistant. For EVERY response, you must answer in BOTH English and Korean. First provide the complete answer in English, then provide '한국어 답변:' followed by the complete Korean translation of your answer."}
        ]
        st.rerun()
    
    st.markdown("""
    <div style="text-align: center; margin-top: 3rem; padding: 10px;">
        <p style="color: #8a5d3b; font-size: 0.82rem; font-style: italic; letter-spacing: 0.3px;">
            Powered by HyperCLOVA X
        </p>
    </div>
    """, unsafe_allow_html=True)

# Chat container with elegant styling
chat_container = st.container()

with chat_container:
    # Display chat history with elegant styling
    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                # Enhanced styling for Korean text
                if message["role"] == "assistant" and "한국어 답변:" in message["content"]:
                    parts = message["content"].split("한국어 답변:", 1)
                    english_part = parts[0].strip()
                    korean_part = parts[1].strip() if len(parts) > 1 else ""
                    
                    st.markdown(english_part)
                    st.markdown(f"""
                    <div style="margin-top: 1.2rem; padding-top: 1rem; border-top: 1px solid rgba(159, 118, 75, 0.2);">
                        <span style="color: #8a5d3b; font-weight: 500; letter-spacing: 0.3px;">한국어 답변:</span><br>
                        <div style="margin-top: 0.5rem;">{korean_part}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(message["content"])

    # Chat input with placeholder
    if prompt := st.chat_input("Ask something in English or Korean..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Display assistant response
        with st.chat_message("assistant"):
            if not st.session_state.api_key:
                st.markdown("""
                <div style="color: #8a5d3b; padding: 0.5rem 0; font-style: italic;">
                    Please enter your HyperCLOVA API Key in the sidebar to continue.
                </div>
                """, unsafe_allow_html=True)
            else:
                message_placeholder = st.empty()
                
                # Elegant loading animation
                st.markdown("""
                <div style="display: flex; align-items: center; margin: 0.8rem 0; color: #8a5d3b; font-style: italic;">
                    <span>Crafting response</span>
                    <div class="loading-dots">
                        <style>
                            .loading-dots {
                                display: inline-flex;
                                align-items: center;
                                height: 1.5rem;
                            }
                            .loading-dots::after {
                                content: '...';
                                color: #9c7a54;
                                animation: dots 2s infinite;
                                font-weight: 400;
                                margin-left: 2px;
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
                        "maxTokens": 1024,
                        "temperature": 0.7,
                        "topP": 0.8,
                    }
                    
                    response = requests.post(endpoint, headers=headers, json=payload)
                    
                    if response.status_code == 200:
                        result = response.json()
                        assistant_response = result['result']['message']['content']
                        
                        # Format the response with elegant styling
                        if "한국어 답변:" in assistant_response:
                            parts = assistant_response.split("한국어 답변:", 1)
                            english_part = parts[0].strip()
                            korean_part = parts[1].strip() if len(parts) > 1 else ""
                            
                            formatted_response = f"{english_part}\n\n<div style='margin-top: 1.2rem; padding-top: 1rem; border-top: 1px solid rgba(159, 118, 75, 0.2);'><span style='color: #8a5d3b; font-weight: 500; letter-spacing: 0.3px;'>한국어 답변:</span><br><div style='margin-top: 0.5rem;'>{korean_part}</div></div>"
                            message_placeholder.markdown(formatted_response, unsafe_allow_html=True)
                        else:
                            message_placeholder.markdown(assistant_response)
                        
                        # Add assistant response to chat history
                        st.session_state.messages.append({"role": "assistant", "content": assistant_response})
                    else:
                        message_placeholder.markdown(f"""
                        <div style="color: #a85432; padding: 0.5rem 0;">
                            API Error {response.status_code}: {response.text}
                        </div>
                        """, unsafe_allow_html=True)
                except Exception as e:
                    message_placeholder.markdown(f"""
                    <div style="color: #a85432; padding: 0.5rem 0;">
                        Request failed: {str(e)}
                    </div>
                    """, unsafe_allow_html=True)

# Add a subtle footer
st.markdown("""
<div style="text-align: center; margin-top: 2rem; opacity: 0.7;">
    <div style="height: 1px; width: 80px; margin: 1rem auto; background: linear-gradient(90deg, transparent, rgba(159, 118, 75, 0.3), transparent);"></div>
    <p style="color: #8a5d3b; font-size: 0.8rem; font-style: italic; letter-spacing: 0.3px;">
        Elegant bilingual conversations
    </p>
</div>
""", unsafe_allow_html=True)
