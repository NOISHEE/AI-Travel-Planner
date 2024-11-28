import streamlit as st

def sign_up():
    st.title("📝 Sign Up")
    username = st.text_input("👤 Username", placeholder="Enter a unique username")
    password = st.text_input("🔒 Password", placeholder="Choose a strong password", type="password")

    if st.button("Sign Up"):
        if username and password:
            if username in st.session_state.users:
                st.error("🚨 Username already exists. Try another one.")
            else:
                st.session_state.users[username] = password
                st.success("🎉 Sign-up successful! You can now log in.")
        else:
            st.error("⚠️ Please fill in both fields.")
