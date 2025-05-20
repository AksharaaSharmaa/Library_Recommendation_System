def add_custom_css():
    import streamlit as st
    st.markdown("""
    <style>
        /* Main app background */
        .stApp {
            background: linear-gradient(135deg, #f9f2e7, #f0e4d3, #e6d7c3);
            color: #4a3728;
        }
        
        /* Darker sidebar background */
        [data-testid="stSidebar"] {
            background: linear-gradient(135deg, #e6d7c3, #d2b48c, #c9b18c) !important;
            border-right: 1px solid rgba(139, 90, 43, 0.2);
        }
        
        /* Make all text dark brown */
        p, div, span, label, h1, h2, h3, h4, h5, h6, li, a, .stMarkdown, .stText {
            color: #4a3728 !important;
        }
        
        /* Override any white text in elements */
        .stButton button {
            background: linear-gradient(90deg, #8b5a2b, #d2b48c);
            color: #fff;
            border: none;
            padding: 10px 15px;
            border-radius: 25px;
            transition: all 0.3s ease;
        }
        
        .stButton button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(139, 90, 43, 0.4);
        }
        
        .stTextInput input, .stNumberInput input, .stSelectbox, .stMultiselect {
            background-color: rgba(245, 231, 211, 0.7);
            color: #4a3728;
            border: 1px solid #a67c52;
            border-radius: 25px;
        }
        
        .stChat .message.user {
            background-color: #d2b48c;
            border-radius: 20px;
        }
        
        .stChat .message.assistant {
            background-color: #b39b7d;
            border-radius: 20px;
        }
        
        div[data-testid="stVerticalBlock"] {
            padding: 0 10px;
        }
        
        .book-title {
            color: #603913;
            font-size: 1.2rem;
            margin-bottom: 10px;
            font-weight: 600;
        }
        
        .book-info {
            margin-bottom: 8px;
            color: #4a3728;
            line-height: 1.5;
        }
        
        .like-button {
            background: linear-gradient(90deg, #8b5a2b, #a67c52);
            color: #fff;
            border: none;
            padding: 5px 10px;
            border-radius: 20px;
            cursor: pointer;
            font-size: 0.8rem;
            transition: all 0.3s ease;
        }
        
        .like-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 3px 10px rgba(139, 90, 43, 0.4);
        }
        
        .chat-container {
            display: flex;
            flex-direction: column;
            gap: 20px;
            margin-bottom: 30px;
            padding: 15px;
        }
        
        .chat-message {
            padding: 15px 20px;
            border-radius: 20px;
            max-width: 85%;
            box-shadow: 0 3px 10px rgba(74, 55, 40, 0.2);
            line-height: 1.6;
        }
        
        .assistant-message {
            align-self: flex-start;
            background: linear-gradient(to right, #b39b7d, #9e8974);
            border-left: 3px solid #8b5a2b;
            margin-left: 10px;
        }
        
        .user-message {
            align-self: flex-end;
            background: linear-gradient(to right, #c9b18c, #a67c52);
            border-right: 3px solid #603913;
            margin-right: 10px;
        }
        
        .korean-text {
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid rgba(139, 90, 43, 0.3);
        }
        
        .korean-label {
            color: #603913;
            font-weight: 600;
            display: inline-block;
            margin-bottom: 5px;
        }
        
        .message-timestamp {
            font-size: 0.7rem;
            color: #7d5a41;
            margin-top: 8px;
            text-align: right;
        }
        
        .message-avatar {
            width: 28px;
            height: 28px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 5px;
            font-size: 0.8rem;
            font-weight: bold;
            color: white !important; /* Make avatar text white */
        }
        
        .user-avatar {
            background: linear-gradient(135deg, #8b5a2b, #a67c52);
            color: white !important; /* Make avatar text white */
            align-self: flex-end;
            margin-right: 10px;
        }
        
        .assistant-avatar {
            background: linear-gradient(135deg, #603913, #8b5a2b);
            color: white !important; /* Make avatar text white */
            align-self: flex-start;
            margin-left: 10px;
        }
        
        .message-with-avatar {
            display: flex;
            flex-direction: column;
        }
        
        /* Remove container backgrounds */
        .stHeader, div[data-testid="stDecoration"], div[data-testid="stToolbar"] {
            background: none !important;
            border: none !important;
            box-shadow: none !important;
        }
        
        /* Keep the answer container but make it darker */
        .stTextArea textarea {
            background-color: #b39b7d !important;
            color: #4a3728 !important;
            border: 1px solid #8b5a2b !important;
            border-radius: 15px !important;
        }
        
        /* Remove rectangular containers by making them transparent */
        [data-testid="block-container"], [data-testid="stExpander"] {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }
        
        /* Ensure sidebar text is dark brown */
        [data-testid="stSidebar"] p, 
        [data-testid="stSidebar"] div, 
        [data-testid="stSidebar"] span, 
        [data-testid="stSidebar"] label {
            color: #4a3728 !important;
        }
        
        /* Override any white text in inputs or special elements */
        input, textarea, select, .stSelectbox, .stMultiselect {
            color: #4a3728 !important;
        }
        
        /* Menu items and dropdowns */
        .stSelectbox ul li, .stMultiselect ul li {
            color: #4a3728 !important;
        }
        
        /* Gradient divider */
        .gradient-divider {
            height: 3px;
            background: linear-gradient(90deg, transparent, #8b5a2b, #a67c52, transparent);
            margin: 25px 0;
            border-radius: 3px;
        }
        
        /* Footer text */
        footer {
            color: #4a3728 !important;
        }
        
        /* Code blocks */
        code, pre {
            color: #603913 !important;
        }
    </style>
    """, unsafe_allow_html=True)

def gradient_title(title_text):
    import streamlit as st
    st.markdown(f"""
    <h1 style="text-align: center; 
              background: linear-gradient(90deg, #8b5a2b, #a67c52, #b28b5c);
              -webkit-background-clip: text;
              -webkit-text-fill-color: transparent;
              font-weight: 800;
              font-size: 2.5rem;
              margin-bottom: 20px;
              text-shadow: 1px 1px 2px rgba(139, 90, 43, 0.1);">
        {title_text}
    </h1>
    """, unsafe_allow_html=True)
