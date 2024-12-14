import streamlit as st
import requests
from dotenv import load_dotenv
import os
from openai import OpenAI

load_dotenv()

FASTAPI_URL = os.getenv("FASTAPI_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

def is_travel_related_gpt(query):
    """
    Uses OpenAI's GPT model to determine if the query is travel-related.
    """

    messages = [
        {"role": "system", "content": "You are an assistant that determines if a query is related to travel."},
        {"role": "user", "content": f"Is the following query related to travel? Respond with 'Yes' or 'No' only.\n\nQuery: {query}"}
    ]
        
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    answer = response.choices[0].message.content
    return answer == "yes"

def chat():
    st.title("🌍 Travel Itinerary & Vlogs")

    # Query input
    query = st.text_area("✍️ Enter your travel-related query:", 
                         placeholder="e.g., 'Plan a 5-day itinerary for Paris'")

    # Button: Generate everything (OpenAI response, web suggestions, YouTube videos)
    if st.button("Generate Full Travel Suggestions"):
        if query.strip():
            st.write(f"🤔 **Your Query:** {query}")
            
            # Step 1: Check if the query is travel-related
            if not is_travel_related_gpt(query):
                st.error("❌ This query doesn't seem travel-related. Please try again with a travel-focused query.")
                return

            # Step 2: Generate Itinerary using Pinecone and GPT
            st.info("💡 **Generating your personalized travel itinerary...**")
            response = fetch_and_generate_response(query, top_k=5, threshold=0.75)
            if response:
                st.markdown(response)
            else:
                st.warning("⚠️ Could not generate a proper itinerary. Please try refining your query.")

            # Step 3: Fetch General Web Search Results
            itinerary_results = search_web(query=f"Create a detailed travel itinerary: {query}")
            if itinerary_results and "results" in itinerary_results:
                for idx, item in enumerate(itinerary_results["results"], start=1):
                    st.markdown(f"### Here is your related web search in case you want anymore information about the place")
                    st.write(f"📍 Description: {item.get('content', 'No description available.')}")
                    st.write(f"🌐 **Learn More:** [Link]({item.get('url', '#')})")
                    if "images" in itinerary_results:
                        for img in item.get("images", []):
                            st.image(img["url"], caption=img.get("description", ""))
                    st.markdown("---")
            else:
                st.warning("⚠️ No proper web suggestions found. Please try refining your query.")

            # Step 4: Fetch Related YouTube Video
            video_results = search_youtube(query=f"Best travel vlogs for {query}")
            if video_results and "results" in video_results and len(video_results["results"]) > 0:
                video_url = video_results["results"][0]["url"]
                st.video(video_url)
            else:
                st.warning("🔍 No related YouTube video found for your itinerary.")

            # Step 5: PDF Download Button
            if response:
                st.info("💾 **Download Your Itinerary as a PDF**")

                # Create the PDF content for only OpenAI response
                pdf = FPDF()
                pdf.set_auto_page_break(auto=True, margin=15)
                pdf.add_page()
                pdf.set_font("Arial", size=12)

                # Add only the OpenAI response content to the PDF
                pdf.multi_cell(0, 10, response.encode('latin-1', 'replace').decode('latin-1'))

                # Save the PDF as a virtual file
                pdf_file = "travel_itinerary.pdf"
                pdf.output(pdf_file)

                # Allow download without clearing the page
                with open(pdf_file, "rb") as file:
                    st.download_button(
                        label="📥 Download PDF",
                        data=file,
                        file_name=pdf_file,
                        mime="application/pdf"
                    )
        else:
            st.error("⚠️ Please enter a valid query.")

# Run the app
if __name__ == "__main__":
    chat()