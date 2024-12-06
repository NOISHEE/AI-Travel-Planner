import streamlit as st
from fast_api.websearch_normal import search_web
from fast_api.youtube_search import search_youtube

def chat():
    st.title("🌍 Travel Itinerary & Vlogs")

    query = st.text_area("✍️ Enter your travel-related query:", 
                         placeholder="e.g., 'Plan a 5-day itinerary for Paris'")

    if st.button("Generate Itinerary & Video"):
        if query.strip():
            st.write(f"🤔 **Your Query:** {query}")
            st.info("💡 **Generating your travel itinerary...**")

            # Step 1: Fetch General Web Search Results
            itinerary_results = search_web(query=f"Create a detailed travel itinerary: {query}")
            if itinerary_results and "results" in itinerary_results:
                st.success("✅ Your Travel Itinerary:")
                for idx, item in enumerate(itinerary_results["results"], start=1):
                    st.markdown(f"### Day {idx}: {item['title']}")
                    st.write(f"📍 Description: {item.get('content', 'No description available.')}")
                    st.write(f"🌐 **Learn More:** [Link]({item.get('url', '#')})")
                    if "images" in itinerary_results:
                        for img in item.get("images", []):
                            st.image(img["url"], caption=img.get("description", ""))
                    st.markdown("---")
            else:
                st.warning("⚠️ Could not generate a proper itinerary. Please try refining your query.")

            # Step 2: Fetch Related YouTube Video
            st.info("💡 **Searching for a related YouTube video...**")
            video_results = search_youtube(query=f"Best travel vlogs for {query}")
            if video_results and "results" in video_results and len(video_results["results"]) > 0:
                video_url = video_results["results"][0]["url"]
                st.video(video_url)
            else:
                st.warning("🔍 No related YouTube video found for your itinerary.")
        else:
            st.error("⚠️ Please enter a valid query.")
