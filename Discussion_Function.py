from datetime import datetime
import streamlit as st
from pymongo import MongoClient

def get_discussion_collection():
    """Get the MongoDB collection for discussions"""
    try:
        # Use the existing database client from session state
        if 'db_client' not in st.session_state:
            # If no client exists, initialize connection
            from login import init_connection  # Import your connection function
            client = init_connection()
            if client is None:
                return None
        else:
            client = st.session_state.db_client
        
        # Use the same database as your login system
        db = client["Login_Credentials"]
        return db["discussions"]
    except Exception as e:
        st.error(f"Error connecting to discussion database: {e}")
        return None

def save_discussion_post(username, content):
    """Save a discussion post to MongoDB"""
    discussion_collection = get_discussion_collection()
    if not discussion_collection:
        return False
    
    try:
        post_data = {
            "username": username,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "likes": 0,
            "replies": []
        }
        discussion_collection.insert_one(post_data)
        return True
    except Exception as e:
        st.error(f"Error saving discussion post: {e}")
        return False

def get_all_discussion_posts():
    """Get all discussion posts from MongoDB, sorted by timestamp (newest first)"""
    discussion_collection = get_discussion_collection()
    if not discussion_collection:
        return []
    
    try:
        posts = list(discussion_collection.find().sort("timestamp", -1))
        return posts
    except Exception as e:
        st.error(f"Error fetching discussion posts: {e}")
        return []

def save_reply_to_post(post_id, username, reply_content):
    """Save a reply to a specific discussion post"""
    discussion_collection = get_discussion_collection()
    if not discussion_collection:
        return False
    
    try:
        reply_data = {
            "username": username,
            "content": reply_content,
            "timestamp": datetime.now().isoformat()
        }
        
        discussion_collection.update_one(
            {"_id": post_id},
            {"$push": {"replies": reply_data}}
        )
        return True
    except Exception as e:
        st.error(f"Error saving reply: {e}")
        return False

def display_discussion_post(post, index):
    """Display a single discussion post with replies"""
    with st.container():
        # Post header
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**{post['username']}**")
        with col2:
            timestamp = datetime.fromisoformat(post['timestamp'])
            st.markdown(f"*{timestamp.strftime('%Y-%m-%d %H:%M')}*")
        
        # Post content
        st.markdown(f"{post['content']}")
        
        # Reply section
        if post.get('replies'):
            st.markdown("**Replies:**")
            for reply in post['replies']:
                reply_timestamp = datetime.fromisoformat(reply['timestamp'])
                st.markdown(f"↳ **{reply['username']}** ({reply_timestamp.strftime('%Y-%m-%d %H:%M')}): {reply['content']}")
        
        # Reply input (only if user is logged in)
        if hasattr(st.session_state, 'username') and st.session_state.username:
            with st.expander("💬 Reply to this post"):
                reply_content = st.text_area(
                    "Your reply:", 
                    key=f"reply_input_{index}",
                    placeholder="Write your reply here..."
                )
                if st.button("Post Reply", key=f"reply_btn_{index}"):
                    if reply_content.strip():
                        if save_reply_to_post(post['_id'], st.session_state.username, reply_content.strip()):
                            st.success("Reply posted successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to post reply.")
                    else:
                        st.warning("Please enter a reply.")
