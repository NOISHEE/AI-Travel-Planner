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
from utils import (
    pc,
    hash_password,
    verify_password,
    get_snowflake_connection,
    query_pinecone_with_threshold,
    fetch_and_generate_response,
    embed_query,
    get_channel_videos,
    get_transcript,
    store_transcript_in_pinecone,
    search_youtube_videos,
    get_ada_embedding,
    search_web,
    search_youtube,
    TEXT_INDEX_NAME,  # Newly added import
)

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# FastAPI app
app = FastAPI()

class SignupModel(BaseModel):
    username: str
    password: str

class LoginModel(BaseModel):
    username: str
    password: str

class ItineraryRequest(BaseModel):
    query: str

# -------- Endpoints --------

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

import base64

# Changes in main.py

# 1. Import TEXT_INDEX_NAME from utils
from utils import (
    pc,
    hash_password,
    verify_password,
    get_snowflake_connection,
    query_pinecone_with_threshold,
    fetch_and_generate_response,
    embed_query,
    get_channel_videos,
    get_transcript,
    store_transcript_in_pinecone,
    search_youtube_videos,
    get_ada_embedding,
    search_web,
    search_youtube,
    TEXT_INDEX_NAME,  # Newly added import
)

# 2. Update the generate_itinerary function to use TEXT_INDEX_NAME from utils and remove redundant checks
@app.post("/generate-itinerary")
async def generate_itinerary(request: ItineraryRequest):
    try:
        # Use the TEXT_INDEX_NAME directly from utils instead of re-fetching from environment
        pinecone_index = pc.Index(TEXT_INDEX_NAME)  # Create Pinecone index object

        # Generate the AI response
        ai_response = fetch_and_generate_response(request.query, pinecone_index)
        web_results = search_web(request.query)
        youtube_results = search_youtube(request.query)

        # Return the response
        return {
            "response": ai_response,
            "web_results": web_results.get("results", []),
            "youtube_results": youtube_results.get("results", []),
        }
    except Exception as e:
        logging.error(f"Error in generating itinerary: {e}")
        raise HTTPException(status_code=500, detail="Itinerary generation failed.")

@app.get("/")
async def root():
    return {"message": "Welcome to the Travel API!"}
