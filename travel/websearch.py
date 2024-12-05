import requests
import streamlit as st

# Tavily API Base URL
TAVILY_API_URL = "https://api.tavily.com/search"

# Replace with your Tavily API Key
TAVILY_API_KEY = "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"

def search_tavily(query, max_results=5, search_depth="basic", include_answer=False, include_images=False):
    """
    Function to query the Tavily Search API.
    
    Args:
        query (str): The search query.
        max_results (int): Maximum number of results to return (default is 5).
        search_depth (str): Search depth, "basic" or "advanced" (default is "basic").
        include_answer (bool): Whether to include a short answer to the query (default is False).
        include_images (bool): Whether to include query-related images (default is False).
    
    Returns:
        dict: Response data from the Tavily API or an error message.
    """
    payload = {
            "api_key": TAVILY_API_KEY,
            "query": query,
            "topic": "Travel", 
            "max_results": max_results,
            "include_answer": include_answer,
            "include_domains": ["youtube.com", "vimeo.com"],  # Restrict to video platforms
        }

    try:
        response = requests.post(TAVILY_API_URL, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": f"Error: {response.status_code} - {response.json().get('message', 'Unknown error')}"
            }
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {e}"}
