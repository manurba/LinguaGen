import io
import os
import uuid

from fastapi import FastAPI, File, Form, UploadFile

from lingua.agents.LinguaAgent import LinguaGen
from lingua.utils.dataclass import audio2text, text2audio

app = FastAPI()


@app.get("/new_conversation")
async def new_conversation():
    return {"conversation_id": str(uuid.uuid4())}


@app.post("/get_response")
async def compute_reply(
    conversation_id: str = Form(...), file: UploadFile = File(...)
):
    audio_file = io.BytesIO(await file.read())

    response = await audio2text(
        request_url="https://api.openai.com/v1/audio/transcriptions",
        request_header={"Authorization": f"Bearer {os.getenv('API_KEY')}"},
        file_path=audio_file,
        model="whisper-1",
    )

    request_audio = {
        "parent_message_id": conversation_id,
        "messages": [
            {
                "id": uuid.uuid4(),
                "author": {"role": "user"},
                "content": {
                    "content_type": "text",
                    "parts": [response["text"]],
                },
            }
        ],
    }

    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {
            "role": "user",
            "content": request_audio["messages"][0]["content"]["parts"][0],
        },
    ]

    lingua = LinguaGen()

    response = await lingua.request_handler(
        request_id=request_audio["parent_message_id"],
        request_json={
            "model": "gpt-3.5-turbo-0125",
            "messages": messages,
            "max_tokens": 100,
        },
        request_url="https://api.openai.com/v1/chat/completions",
        max_requests_per_minute=415 * 0.5,
        max_tokens_per_minute=60_000 * 0.5,
        token_encoding_name="cl100k_base",
        max_attempts=5,
    )

    response_text = response[conversation_id]["response"]

    response = await text2audio(
        request_url="https://api.openai.com/v1/audio/speech",
        request_header={
            "Authorization": f"Bearer {os.getenv('API_KEY')}",
            "Content-Type": "application/json",
        },
        voice="alloy",
        input=response_text,
        model="tts-1",
    )

    file_name = f"data/{conversation_id}_output.mp3"
    with open(file_name, "wb") as audio_file:
        audio_file.write(response)

    return {"file": file_name, "response_text": response_text}
