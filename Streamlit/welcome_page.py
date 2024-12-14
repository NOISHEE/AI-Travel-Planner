import streamlit as st
from dotenv import load_dotenv
import os
load_dotenv()

FASTAPI_URL = os.getenv("FASTAPI_URL")


def welcome_page():
    # Set a local image path
    image_path = "/Users/nishitamatlani/Documents/ADS/Final Project/Streamlit/welcome.png"

    # Render the welcome page content with st.image
    st.markdown(
        """
        <div style="text-align: center;">
            <h1 style="color: #4CAF50;">🤖 Welcome to AI Planner</h1>
            <p style="font-size: 18px;">Plan smarter, chat better, and stay productive!</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    # Use st.image to display the local image
    st.image(image_path, caption="Welcome Banner", use_column_width=True)

