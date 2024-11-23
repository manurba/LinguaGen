from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, Header
from typing import Optional
from app.services.chat import ChatService
from app.core.dependencies import verify_token
import uuid
from app.core.database import get_db_connection
import logging
import json

router = APIRouter()
chat_service = ChatService()

@router.get("/new_conversation")
async def new_conversation(authorization: str = Header(...)):
    """
    Create a new conversation. Requires JWT token in Authorization header.
    """
    try:
        # Remove 'Bearer ' prefix if present
        token = authorization.replace('Bearer ', '')
        
        # Verify token and get user data
        user_data = await verify_token(token)
        
        conversation_id = uuid.uuid4().hex
        conn = await get_db_connection()
        try:
            # Store initial messages as proper JSON
            initial_messages = json.dumps([
                {'role': 'system', 'content': 'You are a helpful assistant.'}
            ])
            
            await conn.execute(
                "INSERT INTO conversations (id, email, messages) VALUES ($1, $2, $3)",
                conversation_id,
                user_data["email"],
                initial_messages
            )
            return {"conversation_id": conversation_id}
        finally:
            await conn.close()

    except Exception as e:
        logging.error(f"Error creating new conversation: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")

@router.post("/get_response")
async def get_response(
    authorization: str = Header(...),
    conversation_id: str = Form(...),
    file: Optional[UploadFile] = File(None),
    text_input: Optional[str] = Form(None)
):
    """
    Get response for a conversation. Requires JWT token in Authorization header.
    """
    try:
        token = authorization.replace('Bearer ', '')
        user_data = await verify_token(token)
        
        if not file and not text_input:
            raise HTTPException(status_code=400, detail="No input provided")
            
        return await chat_service.process_input(
            conversation_id=conversation_id,
            file=file,
            text_input=text_input,
            user_email=user_data["email"]  # Pass user email to the service
        )
        
    except Exception as e:
        logging.error(f"Error processing response: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get_conversation")
async def get_conversation(conversation_id: str, authorization: str = Header(...)):
    """
    Get conversation messages. Requires JWT token in Authorization header.
    """
    try:
        token = authorization.replace('Bearer ', '')
        user_data = await verify_token(token)
        
        conn = await get_db_connection()
        try:
            row = await conn.fetchrow(
                "SELECT messages FROM conversations WHERE id=$1 AND email=$2",
                conversation_id,
                user_data["email"]
            )
            if not row:
                raise HTTPException(status_code=404, detail="Conversation not found")
            messages = json.loads(row["messages"])
            return {"messages": messages}
        finally:
            await conn.close()
    except Exception as e:
        logging.error(f"Error fetching conversation: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Internal server error")

