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

def apply_minimal_css():
    """Apply simplified CSS with minimal styling and reduced spacing"""
    st.markdown(f"""
    <style>
        :root {{
            --color-primary: {COLOR_PRIMARY};
            --color-secondary: {COLOR_SECONDARY};
            --color-text: {COLOR_TEXT};
        }}
        
        .stApp {{
            color: var(--color-text);
        }}
        
        .dashboard-header {{
            background-color: var(--color-primary);
            padding: 1rem;
            color: white;
            margin-bottom: 1rem;
        }}
        
        .admin-badge {{
            background-color: var(--color-primary);
            color: white;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            font-size: 0.8rem;
        }}
        
        .user-badge {{
            background-color: var(--color-secondary);
            color: white;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            font-size: 0.8rem;
        }}
        
        .section-title {{
            color: var(--color-primary);
            border-bottom: 1px solid var(--color-secondary);
            padding-bottom: 0.3rem;
            margin-bottom: 0.8rem;
        }}
        
        .log-entry {{
            padding: 0.3rem;
            border-bottom: 1px solid #eee;
        }}
        
        .log-timestamp {{
            color: var(--color-secondary);
            font-size: 0.8rem;
        }}
        
        /* Reduce spacing in all Streamlit components */
        .stSelectbox, .stButton, .stDataFrame {{
            margin-bottom: 0.5rem !important;
        }}
        
        .stTabs [data-baseweb="tab-panel"] {{
            padding-top: 0.5rem !important;
        }}
        
        div.block-container {{
            padding-top: 1rem !important;
            padding-bottom: 1rem !important;
        }}
    </style>
    """, unsafe_allow_html=True)

def render_header():
    """Render a simple dashboard header"""
    current_time = datetime.now().strftime("%A, %B %d, %Y %H:%M")
    
    st.markdown(f"""
    <div class="dashboard-header">
        <h2 style="margin:0;">Administration Dashboard</h2>
        <p style="margin:0; opacity:0.8;">Welcome, {st.session_state.username} • {current_time}</p>
    </div>
    """, unsafe_allow_html=True)

def render_user_table(users):
    """Render a basic user table"""
    if not users:
        st.warning("No users found in the database")
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
    
    # Display table
    st.markdown(display_df.to_html(escape=False, index=False), unsafe_allow_html=True)
    
    return df

def render_user_actions(users):
    """Render user action controls"""
    st.markdown('<h4 class="section-title">User Management</h4>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Delete User")
        
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
    
    with col2:
        st.subheader("Admin Rights")
        
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

def render_system_metrics(users):
    """Render simplified system metrics"""
    st.markdown('<h4 class="section-title">System Metrics</h4>', unsafe_allow_html=True)
    
    # Prepare metrics
    total_users = len(users)
    admin_count = sum(1 for user in users if user.get("is_admin", False))
    regular_users = total_users - admin_count
    
    # Create columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Users", total_users)
    
    with col2:
        st.metric("Administrators", admin_count)
    
    with col3:
        st.metric("Regular Users", regular_users)
    
    # User composition pie chart
    fig = go.Figure(data=[go.Pie(
        labels=['Administrators', 'Regular Users'],
        values=[admin_count, regular_users],
        hole=.3,
        marker_colors=[COLOR_PRIMARY, COLOR_SECONDARY]
    )])
    
    fig.update_layout(
        title="User Composition",
        height=250,
        margin=dict(l=5, r=5, t=30, b=5),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color=COLOR_TEXT)
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_activity_log():
    """Render system activity log"""
    st.markdown('<h4 class="section-title">System Activity Log</h4>', unsafe_allow_html=True)
    
    # Initialize activity log if not exists
    if 'activity_log' not in st.session_state:
        st.session_state.activity_log = []
        log_action(f"User login: {st.session_state.username}")
        log_action("Database connection established")
    
    # Display logs with custom styling
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
        if st.button("Clear Log", key="clear_log_btn"):
            st.session_state.activity_log = []
            st.rerun()

def main():
    # Check admin permissions
    if not st.session_state.get('is_admin', False):
        st.error("You don't have permission to access this administration dashboard")
        if st.button("Return to Homepage"):
            # Logic to redirect to homepage would go here
            pass
        return
    
    # Apply minimal styling
    apply_minimal_css()
    
    # Page configuration
    st.title("Admin Dashboard")
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown(f"### Welcome, {st.session_state.username}")
        st.markdown("---")
        
        menu_selection = st.radio(
            "Navigation",
            ["Dashboard Overview", "User Management", "Activity Logs"],
            index=0
        )
        
        st.markdown("---")
        
        if st.button("Refresh Data"):
            st.rerun()
        
        if st.button("Logout"):
            # Logic for logout would go here
            pass
    
    # Main content area
    render_header()
    
    # Get user data
    users = get_all_users()
    
    # Determine which content to show based on navigation
    if menu_selection == "Dashboard Overview":
        render_system_metrics(users)
        render_user_table(users)
        
    elif menu_selection == "User Management":
        render_user_table(users)
        render_user_actions(users)
        
    elif menu_selection == "Activity Logs":
        render_activity_log()
    
    # Simple footer
    st.markdown("""
    <div style="text-align: center; margin-top: 1rem; padding: 0.5rem; opacity: 0.7;">
        <p>Administration Dashboard • &copy; 2025</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
