import os
import logging
import requests
import nltk
from dotenv import load_dotenv
from io import BytesIO
from fastapi import FastAPI, HTTPException, Depends, Form
from pydantic import BaseModel
from fpdf import FPDF
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from passlib.context import CryptContext
import openai
from pinecone import Pinecone, ServerlessSpec
import snowflake.connector

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Initialize APIs
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

if not all([PINECONE_API_KEY, PINECONE_ENVIRONMENT, OPENAI_API_KEY, YOUTUBE_API_KEY, TAVILY_API_KEY]):
    logging.error("One or more API keys are missing. Check your .env file.")
    exit(1)

openai.api_key = OPENAI_API_KEY
pc = Pinecone(api_key=PINECONE_API_KEY)
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
nltk.download("punkt")

# FastAPI app
app = FastAPI()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class SignupModel(BaseModel):
    username: str
    password: str

class LoginModel(BaseModel):
    username: str
    password: str

class ItineraryRequest(BaseModel):
    query: str

class PDFGenerator:
    @staticmethod
    def generate_pdf(content):
        pdf_file = BytesIO()
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, content)
        pdf.output(pdf_file)
        pdf_file.seek(0)
        return pdf_file.getvalue().hex()

# Utility functions
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

def fetch_and_generate_response(query, top_k=5, threshold=0.75):
    try:
        embedding = openai.Embedding.create(
            input=query, model="text-embedding-ada-002"
        )['data'][0]['embedding']

        if "youtube-query-index" not in pc.list_indexes().names():
            pc.create_index(
                name="youtube-query-index",
                dimension=1536,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-west-2")
            )

        index = pc.Index("youtube-query-index")
        results = index.query(vector=embedding, top_k=top_k, include_metadata=True)
        filtered_matches = [
            match for match in results.get("matches", []) if match.get("score", 0) >= threshold
        ]

        if not filtered_matches:
            return "No relevant data found."

        context = "\n".join([
            f"Text: {match['metadata']['text']} (Source: {match['metadata'].get('title', 'Unknown')})"
            for match in filtered_matches
        ])

        messages = [
            {"role": "system", "content": "Provide detailed travel itineraries."},
            {"role": "user", "content": f"Context:\n{context}\nQuery: {query}"}
        ]

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages
        )['choices'][0]['message']['content']
        return response
    except Exception as e:
        logging.error(f"Error in generating response: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate itinerary response.")

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

@app.post("/signup")
async def signup(username: str, password: str, conn=Depends(get_snowflake_connection)):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Username already taken")

        hashed_password = hash_password(password)
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
            (username, hashed_password),
        )
        conn.commit()
        return {"message": "User signed up successfully"}
    except Exception as e:
        logging.error(f"Error during signup: {e}")
        raise HTTPException(status_code=500, detail="Signup failed.")
    finally:
        cursor.close()
        conn.close()

@app.post("/login")
async def login(username: str, password: str, conn=Depends(get_snowflake_connection)):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM users WHERE username = %s", (username,))
        result = cursor.fetchone()
        if not result or not verify_password(password, result[0]):
            raise HTTPException(status_code=401, detail="Invalid username or password")
        return {"message": "Login successful"}
    except Exception as e:
        logging.error(f"Error during login: {e}")
        raise HTTPException(status_code=500, detail="Login failed.")
    finally:
        cursor.close()
        conn.close()

@app.post("/generate-itinerary")
async def generate_itinerary(request: ItineraryRequest):
    try:
        ai_response = fetch_and_generate_response(request.query)
        web_results = search_web(request.query)
        youtube_results = search_youtube(request.query)

        # pdf_content = PDFGenerator.generate_pdf(ai_response)

        return {
            "response": ai_response,
            "web_results": web_results.get("results", []),
            "youtube_results": youtube_results.get("results", []),
            # "pdf": pdf_content
        }
    except Exception as e:
        logging.error(f"Error in generating itinerary: {e}")
        raise HTTPException(status_code=500, detail="Itinerary generation failed.")

@app.get("/")
async def root():
    return {"message": "Welcome to the Travel API!"}
