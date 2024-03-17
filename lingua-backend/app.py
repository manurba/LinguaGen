import io
import os
import uuid
from typing import Optional

import aiofiles
import aiosqlite

# import motor.motor_asyncio
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
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
    ],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

app.mount("/data", StaticFiles(directory="data/"), name="data")

SQL_DATABASE_URL = os.getenv("SQL_DATABASE_URL")


async def create_conversation(conversation_id):
    async with aiosqlite.connect(SQL_DATABASE_URL) as db:
        await db.execute(
            "INSERT INTO conversations (id, messages) VALUES (?, ?)",
            (
                conversation_id,
                "[{'role': 'system', 'content': 'You are a helpful assistant.'}]",
            ),
        )
        await db.commit()


async def update_conversation(conversation_id, new_message):
    async with aiosqlite.connect(SQL_DATABASE_URL) as db:
        await db.execute(
            "UPDATE conversations SET messages = ? WHERE id = ?",
            (new_message, conversation_id),
        )
        await db.commit()


async def get_conversation(conversation_id):
    async with aiosqlite.connect(SQL_DATABASE_URL) as db:
        cursor = await db.execute(
            "SELECT messages FROM conversations WHERE id = ?",
            (conversation_id,),
        )
        row = await cursor.fetchone()
        return row[0] if row else None


@app.get("/new_conversation")
async def new_conversation():
    conversation_id = uuid.uuid4().hex
    await create_conversation(conversation_id)
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

    conversation = eval(conversation)
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
