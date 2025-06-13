import pymongo
from datetime import datetime, date
import json
import streamlit as st
from collections import defaultdict

def get_mongodb_connection():
    """Get MongoDB connection using your existing connection function"""
    try:
        # Use your existing connection logic
        if 'db_client' not in st.session_state:
            client = init_connection()
            if client is None:
                return None
        else:
            client = st.session_state.db_client
        
        # Use your existing database
        db = client["Login_Credentials"]
        return db
    except Exception as e:
        st.error(f"Failed to connect to MongoDB: {str(e)}")
        return None

def save_chat_session(username, messages, session_id=None):
    """Save current chat session to MongoDB with day-wise organization"""
    try:
        db = get_mongodb_connection()
        if not db:
            return False
            
        chat_collection = db["chat_history"]
        
        # Filter out system messages and prepare messages for storage
        user_messages = [msg for msg in messages if msg.get("role") != "system"]
        
        # Get current date for day-wise organization
        current_date = datetime.now().date()
        current_datetime = datetime.now()
        
        chat_session = {
            "username": username or "anonymous",
            "session_id": session_id or f"session_{current_datetime.strftime('%Y%m%d_%H%M%S')}",
            "messages": user_messages,
            "timestamp": current_datetime.isoformat(),
            "date": current_date.isoformat(),  # Add date field for day-wise grouping
            "message_count": len(user_messages),
            "last_updated": current_datetime.isoformat()
        }
        
        # Update if session exists, otherwise insert new
        result = chat_collection.update_one(
            {"session_id": chat_session["session_id"]},
            {"$set": chat_session},
            upsert=True
        )
        
        return True
    except Exception as e:
        st.error(f"Failed to save chat session: {str(e)}")
        return False

def get_user_chat_history_by_date(username):
    """Get all chat sessions for a user organized by date"""
    try:
        db = get_mongodb_connection()
        if not db:
            return {}
            
        chat_collection = db["chat_history"]
        
        # Get all sessions for the user, sorted by timestamp (newest first)
        sessions = list(chat_collection.find(
            {"username": username or "anonymous"}
        ).sort("timestamp", -1))
        
        # Group sessions by date
        sessions_by_date = defaultdict(list)
        for session in sessions:
            # Handle both old sessions (without date field) and new sessions (with date field)
            if 'date' in session:
                session_date = session['date']
            else:
                # Extract date from timestamp for backward compatibility
                try:
                    session_datetime = datetime.fromisoformat(session['timestamp'])
                    session_date = session_datetime.date().isoformat()
                except:
                    session_date = datetime.now().date().isoformat()
            
            sessions_by_date[session_date].append(session)
        
        # Convert defaultdict to regular dict and sort dates (newest first)
        sorted_sessions = {}
        for date_key in sorted(sessions_by_date.keys(), reverse=True):
            sorted_sessions[date_key] = sessions_by_date[date_key]
        
        return sorted_sessions
    except Exception as e:
        st.error(f"Failed to retrieve chat history: {str(e)}")
        return {}

def get_user_chat_history(username):
    """Get all chat sessions for a user (legacy function for backward compatibility)"""
    try:
        db = get_mongodb_connection()
        if not db:
            return []
            
        chat_collection = db["chat_history"]
        
        # Get all sessions for the user, sorted by timestamp (newest first)
        sessions = list(chat_collection.find(
            {"username": username or "anonymous"}
        ).sort("timestamp", -1))
        
        return sessions
    except Exception as e:
        st.error(f"Failed to retrieve chat history: {str(e)}")
        return []

def delete_chat_session(session_id):
    """Delete a specific chat session"""
    try:
        db = get_mongodb_connection()
        if not db:
            return False
            
        chat_collection = db["chat_history"]
        result = chat_collection.delete_one({"session_id": session_id})
        
        return result.deleted_count > 0
    except Exception as e:
        st.error(f"Failed to delete chat session: {str(e)}")
        return False

def delete_all_chats_for_date(username, date_str):
    """Delete all chat sessions for a user on a specific date"""
    try:
        db = get_mongodb_connection()
        if not db:
            return False
            
        chat_collection = db["chat_history"]
        
        # Delete all sessions for the user on the specified date
        result = chat_collection.delete_many({
            "username": username or "anonymous",
            "date": date_str
        })
        
        # Also handle old sessions without date field
        # Get sessions without date field and check their timestamp
        old_sessions = list(chat_collection.find({
            "username": username or "anonymous",
            "date": {"$exists": False}
        }))
        
        deleted_old_count = 0
        for session in old_sessions:
            try:
                session_datetime = datetime.fromisoformat(session['timestamp'])
                if session_datetime.date().isoformat() == date_str:
                    chat_collection.delete_one({"_id": session["_id"]})
                    deleted_old_count += 1
            except:
                continue
        
        total_deleted = result.deleted_count + deleted_old_count
        return total_deleted > 0
    except Exception as e:
        st.error(f"Failed to delete chat sessions for date: {str(e)}")
        return False

def load_chat_session(session_id):
    """Load a specific chat session"""
    try:
        db = get_mongodb_connection()
        if not db:
            return None
            
        chat_collection = db["chat_history"]
        session = chat_collection.find_one({"session_id": session_id})
        
        return session
    except Exception as e:
        st.error(f"Failed to load chat session: {str(e)}")
        return None

def display_chat_history_by_date(username):
    """Display chat history organized by date with day-wise delete functionality"""
    sessions_by_date = get_user_chat_history_by_date(username)
    
    if not sessions_by_date:
        st.info("No chat history found.")
        return
    
    for date_str, sessions in sessions_by_date.items():
        # Format date for display
        try:
            date_obj = datetime.fromisoformat(date_str).date()
            if date_obj == date.today():
                date_display = "Today"
            elif date_obj == date.today().replace(day=date.today().day - 1):
                date_display = "Yesterday"
            else:
                date_display = date_obj.strftime("%B %d, %Y")
        except:
            date_display = date_str
        
        # Create expandable section for each date
        with st.expander(f"📅 {date_display} ({len(sessions)} chats)", expanded=False):
            # Date header with delete all button
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{len(sessions)} conversations on {date_display}**")
            with col2:
                if st.button(f"🗑️ Delete All", key=f"delete_all_{date_str}"):
                    # Confirmation dialog
                    if st.button(f"Confirm Delete All for {date_display}", key=f"confirm_delete_{date_str}"):
                        if delete_all_chats_for_date(username, date_str):
                            st.success(f"All chats for {date_display} deleted!")
                            st.rerun()
                        else:
                            st.error("Failed to delete chats")
            
            st.markdown("---")
            
            # Display individual sessions for this date
            for i, session in enumerate(sessions):
                display_chat_history_card(session, f"{date_str}_{i}")

def display_chat_history_card(session, index):
    """Display a chat history session card"""
    with st.container():
        # Create a card-like container
        st.markdown(f"""
        <div style="border: 1px solid #ddd; border-radius: 10px; padding: 15px; margin: 10px 0; 
                    background: linear-gradient(135deg, #f8f9fa, #e9ecef);">
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            # Session info
            timestamp = datetime.fromisoformat(session['timestamp'])
            st.markdown(f"**Session:** {session['session_id']}")
            st.markdown(f"**Time:** {timestamp.strftime('%H:%M:%S')}")
            st.markdown(f"**Messages:** {session['message_count']}")
            
            # Show first user message as preview
            if session['messages']:
                first_message = session['messages'][0]
                if first_message.get('role') == 'user':
                    preview = first_message['content'][:100]
                    if len(first_message['content']) > 100:
                        preview += "..."
                    st.markdown(f"**Preview:** {preview}")
        
        with col2:
            if st.button("View", key=f"view_session_{index}"):
                st.session_state.selected_chat_session = session
                st.session_state.app_stage = "view_chat_session"
                st.rerun()
        
        with col3:
            if st.button("Delete", key=f"delete_session_{index}"):
                if delete_chat_session(session['session_id']):
                    st.success("Chat session deleted!")
                    st.rerun()
                else:
                    st.error("Failed to delete session")
        
        st.markdown("</div>", unsafe_allow_html=True)

def get_chat_statistics(username):
    """Get chat statistics for a user"""
    try:
        db = get_mongodb_connection()
        if not db:
            return {}
            
        chat_collection = db["chat_history"]
        
        # Get all sessions for the user
        sessions = list(chat_collection.find({"username": username or "anonymous"}))
        
        if not sessions:
            return {}
        
        # Calculate statistics
        total_sessions = len(sessions)
        total_messages = sum(session.get('message_count', 0) for session in sessions)
        
        # Get unique dates
        dates = set()
        for session in sessions:
            if 'date' in session:
                dates.add(session['date'])
            else:
                try:
                    session_datetime = datetime.fromisoformat(session['timestamp'])
                    dates.add(session_datetime.date().isoformat())
                except:
                    continue
        
        active_days = len(dates)
        
        # Latest activity
        latest_session = max(sessions, key=lambda x: x['timestamp'])
        latest_activity = datetime.fromisoformat(latest_session['timestamp'])
        
        return {
            'total_sessions': total_sessions,
            'total_messages': total_messages,
            'active_days': active_days,
            'latest_activity': latest_activity,
            'average_messages_per_session': round(total_messages / total_sessions, 1) if total_sessions > 0 else 0
        }
    except Exception as e:
        st.error(f"Failed to get chat statistics: {str(e)}")
        return {}

def auto_save_current_session():
    """Auto-save current chat session"""
    if hasattr(st.session_state, 'messages') and len(st.session_state.messages) > 1:
        username = getattr(st.session_state, 'username', 'anonymous')
        session_id = getattr(st.session_state, 'current_session_id', 
                           f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        if not hasattr(st.session_state, 'current_session_id'):
            st.session_state.current_session_id = session_id
            
        save_chat_session(username, st.session_state.messages, session_id)

def periodic_auto_save():
    """Periodically save chat sessions"""
    if not hasattr(st.session_state, 'messages'):
        return
        
    current_message_count = len(st.session_state.messages)
    
    # Initialize last_save_count if it doesn't exist
    if not hasattr(st.session_state, 'last_save_count'):
        st.session_state.last_save_count = 0
    
    # Auto-save every 5 messages
    if (current_message_count > st.session_state.last_save_count and 
        current_message_count % 5 == 0 and 
        current_message_count > 1):  # Don't save if only system message
        
        username = getattr(st.session_state, 'username', 'anonymous')
        if save_chat_session(username, st.session_state.messages, st.session_state.current_session_id):
            st.session_state.last_save_count = current_message_count

import streamlit as st
from datetime import datetime, date
from MongoDB_Chats_Function import *

def display_chat_history_page():
    """Main chat history page with day-wise organization"""
    st.markdown("<h1 style='text-align:center;'>💬 Chat History</h1>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center;'>Your conversations organized by date</div>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Check if user is logged in
    if not hasattr(st.session_state, 'username') or not st.session_state.username:
        st.warning("Please log in to view your chat history.")
        return
    
    username = st.session_state.username
    
    # Display chat statistics
    stats = get_chat_statistics(username)
    if stats:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Chats", stats['total_sessions'])
        with col2:
            st.metric("Total Messages", stats['total_messages'])
        with col3:
            st.metric("Active Days", stats['active_days'])
        with col4:
            avg_msg = stats.get('average_messages_per_session', 0)
            st.metric("Avg Messages/Chat", avg_msg)
        
        st.markdown("---")
    
    # Get and display chat history by date
    sessions_by_date = get_user_chat_history_by_date(username)
    
    if not sessions_by_date:
        st.info("No chat history found. Start a conversation to see your history here!")
        if st.button("Start New Conversation"):
            st.session_state.app_stage = "welcome"
            st.rerun()
        return
    
    # Display sessions organized by date
    for date_str, sessions in sessions_by_date.items():
        # Format date for display
        try:
            date_obj = datetime.fromisoformat(date_str).date()
            today = date.today()
            
            if date_obj == today:
                date_display = "📅 Today"
                date_color = "#28a745"  # Green
            elif date_obj == today.replace(day=today.day - 1):
                date_display = "📅 Yesterday"
                date_color = "#ffc107"  # Yellow
            else:
                date_display = f"📅 {date_obj.strftime('%B %d, %Y')}"
                date_color = "#6c757d"  # Gray
        except:
            date_display = f"📅 {date_str}"
            date_color = "#6c757d"
        
        # Create expandable section for each date
        with st.expander(f"{date_display} ({len(sessions)} conversations)", expanded=date_obj == today if 'date_obj' in locals() else False):
            # Date header with statistics and delete all button
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                total_messages_day = sum(session.get('message_count', 0) for session in sessions)
                st.markdown(f"""
                <div style="padding: 10px; border-left: 4px solid {date_color};">
                    <strong>{len(sessions)} conversations</strong><br>
                    <small>{total_messages_day} total messages</small>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                # Export day's chats as JSON
                if st.button(f"📥 Export", key=f"export_{date_str}"):
                    export_data = {
                        'date': date_str,
                        'username': username,
                        'sessions': sessions,
                        'exported_at': datetime.now().isoformat()
                    }
                    
                    json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
                    st.download_button(
                        label="Download JSON",
                        data=json_str,
                        file_name=f"chat_history_{date_str}.json",
                        mime="application/json",
                        key=f"download_{date_str}"
                    )
            
            with col3:
                # Delete all chats for this date
                if st.button(f"🗑️ Delete All", key=f"delete_all_{date_str}", type="secondary"):
                    st.session_state[f"confirm_delete_{date_str}"] = True
            
            # Confirmation for delete all
            if st.session_state.get(f"confirm_delete_{date_str}", False):
                st.warning(f"Are you sure you want to delete ALL {len(sessions)} conversations from {date_display}?")
                col_yes, col_no = st.columns(2)
                
                with col_yes:
                    if st.button("✅ Yes, Delete All", key=f"confirm_yes_{date_str}"):
                        if delete_all_chats_for_date(username, date_str):
                            st.success(f"All conversations from {date_display} deleted!")
                            # Clear confirmation state
                            if f"confirm_delete_{date_str}" in st.session_state:
                                del st.session_state[f"confirm_delete_{date_str}"]
                            st.rerun()
                        else:
                            st.error("Failed to delete conversations")
                
                with col_no:
                    if st.button("❌ Cancel", key=f"confirm_no_{date_str}"):
                        # Clear confirmation state
                        if f"confirm_delete_{date_str}" in st.session_state:
                            del st.session_state[f"confirm_delete_{date_str}"]
                        st.rerun()
            
            st.markdown("---")
            
            # Display individual chat sessions for this date
            for i, session in enumerate(sessions):
                display_individual_chat_card(session, f"{date_str}_{i}")

def display_individual_chat_card(session, index):
    """Display an individual chat session card with enhanced styling"""
    timestamp = datetime.fromisoformat(session['timestamp'])
    
    # Create a styled card
    st.markdown(f"""
    <div style="
        border: 1px solid #e0e0e0; 
        border-radius: 12px; 
        padding: 16px; 
        margin: 8px 0; 
        background: linear-gradient(135deg, #ffffff, #f8f9fa);
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    ">
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
    
    with col1:
        # Session details
        st.markdown(f"**🕒 {timestamp.strftime('%H:%M:%S')}**")
        st.markdown(f"💬 {session['message_count']} messages")
        
        # Show preview of first user message
        if session.get('messages'):
            for msg in session['messages']:
                if msg.get('role') == 'user':
                    preview = msg['content'][:80]
                    if len(msg['content']) > 80:
                        preview += "..."
                    st.markdown(f"*{preview}*")
                    break
        
        # Session ID (small text)
        st.markdown(f"<small style='color: #6c757d;'>ID: {session['session_id']}</small>", unsafe_allow_html=True)
    
    with col2:
        if st.button("👁️ View", key=f"view_{index}"):
            st.session_state.selected_chat_session = session
            st.session_state.app_stage = "view_chat_session"
            st.rerun()
    
    with col3:
        if st.button("📄 Export", key=f"export_single_{index}"):
            # Export single session
            json_str = json.dumps(session, indent=2, ensure_ascii=False)
            st.download_button(
                label="Download",
                data=json_str,
                file_name=f"chat_{session['session_id']}.json",
                mime="application/json",
                key=f"download_single_{index}"
            )
    
    with col4:
        if st.button("🗑️ Delete", key=f"delete_{index}"):
            if delete_chat_session(session['session_id']):
                st.success("Chat deleted!")
                st.rerun()
            else:
                st.error("Failed to delete")
    
    st.markdown("</div>", unsafe_allow_html=True)

def display_chat_session_viewer():
    """Display the selected chat session in a readable format"""
    if not hasattr(st.session_state, 'selected_chat_session') or not st.session_state.selected_chat_session:
        st.error("No chat session selected.")
        return
    
    session = st.session_state.selected_chat_session
    timestamp = datetime.fromisoformat(session['timestamp'])
    
    # Header
    st.markdown(f"<h2 style='text-align:center;'>💬 Chat Session</h2>", unsafe_allow_html=True)
    st.markdown(f"<div style='text-align:center;'>📅 {timestamp.strftime('%B %d, %Y at %H:%M:%S')}</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='text-align:center;'><small>Session ID: {session['session_id']}</small></div>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Display messages
    for i, message in enumerate(session.get('messages', [])):
        role = message.get('role', 'unknown')
        content = message.get('content', '')
        
        if role == 'user':
            # User message (right-aligned, blue)
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #007bff, #0056b3);
                color: white;
                padding: 12px 16px;
                border-radius: 18px 18px 4px 18px;
                margin: 8px 0 8px 20%;
                box-shadow: 0 2px 4px rgba(0,123,255,0.3);
            ">
                <strong>You:</strong><br>
                {content}
            </div>
            """, unsafe_allow_html=True)
        
        elif role == 'assistant':
            # Assistant message (left-aligned, gray)
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #f8f9fa, #e9ecef);
                color: #333;
                padding: 12px 16px;
                border-radius: 18px 18px 18px 4px;
                margin: 8px 20% 8px 0;
                border-left: 4px solid #28a745;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            ">
                <strong>🤖 Assistant:</strong><br>
                {content}
            </div>
            """, unsafe_allow_html=True)
    
    # Back button
    st.markdown("---")
    if st.button("← Back to Chat History"):
        st.session_state.app_stage = "chat_history"
        if 'selected_chat_session' in st.session_state:
            del st.session_state.selected_chat_session
        st.rerun()

# Add this to your sidebar setup function
def setup_chat_history_sidebar():
    """Add chat history option to sidebar"""
    if hasattr(st.session_state, 'username') and st.session_state.username:
        if st.sidebar.button("💬 Chat History"):
            st.session_state.app_stage = "chat_history"
            st.rerun()
        
        # Quick stats in sidebar
        stats = get_chat_statistics(st.session_state.username)
        if stats:
            st.sidebar.markdown("### 📊 Your Stats")
            st.sidebar.markdown(f"📝 {stats['total_sessions']} chats")
            st.sidebar.markdown(f"💬 {stats['total_messages']} messages")
            st.sidebar.markdown(f"📅 {stats['active_days']} active days")
