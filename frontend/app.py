import streamlit as st
import requests
from pages.welcome_page import welcome_page
from pages.signup_page import sign_up
from pages.login_page import login

FASTAPI_URL = "http://127.0.0.1:8000"  # Replace with your FastAPI server URL

# Set the page configuration ONCE at the top of app.py
st.set_page_config(page_title="AI Planner", page_icon="🤖", layout="wide")

# Initialize session state variables
if "page" not in st.session_state:
    st.session_state.page = "Welcome"
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "users" not in st.session_state:
    st.session_state.users = {}
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # Store chat messages

# Sidebar navigation
st.sidebar.title("🚀 Navigation")
selected_page = st.sidebar.radio(
    "Go to:",
    ["🏠 Welcome", "🔑 Login", "📝 Sign Up", "💬 Chat"],
    index=["Welcome", "Login", "Sign Up", "Chat"].index(st.session_state.page)
)

# Update the current page based on sidebar selection
if selected_page.startswith("🏠"):
    st.session_state.page = "Welcome"
elif selected_page.startswith("🔑"):
    st.session_state.page = "Login"
elif selected_page.startswith("📝"):
    st.session_state.page = "Sign Up"
elif selected_page.startswith("💬"):
    if not st.session_state.logged_in:
        st.sidebar.warning("🔒 Please log in to access Chat.")
        st.session_state.page = "Login"
    else:
        st.session_state.page = "Chat"

# Chat page function
def chat():
    st.title("💬 Chat with AI Planner")
    st.write("Start planning your itinerary! Ask me anything about travel destinations.")

    # Chat input
    user_query = st.text_input("Your question", key="user_query")

    if user_query:
        try:
            # Make a request to the FastAPI generate-itinerary endpoint
            response = requests.post(f"{FASTAPI_URL}/generate-itinerary", json={"query": user_query})

            if response.status_code == 200:
                data = response.json()
                ai_response = data.get("response", "No response available.")
                web_results = data.get("web_results", [])
                youtube_results = data.get("youtube_results", [])

                # Save the chat to history
                st.session_state.chat_history.append({"user": user_query, "ai": ai_response})

                # Display chat history
                for message in st.session_state.chat_history:
                    st.write(f"**You**: {message['user']}")
                    st.write(f"**AI Planner**: {message['ai']}")

                # Display web and YouTube results
                if web_results:
                    st.write("### 🌐 Web Results")
                    for result in web_results:
                        st.write(f"- [{result['title']}]({result['url']})")

                if youtube_results:
                    st.write("### 📹 YouTube Results")
                    for video in youtube_results:
                        st.write(f"- [{video['title']}]({video['url']})")
            elif response.status_code == 500:
                st.error("⚠️ Itinerary generation failed. Please try again.")
            else:
                st.error(f"⚠️ Unexpected error: {response.json().get('detail', 'Something went wrong.')}")
        except requests.exceptions.RequestException as e:
            st.error(f"⚠️ Unable to connect to the server. Error: {e}")

    # Clear chat button
    if st.button("Clear Chat"):
        st.session_state.chat_history = []

# Page routing logic
if st.session_state.page == "Welcome":
    welcome_page()
elif st.session_state.page == "Sign Up":
    sign_up()
elif st.session_state.page == "Login":
    login()
elif st.session_state.page == "Chat":
    chat()
