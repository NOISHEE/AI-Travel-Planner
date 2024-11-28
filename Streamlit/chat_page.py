import streamlit as st

def chat():
    st.title("💬 Chat with AI")
    query = st.text_area("✍️ Type your question here:", placeholder="e.g., What's the best way to manage my tasks?")
    if st.button("Submit"):
        if query.strip():
            st.write(f"🤔 **Your Question:** {query}")
            st.info("💡 **AI Response:** (Response will be generated here)")
        else:
            st.error("⚠️ Please enter a valid question.")
