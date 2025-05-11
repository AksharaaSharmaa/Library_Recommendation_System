import streamlit as st
import pymongo
import pandas as pd
import time
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import random

# Custom color palette
COLOR_PRIMARY = "#8B5B29"    # Dark brown
COLOR_SECONDARY = "#A67C4D"  # Medium brown
COLOR_BACKGROUND = "#E3D4B9" # Light beige
COLOR_TEXT = "#4B3D2D"       # Dark text
COLOR_ACCENT = "#D9CBA0"     # Light gold

def get_all_users():
    """Get all users from the database"""
    if 'db_client' not in st.session_state:
        return []
    
    client = st.session_state.db_client
    db = client["Login_Credentials"]
    users_collection = db["users"]
    
    return list(users_collection.find({}, {"password": 0}))  # Exclude passwords from the results

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

def generate_user_activity_data():
    """Generate mock user activity data for visualization purposes"""
    users = get_all_users()
    if not users:
        return pd.DataFrame()
    
    # Get usernames
    usernames = [user["username"] for user in users]
    
    # Generate random activity data for the past 7 days
    today = datetime.now()
    dates = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
    
    data = []
    for username in usernames:
        for date in dates:
            logins = random.randint(0, 5)
            actions = random.randint(logins, logins + 10) if logins > 0 else 0
            data.append({
                "username": username,
                "date": date,
                "logins": logins,
                "actions": actions
            })
    
    return pd.DataFrame(data)

def apply_custom_css():
    """Apply custom CSS to make the dashboard more aesthetic"""
    st.markdown(f"""
    <style>
        :root {{
            --color-primary: {COLOR_PRIMARY};
            --color-secondary: {COLOR_SECONDARY};
            --color-background: {COLOR_BACKGROUND};
            --color-text: {COLOR_TEXT};
            --color-accent: {COLOR_ACCENT};
        }}
        
        .stApp {{
            background-color: var(--color-background);
            color: var(--color-text);
        }}
        
        .dashboard-header {{
            background-color: var(--color-primary);
            padding: 1.5rem;
            border-radius: 10px;
            color: white;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        
        .dashboard-card {{
            background-color: white;
            border-radius: 10px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
            border-left: 5px solid var(--color-primary);
        }}
        
        .metric-card {{
            background-color: white;
            border-radius: 10px;
            padding: 1rem;
            text-align: center;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
        }}
        
        .metric-value {{
            font-size: 2.5rem;
            font-weight: bold;
            color: var(--color-primary);
        }}
        
        .metric-label {{
            font-size: 1rem;
            color: var(--color-text);
            opacity: 0.8;
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
        
        .action-button {{
            background-color: var(--color-primary);
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            cursor: pointer;
            transition: background-color 0.3s;
        }}
        
        .action-button:hover {{
            background-color: var(--color-secondary);
        }}
        
        .delete-button {{
            background-color: #d9534f;
        }}
        
        .delete-button:hover {{
            background-color: #c9302c;
        }}
        
        .section-title {{
            color: var(--color-primary);
            border-bottom: 2px solid var(--color-accent);
            padding-bottom: 0.5rem;
            margin-bottom: 1.5rem;
        }}
        
        .stDataFrame {{
            border: 1px solid var(--color-accent) !important;
            border-radius: 10px !important;
            overflow: hidden !important;
        }}
        
        .log-entry {{
            padding: 0.5rem;
            border-bottom: 1px solid #eee;
        }}
        
        .log-timestamp {{
            color: var(--color-secondary);
            font-size: 0.8rem;
        }}
        
        /* Override Streamlit's default styling */
        button {{
            border-radius: 5px !important;
        }}
        
        .stSelectbox > div > div {{
            background-color: white !important;
        }}
    </style>
    """, unsafe_allow_html=True)

def custom_metric(label, value, icon=""):
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{value} {icon}</div>
        <div class="metric-label">{label}</div>
    </div>
    """, unsafe_allow_html=True)

def render_header():
    """Render the dashboard header"""
    current_time = datetime.now().strftime("%A, %B %d, %Y %H:%M")
    
    st.markdown(f"""
    <div class="dashboard-header">
        <h1 style="margin:0;">Administration Dashboard</h1>
        <p style="margin:0; opacity:0.8;">Welcome, {st.session_state.username} • {current_time}</p>
    </div>
    """, unsafe_allow_html=True)

def render_user_table(users):
    """Render a custom styled user table"""
    if not users:
        st.warning("No users found in the database")
        return
    
    st.markdown('<h3 class="section-title">System Users</h3>', unsafe_allow_html=True)
    
    # Convert to dataframe for easier manipulation
    df = pd.DataFrame(users)
    
    # Add custom styling
    def highlight_admin(val):
        if val.get("is_admin", False):
            return '<span class="admin-badge">Admin</span>'
        return '<span class="user-badge">User</span>'
    
    df['role'] = df.apply(highlight_admin, axis=1)
    df['last_login'] = [
        (datetime.now() - timedelta(days=random.randint(0, 10), 
                                    hours=random.randint(0, 23))).strftime("%Y-%m-%d %H:%M")
        for _ in range(len(df))
    ]
    
    # Select and rearrange columns
    display_df = pd.DataFrame({
        "Username": df["username"],
        "Role": df["role"],
        "Last Login": df["last_login"]
    })
    
    # Use custom styling
    st.markdown(f"""
    <div class="dashboard-card">
        {display_df.to_html(escape=False, index=False)}
    </div>
    """, unsafe_allow_html=True)
    
    return df

def render_user_actions(users):
    """Render user action controls"""
    st.markdown('<h3 class="section-title">User Management</h3>', unsafe_allow_html=True)
    
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    
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
                    time.sleep(1)
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
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Failed to update user status. Please try again.")
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_system_metrics(users):
    """Render system metrics with custom styling"""
    st.markdown('<h3 class="section-title">System Metrics</h3>', unsafe_allow_html=True)
    
    # Prepare metrics
    total_users = len(users)
    admin_count = sum(1 for user in users if user.get("is_admin", False))
    regular_users = total_users - admin_count
    
    # Calculate admin percentage
    admin_percentage = (admin_count / total_users * 100) if total_users > 0 else 0
    
    # Create columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        custom_metric("Total Users", total_users, "👥")
    
    with col2:
        custom_metric("Administrators", admin_count, "👑")
    
    with col3:
        custom_metric("Regular Users", regular_users, "👤")
    
    with col4:
        custom_metric("Admin Ratio", f"{admin_percentage:.1f}%", "📊")
    
    # Create charts
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
    with col1:
        # User composition pie chart
        fig = go.Figure(data=[go.Pie(
            labels=['Administrators', 'Regular Users'],
            values=[admin_count, regular_users],
            hole=.3,
            marker_colors=[COLOR_PRIMARY, COLOR_SECONDARY]
        )])
        
        fig.update_layout(
            title="User Composition",
            height=300,
            margin=dict(l=20, r=20, t=50, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color=COLOR_TEXT)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Mock user growth over time
        dates = [(datetime.now() - timedelta(days=i)).strftime("%b %d") for i in range(30, 0, -5)]
        dates.reverse()
        
        # Generate some random growth data
        user_counts = [max(2, int(total_users * 0.6))]
        for i in range(1, len(dates)):
            previous = user_counts[i-1]
            change = random.randint(-1, 3)  # Random growth
            user_counts.append(max(1, previous + change))
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates,
            y=user_counts,
            mode='lines+markers',
            name='Users',
            line=dict(color=COLOR_PRIMARY, width=3),
            marker=dict(size=8, color=COLOR_SECONDARY)
        ))
        
        fig.update_layout(
            title="User Growth Trend",
            height=300,
            margin=dict(l=20, r=20, t=50, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color=COLOR_TEXT),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)')
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_activity_dashboard():
    """Render user activity dashboard"""
    st.markdown('<h3 class="section-title">User Activity Analysis</h3>', unsafe_allow_html=True)
    
    activity_data = generate_user_activity_data()
    if activity_data.empty:
        st.warning("No activity data available")
        return
    
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    
    # Aggregate data for visualizations
    daily_activity = activity_data.groupby('date')[['logins', 'actions']].sum().reset_index()
    daily_activity['date'] = pd.to_datetime(daily_activity['date'])
    daily_activity = daily_activity.sort_values('date')
    
    user_activity = activity_data.groupby('username')[['logins', 'actions']].sum().reset_index()
    user_activity = user_activity.sort_values('actions', ascending=False)
    
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["Daily Overview", "User Comparison", "Activity Heatmap"])
    
    with tab1:
        # Daily activity chart
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=daily_activity['date'],
            y=daily_activity['logins'],
            name='Logins',
            marker_color=COLOR_SECONDARY
        ))
        
        fig.add_trace(go.Scatter(
            x=daily_activity['date'],
            y=daily_activity['actions'],
            name='Actions',
            mode='lines+markers',
            line=dict(color=COLOR_PRIMARY, width=3),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            title="System Activity - Last 7 Days",
            xaxis_title="Date",
            yaxis_title="Count",
            legend_title="Activity Type",
            height=400,
            margin=dict(l=20, r=20, t=50, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color=COLOR_TEXT),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)')
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        # User comparison chart
        fig = px.bar(
            user_activity,
            x='username',
            y=['logins', 'actions'],
            title="Activity by User",
            barmode='group',
            color_discrete_sequence=[COLOR_SECONDARY, COLOR_PRIMARY]
        )
        
        fig.update_layout(
            xaxis_title="Username",
            yaxis_title="Count",
            legend_title="Activity Type",
            height=400,
            margin=dict(l=20, r=20, t=50, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color=COLOR_TEXT),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)')
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        # Heatmap of user activity
        pivot_data = activity_data.pivot_table(
            index="username", 
            columns="date", 
            values="actions", 
            aggfunc="sum"
        ).fillna(0)
        
        fig = px.imshow(
            pivot_data,
            color_continuous_scale=[[0, "white"], [0.5, COLOR_ACCENT], [1, COLOR_PRIMARY]],
            title="User Activity Heatmap"
        )
        
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Username",
            height=400,
            margin=dict(l=20, r=20, t=50, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color=COLOR_TEXT)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_activity_log():
    """Render system activity log"""
    st.markdown('<h3 class="section-title">System Activity Log</h3>', unsafe_allow_html=True)
    
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    
    # Initialize activity log if not exists
    if 'activity_log' not in st.session_state:
        st.session_state.activity_log = []
        # Add some sample logs for initial display
        sample_logs = [
            "System started by admin",
            f"User login: {st.session_state.username}",
            "Database connection established",
            "Configuration loaded successfully"
        ]
        
        for log in sample_logs:
            timestamp = (datetime.now() - timedelta(minutes=random.randint(5, 60))).strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.activity_log.append({"timestamp": timestamp, "action": log})
    
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
        if st.button("Export Activity Log", key="export_log_btn"):
            # In a real application, this would save to a file
            st.info("Log export functionality will be implemented in a future update")
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_system_health():
    """Render system health metrics"""
    st.markdown('<h3 class="section-title">System Health</h3>', unsafe_allow_html=True)
    
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # CPU Usage
        cpu_usage = random.randint(15, 45)
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=cpu_usage,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "CPU Usage", 'font': {'size': 24}},
            gauge={
                'axis': {'range': [None, 100], 'tickwidth': 1},
                'bar': {'color': COLOR_PRIMARY},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, 50], 'color': '#e6f2e6'},
                    {'range': [50, 80], 'color': '#fff2cc'},
                    {'range': [80, 100], 'color': '#f2cccc'}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        
        fig.update_layout(
            height=250,
            margin=dict(l=20, r=20, t=30, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color=COLOR_TEXT)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Memory Usage
        memory_usage = random.randint(30, 70)
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=memory_usage,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Memory Usage", 'font': {'size': 24}},
            gauge={
                'axis': {'range': [None, 100], 'tickwidth': 1},
                'bar': {'color': COLOR_SECONDARY},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, 50], 'color': '#e6f2e6'},
                    {'range': [50, 80], 'color': '#fff2cc'},
                    {'range': [80, 100], 'color': '#f2cccc'}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        
        fig.update_layout(
            height=250,
            margin=dict(l=20, r=20, t=30, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color=COLOR_TEXT)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col3:
        # Database Connections
        db_connections = random.randint(3, 12)
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=db_connections,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "DB Connections", 'font': {'size': 24}},
            gauge={
                'axis': {'range': [None, 20], 'tickwidth': 1},
                'bar': {'color': COLOR_ACCENT},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, 10], 'color': '#e6f2e6'},
                    {'range': [10, 15], 'color': '#fff2cc'},
                    {'range': [15, 20], 'color': '#f2cccc'}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 18
                }
            }
        ))
        
        fig.update_layout(
            height=250,
            margin=dict(l=20, r=20, t=30, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color=COLOR_TEXT)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # System uptime and status
    st.markdown("### System Status")
    
    status_col1, status_col2 = st.columns(2)
    
    with status_col1:
        st.markdown(f"""
        - **System Uptime:** 7 days, 14 hours, 23 minutes
        - **Last Backup:** {(datetime.now() - timedelta(days=1, hours=6)).strftime("%Y-%m-%d %H:%M")}
        - **MongoDB Status:** Online
        """)
    
    with status_col2:
        st.markdown(f"""
        - **Authentication Service:** Operational
        - **Storage Usage:** 4.3 GB / 10 GB
        - **Next Scheduled Maintenance:** {(datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")}
        """)
    
    st.markdown('</div>', unsafe_allow_html=True)

def main():
    # Check admin permissions
    if not st.session_state.get('is_admin', False):
        st.error("You don't have permission to access this administration dashboard")
        if st.button("Return to Homepage", key="return_homepage_btn"):
            # Logic to redirect to homepage would go here
            pass
        return
    
    # Apply custom styling
    apply_custom_css()
    
    # Page configuration
    st.set_page_config(
        page_title="Admin Dashboard",
        page_icon="🔐",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Sidebar navigation
    with st.sidebar:
        # Removed the image from here
        st.markdown(f"### Welcome, {st.session_state.username}")
        st.markdown("---")
        
        menu_selection = st.radio(
            "Navigation",
            ["Dashboard Overview", "User Management", "System Health", "Activity Logs"],
            index=0
        )
        
        st.markdown("---")
        st.markdown("### Quick Actions")
        
        if st.button("Refresh Data", key="refresh_btn"):
            st.rerun()
        
        if st.button("System Backup", key="backup_btn"):
            st.sidebar.success("Backup initiated successfully!")
        
        if st.button("Logout", key="sidebar_logout_btn"):  # Changed key name to make it unique
            # Logic for logout would go here
            pass
    
    # Main content area
    render_header()
    
    # Get user data
    users = get_all_users()
    
    # Determine which content to show based on navigation
    if menu_selection == "Dashboard Overview":
        render_system_metrics(users)
        render_activity_dashboard()
        render_system_health()
        
    elif menu_selection == "User Management":
        render_user_table(users)
        render_user_actions(users)
        
    elif menu_selection == "System Health":
        render_system_health()
        
    elif menu_selection == "Activity Logs":
        render_activity_log()
    
    # Footer
    st.markdown("""
    <div style="text-align: center; margin-top: 3rem; padding: 1rem; opacity: 0.7;">
        <p>Administration Dashboard v2.0 • &copy; 2025</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
