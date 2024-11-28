import streamlit as st

def login():
    st.title("🔑 Login")
    username = st.text_input("👤 Username", placeholder="Enter your username")
    password = st.text_input("🔒 Password", placeholder="Enter your password", type="password")

    if st.button("Login"):
        if username in st.session_state.users:
            if st.session_state.users[username] == password:
                st.success("✅ Login successful! Redirecting to Chat...")
                st.session_state.logged_in = True
            else:
                st.error("🚫 Incorrect password. Please try again.")
        else:
            st.error("⚠️ Username not found. Please sign up first.")
