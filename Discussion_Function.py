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

def display_discussion_post(post, index):
    import streamlit as st
    from datetime import datetime

    # Optional: Custom CSS for background and font
    st.markdown("""
        <style>
        .community-post-container {
            background: linear-gradient(120deg, #f8f3ed 0%, #f7eee4 100%);
            border-radius: 12px;
            padding: 2em 2em 1.5em 2em;
            margin-bottom: 2em;
            font-family: 'Georgia', serif;
        }
        .post-header {
            display: flex;
            align-items: center;
            gap: 0.8em;
        }
        .post-title {
            font-size: 2em;
            font-weight: 500;
            margin-bottom: 0.2em;
        }
        .post-username {
            font-weight: bold;
            font-size: 1.1em;
        }
        .post-timestamp {
            margin-left: auto;
            color: #594a3f;
            font-style: italic;
            font-size: 1.1em;
        }
        .post-content {
            margin: 1.2em 0 0.7em 0;
            font-size: 1.15em;
        }
        .replies-label {
            font-weight: bold;
            margin-top: 1em;
            margin-bottom: 0.3em;
        }
        .reply-block {
            margin-left: 1.5em;
            font-size: 1.07em;
            margin-top: 0.2em;
        }
        .reply-username {
            font-weight: bold;
        }
        </style>
    """, unsafe_allow_html=True)

    post_time = datetime.fromisoformat(post["timestamp"]).strftime("%Y-%m-%d %H:%M")

    # Main container
    st.markdown(f"""
    <div class="community-post-container">
        <div class="post-header">
            <span style="font-size:1.5em; margin-right:0.4em;">📚</span>
            <span class="post-title">Community Posts</span>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span class="post-username">{post['username']}</span>
            <span class="post-timestamp">{post_time}</span>
        </div>
        <div class="post-content">{post['content']}</div>
        <div class="replies-label">Replies:</div>
    """, unsafe_allow_html=True)

    # Replies
    if post.get('replies'):
        for reply in post['replies']:
            reply_time = datetime.fromisoformat(reply["timestamp"]).strftime("%Y-%m-%d %H:%M")
            st.markdown(
                f"""
                <div class="reply-block">
                    ↳ <span class="reply-username">{reply['username']}</span> ({reply_time}): {reply['content']}
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.markdown('<div class="reply-block" style="color:#aaa;">No replies yet.</div>', unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # Reply input (if user is logged in)
    if hasattr(st.session_state, 'username') and st.session_state.username:
        with st.expander("💬 Reply to this post"):
            # Custom input box style
            st.markdown("""
                <style>
                textarea[data-testid="stTextArea"] {
                    background-color: #f8f3ed;
                    border-radius: 8px;
                    border: 1.5px solid #b8a488;
                    font-size: 16px;
                    padding: 10px;
                    color: #594a3f;
                }
                </style>
            """, unsafe_allow_html=True)
            reply_content = st.text_area(
                "",
                key=f"reply_input_{index}",
                placeholder="Write your reply here...",
                height=70,
                label_visibility="collapsed"
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

