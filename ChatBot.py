import streamlit as st
import requests
import json
from datetime import datetime
from difflib import SequenceMatcher

# --- API KEYS ---
HYPERCLOVA_API_KEY = "nv-270db94eb8bf42108110b22f551e655axCwf"
LIBRARY_API_KEY = "70b5336f9e785c681d5ff58906e6416124f80f59faa834164d297dcd8db63036"

# --- Utility Functions ---

def call_hyperclova_api(messages, api_key):
    """Call HyperCLOVA API and return response text."""
    endpoint = "https://clovastudio.stream.ntruss.com/testapp/v1/chat-completions/HCX-003"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "messages": messages,
        "maxTokens": 64,
        "temperature": 0.3,
        "topP": 0.8,
    }
    response = requests.post(endpoint, headers=headers, json=payload)
    if response.status_code == 200:
        result = response.json()
        return result['result']['message']['content']
    else:
        st.error(f"HyperCLOVA API error: {response.status_code}")
        return None

def analyze_prompt_with_hyperclova(prompt, api_key):
    """Ask HyperCLOVA to classify the prompt as 'genre', 'author', or 'other' and extract the relevant value."""
    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert at classifying book search prompts. "
                "Given a user prompt, classify it as either 'genre', 'author', or 'other'. "
                "If it's a genre, return: GENRE:<genre name>. "
                "If it's an author, return: AUTHOR:<author name>. "
                "If neither, return: OTHER."
            )
        },
        {
            "role": "user",
            "content": f"Prompt: {prompt}"
        }
    ]
    result = call_hyperclova_api(messages, api_key)
    if result:
        result = result.strip()
        if result.upper().startswith("GENRE:"):
            return "genre", result[len("GENRE:"):].strip()
        elif result.upper().startswith("AUTHOR:"):
            return "author", result[len("AUTHOR:"):].strip()
        else:
            return "other", None
    return "other", None

def get_books_by_genre(genre, auth_key, page_no=1, page_size=10):
    """Use HyperCLOVA to map genre to DTL KDC code, then fetch books by that code."""
    # For brevity, we use a simple mapping or fallback to the existing KDC extraction logic.
    # In production, use your existing extract_keywords_with_hyperclova logic.
    dtl_kdc_code = None
    dtl_kdc_dict = load_dtl_kdc_json()
    for code, label in dtl_kdc_dict.items():
        if genre.lower() in label.lower():
            dtl_kdc_code = code
            break
    if not dtl_kdc_code:
        # fallback: use first code
        dtl_kdc_code = list(dtl_kdc_dict.keys())[0]
    # Call the Library API for books by DTL KDC code
    url = "http://data4library.kr/api/loanItemSrch"
    params = {
        "authKey": auth_key,
        "startDt": "2000-01-01",
        "endDt": datetime.now().strftime("%Y-%m-%d"),
        "format": "json",
        "pageNo": page_no,
        "pageSize": page_size,
        "dtl_kdc": dtl_kdc_code
    }
    r = requests.get(url, params=params)
    if r.status_code == 200:
        data = r.json()
        docs = data.get("response", {}).get("docs", [])
        books = []
        for doc in docs:
            book_data = doc.get("doc", doc)
            books.append({
                "bookname": book_data.get("bookname", "Unknown Title"),
                "authors": book_data.get("authors", "Unknown Author"),
                "publisher": book_data.get("publisher", "Unknown Publisher"),
                "publication_year": book_data.get("publication_year", "Unknown Year"),
                "isbn13": book_data.get("isbn13", ""),
                "loan_count": int(book_data.get("loan_count", 0)),
                "bookImageURL": book_data.get("bookImageURL", "")
            })
        return books
    return []

def get_books_by_author(author, auth_key, page_no=1, page_size=10):
    """Call Library API to search books by author name."""
    url = "http://data4library.kr/api/srchBooks"
    params = {
        "authKey": auth_key,
        "author": author,
        "format": "json",
        "pageNo": page_no,
        "pageSize": page_size,
        "sort": "loan",
        "order": "desc"
    }
    r = requests.get(url, params=params)
    if r.status_code == 200:
        data = r.json()
        docs = data.get("response", {}).get("docs", [])
        books = []
        for doc in docs:
            books.append({
                "bookname": doc.get("bookname", "Unknown Title"),
                "authors": doc.get("authors", "Unknown Author"),
                "publisher": doc.get("publisher", "Unknown Publisher"),
                "publication_year": doc.get("publication_year", "Unknown Year"),
                "isbn13": doc.get("isbn13", ""),
                "loan_count": int(doc.get("loan_count", 0)),
                "bookImageURL": doc.get("bookImageURL", "")
            })
        return books
    return []

@st.cache_resource
def load_dtl_kdc_json():
    """Load DTL KDC code mapping (replace with your actual mapping file)."""
    # Example minimal mapping for demonstration
    return {
        "813.7": "한국 소설",
        "823": "영미 소설",
        "840": "독일 소설",
        "860": "스페인 소설",
        "880": "일본 소설"
    }

# --- Streamlit UI ---

def display_books(books):
    for book in books:
        st.markdown(f"""
        **{book['bookname']}**
        - Author: {book['authors']}
        - Publisher: {book['publisher']}
        - Year: {book['publication_year']}
        - Loan Count: {book['loan_count']}
        """)
        if book['bookImageURL']:
            st.image(book['bookImageURL'], width=120)

def main():
    st.title("Book Recommendation App")
    st.write("Enter your favorite genre or author. HyperCLOVA will analyze your prompt.")

    user_prompt = st.text_input("Your prompt:")

    if st.button("Search"):
        if not user_prompt:
            st.warning("Please enter a prompt.")
            return
        # Analyze prompt with HyperCLOVA
        kind, value = analyze_prompt_with_hyperclova(user_prompt, HYPERCLOVA_API_KEY)
        st.write(f"Prompt type detected: {kind} ({value})")
        if kind == "genre" and value:
            books = get_books_by_genre(value, LIBRARY_API_KEY, page_no=1, page_size=10)
            if books:
                st.success(f"Showing books for genre: {value}")
                display_books(books)
            else:
                st.error("No books found for this genre.")
        elif kind == "author" and value:
            books = get_books_by_author(value, LIBRARY_API_KEY, page_no=1, page_size=10)
            if books:
                st.success(f"Showing books by author: {value}")
                display_books(books)
            else:
                st.error("No books found for this author.")
        else:
            st.info("Please enter a more specific genre or author name.")

if __name__ == "__main__":
    main()
