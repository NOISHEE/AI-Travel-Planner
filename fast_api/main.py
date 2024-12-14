from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import snowflake.connector
from passlib.context import CryptContext
import os
from fastapi import Form
from websearch_normal import search_web, generate_response
from youtube_search import search_youtube
from openai_response import is_travel_related_gpt, fetch_and_generate_response, generate_response_with_relevant_data



# FastAPI app
app = FastAPI()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Snowflake connection details (update with your credentials)
SNOWFLAKE_USER = "vicksInhaler"
SNOWFLAKE_PASSWORD = "vicksInhaler@123"
SNOWFLAKE_ACCOUNT = "vt67315.us-east-2.aws"
SNOWFLAKE_DATABASE = "ADS_TRAVEL"
SNOWFLAKE_SCHEMA = "PUBLIC"
SNOWFLAKE_WAREHOUSE = "COMPUTE_WH"

def get_snowflake_connection():
    return snowflake.connector.connect(
        user=SNOWFLAKE_USER,
        password=SNOWFLAKE_PASSWORD,
        account=SNOWFLAKE_ACCOUNT,
        database=SNOWFLAKE_DATABASE,
        schema=SNOWFLAKE_SCHEMA,
        warehouse=SNOWFLAKE_WAREHOUSE
    )

class SignupModel(BaseModel):
    username: str
    password: str

class LoginModel(BaseModel):
    username: str
    password: str

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

@app.post("/signup")
async def signup(username: str, password: str):
    conn = get_snowflake_connection()
    try:
        cursor = conn.cursor()
        # Check if username already exists
        cursor.execute("SELECT username FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Username already taken")

        # Insert the new user
        hashed_password = hash_password(password)
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
            (username, hashed_password),
        )
        conn.commit()
        return {"message": "User signed up successfully"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@app.post("/login")
async def login(username: str, password: str):
    conn = get_snowflake_connection()
    try:
        cursor = conn.cursor()
        # Check if the user exists
        cursor.execute("SELECT password_hash FROM users WHERE username = %s", (username,))
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=401, detail="Invalid username or password")

        # Verify the password
        stored_password_hash = result[0]
        if not verify_password(password, stored_password_hash):
            raise HTTPException(status_code=401, detail="Invalid username or password")

        return {"message": "Login successful"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

## --- websearch----
# Request model for search_web endpoint
class SearchRequest(BaseModel):
    query: str
    max_results: int = 1  # Default to 1 result

# Endpoint for the search_web function
@app.post("/search")
async def search(request: SearchRequest):
    try:
        results = search_web(query=request.query, max_results=request.max_results)
        if "error" in results:
            raise HTTPException(status_code=400, detail=results["error"])
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Request model for generate_response endpoint
class GenerateRequest(BaseModel):
    query: str

# Endpoint for the generate_response function
@app.post("/generate-response")
async def generate(request: GenerateRequest):
    try:
        response = generate_response(query=request.query)
        if response.startswith("Error"):
            raise HTTPException(status_code=400, detail=response)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# ------youtube search --------
# Request model for the YouTube search endpoint
class YouTubeSearchRequest(BaseModel):
    query: str
    max_results: int = 1  # Default to 1 result

# Endpoint for the YouTube search function
@app.post("/youtube-search")
async def youtube_search(request: YouTubeSearchRequest):
    try:
        results = search_youtube(query=request.query, max_results=request.max_results)
        if "error" in results:
            raise HTTPException(status_code=400, detail=results["error"])
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------Open ai response ------
# Request model for the OpenAI response generation
class GenerateResponseRequest(BaseModel):
    query: str
    top_k: int = 5
    threshold: float = 0.75

# Endpoint to validate if a query is travel-related
@app.post("/validate-query")
async def validate_query(query: str):
    try:
        is_travel_related = is_travel_related_gpt(query)
        return {"is_travel_related": is_travel_related}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error validating query: {e}")

# Endpoint to fetch and generate a detailed response
@app.post("/generate-openai-response")
async def generate_openai_response(request: GenerateResponseRequest):
    try:
        # Validate if the query is travel-related
        is_travel_related = is_travel_related_gpt(request.query)
        if not is_travel_related:
            raise HTTPException(
                status_code=400, 
                detail="This query doesn't seem travel-related. Please try with a travel-focused query."
            )
        
        # Fetch relevant matches from Pinecone (use request.top_k and request.threshold)
        # Mock Pinecone results for demonstration
        relevant_matches = [
            {"metadata": {"text": "Visit the Eiffel Tower and the Louvre Museum.", "title": "Paris Highlights"}},
            {"metadata": {"text": "Enjoy a Seine River Cruise and explore Montmartre.", "title": "Romantic Paris"}},
        ]

        # Generate the response using OpenAI
        response = generate_response_with_relevant_data(request.query, relevant_matches)
        return {"response": response}
    except HTTPException as http_err:
        # Log and re-raise HTTP exceptions
        logging.error(f"HTTP Error: {http_err.detail}")
        raise http_err
    except Exception as e:
        # Handle other exceptions gracefully
        logging.error(f"Internal Server Error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred while processing your request.")

