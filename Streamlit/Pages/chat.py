import streamlit as st

# Set up the Streamlit page
st.set_page_config(
    page_title="Travel Query Input",
    page_icon="🗺️",
    layout="wide",
)

# Helper function for center-aligned text
def center_text(content, heading=False):
    """Display text center-aligned."""
    if heading:
        st.markdown(f"<h2 style='text-align: center;'>{content}</h2>", unsafe_allow_html=True)
    else:
        st.markdown(f"<p style='text-align: center;'>{content}</p>", unsafe_allow_html=True)

# Travel Query Input Page
def travel_query_input():
    center_text("🗺️ Travel Query Input", heading=True)
    center_text(
        "Enter your travel-related question or preference below, and our AI will provide personalized suggestions."
    )
    
    # Travel Query Input Box
    query = st.text_area(
        "What would you like to know?",
        placeholder="e.g., Best things to do in Paris in summer, top activities in Bali, or family-friendly destinations in Europe.",
    )
    
    # Button to process query
    if st.button("Submit Query"):
        if query.strip():
            # Display the user's query and a mock response (can integrate with backend here)
            st.write(f"### Your Query: {query}")
            st.info("Processing your query... (This is where AI-generated responses will appear)")
            # You can add a function call here to retrieve real responses
            # response = process_query(query)
            # st.success(response)
        else:
            st.error("Please enter a valid query.")

# Run the travel query input page
travel_query_input()
