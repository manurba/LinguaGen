import io
import os
import uuid
from typing import Optional

import aiofiles
import motor.motor_asyncio
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, UploadFile

from lingua.agents.LinguaAgent import LinguaGen
from lingua.utils.dataclass import audio2text, text2audio

load_dotenv()

# Initialize MongoDB client and select your database and collection
client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv("MONGO_URI"))
db = client.conversations_database
conversations_collection = db.get_collection(os.getenv("MONGO_DB_COLLECTION"))

# Initialize FastAPI app
app = FastAPI()


@app.get("/new_conversation")
async def new_conversation():
    conversation_id = uuid.uuid4().hex
    # Create a new conversation entry in MongoDB with a system message
    await conversations_collection.insert_one(
        {
            "_id": conversation_id,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."}
            ],
        }
    )
    return {"conversation_id": conversation_id}


async def update_or_create_conversation(conversation_id, new_message):
    # Check if the conversation already exists
    conversation = await conversations_collection.find_one(
        {"_id": conversation_id}
    )

    if conversation:
        # If it exists, append the new message
        await conversations_collection.update_one(
            {"_id": conversation_id},
            {"$push": {"messages": {"$each": new_message}}},
        )


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

    get_conversation = await conversations_collection.find_one(
        {"_id": conversation_id}
    )

    conversation = get_conversation["messages"]

    conversation.append({"role": "user", "content": text_response})

    id_request_audio = uuid.uuid4().hex
    lingua = LinguaGen()
    response = await lingua.request_handler(
        request_id=id_request_audio,
        request_json={
            "model": "gpt-3.5-turbo-0125",
            "messages": conversation,
            "max_tokens": 100,
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

    await update_or_create_conversation(conversation_id, conversation)

    return {"file": file_name, "conversation": conversation}
