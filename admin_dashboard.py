import streamlit as st
import pymongo
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# Simplified color palette
COLOR_PRIMARY = "#8B5B29"    # Dark brown
COLOR_SECONDARY = "#A67C4D"  # Medium brown
COLOR_TEXT = "#4B3D2D"       # Dark text
COLOR_ACCENT = "#D4A76A"     # Light brown accent
COLOR_LIGHT = "#F3E9DC"      # Very light brown for backgrounds

def get_all_users():
    """Get all users from the database"""
    if 'db_client' not in st.session_state:
        return []
    
    client = st.session_state.db_client
    db = client["Login_Credentials"]
    users_collection = db["users"]
    
    return list(users_collection.find({}, {"password": 0}))  # Exclude passwords

def delete_user(username):
    """Delete a user from the database"""
    if 'db_client' not in st.session_state:
        return False
    
    client = st.session_state.db_client
    db = client["Login_Credentials"]
    users_collection = db["users"]
    
    if username == "admin":
        return False  # Prevent deleting the admin account
    
    result = users_collection.delete_one({"username": username})
    
    # Log the action
    log_action(f"User '{username}' deleted by {st.session_state.username}")
    
    return result.deleted_count > 0

def toggle_admin_status(username):
    """Toggle the admin status of a user"""
    if 'db_client' not in st.session_state:
        return False
    
    client = st.session_state.db_client
    db = client["Login_Credentials"]
    users_collection = db["users"]
    
    if username == "admin":
        return False  # Cannot change the main admin's status
    
    user = users_collection.find_one({"username": username})
    if not user:
        return False
    
    current_status = user.get("is_admin", False)
    result = users_collection.update_one(
        {"username": username},
        {"$set": {"is_admin": not current_status}}
    )
    
    # Log the action
    new_status = "granted to" if not current_status else "removed from"
    log_action(f"Admin rights {new_status} '{username}' by {st.session_state.username}")
    
    return result.modified_count > 0

def log_action(action_text):
    """Log an action in the session state"""
    if 'activity_log' not in st.session_state:
        st.session_state.activity_log = []
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.activity_log.insert(0, {"timestamp": timestamp, "action": action_text})
    
    # Keep only the latest 100 actions
    if len(st.session_state.activity_log) > 100:
        st.session_state.activity_log = st.session_state.activity_log[:100]

def apply_enhanced_css():
    """Apply enhanced CSS with modern styling"""
    st.markdown(f"""
    <style>
        :root {{
            --color-primary: {COLOR_PRIMARY};
            --color-secondary: {COLOR_SECONDARY};
            --color-text: {COLOR_TEXT};
            --color-accent: {COLOR_ACCENT};
            --color-light: {COLOR_LIGHT};
        }}
        
        .stApp {{
            color: var(--color-text);
            background-color: #FAFAFA;
        }}
        
        .dashboard-header {{
            background: linear-gradient(135deg, var(--color-primary), var(--color-secondary));
            padding: 1.5rem;
            color: white;
            margin-bottom: 1.5rem;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        
        .dashboard-header h2 {{
            margin: 0;
            font-weight: 600;
            letter-spacing: 0.5px;
        }}
        
        .dashboard-header p {{
            margin: 0.5rem 0 0;
            opacity: 0.9;
            font-size: 0.9rem;
        }}
        
        .admin-badge {{
            background-color: var(--color-primary);
            color: white;
            padding: 0.25rem 0.6rem;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 500;
            display: inline-block;
        }}
        
        .user-badge {{
            background-color: var(--color-secondary);
            color: white;
            padding: 0.25rem 0.6rem;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 500;
            display: inline-block;
        }}
        
        .section-title {{
            color: var(--color-primary);
            border-bottom: 2px solid var(--color-accent);
            padding-bottom: 0.5rem;
            margin-bottom: 1rem;
            font-weight: 600;
            letter-spacing: 0.3px;
        }}
        
        .card {{
            background-color: white;
            border-radius: 8px;
            padding: 1.2rem;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
            margin-bottom: 1rem;
            border-left: 3px solid var(--color-accent);
        }}
        
        .metric-card {{
            background-color: white;
            border-radius: 8px;
            padding: 1rem;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
            text-align: center;
            transition: transform 0.2s;
        }}
        
        .metric-card:hover {{
            transform: translateY(-2px);
        }}
        
        .metric-value {{
            font-size: 1.8rem;
            font-weight: 600;
            color: var(--color-primary);
            margin: 0.5rem 0;
        }}
        
        .metric-label {{
            font-size: 0.9rem;
            color: var(--color-text);
            opacity: 0.8;
        }}
        
        .log-entry {{
            padding: 0.5rem 0.8rem;
            border-bottom: 1px solid #eee;
            margin-bottom: 0.3rem;
            transition: background-color 0.2s;
        }}
        
        .log-entry:hover {{
            background-color: var(--color-light);
        }}
        
        .log-timestamp {{
            color: var(--color-secondary);
            font-size: 0.8rem;
            font-weight: 500;
        }}
        
        .data-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        .data-table th {{
            background-color: var(--color-light);
            color: var(--color-primary);
            padding: 0.7rem;
            text-align: left;
            font-weight: 600;
        }}
        
        .data-table td {{
            padding: 0.7rem;
            border-bottom: 1px solid #eee;
        }}
        
        .data-table tr:hover {{
            background-color: var(--color-light);
        }}
        
        /* Custom sidebar styling */
        [data-testid="stSidebar"] {{
            background-color: white;
            border-right: 1px solid #eee;
        }}
        
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{
            padding-left: 1rem;
            color: var(--color-primary);
            font-weight: 500;
        }}
        
        /* Improve button styling */
        .stButton button {{
            border-radius: 6px !important;
            font-weight: 500 !important;
            transition: all 0.2s !important;
        }}
        
        .stButton button:hover {{
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1) !important;
        }}
        
        /* Custom footer */
        .footer {{
            text-align: center;
            padding: 1rem;
            margin-top: 2rem;
            color: var(--color-text);
            opacity: 0.7;
            font-size: 0.85rem;
            border-top: 1px solid #eee;
        }}
        
        /* Reduce spacing in all Streamlit components */
        .stSelectbox, .stButton, .stDataFrame {{
            margin-bottom: 0.8rem !important;
        }}
        
        .stTabs [data-baseweb="tab-panel"] {{
            padding-top: 0.8rem !important;
        }}
        
        div.block-container {{
            padding-top: 1.5rem !important;
            padding-bottom: 1.5rem !important;
            max-width: 1200px;
        }}
        
        /* Tab styling */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 8px;
        }}
        
        .stTabs [data-baseweb="tab"] {{
            padding: 8px 16px;
            border-radius: 6px 6px 0 0;
        }}
        
        .stTabs [data-baseweb="tab-border"] {{
            background-color: var(--color-accent);
        }}
        
        /* Radio buttons custom styling */
        [data-testid="stRadio"] label {{
            padding: 0.5rem 0.8rem;
            border-radius: 6px;
            transition: background-color 0.2s;
        }}
        
        [data-testid="stRadio"] label:hover {{
            background-color: var(--color-light);
        }}
    </style>
    """, unsafe_allow_html=True)

def render_header():
    """Render an enhanced dashboard header"""
    current_time = datetime.now().strftime("%A, %B %d, %Y %H:%M")
    
    st.markdown(f"""
    <div class="dashboard-header">
        <h2>Administration Dashboard</h2>
        <p>Welcome, {st.session_state.username} • {current_time}</p>
    </div>
    """, unsafe_allow_html=True)

def render_user_table(users):
    """Render an enhanced user table"""
    if not users:
        st.markdown("""
        <div class="card">
            <p style="text-align: center; padding: 1.5rem 0;">No users found in the database</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    st.markdown('<h4 class="section-title">System Users</h4>', unsafe_allow_html=True)
    
    # Convert to dataframe for easier manipulation
    df = pd.DataFrame(users)
    
    # Add custom styling
    def highlight_admin(val):
        if val.get("is_admin", False):
            return '<span class="admin-badge">Admin</span>'
        return '<span class="user-badge">User</span>'
    
    df['role'] = df.apply(highlight_admin, axis=1)
    
    # Select columns
    display_df = pd.DataFrame({
        "Username": df["username"],
        "Role": df["role"]
    })
    
    # Display table with custom styling
    table_html = display_df.to_html(escape=False, index=False, classes="data-table")
    
    st.markdown(f"""
    <div class="card">
        {table_html}
    </div>
    """, unsafe_allow_html=True)
    
    return df

def render_user_actions(users):
    """Render enhanced user action controls"""
    st.markdown('<h4 class="section-title">User Management</h4>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="card">
            <h5 style="margin-top:0;">Delete User</h5>
        """, unsafe_allow_html=True)
        
        user_to_delete = st.selectbox(
            "Select user to delete:",
            options=[user["username"] for user in users if user["username"] != "admin"],
            index=None,
            placeholder="Choose a user..."
        )
        
        delete_btn = st.button("Delete Selected User", type="primary", key="delete_btn", 
                              help="Permanently remove user from the system")
        
        if delete_btn and user_to_delete:
            with st.spinner(f"Deleting user '{user_to_delete}'..."):
                if delete_user(user_to_delete):
                    st.success(f"User '{user_to_delete}' has been deleted successfully")
                    st.rerun()
                else:
                    st.error("Failed to delete user. Please try again.")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="card">
            <h5 style="margin-top:0;">Admin Rights</h5>
        """, unsafe_allow_html=True)
        
        user_to_modify = st.selectbox(
            "Modify admin rights for:",
            options=[user["username"] for user in users if user["username"] != "admin"],
            index=None,
            placeholder="Choose a user..."
        )
        
        if user_to_modify:
            is_admin = next((user.get("is_admin", False) for user in users if user["username"] == user_to_modify), False)
            
            status_text = "Remove Admin Rights" if is_admin else "Grant Admin Rights"
            
            admin_btn = st.button(status_text, type="primary", key="admin_btn")
            
            if admin_btn:
                with st.spinner(f"Updating rights for '{user_to_modify}'..."):
                    if toggle_admin_status(user_to_modify):
                        action = "removed from" if is_admin else "granted to"
                        st.success(f"Admin rights {action} '{user_to_modify}' successfully")
                        st.rerun()
                    else:
                        st.error("Failed to update user status. Please try again.")
        
        st.markdown("</div>", unsafe_allow_html=True)

def render_system_metrics(users):
    """Render enhanced system metrics"""
    st.markdown('<h4 class="section-title">System Metrics</h4>', unsafe_allow_html=True)
    
    # Prepare metrics
    total_users = len(users)
    admin_count = sum(1 for user in users if user.get("is_admin", False))
    regular_users = total_users - admin_count
    
    # Create metrics in cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Users</div>
            <div class="metric-value">{total_users}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Administrators</div>
            <div class="metric-value">{admin_count}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Regular Users</div>
            <div class="metric-value">{regular_users}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # User composition pie chart
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    
    fig = go.Figure(data=[go.Pie(
        labels=['Administrators', 'Regular Users'],
        values=[admin_count, regular_users],
        hole=.4,
        marker_colors=[COLOR_PRIMARY, COLOR_SECONDARY],
        textinfo='percent+label',
        insidetextorientation='radial'
    )])
    
    fig.update_layout(
        title={
            'text': "User Composition",
            'y':0.95,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        height=300,
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color=COLOR_TEXT),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.1,
            xanchor="center",
            x=0.5
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

def render_activity_log():
    """Render enhanced system activity log"""
    st.markdown('<h4 class="section-title">System Activity Log</h4>', unsafe_allow_html=True)
    
    # Initialize activity log if not exists
    if 'activity_log' not in st.session_state:
        st.session_state.activity_log = []
        log_action(f"User login: {st.session_state.username}")
        log_action("Database connection established")
    
    # Display logs with custom styling
    st.markdown("<div class='card' style='padding: 0.5rem;'>", unsafe_allow_html=True)
    
    if not st.session_state.activity_log:
        st.info("No activity recorded yet")
    else:
        log_html = ""
        for entry in st.session_state.activity_log:
            log_html += f"""
            <div class="log-entry">
                <span class="log-timestamp">{entry['timestamp']}</span>
                <span class="log-text"> • {entry['action']}</span>
            </div>
            """
        
        st.markdown(log_html, unsafe_allow_html=True)
    
        # Add export option
        st.markdown("<div style='padding: 0.5rem 0.8rem;'>", unsafe_allow_html=True)
        if st.button("Clear Log", key="clear_log_btn"):
            st.session_state.activity_log = []
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

def render_sidebar():
    """Render an enhanced sidebar"""
    # Logo and title
    st.sidebar.markdown("""
    <div style="text-align: center; padding: 1rem 0;">
        <div style="font-size: 1.5rem; font-weight: 600; color: var(--color-primary);">Admin Portal</div>
        <div style="height: 2px; background: linear-gradient(90deg, white, var(--color-accent), white); margin: 0.5rem 0;"></div>
    </div>
    """, unsafe_allow_html=True)
    
    st.sidebar.markdown("""
    <div style="padding: 0.5rem; margin-bottom: 1rem;">
        <p style="font-weight: 600; margin-bottom: 0.5rem;">Navigation</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Menu with icons
    menu_selection = st.sidebar.radio(
        "",
        ["Dashboard Overview", "User Management", "Activity Logs"],
        index=0,
        format_func=lambda x: {
            "Dashboard Overview": "📊 Dashboard Overview",
            "User Management": "👥 User Management",
            "Activity Logs": "📝 Activity Logs"
        }[x]
    )
    
    # User info card
    st.sidebar.markdown("""
    <div style="background-color: var(--color-light); border-radius: 8px; padding: 1rem; margin-top: 2rem;">
        <div style="font-weight: 600; margin-bottom: 0.5rem;">Current User</div>
        <div style="display: flex; align-items: center;">
            <div style="width: 30px; height: 30px; border-radius: 50%; background-color: var(--color-primary); color: white; 
                        display: flex; align-items: center; justify-content: center; margin-right: 0.8rem;">
                <span style="font-weight: 500; font-size: 0.9rem;">
                    {0}
                </span>
            </div>
            <div>
                <div style="font-weight: 500;">{1}</div>
                <div style="font-size: 0.8rem; opacity: 0.7;">Administrator</div>
            </div>
        </div>
    </div>
    """.format(
        st.session_state.username[0].upper(),
        st.session_state.username
    ), unsafe_allow_html=True)
    
    # System info
    st.sidebar.markdown("""
    <div style="padding: 0.5rem; font-size: 0.75rem; opacity: 0.7; margin-top: 2rem;">
        <div>System Version: 1.2.0</div>
        <div>Last Update: May 9, 2025</div>
    </div>
    """, unsafe_allow_html=True)
    
    return menu_selection

def render_footer():
    """Render enhanced footer"""
    st.markdown("""
    <div class="footer">
        <p>Administration Dashboard • &copy; 2025 • All Rights Reserved</p>
    </div>
    """, unsafe_allow_html=True)

def main():
    # Check admin permissions
    if not st.session_state.get('is_admin', False):
        st.error("You don't have permission to access this administration dashboard")
        if st.button("Return to Homepage"):
            # Logic to redirect to homepage would go here
            pass
        return
    
    # Apply enhanced styling
    apply_enhanced_css()
    
    # Sidebar navigation
    menu_selection = render_sidebar()
    
    # Main content container
    st.markdown('<div style="padding: 0 1rem;">', unsafe_allow_html=True)
    
    # Header
    render_header()
    
    # Get user data
    users = get_all_users()
    
    # Tabs based on navigation selection
    if menu_selection == "Dashboard Overview":
        col1, col2 = st.columns([2, 1])
        
        with col1:
            render_system_metrics(users)
        
        with col2:
            render_user_table(users)
        
    elif menu_selection == "User Management":
        col1, col2 = st.columns([1, 2])
        
        with col1:
            render_user_table(users)
            
        with col2:
            render_user_actions(users)
        
    elif menu_selection == "Activity Logs":
        render_activity_log()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer
    render_footer()

if __name__ == "__main__":
    main()
