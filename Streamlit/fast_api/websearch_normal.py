import requests
from bs4 import BeautifulSoup

# Tavily API configurations
TAVILY_API_URL = "https://api.tavily.com/search"
TAVILY_API_KEY = "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"  # Replace with your API Key

def search_web(query, max_results=1):
    """
    Query Tavily API for web search results.
    """
    payload = {
        "api_key": TAVILY_API_KEY,
        "query": query,
        "max_results": max_results,
        "exclude_domains": ["youtube.com", "vimeo.com"],
        "include_raw_content": True,
    }

    response = requests.post(TAVILY_API_URL, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": f"Error: {response.status_code} - {response.json().get('message', 'Unknown error')}"}


def extract_content(url):
    """
    Extracts main content from a web page using BeautifulSoup.
    """
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            paragraphs = soup.find_all("p")  # Extract paragraphs
            content = "\n".join(p.text for p in paragraphs if p.text.strip())
            return content
        else:
            return f"Failed to extract content. HTTP Status: {response.status_code}"
    except Exception as e:
        return f"Error occurred while scraping: {e}"


def format_itinerary(content, query):
    """
    Formats the raw content into a structured response.
    """
    # Basic formatting for readability
    itinerary = f"For your query '{query}', here's the extracted information:\n\n"
    paragraphs = content.split("\n")
    for idx, para in enumerate(paragraphs[:5], start=1):  # Include the first 5 paragraphs
        itinerary += f"- **Day {idx}**: {para.strip()}\n"
    itinerary += "\nFor more details, check the source link provided."
    return itinerary


def generate_response(query):
    """
    Full pipeline: Search web, extract content, and format the response.
    """
    # Step 1: Search the web using Tavily
    search_results = search_web(query=query, max_results=1)
    if "error" in search_results:
        return f"Error with Tavily API: {search_results['error']}"

    # Step 2: Extract content from the first result
    if "results" in search_results and len(search_results["results"]) > 0:
        first_result = search_results["results"][0]
        url = first_result.get("url")
        title = first_result.get("title")
        extracted_content = extract_content(url)

        # Step 3: Format the response
        if extracted_content:
            formatted_response = format_itinerary(extracted_content, query)
            return f"**{title}**\n\n{formatted_response}"
        else:
            return "Failed to extract content from the webpage."
    else:
        return "No relevant results found for the query."


# Example Usage
if __name__ == "__main__":
    user_query = "5-day itinerary for Paris"
    final_response = generate_response(user_query)
    print(final_response)
