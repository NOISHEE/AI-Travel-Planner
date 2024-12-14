import logging
from openai import OpenAI
from dotenv import load_dotenv
import os
import os
import logging
from io import BytesIO
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from fpdf import FPDF
from passlib.context import CryptContext
import nltk
import openai
import requests
import snowflake.connector
from pinecone import Pinecone, ServerlessSpec
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from tavily import TavilyClient

load_dotenv()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Initialize APIs
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
DIMENSION = int(os.getenv("DIMENSION", 512))
METRIC = os.getenv("METRIC", "cosine")
TEXT_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

if not all([PINECONE_API_KEY, PINECONE_ENVIRONMENT, OPENAI_API_KEY, YOUTUBE_API_KEY, TAVILY_API_KEY]):
    logging.error("One or more API keys are missing. Check your .env file.")
    exit(1)

client = OpenAI(api_key=OPENAI_API_KEY)
pc = Pinecone(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
nltk.download("punkt")

# Check if the index exists, and create it if necessary
if TEXT_INDEX_NAME not in pc.list_indexes().names():
    pc.create_index(
        name=TEXT_INDEX_NAME,
        dimension=DIMENSION,
        metric=METRIC,
        spec=ServerlessSpec(cloud='aws', region='us-east-1')  # Adjust cloud and region as needed
    )
    logging.info(f"Index '{TEXT_INDEX_NAME}' created successfully.")
else:
    logging.info(f"Index '{TEXT_INDEX_NAME}' already exists.")

# Connect to the existing index
text_index = pc.Index(TEXT_INDEX_NAME)


def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def get_snowflake_connection():
    user = os.getenv("SNOWFLAKE_USER")
    password = os.getenv("SNOWFLAKE_PASSWORD")
    account = os.getenv("SNOWFLAKE_ACCOUNT")
    database = os.getenv("SNOWFLAKE_DATABASE")
    schema = os.getenv("SNOWFLAKE_SCHEMA")
    warehouse = os.getenv("SNOWFLAKE_WAREHOUSE")

    if not all([user, password, account, database, schema, warehouse]):
        raise HTTPException(status_code=500, detail="One or more Snowflake environment variables are missing")

    return snowflake.connector.connect(
        user=user,
        password=password,
        account=account,
        database=database,
        schema=schema,
        warehouse=warehouse,
    )

def search_web(query, max_results=3):
    payload = {
        "api_key": TAVILY_API_KEY,
        "query": query,
        "max_results": max_results,
        "exclude_domains": ["youtube.com", "vimeo.com"],
        "include_raw_content": True
    }
    try:
        response = requests.post("https://api.tavily.com/search", json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error in web search: {e}")
        return {"error": "Failed to fetch web search results."}

def search_youtube(query, max_results=3):
    try:
        payload = {
            "api_key": TAVILY_API_KEY,
            "query": query,
            "max_results": max_results,
            "include_domains": ["youtube.com"]
        }
        response = requests.post("https://api.tavily.com/search", json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error in YouTube search: {e}")
        return {"error": "Failed to fetch YouTube results."}

def query_pinecone_with_threshold(query_vector, pinecone_index, top_k=5, threshold=0.75):
    """
    Query Pinecone for the top k matches and filter by relevance threshold.
    """
    try:
        result = pinecone_index.query(
            vector=query_vector,
            top_k=top_k,
            include_metadata=True
        )
        logging.info(f"Fetched {len(result['matches'])} matches from Pinecone.")
        
        filtered_matches = [match for match in result['matches'] if match['score'] >= threshold]
        
        if not filtered_matches:
            logging.warning("No matches exceeded the relevance threshold.")
        else:
            logging.info(f"{len(filtered_matches)} matches passed the relevance threshold of {threshold}.")
        return filtered_matches
    except Exception as e:
        logging.error(f"Error querying Pinecone: {e}")
        return []

def generate_response_with_relevant_data(query, relevant_matches):
    """
    Generate a response using only the relevant matches filtered by similarity.
    """
    if not relevant_matches:
        return "Sorry, I couldn't find relevant information for your query. Please try again with more details."

    context = "\n".join([
        f"Text: {match['metadata']['text']} (Source: {match['metadata'].get('title', 'Unknown')})"
        for match in relevant_matches
    ])
    
    messages = [
        {
            "role": "system",
            "content": """
You are an expert travel assistant. Your job is to create detailed, engaging, and personalized travel itineraries for users based on the provided context and query.

When crafting a response:
- Include a well-structured itinerary with clear days and activities.
- Mention must-visit attractions, local landmarks, and hidden gems.
- Suggest the best stores for shopping, including local markets, luxury boutiques, and specialty stores relevant to the destination.
- Recommend restaurants or cafes for meals, including breakfast, lunch, and dinner, highlighting local cuisines.
- Add tips for efficient travel, such as transportation options, best times to visit attractions, and any special considerations (e.g., tickets, attire).
- Include brief cultural insights or unique experiences that enhance the trip.
- Use an engaging, friendly, and professional tone.

If the user asks for an itinerary for a specific duration (e.g., "3 days in Paris"), structure your response by days:
- Day 1: Morning, afternoon, and evening activities.
- Day 2: Repeat with a similar structure.
- Add extra details for each activity (e.g., timings, location, and why it's worth visiting).
            """
        },
        {"role": "user", "content": f"Context:\n{context}\n\nQuery: {query}\n\nProvide a detailed and accurate response."}
    ]

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"Error generating response from GPT: {e}")
        return "Sorry, there was an error generating your response."

def fetch_and_generate_response(query, pinecone_index, top_k=5, threshold=0.75):
    """
    Fetch relevant data from Pinecone and use GPT to craft a response.
    """
    # Generate query vector
    query_vector = embed_query(query)
    if query_vector is None:
        return "Failed to generate embedding for the query."

    # Query Pinecone with threshold
    relevant_matches = query_pinecone_with_threshold(
        query_vector, pinecone_index, top_k=top_k, threshold=threshold
    )

    # Generate and return GPT-based response
    return generate_response_with_relevant_data(query, relevant_matches)

def get_ada_embedding(text):
    """
    Generate embeddings using OpenAI's "text-embedding-ada-002" model.

    Parameters:
        text (str): The input text to generate embeddings for.

    Returns:
        list: A list of floating-point values representing the embedding vector,
              or None if an error occurs during the embedding generation.
    """
    try:
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        embedding = response.data[0].embedding
        logging.info(f"Successfully generated embedding for text of length {len(text)}.")
        return embedding
    except Exception as e:
        logging.error(f"Unexpected error generating ADA embedding: {e}")
    return None


def combined_short_transcripts(transcript, min_length=300):
    consolidated_transcript = []
    current_text = ""
    current_start = None

    for record in transcript:
        if current_start is None:
            current_start = record['start']

        current_text += " " + record['text']

        if len(current_text.strip()) >= min_length:
            consolidated_transcript.append({
                "text": current_text.strip(),
                "start": current_start
            })
            current_text = ""
            current_start = None
    if current_text.strip() and len(current_text.strip()) >= min_length:
        consolidated_transcript.append({
            "text": current_text.strip(),
            "start": current_start
        })

    return consolidated_transcript

def get_channel_videos(channel_username):
    """
    Fetch all video IDs from the given channel username.
    """
    try:
        channel_response = youtube.channels().list(
            part="snippet,contentDetails",
            forUsername=channel_username
        ).execute()

        if "items" not in channel_response or not channel_response["items"]:
            logging.error("Channel not found.")
            return []

        uploads_playlist_id = channel_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        videos = []

        next_page_token = None
        while True:
            playlist_response = youtube.playlistItems().list(
                part="snippet",
                playlistId=uploads_playlist_id,
                maxResults=50,
                pageToken=next_page_token
            ).execute()

            videos.extend([
                {
                    "videoId": item["snippet"]["resourceId"]["videoId"],
                    "title": item["snippet"]["title"]
                } for item in playlist_response["items"]
            ])

            next_page_token = playlist_response.get("nextPageToken")
            if not next_page_token:
                break

        return videos
    except Exception as e:
        logging.error(f"Error fetching channel videos: {e}")
        return []

def get_transcript(video_id, language="en"):
    """
    Fetch YouTube video transcript using the Transcript API.
    """
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[language])
        return transcript
    except Exception as e:
        logging.error(f"Error fetching transcript for video {video_id}: {str(e)}")
        return []

def store_transcript_in_pinecone(transcript, video_id, video_title, pinecone_index):
    """
    Store the transcript into Pinecone with timestamp data.
    Parameters:
        transcript (list): List of transcript segments from YouTube.
        video_id (str): ID of the video.
        video_title (str): Title of the video.
        pinecone_index (Index): The Pinecone index object.
    """
    consolidated_transcript = combined_short_transcripts(transcript)

    for record in consolidated_transcript:
        text = record["text"]
        embedding = get_ada_embedding(text)

        if embedding is None:
            logging.warning(f"Skipping transcript entry at {record['start']}s due to missing embedding.")
            continue

        vector_data = {
            "id": f"{video_id}-{record['start']}",
            "values": embedding,
            "metadata": {
                "video_id": video_id,
                "timestamp": record["start"],
                "text": text,
                "title": video_title
            },
        }

        try:
            pinecone_index.upsert([(vector_data["id"], vector_data["values"], vector_data["metadata"])])
            logging.info(f"Transcript entry at {record['start']}s stored successfully.")
        except Exception as e:
            logging.error(f"Failed to store transcript entry at {record['start']}s: {e}")


def search_youtube_videos(query, max_results=2):
    """
    Search YouTube for videos related to the given query.
    """
    try:
        response = youtube.search().list(
            q=query + ' itinerary',
            part="snippet",
            type="video",
            maxResults=max_results
        ).execute()

        videos = [
            {
                "videoId": item["id"]["videoId"],
                "title": item["snippet"]["title"]
            } for item in response["items"]
        ]
        return videos
    except Exception as e:
        logging.error(f"Error searching YouTube videos: {e}")
        return []

def embed_query(query):
    """
    Generate a vector embedding for the given query using OpenAI's "text-embedding-ada-002" model.

    Parameters:
        query (str): The input text query to be embedded.

    Returns:
        list: A list of floating-point values representing the embedding vector,
              or None if an error occurs during the embedding generation.
    """
    try:
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=query
        )
        embedding = response.data[0].embedding
        logging.info(f"Generated embedding for query: '{query[:30]}...'")
        return embedding
    except Exception as e:
        logging.error(f"Unexpected error generating embedding for query: {e}")
    return None


