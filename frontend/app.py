import streamlit as st
from pages.welcome_page import welcome_page
from pages.signup_page import sign_up
from pages.login_page import login
from pages.chat_page import chat

# Set the page configuration ONCE at the top of app.py
st.set_page_config(page_title="AI Planner", page_icon="🤖", layout="wide")

# Initialize session state variables
if "page" not in st.session_state:
    st.session_state.page = "Welcome"
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "users" not in st.session_state:
    st.session_state.users = {}

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

# Page routing logic
if st.session_state.page == "Welcome":
    welcome_page()
elif st.session_state.page == "Sign Up":
    sign_up()
elif st.session_state.page == "Login":
    login()
elif st.session_state.page == "Chat":
    chat()
