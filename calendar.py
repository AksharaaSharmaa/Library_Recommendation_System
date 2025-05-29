import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def get_user_library_collection():
    """Get user library collection from MongoDB"""
    client = st.session_state.db_client
    db = client["Login_Credentials"]
    return db["user_libraries"]

def get_reading_schedule_collection():
    """Get reading schedule collection from MongoDB"""
    client = st.session_state.db_client
    db = client["Login_Credentials"]
    return db["reading_schedules"]

def get_liked_books(username):
    """Fetch liked books from MongoDB"""
    user_library = get_user_library_collection()
    doc = user_library.find_one({"username": username})
    return doc.get("liked_books", []) if doc else []

def save_reading_schedule(username, schedule_data):
    """Save reading schedule to MongoDB"""
    schedule_collection = get_reading_schedule_collection()
    schedule_collection.update_one(
        {"username": username},
        {"$set": {
            "username": username,
            "schedule": schedule_data,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }},
        upsert=True
    )

def get_reading_schedule(username):
    """Get reading schedule from MongoDB"""
    schedule_collection = get_reading_schedule_collection()
    doc = schedule_collection.find_one({"username": username})
    return doc.get("schedule", []) if doc else []

def generate_reading_schedule_with_ai(books, daily_hours, total_days, api_key):
    """Generate reading schedule using HyperCLOVA API"""
    # This would call your HyperCLOVA API
    # For now, returning a basic schedule structure
    schedule = []
    days_per_book = max(1, total_days // len(books)) if books else 1
    
    for i, book in enumerate(books):
        start_day = i * days_per_book
        end_day = min((i + 1) * days_per_book - 1, total_days - 1)
        
        schedule.append({
            "book": book,
            "start_date": datetime.now() + timedelta(days=start_day),
            "end_date": datetime.now() + timedelta(days=end_day),
            "daily_hours": daily_hours,
            "status": "To Read",
            "progress": 0,
            "notes": ""
        })
    
    return schedule

def display_calendar_view(schedule):
    """Display calendar view of reading schedule"""
    st.subheader("📅 Reading Calendar")
    
    if not schedule:
        st.info("No reading schedule created yet. Create one below!")
        return
    
    # Create a DataFrame for calendar visualization
    cal_data = []
    for item in schedule:
        current_date = item["start_date"]
        while current_date <= item["end_date"]:
            cal_data.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "book": item["book"].get("bookname", "Unknown Title"),
                "hours": item["daily_hours"],
                "status": item["status"]
            })
            current_date += timedelta(days=1)
    
    if cal_data:
        df = pd.DataFrame(cal_data)
        
        # Create a heatmap-style calendar
        fig = px.scatter(df, 
                        x="date", 
                        y="book", 
                        size="hours",
                        color="status",
                        hover_data=["hours"],
                        title="Reading Schedule Calendar")
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

def display_progress_dashboard(schedule):
    """Display reading progress dashboard"""
    st.subheader("📈 Reading Progress Dashboard")
    
    if not schedule:
        return
    
    # Calculate statistics
    total_books = len(schedule)
    completed_books = len([s for s in schedule if s["status"] == "Finished"])
    in_progress_books = len([s for s in schedule if s["status"] == "Reading"])
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Books", total_books)
    with col2:
        st.metric("Completed", completed_books)
    with col3:
        st.metric("In Progress", in_progress_books)
    
    # Progress chart
    if total_books > 0:
        status_counts = {"To Read": 0, "Reading": 0, "Finished": 0}
        for item in schedule:
            status_counts[item["status"]] += 1
        
        fig = px.pie(values=list(status_counts.values()), 
                    names=list(status_counts.keys()),
                    title="Reading Status Distribution")
        st.plotly_chart(fig, use_container_width=True)

def display_book_timeline(schedule):
    """Display book timeline/Gantt chart"""
    st.subheader("📖 Book Reading Timeline")
    
    if not schedule:
        return
    
    # Create Gantt chart data
    gantt_data = []
    for i, item in enumerate(schedule):
        book_title = item["book"].get("bookname", f"Book {i+1}")
        gantt_data.append({
            "Task": book_title,
            "Start": item["start_date"],
            "Finish": item["end_date"],
            "Status": item["status"]
        })
    
    if gantt_data:
        df_gantt = pd.DataFrame(gantt_data)
        
        # Create timeline chart
        fig = px.timeline(df_gantt, 
                         x_start="Start", 
                         x_end="Finish", 
                         y="Task",
                         color="Status",
                         title="Reading Timeline")
        
        fig.update_yaxes(categoryorder="total ascending")
        st.plotly_chart(fig, use_container_width=True)

def main():
    """Main calendar application function"""
    st.title("📅 My Reading Schedule")
    st.markdown("Plan and track your reading journey with your favorite books!")
    
    # Check if user is logged in
    if not hasattr(st.session_state, 'username') or not st.session_state.username:
        st.error("Please log in to access your reading schedule.")
        return
    
    username = st.session_state.username
    
    # Initialize session state for calendar
    if "reading_schedule" not in st.session_state:
        st.session_state.reading_schedule = get_reading_schedule(username)
    
    # Sidebar navigation
    with st.sidebar:
        st.subheader("Navigation")
        page = st.selectbox("Choose a view:", 
                           ["Schedule Creator", "Calendar View", "Progress Dashboard", "Timeline View"])
    
    if page == "Schedule Creator":
        st.header("Create Your Reading Schedule")
        
        # Get liked books
        liked_books = get_liked_books(username)
        
        if not liked_books:
            st.warning("You don't have any liked books yet. Please add some books to your library first!")
            if st.button("Go to Book Discovery"):
                st.session_state.app_stage = "welcome"
                st.rerun()
            return
        
        st.subheader("Your Liked Books:")
        
        # Display liked books with selection
        selected_books = []
        for i, book in enumerate(liked_books):
            col1, col2 = st.columns([1, 4])
            
            with col1:
                if st.checkbox(f"Select", key=f"book_select_{i}"):
                    selected_books.append(book)
            
            with col2:
                title = book.get('bookname', 'Unknown Title')
                author = book.get('authors', 'Unknown Author')
                st.write(f"**{title}** by {author}")
        
        if selected_books:
            st.subheader("Schedule Settings")
            
            col1, col2 = st.columns(2)
            with col1:
                daily_hours = st.number_input("Hours per day:", min_value=0.5, max_value=12.0, value=1.0, step=0.5)
            
            with col2:
                total_days = st.number_input("Total days:", min_value=1, max_value=365, value=30)
            
            if st.button("Generate Reading Schedule"):
                # Generate schedule
                schedule = generate_reading_schedule_with_ai(
                    selected_books, 
                    daily_hours, 
                    total_days, 
                    st.session_state.get("api_key")
                )
                
                # Save to database
                save_reading_schedule(username, schedule)
                st.session_state.reading_schedule = schedule
                
                st.success(f"Reading schedule created for {len(selected_books)} books over {total_days} days!")
                st.rerun()
    
    elif page == "Calendar View":
        display_calendar_view(st.session_state.reading_schedule)
    
    elif page == "Progress Dashboard":
        display_progress_dashboard(st.session_state.reading_schedule)
    
    elif page == "Timeline View":
        display_book_timeline(st.session_state.reading_schedule)
    
    # Display current schedule
    if st.session_state.reading_schedule:
        st.subheader("Current Reading Schedule")
        
        for i, item in enumerate(st.session_state.reading_schedule):
            with st.expander(f"📖 {item['book'].get('bookname', 'Unknown Title')}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Start Date:** {item['start_date'].strftime('%Y-%m-%d')}")
                    st.write(f"**End Date:** {item['end_date'].strftime('%Y-%m-%d')}")
                    st.write(f"**Daily Hours:** {item['daily_hours']}")
                
                with col2:
                    # Status update
                    new_status = st.selectbox(
                        "Status:", 
                        ["To Read", "Reading", "Finished"],
                        index=["To Read", "Reading", "Finished"].index(item["status"]),
                        key=f"status_{i}"
                    )
                    
                    # Progress slider
                    progress = st.slider(
                        "Progress %:", 
                        0, 100, 
                        item["progress"],
                        key=f"progress_{i}"
                    )
                    
                    # Notes
                    notes = st.text_area(
                        "Notes:", 
                        item["notes"],
                        key=f"notes_{i}"
                    )
                
                # Update button
                if st.button(f"Update", key=f"update_{i}"):
                    st.session_state.reading_schedule[i]["status"] = new_status
                    st.session_state.reading_schedule[i]["progress"] = progress
                    st.session_state.reading_schedule[i]["notes"] = notes
                    
                    # Save to database
                    save_reading_schedule(username, st.session_state.reading_schedule)
                    st.success("Schedule updated!")
                    st.rerun()

if __name__ == "__main__":
    main()
