import streamlit as st
import requests
from fpdf import FPDF
from dotenv import load_dotenv
import os
import BytesIO

# Load environment variables
load_dotenv()

FASTAPI_URL = os.getenv("FASTAPI_URL")

# Function to make POST request to FastAPI
def call_fastapi_endpoint(endpoint, payload):
    url = f"{FASTAPI_URL}{endpoint}"
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()  # Raise exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Failed to call {endpoint}: {e}")
        return None

def create_pdf_with_unicode(content):
    """
    Generate a well-formatted PDF with Unicode support using Noto Sans font.
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Add the custom Unicode font (ensure the path to the font file is correct)
    pdf.add_font('NotoSans', '', 'noto-sans-v27-latin-regular.ttf', uni=True)

    # Add title to the PDF
    pdf.set_font('NotoSans', size=16)  # Set the custom font for title
    pdf.cell(0, 10, "Your Travel Itinerary", ln=True, align="C")
    pdf.ln(10)  # Add a line break

    # Add the OpenAI-generated response
    pdf.set_font('NotoSans', size=12)  # Set the custom font for content
    paragraphs = content.split("\n\n")
    for paragraph in paragraphs:
        pdf.multi_cell(0, 10, paragraph)
        pdf.ln(5)  # Add spacing between paragraphs

    # Save the PDF to an in-memory BytesIO object
    pdf_stream = BytesIO()
    pdf.output(pdf_stream, dest='F')
    pdf_stream.seek(0)  # Rewind the stream to the beginning
    return pdf_stream

# Main Streamlit App
def chat():
    st.title("🌍 Travel Itinerary & Vlogs")

    # Query input
    query = st.text_area("✍️ Enter your travel-related query:", placeholder="e.g., 'Plan a 5-day itinerary for Paris'")

    if st.button("Generate Full Travel Suggestions"):
        if query.strip():
            st.write(f"🤔 **Your Query:** {query}")
            
            # Step 1: Validate query and generate OpenAI response
            st.info("💡 **Generating your personalized travel itinerary...**")
            response_payload = {"query": query, "top_k": 5, "threshold": 0.75}
            itinerary_response = call_fastapi_endpoint("/generate-openai-response", response_payload)

            if itinerary_response and "response" in itinerary_response:
                st.markdown(itinerary_response["response"])
            else:
                st.warning("⚠️ Could not generate a proper itinerary. Please try refining your query.")

            # Step 2: Fetch web search results
            st.info("🔍 **Fetching additional web suggestions...**")
            search_payload = {"query": f"Create a detailed travel itinerary: {query}", "max_results": 3}
            search_results = call_fastapi_endpoint("/search", search_payload)

            if search_results and "results" in search_results:
                st.markdown("### Related Web Search Results:")
                for idx, item in enumerate(search_results["results"], start=1):
                    st.write(f"**{idx}.** {item.get('title', 'No Title')}")
                    st.write(f"📍 Description: {item.get('content', 'No description available.')}")
                    st.write(f"🌐 **Learn More:** [Link]({item.get('url', '#')})")
                    st.markdown("---")
            else:
                st.warning("⚠️ No proper web suggestions found. Please try refining your query.")

            # Step 3: Fetch related YouTube videos
            st.info("🎥 **Fetching related YouTube videos...**")
            youtube_payload = {"query": f"Best travel vlogs for {query}", "max_results": 3}
            youtube_results = call_fastapi_endpoint("/youtube-search", youtube_payload)

            if youtube_results and "results" in youtube_results and len(youtube_results["results"]) > 0:
                st.markdown("### 🎥 Related YouTube Videos:")
                for idx, video in enumerate(youtube_results["results"], start=1):
                    st.write(f"**{idx}.** {video.get('title', 'No Title')}")
                    st.video(video.get("url", "#"))
                    st.markdown("---")
            else:
                st.warning("🔍 No related YouTube video found for your itinerary.")

                # Step 4: PDF Download Button
            # Step 4: PDF Download Button
            if itinerary_response and "response" in itinerary_response:
                st.info("💾 **Download Your Itinerary as a PDF**")

                # Generate the PDF in-memory
                try:
                    pdf_file = create_pdf_with_unicode(itinerary_response["response"])

                    # Provide the download button
                    st.download_button(
                        label="📥 Download PDF",
                        data=pdf_file,
                        file_name="travel_itinerary.pdf",
                        mime="application/pdf"
                    )
                except Exception as e:
                    st.error(f"⚠️ Failed to generate the PDF. Error: {e}")

if __name__ == "__main__":
    chat()
