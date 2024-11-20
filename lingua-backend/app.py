import io
import os
import uuid
from datetime import datetime, timedelta
from typing import Optional

import aiofiles
import asyncpg
import jwt

# import motor.motor_asyncio
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from google.auth.transport import requests
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from lingua.agents.LinguaAgent import LinguaGen
from lingua.utils.dataclass import audio2text, text2audio

load_dotenv()

# # Initialize MongoDB client and select your database and collection
# client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv("MONGO_URI"))
# db = client.conversations_database
# conversations_collection = db.get_collection(os.getenv("MONGO_DB_COLLECTION"))


# Initialize FastAPI app
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://linguagen.azurewebsites.net",
        "https://linguagen.tech",
        "https://core.linguagen.tech",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "Authorization", "Content-Type"],
    expose_headers=["*"],
)

app.mount("/data", StaticFiles(directory="data/"), name="data")

DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@db:5432/{os.getenv('POSTGRES_DB')}"


# Add after SQL_DATABASE_URL definition
async def init_db():
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS whitelist (
            email TEXT PRIMARY KEY,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            email TEXT,
            messages TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS whitelist_requests (
            email TEXT PRIMARY KEY,
            requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending'
        )
    ''')
    await conn.close()


# Add after app initialization
@app.on_event("startup")
async def startup_event():
    await init_db()


async def check_whitelist(email: str) -> bool:
    conn = await asyncpg.connect(DATABASE_URL)
    result = await conn.fetchval(
        'SELECT email FROM whitelist WHERE email = $1',
        email
    )
    await conn.close()
    return bool(result)


async def create_conversation(conversation_id, email):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute(
            "INSERT INTO conversations (id, email, messages) VALUES ($1, $2, $3)",
            conversation_id,
            email,
            "[{'role': 'system', 'content': 'You are a helpful assistant.'}]",
        )
    finally:
        await conn.close()


async def update_conversation(conversation_id, new_message):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute(
            "UPDATE conversations SET messages = $1 WHERE id = $2",
            new_message, conversation_id,
        )
    finally:
        await conn.close()


async def get_conversation(conversation_id):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        row = await conn.fetchrow(
            "SELECT email, messages, created_at FROM conversations WHERE id = $1",
            conversation_id,
        )
        return row if row else None
    finally:
        await conn.close()


@app.get("/new_conversation")
async def new_conversation(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="No valid token provided")

    token = authorization.split(" ")[1]
    payload = await verify_token(token)
    email = payload["email"]

    conversation_id = uuid.uuid4().hex
    await create_conversation(conversation_id, email)
    return {"conversation_id": conversation_id}


@app.post("/get_response")
async def compute_reply(
    conversation_id: str = Form(...),
    file: UploadFile = File(None),
    text_input: Optional[str] = Form(None),
):
    if text_input:
        text_response = text_input
    else:
        if file is not None:
            audio_file = io.BytesIO(await file.read())
            response = await audio2text(
                request_url="https://api.openai.com/v1/audio/transcriptions",
                request_header={
                    "Authorization": f"Bearer {os.getenv('API_KEY')}"
                },
                file_path=audio_file,
                model="whisper-1",
            )
            # Extract the text part from the response
            text_response = response["text"]
        else:
            return {"error": "No input provided"}

    conversation = await get_conversation(conversation_id)

    if not conversation:
        return {"error": "Conversation not found"}

    conversation =  eval(conversation['messages'])
    conversation.append({"role": "user", "content": text_response})

    # id_request_audio = uuid.uuid4().hex
    lingua = LinguaGen()
    response = await lingua.request_handler(
        # request_id=id_request_audio,
        request_id=conversation_id,
        request_json={
            "model": "gpt-3.5-turbo-0125",
            "messages": conversation,
            "max_tokens": 600,
        },
        request_url="https://api.openai.com/v1/chat/completions",
        max_requests_per_minute=415 * 0.5,
        max_tokens_per_minute=60_000 * 0.5,
        token_encoding_name="cl100k_base",
        max_attempts=5,
    )

    lingua_response = response[conversation_id]["response"]

    conversation.append({"role": "assistant", "content": lingua_response})

    response = await text2audio(
        request_url="https://api.openai.com/v1/audio/speech",
        request_header={
            "Authorization": f"Bearer {os.getenv('API_KEY')}",
            "Content-Type": "application/json",
        },
        voice="alloy",
        input=lingua_response,
        model="tts-1",
    )

    file_name = f"data/{conversation_id}_output.mp3"
    async with aiofiles.open(file_name, "wb") as audio_file:
        await audio_file.write(response)

    # await update_or_create_conversation(conversation_id, conversation)
    await update_conversation(conversation_id, str(conversation))

    return {"file": file_name, "conversation": conversation}


# Add new OAuth routes
@app.post("/auth/google-login")
async def google_login(request: Request):
    try:
        # Get the request body as JSON
        body = await request.json()
        code = body.get("code")
        if not code:
            raise HTTPException(
                status_code=400, detail="Authorization code is required"
            )

        # Create the flow using the client secrets
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                    "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uri": os.getenv("REDIRECT_URI"),
                }
            },
            scopes=[
                "https://www.googleapis.com/auth/userinfo.email",
                "https://www.googleapis.com/auth/userinfo.profile",
                "openid",
            ],
        )

        # Set the redirect URI
        flow.redirect_uri = os.getenv("REDIRECT_URI")

        try:
            # Exchange the authorization code for credentials
            flow.fetch_token(code=code)
        except Exception as e:
            print(f"Error fetching token: {str(e)}")
            raise HTTPException(
                status_code=400, detail="Failed to exchange authorization code"
            )

        try:
            # Get the ID token from credentials
            credentials = flow.credentials
            id_info = id_token.verify_oauth2_token(
                credentials.id_token,
                requests.Request(),
                os.getenv("GOOGLE_CLIENT_ID"),
                clock_skew_in_seconds=2,
            )
        except Exception as e:
            print(f"Error verifying token: {str(e)}")
            raise HTTPException(
                status_code=400, detail="Failed to verify Google token"
            )

        # Add whitelist check after verifying Google token
        user_email = id_info["email"]
        print(f"This is the user email: {user_email}")
        is_whitelisted = await check_whitelist(user_email)

        if not is_whitelisted:
            raise HTTPException(
                status_code=403,
                detail="Access denied. Your email is not whitelisted.",
            )

        # Create a JWT token for your application
        try:
            token = jwt.encode(
                {
                    "sub": id_info["sub"],
                    "email": id_info["email"],
                    "name": id_info.get("name", ""),
                    "exp": datetime.utcnow() + timedelta(days=1),
                },
                os.getenv("JWT_SECRET_KEY"),
                algorithm="HS256",
            )
        except Exception as e:
            print(f"Error creating JWT: {str(e)}")
            raise HTTPException(
                status_code=500, detail="Failed to create authentication token"
            )

        return JSONResponse(content={"token": token})

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Unexpected error in google_login: {str(e)}")
        raise HTTPException(status_code=500, detail="Authentication failed")


# Add this middleware to protect your routes
async def verify_token(token: str):
    try:
        payload = jwt.decode(
            token, os.getenv("JWT_SECRET_KEY"), algorithms=["HS256"]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        print(f"Unexpected error in verify_token: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Token verification failed"
        )


# Example of protecting a route (you can add this to other routes that need protection)
@app.get("/protected-route")
async def protected_route(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        return {"error": "No valid token provided"}, 401

    token = authorization.split(" ")[1]
    payload = await verify_token(token)

    if not payload:
        return {"error": "Invalid or expired token"}, 401

    return {"message": "Access granted", "user": payload}


# Add these new admin endpoints
@app.post("/admin/whitelist/add")
async def add_to_whitelist(email: str, authorization: str = Header(None)):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute(
            "INSERT INTO whitelist (email) VALUES ($1)", email
        )
        return {"message": f"Added {email} to whitelist"}
    except asyncpg.UniqueViolationError:
        raise HTTPException(
            status_code=400, detail="Email already whitelisted"
        )
    finally:
        await conn.close()


@app.delete("/admin/whitelist/remove")
async def remove_from_whitelist(email: str, authorization: str = Header(None)):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute(
            "DELETE FROM whitelist WHERE email = $1", email
        )
        return {"message": f"Removed {email} from whitelist"}
    finally:
        await conn.close()


@app.post("/auth/request-access")
async def request_access(request: Request):
    data = await request.json()
    email = data.get("email")

    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute(
            "INSERT INTO whitelist_requests (email) VALUES ($1)", email
        )
        return {"message": "Access request submitted successfully"}
    except asyncpg.UniqueViolationError:
        return {"message": "Access request already submitted"}
    finally:
        await conn.close()
