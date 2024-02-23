from fastapi import FastAPI, File, UploadFile

from lingua.utils.dataclass import (
    text_from_audio,
    text_to_audio
)
from lingua.agents.LinguaAgent import LinguaGen
import os
import uuid
import io

app = FastAPI()

@app.post("/get_response")
async def compute_reply(file: UploadFile = File(...)):
    audio_file = io.BytesIO(await file.read())

    response = await text_from_audio(
        request_url="https://api.openai.com/v1/audio/transcriptions",
        request_header={"Authorization": f"Bearer {os.getenv('API_KEY')}"},
        file_path=audio_file,
        model="whisper-1"
    )

    id_request = str(uuid.uuid4())

    request_audio = {
        "parent_message_id": id_request,
        "messages": [
            {
                "id": uuid.uuid4(),
                "author": {"role": "user"},
                "content": {
                    "content_type": "text",
                    "parts": [response["text"]]
                }
            }
        ]
    }

    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant."
        },
        {
            "role": "user",
            "content": request_audio["messages"][0]["content"]["parts"][0]
        }
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
        max_requests_per_minute=415*.5,
        max_tokens_per_minute=60_000*.5,
        token_encoding_name="cl100k_base",
        max_attempts=5,
    )
    
    response = await text_to_audio(
        request_url="https://api.openai.com/v1/audio/speech",
        request_header={
            "Authorization": f"Bearer {os.getenv('API_KEY')}",
            "Content-Type": "application/json"
        },
        voice="alloy",
        input=response[id_request]["response"],
        model="tts-1",
    )

    return {"filename": file.filename}
