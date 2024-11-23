from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int
    created_at: datetime

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model: Optional[str] = "gpt-3.5-turbo"
    temperature: Optional[float] = 0.7

class ChatResponse(BaseModel):
    message: ChatMessage
    usage: Optional[Dict] = None
