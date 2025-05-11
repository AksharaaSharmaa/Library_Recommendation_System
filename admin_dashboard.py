import streamlit as st
import pymongo

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
    
    return result.modified_count > 0

def main():
    
    if not st.session_state.get('is_admin', False):
        st.error("You don't have permission to access this page")
        return
    
    st.write(f"Welcome, Administrator {st.session_state.username}!")
    
    # User Management Section
    st.header("User Management")
    
    users = get_all_users()
    
    if not users:
        st.warning("No users found in the database")
    else:
        # Convert users list to a format suitable for display
        user_data = []
        for user in users:
            user_data.append({
                "Username": user["username"],
                "Admin": "Yes" if user.get("is_admin", False) else "No"
            })
        
        st.dataframe(user_data)
        
        # User actions
        st.subheader("User Actions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Delete user
            user_to_delete = st.selectbox(
                "Select user to delete:",
                options=[user["username"] for user in users if user["username"] != "admin"],
                index=None,
                placeholder="Choose a user..."
            )
            
            if user_to_delete and st.button("Delete User"):
                if delete_user(user_to_delete):
                    st.success(f"User '{user_to_delete}' has been deleted")
                    st.rerun()
                else:
                    st.error("Failed to delete user")
        
        with col2:
            # Change admin status
            user_to_modify = st.selectbox(
                "Change admin rights for:",
                options=[user["username"] for user in users if user["username"] != "admin"],
                index=None,
                placeholder="Choose a user..."
            )
            
            if user_to_modify:
                is_admin = next((user.get("is_admin", False) for user in users if user["username"] == user_to_modify), False)
                
                status_text = "Remove Admin Rights" if is_admin else "Grant Admin Rights"
                
                if st.button(status_text):
                    if toggle_admin_status(user_to_modify):
                        action = "removed from" if is_admin else "granted to"
                        st.success(f"Admin rights {action} '{user_to_modify}'")
                        st.rerun()
                    else:
                        st.error("Failed to update user status")
    
    # System Stats
    st.header("System Statistics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(label="Total Users", value=len(users))
    
    with col2:
        admin_count = sum(1 for user in users if user.get("is_admin", False))
        st.metric(label="Admins", value=admin_count)
    
    with col3:
        st.metric(label="Regular Users", value=len(users) - admin_count)
    
    # Activity Log (Placeholder)
    st.header("Recent System Activity")
    st.info("Activity logging will be implemented in a future update")

if __name__ == "__main__":
    # This allows the file to be imported by the login system
    # The login system will call main() when needed
    pass