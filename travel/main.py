from travel import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import snowflake.connector
from passlib.context import CryptContext
import os
from travel import Form

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
