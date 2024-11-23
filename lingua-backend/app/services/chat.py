from lingua.agents.LinguaAgent import LinguaGen
from lingua.utils.dataclass import audio2text, text2audio
import aiofiles
import io
from app.core.config import settings
from app.core.database import get_db_connection
from fastapi import HTTPException, UploadFile
from typing import Optional
import logging
import traceback
import json
import uuid
import os
from datetime import datetime
import base64

class ChatService:
    def __init__(self):
        self.lingua = LinguaGen()
    
    async def process_input(
        self,
        conversation_id: str,
        user_email: str,
        file: Optional[UploadFile] = None,
        text_input: Optional[str] = None
    ):
        try:
            logging.info(f"Starting process_input for user: {user_email}")
            
            # Get text input from either source
            if text_input:
                text_response = text_input
                logging.info("Using provided text input")
            elif file:
                logging.info("Processing audio file")
                audio_file = io.BytesIO(await file.read())
                response = await audio2text(
                    request_url="https://api.openai.com/v1/audio/transcriptions",
                    request_header={
                        "Authorization": f"Bearer {settings.API_KEY}"
                    },
                    file_path=audio_file,
                    model="whisper-1",
                )
                text_response = response["text"]
                logging.info(f"Audio transcribed: {text_response}")
            else:
                raise ValueError("No input provided")
                
            # Verify conversation belongs to user
            conn = await get_db_connection()
            try:
                logging.info("Fetching conversation from database")
                conversation = await conn.fetchrow(
                    "SELECT messages FROM conversations WHERE id = $1 AND email = $2",
                    conversation_id, user_email
                )

                if not conversation:
                    logging.error(f"Conversation not found or access denied for ID: {conversation_id}")
                    raise HTTPException(
                        status_code=404,
                        detail="Conversation not found or access denied"
                    )
                
                logging.info("Generating response")
                # Fetch and parse messages with better error handling
                try:
                    if isinstance(conversation['messages'], str):
                        # Try to parse if it's a string
                        messages = json.loads(conversation['messages'].replace("'", '"'))
                    else:
                        # If it's already a list/dict, use it directly
                        messages = conversation['messages']
                except json.JSONDecodeError as je:
                    logging.error(f"JSON decode error: {str(je)}")
                    logging.error(f"Raw messages: {conversation['messages']}")
                    # Initialize with system message if parsing fails
                    messages = [{'role': 'system', 'content': 'You are a helpful assistant.'}]
                
                # Ensure messages is a list
                if not isinstance(messages, list):
                    messages = [{'role': 'system', 'content': 'You are a helpful assistant.'}]
                
                # Add new user message
                messages.append({"role": "user", "content": text_response})
                print(messages)
                # Generate response using LinguaGen
                response = await self.lingua.request_handler(
                    request_id=conversation_id,
                    request_json={
                        "model": "gpt-3.5-turbo-0125",
                        "messages": messages,
                        "max_tokens": 600,
                    },
                    request_url="https://api.openai.com/v1/chat/completions",
                    max_requests_per_minute=415 * 0.5,
                    max_tokens_per_minute=60_000 * 0.5,
                    token_encoding_name="cl100k_base",
                    max_attempts=5,
                )
                
                lingua_response = response[conversation_id]["response"]
                
                # Generate audio response
                audio_response = await text2audio(
                    request_url="https://api.openai.com/v1/audio/speech",
                    request_header={
                        "Authorization": f"Bearer {settings.API_KEY}",
                        "Content-Type": "application/json",
                    },
                    voice="alloy",
                    input=lingua_response,
                    model="tts-1",
                )
                
                # Convert audio bytes to base64 for transmission
                audio_base64 = base64.b64encode(audio_response).decode('utf-8')
                
                # Update messages without audio file path
                messages.append({
                    "role": "assistant",
                    "content": lingua_response
                })
                
                # Store messages as proper JSON string
                await conn.execute(
                    "UPDATE conversations SET messages = $1 WHERE id = $2",
                    json.dumps(messages), conversation_id
                )
                
                return {
                    "audio_data": audio_base64,
                    "conversation": messages
                }
                
            finally:
                await conn.close()
                
        except Exception as e:
            logging.error(f"Error in process_input: {str(e)}")
            logging.error(f"Traceback: {traceback.format_exc()}")
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=str(e))
