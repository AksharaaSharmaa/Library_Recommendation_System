import streamlit as st
import hashlib
import pymongo
import os
import importlib.util
import sys
import base64
import os.path

st.set_page_config(
    page_title="Book Wanderer: Library Recommendation System",
    page_icon="📚",
    layout="wide",
)

def load_page_based_on_role():
    """Load different pages based on user role"""
    if st.session_state.is_admin:
        # Check if admin_dashboard.py exists
        if os.path.exists("admin_dashboard.py"):
            load_app("admin_dashboard.py")
        else:
            st.error("Admin dashboard not found. Please make sure admin_dashboard.py exists in the app directory.")
            st.info("Contact the application administrator for assistance.")
    else:
        # Check if ChatBot.py exists
        if os.path.exists("ChatBot.py"):
            load_app("ChatBot.py")
        else:
            st.error("ChatBot interface not found. Please make sure ChatBot.py exists in the app directory.")
            st.info("Contact the application administrator for assistance.")


# Function to create a hashed password
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# Function to verify the hashed password
def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return True
    return False

# Initialize connection to MongoDB (with embedded secrets for testing)
def init_connection():
    try:
        # For local development
        if os.environ.get('LOCAL_DEV') == 'true':
            connection_string = "mongodb://localhost:27017/"
        else:
            # EMBEDDED SECRETS FOR TESTING ONLY - REPLACE WITH YOUR ACTUAL MONGODB ATLAS CONNECTION STRING
            # In production, use st.secrets["mongodb"]["uri"] instead
            mongodb_uri = "mongodb+srv://sonuakshara:ba8bGgDR3LyllGuQ@library-login-credentia.xcioxmw.mongodb.net/?retryWrites=true&w=majority&appName=Library-Login-Credentials"
            
            # Create a fake secrets dict for testing
            if "mongodb" not in st.secrets:
                st.secrets._secrets["mongodb"] = {"uri": mongodb_uri}
            
            connection_string = st.secrets["mongodb"]["uri"]
        
        # Connect to MongoDB
        client = pymongo.MongoClient(connection_string)
        # Ping the server to confirm connection
        client.admin.command('ping')
        st.session_state.db_client = client
        return client
    except Exception as e:
        st.error(f"Error connecting to MongoDB: {e}")
        return None

# Initialize database and collections
def init_db():
    if 'db_client' not in st.session_state:
        client = init_connection()
        if client is None:
            return None
    else:
        client = st.session_state.db_client
    
    # Get or create the database
    db = client["Login_Credentials"]
    
    # Get or create the users collection
    users_collection = db["users"]
    
    # Create a unique index on username to prevent duplicates
    users_collection.create_index([("username", pymongo.ASCENDING)], unique=True)
    
    # Check if admin user exists, if not create it
    if users_collection.find_one({"username": "admin"}) is None:
        users_collection.insert_one({
            "username": "admin",
            "password": make_hashes("admin123"),
            "is_admin": True
        })
    
    return users_collection

# Add a new user
def add_user(users_collection, username, password):
    try:
        users_collection.insert_one({
            "username": username,
            "password": make_hashes(password),
            "is_admin": False
        })
        return True
    except pymongo.errors.DuplicateKeyError:
        return False  # User already exists

# Login function
def login_user(users_collection, username, password):
    user = users_collection.find_one({"username": username})
    if user:
        return check_hashes(password, user["password"]), user.get("is_admin", False)
    return False, False

# Get user information
def get_user_info(users_collection, username):
    return users_collection.find_one({"username": username})

# Function to load and run another Python file
def load_app(filepath):
    try:
        # Get the absolute path
        abs_path = os.path.abspath(filepath)
        
        # Get the module name from the file path
        module_name = os.path.splitext(os.path.basename(filepath))[0]
        
        # Import the module dynamically
        spec = importlib.util.spec_from_file_location(module_name, abs_path)
        module = importlib.util.module_from_spec(spec)
        
        # Add the module to sys.modules
        sys.modules[module_name] = module
        
        # Execute the module
        spec.loader.exec_module(module)
        
        # Call the main function if it exists
        if hasattr(module, 'main'):
            module.main()
    except Exception as e:
        st.error(f"Failed to load {filepath}: {e}")
        st.info("Make sure all required Python files are present in your Streamlit app directory.")

# Function to set custom CSS
def set_custom_theme():
    # Define refined color palette with stronger contrast
    primary_dark = "#2A1F1A"       # Darker brown for better readability
    primary_medium = "#7D4F23"     # Rich medium brown
    primary_light = "#A67C4D"      # Light brown
    accent_light = "#E8DCC7"       # Warm light beige
    accent_dark = "#C9B99B"        # Darker accent for contrast
    text_dark = "#1F160F"          # Nearly black text for better readability
    text_light = "#FBF8F5"         # Bright white for text on dark bg
    background = "#F9F6F2"         # Soft off-white background
    card_bg = "#FFFFFF"            # White for cards
    error = "#A33C29"              # Darkened reddish brown for errors
    success = "#4B7920"            # Darkened olive green for success
    
    # Custom CSS with enhanced aesthetics
    st.markdown(f"""
    <style>
        /* Main styles */
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600;700&family=Lato:wght@300;400;500;700&display=swap');
        
        * {{
            font-family: 'Lato', sans-serif;
            -webkit-font-smoothing: antialiased;
        }}
        
        h1, h2, h3, h4, h5, h6 {{
            font-family: 'Cormorant Garamond', serif !important;
            letter-spacing: 0.025em !important;
        }}
        
        /* Body and background */
        .stApp {{
            background: linear-gradient(145deg, {background} 0%, #FFFFFF 100%);
            padding: 0;
            max-width: 100%;
        }}
        
        /* Hide Streamlit elements */
        #MainMenu, footer, header {{
            visibility: hidden;
        }}
        
        /* Hide full screen button */
        button[title="View fullscreen"] {{
            display: none;
        }}
        
        /* Horizontal band above header */
        .horizontal-band {{
            background: linear-gradient(145deg, {primary_dark} 0%, {primary_medium} 100%);
            height: 12px;
            width: 100%;
            position: relative;
            z-index: 999;
        }}
        
        /* Header */
        .app-header {{
            background: linear-gradient(145deg, {primary_dark} 0%, {primary_medium} 100%);
            padding: 2.5rem 1rem;
            border-radius: 0 0 40px 40px;
            box-shadow: 0 12px 30px rgba(42, 31, 26, 0.15);
            text-align: center;
            margin-bottom: 2rem;
            position: relative;
            overflow: hidden;
        }}
        
        /* Book icon decorations for header */
        .app-header::before, .app-header::after {{
            content: "📚";
            position: absolute;
            font-size: 4rem;
            opacity: 0.1;
            transform: rotate(-10deg);
        }}
        
        .app-header::before {{
            top: 10px;
            left: 15px;
        }}
        
        .app-header::after {{
            bottom: -10px;
            right: 20px;
            transform: rotate(15deg);
        }}
        
        .app-header h1 {{
            color: {text_light} !important;
            font-size: 3.5rem !important;
            font-weight: 700 !important;
            margin-bottom: 0.25rem !important;
            text-shadow: 0 3px 6px rgba(0, 0, 0, 0.25);
            letter-spacing: 0.05em;
        }}
        
        .app-header p {{
            color: {accent_light} !important;
            font-size: 1.25rem !important;
            font-weight: 300 !important;
            letter-spacing: 0.04em;
            margin-bottom: 0.5rem !important;
            text-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
        }}
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 0 !important;
            background-color: rgba(255, 255, 255, 0.5) !important;
            padding: 0.25rem !important;
            border-radius: 15px !important;
            display: flex !important;
            margin-bottom: 1.8rem !important;
            border: 1px solid {accent_light} !important;
            box-shadow: 0 4px 12px rgba(42, 31, 26, 0.05);
        }}
        
        .stTabs [data-baseweb="tab"] {{
            height: 3.8rem !important;
            white-space: pre-wrap !important;
            background-color: transparent !important;
            border-radius: 12px !important;
            color: {primary_medium} !important;
            font-weight: 500 !important;
            font-size: 1.25rem !important;
            flex: 1 !important;
            text-align: center !important;
            font-family: 'Cormorant Garamond', serif !important;
            letter-spacing: 0.04em;
            transition: all 0.3s ease !important;
        }}
        
        .stTabs [aria-selected="true"] {{
            background: linear-gradient(145deg, {primary_medium} 0%, {primary_dark} 100%) !important;
            color: {text_light} !important;
            box-shadow: 0 4px 15px rgba(42, 31, 26, 0.2) !important;
            font-weight: 600 !important;
            transform: translateY(-2px);
        }}
        
        /* Form inputs */
        .stTextInput > div > div > input {{
            border: 1px solid {accent_dark} !important;
            border-radius: 12px !important;
            padding: 1.2rem 1rem !important;
            background-color: rgba(255, 255, 255, 0.8) !important;
            font-size: 1rem !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 4px 12px rgba(42, 31, 26, 0.05) !important;
            color: {text_dark} !important;
            margin-bottom: 0.5rem;
        }}
        
        .stTextInput > div > div > input:focus {{
            background-color: rgba(255, 255, 255, 1) !important;
            box-shadow: 0 0 0 2px {primary_light} !important;
            border-color: {primary_light} !important;
            transform: translateY(-2px);
        }}
        
        /* Form labels */
        .stTextInput > label {{
            font-weight: 500 !important;
            font-size: 1.05rem !important;
            color: {primary_dark} !important;
            margin-bottom: 0.5rem !important;
        }}
        
        /* Buttons */
        .stButton > button {{
            background: linear-gradient(145deg, {accent_light} 0%, {accent_dark} 100%) !important;
            color: {primary_dark} !important;
            border: 2px solid {primary_dark} !important;
            padding: 0.9rem 2.5rem !important;
            font-size: 1.15rem !important;
            font-weight: 600 !important;
            border-radius: 14px !important;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
            box-shadow: 0 6px 16px rgba(42, 31, 26, 0.2) !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            min-width: 180px !important;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            position: relative;
            overflow: hidden;
        }}
        
        .stButton > button::after {{
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, 
                          rgba(255,255,255,0) 0%, 
                          rgba(255,255,255,0.1) 50%, 
                          rgba(255,255,255,0) 100%);
            transform: translateX(-100%);
            transition: transform 0.6s ease;
        }}
        
        .stButton > button:hover {{
            box-shadow: 0 10px 25px rgba(42, 31, 26, 0.3) !important;
            transform: translateY(-3px);
            background: linear-gradient(145deg, {accent_dark} 0%, {accent_light} 100%) !important;
        }}
        
        .stButton > button:hover::after {{
            transform: translateX(100%);
        }}
        
        .stButton > button:active {{
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(42, 31, 26, 0.2) !important;
        }}
        
        /* Center button */
        .button-container {{
            display: flex;
            justify-content: center;
            margin-top: 2rem;
        }}
        
        /* Headings */
        h1, h2, h3, h4, h5, h6 {{
            color: {primary_dark} !important;
            font-weight: 600 !important;
        }}
        
        .section-heading {{
            text-align: center;
            font-size: 2.4rem !important;
            margin-bottom: 1.5rem !important;
            font-weight: 700 !important;
            color: {primary_dark} !important;
            letter-spacing: 0.05em;
            background: linear-gradient(145deg, {primary_medium} 0%, {primary_dark} 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        
        /* Success/Error messages */
        .stSuccess {{
            background-color: {success} !important;
            color: white !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 1rem 1.2rem !important;
            font-weight: 500 !important;
            box-shadow: 0 6px 16px rgba(75, 121, 32, 0.25) !important;
        }}
        
        .stError {{
            background-color: {error} !important;
            color: white !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 1rem 1.2rem !important;
            font-weight: 500 !important;
            box-shadow: 0 6px 16px rgba(163, 60, 41, 0.25) !important;
        }}
        
        /* Divider */
        hr {{
            margin: 1.5rem 0;
            border-color: {accent_light};
            border-width: 1px;
        }}
        
        /* User info panel in sidebar */
        .sidebar-user-panel {{
            background: linear-gradient(145deg, rgba(255, 255, 255, 0.8) 0%, rgba(232, 220, 199, 0.6) 100%);
            padding: 1.2rem 1.4rem;
            border-radius: 16px;
            margin-bottom: 1.5rem;
            border: 1px solid rgba(166, 124, 77, 0.2);
            box-shadow: 0 8px 20px rgba(42, 31, 26, 0.08);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
        }}
        
        .sidebar-user-info {{
            display: flex;
            align-items: center;
            margin-bottom: 0.8rem;
        }}
        
        .user-avatar {{
            background: linear-gradient(145deg, {primary_medium} 0%, {primary_dark} 100%);
            color: {text_light};
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            margin-right: 12px;
            font-family: 'Cormorant Garamond', serif !important;
            font-size: 1.5rem;
            box-shadow: 0 4px 10px rgba(42, 31, 26, 0.2);
            border: 2px solid rgba(255, 255, 255, 0.8);
        }}
        
        /* Admin badge styling */
        .admin-badge {{
            display: inline-block;
            background: linear-gradient(145deg, {primary_medium} 0%, {primary_dark} 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 600;
            font-size: 0.85rem;
            margin-top: 0.4rem;
            margin-bottom: 0.5rem;
            padding: 3px 10px;
            border-radius: 8px;
            border: 1px solid rgba(125, 79, 35, 0.3);
            background-color: rgba(232, 220, 199, 0.3);
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }}
        
        /* Sidebar logout button */
        .sidebar-logout-button {
            width: 100%;
            margin-top: 0.8rem;
        }
        
        .sidebar-logout-button button {
            width: 100% !important;
            min-width: auto !important;
            padding: 0.7rem 1rem !important;
            font-size: 0.95rem !important;
            border-radius: 20px !important;
            
            /* Styling to match the image */
            background-color: #f5f1e8 !important;
            color: #6b5b47 !important;
            border: 2px solid #8b7355 !important;
            font-weight: 500 !important;
            letter-spacing: 0.02em !important;
            
            /* Smooth transitions for hover effects */
            transition: all 0.3s ease !important;
            cursor: pointer !important;
            
            /* Text styling */
            text-align: center !important;
            font-family: inherit !important;
        }
        
        /* Hover effects */
        .sidebar-logout-button button:hover {
            background-color: #ede6d7 !important;
            border-color: #7a6649 !important;
            color: #5a4d3a !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 12px rgba(139, 115, 85, 0.2) !important;
        }
        
        /* Active/pressed state */
        .sidebar-logout-button button:active {
            transform: translateY(0) !important;
            box-shadow: 0 2px 6px rgba(139, 115, 85, 0.15) !important;
            background-color: #e8dcc8 !important;
        }
        
        /* Focus state for accessibility */
        .sidebar-logout-button button:focus {
            outline: none !important;
            box-shadow: 0 0 0 3px rgba(139, 115, 85, 0.3) !important;
        }
        
        /* Additional styling for better visual consistency */
        .sidebar-logout-button button:disabled {
            opacity: 0.6 !important;
            cursor: not-allowed !important;
            transform: none !important;
        }
        
        .sidebar-logout-button button:disabled:hover {
            background-color: #f5f1e8 !important;
            border-color: #8b7355 !important;
            transform: none !important;
            box-shadow: none !important;
        }
        
        /* Database connection status */
        .db-status {{
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 500;
            display: inline-flex;
            align-items: center;
            margin-top: 10px;
            transition: all 0.3s ease;
        }}
        
        .db-status.connected {{
            background-color: rgba(75, 121, 32, 0.15);
            color: {success};
            border: 1px solid rgba(75, 121, 32, 0.3);
        }}
        
        .db-status.disconnected {{
            background-color: rgba(163, 60, 41, 0.15);
            color: {error};
            border: 1px solid rgba(163, 60, 41, 0.3);
        }}
        
        .db-status-dot {{
            width: 10px;
            height: 10px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 8px;
            position: relative;
        }}
        
        .db-status.connected .db-status-dot {{
            background-color: {success};
            box-shadow: 0 0 0 rgba(75, 121, 32, 0.4);
            animation: pulse 2s infinite;
        }}
        
        .db-status.disconnected .db-status-dot {{
            background-color: {error};
        }}
        
        @keyframes pulse {{
            0% {{
                box-shadow: 0 0 0 0 rgba(75, 121, 32, 0.4);
            }}
            70% {{
                box-shadow: 0 0 0 10px rgba(75, 121, 32, 0);
            }}
            100% {{
                box-shadow: 0 0 0 0 rgba(75, 121, 32, 0);
            }}
        }}
        
        /* Sidebar general styling */
        .css-1d391kg, .css-163ttbj, section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, rgba(249, 246, 242, 0.95) 0%, rgba(255, 255, 255, 0.95) 100%);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
        }}
        
        /* Add divider after sidebar user panel */
        .sidebar-divider {{
            margin: 1.2rem 0;
            border-color: {accent_light};
            opacity: 0.5;
            height: 1px;
        }}
        
        /* Auth footer with quote */
        .auth-footer {{
            text-align: center;
            font-style: italic;
            font-family: 'Cormorant Garamond', serif !important;
            color: {primary_medium};
            margin-top: 2.5rem;
            font-size: 1.2rem;
            padding: 0.8rem;
            opacity: 0.8;
        }}
        
        /* Media queries for responsiveness */
        @media (max-width: 768px) {{
            .app-header h1 {{
                font-size: 2.8rem !important;
            }}
            
            .app-header p {{
                font-size: 1.1rem !important;
            }}
            
            .section-heading {{
                font-size: 2rem !important;
            }}
            
            .stButton > button {{
                min-width: 150px !important;
                padding: 0.8rem 2rem !important;
            }}
        }}
    </style>
    """, unsafe_allow_html=True)

# Function to display horizontal band and header
def display_header():
    st.markdown(f"""
    <div class="horizontal-band"></div>
    <div class="app-header">
        <h1>Book Wanderer</h1>
        <p>Discover your next favorite read in English and Korean</p>
    </div>
    """, unsafe_allow_html=True)

# Function to display MongoDB connection status
def display_db_status(connected=True):
    if connected:
        st.markdown("""
        <div class="db-status connected">
            <span class="db-status-dot"></span>
            Database connected
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="db-status disconnected">
            <span class="db-status-dot"></span>
            Database disconnected
        </div>
        """, unsafe_allow_html=True)

# Function to display user info in sidebar
def display_sidebar_user_panel():
    with st.sidebar:
        # Get first letter of username for avatar
        first_letter = st.session_state.username[0].upper()
        
        # Create container for user panel
        st.markdown(f"""
        <div class="sidebar-user-panel">
            <div class="sidebar-user-info">
                <div class="user-avatar">{first_letter}</div>
                <span style="font-weight: 500;">Welcome, <strong>{st.session_state.username}</strong></span>
            </div>
            {f'<div class="admin-badge">Admin Access</div>' if st.session_state.is_admin else ''}
        </div>
        """, unsafe_allow_html=True)
        
        # Add logout button with full width in sidebar
        st.markdown('<div class="sidebar-logout-button">', unsafe_allow_html=True)
        if st.button("Logout", key="sidebar_logout_btn", help="Sign out of your account"):
            st.session_state.logged_in = False
            st.session_state.username = ''
            st.session_state.is_admin = False
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Add divider
        st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)

# App layout and functionality
def main():
   
    # Initialize secrets dict if it doesn't exist (for testing only)
    if not hasattr(st, "secrets"):
        st.secrets = type('obj', (object,), {
            '_secrets': {},
            '__getitem__': lambda self, key: self._secrets.get(key, {}),
        })
    
    # Apply custom theme
    set_custom_theme()
    
    # Initialize session state for login status if it doesn't exist
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    if 'username' not in st.session_state:
        st.session_state.username = ''
        
    if 'is_admin' not in st.session_state:
        st.session_state.is_admin = False

    if st.session_state.logged_in:
        display_sidebar_user_panel()
        # Load appropriate page based on user role and hide the login interface
        load_page_based_on_role()
        return
        
    
    # Initialize the database connection and get users collection
    users_collection = init_db()
    
    # Check if database connection was successful
    db_connected = users_collection is not None
    
    # If user is logged in, display sidebar user panel
    if st.session_state.logged_in:
        display_sidebar_user_panel()
    
    # If user is not logged in, show login/signup interface
    if not st.session_state.logged_in:
        # Display header
        display_header()
        
        # Show database connection status (only in development or for admins)
        if os.environ.get('SHOW_DB_STATUS') == 'true' or not db_connected:
            display_db_status(db_connected)
        
        if not db_connected:
            st.error("Failed to connect to the database. Please check your MongoDB connection.")
            st.info("""
            MongoDB connection failed. If testing locally:
            1. Make sure MongoDB is running locally
            2. Set the LOCAL_DEV environment variable to 'true'
            
            For MongoDB Atlas:
            - Check your connection string in the embedded secrets (replace placeholder credentials)
            """)
            return
        
        # Create tabs for Login and SignUp (NO CONTAINER WRAPPING)
        tab1, tab2 = st.tabs(["📝 LOGIN", "✨ SIGN UP"])
        
        with tab1:
            st.markdown('<h2 class="section-heading">Welcome Back</h2>', unsafe_allow_html=True)
            
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type='password', key="login_password")
            
            # Center the login button
            st.markdown('<div class="button-container">', unsafe_allow_html=True)
            login_button = st.button("LOGIN", key="login_btn")
            st.markdown('</div>', unsafe_allow_html=True)
            
            if login_button:
                if not username or not password:
                    st.error("Please fill in all fields")
                else:
                    login_successful, is_admin = login_user(users_collection, username, password)
                    if login_successful:
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.session_state.is_admin = is_admin
                        st.success(f"Logged in successfully")
                        st.rerun()
                    else:
                        st.error("Incorrect username or password")
        
        with tab2:
            st.markdown('<h2 class="section-heading">Join Us</h2>', unsafe_allow_html=True)
            
            new_username = st.text_input("Choose Username", key="signup_username")
            new_password = st.text_input("Create Password", type='password', key="signup_password")
            confirm_password = st.text_input("Confirm Password", type='password', key="confirm_password")
            
            # Center the signup button
            st.markdown('<div class="button-container">', unsafe_allow_html=True)
            signup_button = st.button("CREATE ACCOUNT", key="signup_btn")
            st.markdown('</div>', unsafe_allow_html=True)
            
            if signup_button:
                if new_password != confirm_password:
                    st.error("Passwords do not match")
                elif not new_username or not new_password:
                    st.error("Please fill in all fields")
                else:
                    if add_user(users_collection, new_username, new_password):
                        st.success("Account created successfully!")
                        st.info("You can now log in with your new account")
                    else:
                        st.error("Username already exists")
        
        # Footer with quote about books
        st.markdown('<div class="auth-footer">"A reader lives a thousand lives before he dies." — George R.R. Martin</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
