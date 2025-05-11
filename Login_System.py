import streamlit as st
import hashlib
import pymongo
import os
import importlib.util
import sys
import base64

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
    # Define warm earthy color theme
    primary_dark = "#3D3026"      # Darker brown
    primary_medium = "#8B5B29"    # Medium brown
    primary_light = "#A67C4D"     # Light brown
    accent_light = "#E3D4B9"      # Very light beige
    accent_medium = "#D9CBA0"     # Light beige
    text_dark = "#3D3026"         # Dark brown for text
    text_light = "#F7F4EF"        # Light beige for text on dark bg
    background = "#F9F6F2"        # Soft off-white background
    card_bg = "#FFFFFF"           # White for cards
    error = "#A64D35"             # Reddish brown for errors
    success = "#5D8B29"           # Olive green for success
    
    # Custom CSS with enhanced aesthetics
    st.markdown(f"""
    <style>
        /* Main styles */
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;500;600;700&family=Lato:wght@300;400;700&display=swap');
        
        * {{
            font-family: 'Lato', sans-serif;
        }}
        
        h1, h2, h3, h4, h5, h6 {{
            font-family: 'Cormorant Garamond', serif !important;
        }}
        
        /* Body and background */
        .stApp {{
            background: linear-gradient(135deg, {background} 0%, #FFFFFF 100%);
            padding: 0;
            max-width: 100%;
        }}
        
        /* Hide full screen button */
        button[title="View fullscreen"] {{
            display: none;
        }}
        
        /* Header */
        .app-header {{
            background: linear-gradient(135deg, {primary_dark} 0%, {primary_medium} 100%);
            padding: 2rem 1rem;
            border-radius: 0 0 35px 35px;
            box-shadow: 0 10px 25px rgba(75, 61, 45, 0.15);
            text-align: center;
            margin-bottom: 0; /* Removed space after header */
        }}
        
        .app-header h1 {{
            color: {text_light} !important;
            font-size: 3.2rem !important;
            font-weight: 700 !important;
            margin-bottom: 0.25rem !important;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
            letter-spacing: 1.8px;
        }}
        
        .app-header p {{
            color: {accent_light} !important;
            font-size: 1.15rem !important;
            font-weight: 300 !important;
            letter-spacing: 0.8px;
            margin-bottom: 0.5rem !important;
        }}
        
        /* Login Form Section */
        .login-section {{
            padding: 0.5rem 0;
            max-width: 450px;
            margin: 0 auto;
            position: relative;
        }}
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 0 !important;
            background-color: transparent !important;
            padding: 0 !important;
            border-radius: 15px !important;
            display: flex !important;
            margin-bottom: 1.5rem !important;
            border-bottom: 1px solid {accent_light} !important;
        }}
        
        .stTabs [data-baseweb="tab"] {{
            height: 3.5rem !important;
            white-space: pre-wrap !important;
            background-color: transparent !important;
            border-radius: 15px 15px 0 0 !important;
            color: {primary_medium} !important;
            font-weight: 500 !important;
            font-size: 1.25rem !important;
            flex: 1 !important;
            text-align: center !important;
            font-family: 'Cormorant Garamond', serif !important;
            letter-spacing: 0.5px;
        }}
        
        .stTabs [aria-selected="true"] {{
            background: linear-gradient(135deg, {primary_medium} 0%, {primary_dark} 100%) !important;
            color: {text_light} !important;
            box-shadow: 0 4px 15px rgba(75, 61, 45, 0.15) !important;
            font-weight: 600 !important;
        }}
        
        /* Form inputs */
        .stTextInput > div > div > input {{
            border: 1px solid {accent_light} !important;
            border-radius: 12px !important;
            padding: 1rem !important;
            background-color: rgba(255, 255, 255, 0.7) !important;
            font-size: 1rem !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 2px 8px rgba(75, 61, 45, 0.05) !important;
            color: {primary_dark} !important;
        }}
        
        .stTextInput > div > div > input:focus {{
            background-color: rgba(255, 255, 255, 0.95) !important;
            box-shadow: 0 0 0 2px {primary_light} !important;
            border-color: {primary_light} !important;
        }}
        
        /* Form labels */
        .stTextInput > label {{
            font-weight: 500 !important;
            font-size: 1rem !important;
            color: {primary_dark} !important;
            margin-bottom: 0.5rem !important;
        }}
        
        /* Buttons */
        .stButton > button {{
            background: linear-gradient(135deg, {primary_medium} 0%, {primary_dark} 100%) !important;
            color: {text_light} !important;
            border: none !important;
            padding: 0.8rem 2.2rem !important;
            font-size: 1.05rem !important;
            font-weight: 600 !important;
            border-radius: 12px !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 4px 12px rgba(75, 61, 45, 0.2) !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            min-width: 160px !important;
            letter-spacing: 1.2px;
        }}
        
        .stButton > button:hover {{
            box-shadow: 0 6px 20px rgba(75, 61, 45, 0.35) !important;
            transform: translateY(-2px);
        }}
        
        .stButton > button:active {{
            transform: translateY(0);
            box-shadow: 0 2px 8px rgba(75, 61, 45, 0.2) !important;
        }}
        
        /* Center button */
        .button-container {{
            display: flex;
            justify-content: center;
            margin-top: 1.8rem;
        }}
        
        /* Headings */
        h1, h2, h3, h4, h5, h6 {{
            color: {primary_dark} !important;
            font-weight: 600 !important;
        }}
        
        .section-heading {{
            text-align: center;
            font-size: 2.25rem !important;
            margin-bottom: 1.2rem !important;
            font-weight: 700 !important;
            color: {primary_medium} !important;
            letter-spacing: 1px;
        }}
        
        /* Success/Error messages */
        .stSuccess {{
            background-color: {success} !important;
            color: white !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 0.8rem 1rem !important;
            font-weight: 500 !important;
            box-shadow: 0 4px 12px rgba(93, 139, 41, 0.2) !important;
        }}
        
        .stError {{
            background-color: {error} !important;
            color: white !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 0.8rem 1rem !important;
            font-weight: 500 !important;
            box-shadow: 0 4px 12px rgba(166, 77, 53, 0.2) !important;
        }}
        
        /* Divider */
        hr {{
            margin: 2rem 0;
            border-color: {accent_light};
            border-width: 1px;
        }}
        
        /* User info panel */
        .user-panel {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: linear-gradient(135deg, rgba(75, 61, 45, 0.05) 0%, rgba(166, 124, 77, 0.05) 100%);
            padding: 0.9rem 1.5rem;
            border-radius: 15px;
            margin-bottom: 1.5rem;
            border: 1px solid rgba(166, 124, 77, 0.1);
            box-shadow: 0 4px 15px rgba(75, 61, 45, 0.08);
        }}
        
        .user-panel-info {{
            display: flex;
            align-items: center;
        }}
        
        .user-avatar {{
            background: linear-gradient(135deg, {primary_medium} 0%, {primary_dark} 100%);
            color: {text_light};
            width: 42px;
            height: 42px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            margin-right: 12px;
            font-family: 'Cormorant Garamond', serif !important;
            font-size: 1.3rem;
            box-shadow: 0 3px 8px rgba(75, 61, 45, 0.2);
        }}
        
        /* Logout button */
        .logout-button {{
            background: transparent !important;
            color: {primary_dark} !important;
            border: 1px solid {accent_medium} !important;
            padding: 0.5rem 1rem !important;
            border-radius: 10px !important;
            font-size: 0.875rem !important;
            font-weight: 500 !important;
            transition: all 0.2s ease !important;
            box-shadow: none !important;
        }}
        
        .logout-button:hover {{
            background-color: rgba(227, 212, 185, 0.2) !important;
            border-color: {primary_light} !important;
        }}
        
        /* Decorative elements */
        .decorative-icon {{
            margin: 0 auto;
            display: block;
            text-align: center;
            font-size: 2.2rem;
            color: {primary_light};
            margin-bottom: 0.5rem;
            margin-top: -0.5rem; /* Move icon up to reduce space */
        }}
        
        /* Footer for login page */
        .auth-footer {{
            text-align: center;
            margin-top: 2rem;
            color: {primary_medium};
            font-size: 0.9rem;
            opacity: 0.8;
            max-width: 500px;
            margin-left: auto;
            margin-right: auto;
        }}
        
        /* Main content area */
        .main-content {{
            display: flex;
            justify-content: center;
            align-items: flex-start; /* Changed to flex-start to reduce space */
            flex-direction: column;
            width: 100%;
            padding: 0 20px;
        }}
        
        /* Admin badge styling */
        .admin-badge {{
            background: linear-gradient(135deg, #8B5B29 0%, #3D3026 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 600;
            margin-right: 15px;
            padding: 3px 8px;
            border-radius: 8px;
            border: 1px solid rgba(139, 91, 41, 0.3);
            background-color: rgba(227, 212, 185, 0.1);
        }}
        
        /* Database connection status */
        .db-status {{
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 500;
            display: inline-flex;
            align-items: center;
            margin-top: 5px;
        }}
        
        .db-status.connected {{
            background-color: rgba(93, 139, 41, 0.15);
            color: {success};
            border: 1px solid rgba(93, 139, 41, 0.3);
        }}
        
        .db-status.disconnected {{
            background-color: rgba(166, 77, 53, 0.15);
            color: {error};
            border: 1px solid rgba(166, 77, 53, 0.3);
        }}
        
        .db-status-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 6px;
        }}
        
        .db-status.connected .db-status-dot {{
            background-color: {success};
        }}
        
        .db-status.disconnected .db-status-dot {{
            background-color: {error};
        }}
    </style>
    """, unsafe_allow_html=True)


# Function to display header
def display_header():
    st.markdown(f"""
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

# App layout and functionality
def main():
    # Set page config
    st.set_page_config(
        page_title="Book Recommendation Service",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
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
        
    # Initialize the database connection and get users collection
    users_collection = init_db()
    
    # Check if database connection was successful
    db_connected = users_collection is not None
    
    # If user is not logged in, show login/signup interface
    if not st.session_state.logged_in:
        # Display header
        display_header()
        
        # Create a centered container for the login area without much spacing
        st.markdown('<div class="main-content">', unsafe_allow_html=True)
        
        # Decorative book icon (moved up to reduce space)
        st.markdown('<div class="decorative-icon">📚</div>', unsafe_allow_html=True)
        
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
        
        # Create a login section
        st.markdown('<div class="login-section">', unsafe_allow_html=True)
        
        # Create tabs for Login and SignUp
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
        
        st.markdown('</div>', unsafe_allow_html=True)  # Close login-section
        
        # Footer with quote about books
        st.markdown('<div class="auth-footer">"A reader lives a thousand lives before he dies." — George R.R. Martin</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)  # Close the main-content div
    
    # If logged in, load the main application (without displaying header)
    else:
        if not db_connected:
            st.error("Database connection lost. Please refresh the page.")
            if st.button("Logout", key="error_logout_btn"):
                st.session_state.logged_in = False
                st.session_state.username = ''
                st.session_state.is_admin = False
                st.rerun()
            return
            
        # Create a container for the welcome panel
        col1, col2, col3 = st.columns([1, 3, 1])
        
        with col2:
            # Display user info with avatar and logout button
            first_letter = st.session_state.username[0].upper()
            st.markdown(f"""
            <div class="user-panel">
                <div class="user-panel-info">
                    <div class="user-avatar">{first_letter}</div>
                    <span style="font-weight: 500;">Welcome, <strong>{st.session_state.username}</strong></span>
                </div>
                {'<span class="admin-badge">Admin Access</span>' if st.session_state.is_admin else ''}
            </div>
            """, unsafe_allow_html=True)
            
            # Add logout button
            col_a, col_b, col_c = st.columns([5, 2, 1])
            with col_c:
                if st.button("Logout", key="logout_btn", help="Sign out of your account"):
                    st.session_state.logged_in = False
                    st.session_state.username = ''
                    st.session_state.is_admin = False
                    st.rerun()
        
        # Load the appropriate application based on user role
        try:
            if st.session_state.is_admin:
                # For admin users
                load_app("admin_dashboard.py")
            else:
                # For regular users
                load_app("ChatBot.py")
        except Exception as e:
            st.error(f"Error loading application: {e}")
            st.info("Make sure all required Python files are present in your Streamlit app directory.")

if __name__ == '__main__':
    main()
