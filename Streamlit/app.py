import streamlit as st

# Set up the Streamlit page
st.set_page_config(
    page_title="AI Travel Planner",
    page_icon="🌍",
    layout="wide",
)

# Helper function for center-aligned text
def center_text(content, heading=False):
    """Display text center-aligned."""
    if heading:
        st.markdown(f"<h2 style='text-align: center;'>{content}</h2>", unsafe_allow_html=True)
    else:
        st.markdown(f"<p style='text-align: center;'>{content}</p>", unsafe_allow_html=True)

# Login Page
def login_page():
    center_text("🔐 Login to AI Travel Planner", heading=True)
    center_text("Please log in to access the app's features.")
    
    # Input fields for username and password
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    # Hardcoded credentials for simplicity
    valid_credentials = {"user1": "password123", "admin": "admin123"}

    # Login button
    if st.button("Login"):
        if username in valid_credentials and valid_credentials[username] == password:
            st.success("Login successful!")
            st.session_state.logged_in = True
            st.session_state.page = "Welcome"
        else:
            st.error("Invalid username or password.")

# Welcome Page
def welcome_page():
    center_text("🌍 AI-Powered Travel Planner", heading=True)
    center_text(
        "Plan your next trip with ease! Our AI-powered app provides personalized itineraries, "
        "recommendations, and real-time travel updates based on your preferences."
    )
    center_text(
        "By integrating data from YouTube videos, blogs, and the web, we help you discover "
        "destinations tailored to your interests and needs. Whether it's finding the best activities, "
        "accommodations, or safety tips, this app has you covered!"
    )
    
    # Navigation to profile setup
    col1, col2, col3 = st.columns([3, 1, 3])
    with col2:
        if st.button("Get Started"):
            st.session_state.page = "Profile Setup"

# User Profile Setup
def profile_setup():
    center_text("✈️ Tell Us About Your Travel Preferences", heading=True)
    center_text("Fill in the details below to help us tailor your travel experience.")
    
    with st.form(key="profile_form"):
        name = st.text_input("What’s your name?", placeholder="John Doe")
        destination = st.text_input("Your dream destination", placeholder="e.g., Paris, Tokyo")
        budget = st.selectbox("What’s your budget range?", ["Low", "Medium", "High"])
        activities = st.multiselect(
            "What activities do you enjoy?",
            ["Sightseeing", "Adventure", "Relaxation", "Shopping", "Cultural Experiences"]
        )
        submit_button = st.form_submit_button(label="Save Preferences")
    
    if submit_button:
        st.success("Your preferences have been saved!")
        # Save user data in session state
        st.session_state.user_data = {
            "name": name,
            "destination": destination,
            "budget": budget,
            "activities": activities,
        }
        st.session_state.page = "Travel Query"

# Travel Query Input
def travel_query_input():
    center_text("🗺️ Travel Query Input", heading=True)
    center_text("Ask your travel-related questions below:")

    query = st.text_area(
        "What would you like to know?",
        placeholder="e.g., Best things to do in Paris in summer."
    )
    
    if st.button("Submit Query"):
        if query.strip():
            st.write(f"### Your Query: {query}")
            st.info("Processing your query... (AI response will appear here)")
        else:
            st.error("Please enter a valid query.")

    # Logout option in the sidebar
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.page = "Login"

# App Navigation
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "page" not in st.session_state:
    st.session_state.page = "Login"

if st.session_state.page == "Login":
    login_page()
elif st.session_state.logged_in:
    if st.session_state.page == "Welcome":
        welcome_page()
    elif st.session_state.page == "Profile Setup":
        profile_setup()
    elif st.session_state.page == "Travel Query":
        travel_query_input()
else:
    st.warning("You need to log in to access the app.")
    login_page()
