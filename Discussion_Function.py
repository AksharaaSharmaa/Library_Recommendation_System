from datetime import datetime
import streamlit as st
from bson.objectid import ObjectId  # Needed for MongoDB _id handling

def get_discussion_collection():
    """Get the MongoDB collection for discussions"""
    try:
        # Use the existing database client from session state
        if 'db_client' not in st.session_state:
            # If no client exists, initialize connection
            from Login_System import init_connection  # Corrected import
            client = init_connection()
            if client is None:
                return None
            st.session_state.db_client = client  # Save for reuse
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
    if discussion_collection is None:
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
    if discussion_collection is None:
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
    if discussion_collection is None:
        return False

    try:
        reply_data = {
            "username": username,
            "content": reply_content,
            "timestamp": datetime.now().isoformat()
        }
        # Ensure post_id is an ObjectId
        if not isinstance(post_id, ObjectId):
            post_id = ObjectId(post_id)
        discussion_collection.update_one(
            {"_id": post_id},
            {"$push": {"replies": reply_data}}
        )
        return True
    except Exception as e:
        st.error(f"Error saving reply: {e}")
        return False

def delete_discussion_post(post_id):
    """Delete a discussion post from MongoDB"""
    discussion_collection = get_discussion_collection()
    if discussion_collection is None:
        return False

    try:
        # Ensure post_id is an ObjectId
        if not isinstance(post_id, ObjectId):
            post_id = ObjectId(post_id)
        
        # Delete the post
        result = discussion_collection.delete_one({"_id": post_id})
        return result.deleted_count > 0
    except Exception as e:
        st.error(f"Error deleting discussion post: {e}")
        return False

def display_discussion_post(post, index):
    import streamlit as st
    from datetime import datetime

    # Identify if the post is by the current user
    is_user_post = (
        hasattr(st.session_state, 'username') and 
        st.session_state.username and 
        post['username'] == st.session_state.username
    )

    # Custom styles for distinction
    user_post_style = """
        background-color: #e6f2ff; 
        border-left: 5px solid #3399ff; 
        padding: 1em; 
        border-radius: 8px;
        margin-bottom: 1em;
    """
    other_post_style = """
        background-color: #f9f9f9; 
        padding: 1em; 
        border-radius: 8px;
        margin-bottom: 1em;
    """

    # Choose style
    post_style = user_post_style if is_user_post else other_post_style

    # Main post display
    with st.container():
        st.markdown(
            f'<div style="{post_style}">'
            f'<div style="display: flex; justify-content: space-between;">'
            f'<b>{"🟦 You" if is_user_post else post["username"]}</b>'
            f'<span style="color: #888;">{datetime.fromisoformat(post["timestamp"]).strftime("%Y-%m-%d %H:%M")}</span>'
            f'</div>'
            f'<div style="margin-top: 0.5em;">{post["content"]}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

        # Delete button (only for user's own posts) - Single click deletion
        if is_user_post:
            col1, col2 = st.columns([6, 1])
            with col2:
                if st.button("🗑️", key=f"delete_btn_{index}", help="Delete this post"):
                    try:
                        if delete_discussion_post(post['_id']):
                            st.success("Post deleted successfully!")
                            # Force immediate refresh
                            st.rerun()
                        else:
                            st.error("Failed to delete post. Please try again.")
                    except Exception as e:
                        st.error(f"Error deleting post: {e}")

        # Replies section
        if post.get('replies'):
            st.markdown("**Replies:**")
            for reply in post['replies']:
                is_user_reply = (
                    hasattr(st.session_state, 'username') and 
                    st.session_state.username and 
                    reply['username'] == st.session_state.username
                )
                reply_style = (
                    "background-color: #fffbe6; border-left: 3px solid #ffcc00; padding: 0.5em; border-radius: 6px; margin-bottom: 0.5em;"
                    if is_user_reply else 
                    "background-color: #f4f4f4; padding: 0.5em; border-radius: 6px; margin-bottom: 0.5em;"
                )
                st.markdown(
                    f'<div style="{reply_style}">'
                    f'↳ <b>{"🟨 You" if is_user_reply else reply["username"]}</b> '
                    f'({datetime.fromisoformat(reply["timestamp"]).strftime("%Y-%m-%d %H:%M")}): '
                    f'{reply["content"]}'
                    f'</div>',
                    unsafe_allow_html=True
                )

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
