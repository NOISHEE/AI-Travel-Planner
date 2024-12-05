import streamlit as st
import sys

sys.path.append("..")
from travel import websearch

def chat():
    st.title("💬 Chat with AI (Travel Expert)")
    query = st.text_area("✍️ Type your travel-related question here:", placeholder="e.g., Best travel vlogs for Europe?")
    
    if st.button("Submit"):
        if query.strip():
            st.write(f"🤔 **Your Question:** {query}")
            st.info("💡 **Fetching AI Response...**")
 
            # Call the Tavily API for the query
            results = websearch.search_tavily(query=query, max_results=5)
            
            if results and "results" in results:
                st.success(f"🌐 Found {len(results['results'])} related travel videos:")
                for idx, item in enumerate(results["results"], start=1):
                    st.markdown(f"### {idx}. {item['title']}")
                    st.write(f"**URL:** [Watch Video]({item.get('url', '#')})")
                    st.write(f"**Description:** {item.get('content', 'No description available.')}")
                    st.markdown("---")
            elif "error" in results:
                st.error(f"⚠️ Error: {results['error']}")
            else:
                st.warning("No results found. Please refine your query.")
        else:
            st.error("⚠️ Please enter a valid question.")
