import streamlit as st
import requests
from dotenv import load_dotenv
import os

load_dotenv()

FASTAPI_URL = os.getenv("FASTAPI_URL")

def chat():
    st.title("🌍 Travel Itinerary & Vlogs")

    query = st.text_area("\u270d\ufe0f Enter your travel-related query:", placeholder="e.g., 'Plan a 5-day itinerary for Paris'")

    if st.button("Generate Full Travel Suggestions"):
        if query.strip():
            st.write(f"🤔 **Your Query:** {query}")

            try:
                response = requests.post(f"{FASTAPI_URL}/generate-itinerary", json={"query": query})
                if response.status_code == 200:
                    data = response.json()

                    # Display itinerary response
                    if "response" in data:
                        st.markdown(data["response"])
                    else:
                        st.warning("⚠️ Could not generate a proper itinerary. Please refine your query.")

                    # Display web search results
                    if "web_results" in data:
                        st.markdown("### Related Web Search")
                        for idx, item in enumerate(data["web_results"], start=1):
                            st.write(f"📍 Description: {item.get('content', 'No description available.')}")
                            st.write(f"🌐 **Learn More:** [Link]({item.get('url', '#')})")
                    else:
                        st.warning("⚠️ No proper web suggestions found.")

                    # Display YouTube video results
                    if "youtube_results" in data and len(data["youtube_results"]) > 0:
                        video_url = data["youtube_results"][0]["url"]
                        st.video(video_url)
                    else:
                        st.warning("🔍 No related YouTube video found.")

                    # PDF download
                    if "pdf" in data:
                        st.info("💾 **Download Your Itinerary as a PDF**")
                        st.download_button(
                            label="📥 Download PDF",
                            data=bytes.fromhex(data["pdf"]),
                            file_name="travel_itinerary.pdf",
                            mime="application/pdf"
                        )
                else:
                    st.error(f"⚠️ Backend Error: {response.json().get('detail', 'Unknown error.')}")
            except requests.exceptions.RequestException as e:
                st.error(f"⚠️ Unable to connect to the server. Error: {e}")
        else:
            st.error("⚠️ Please enter a valid query.")