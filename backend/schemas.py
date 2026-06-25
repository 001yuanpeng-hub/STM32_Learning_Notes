from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ChatRequest(BaseModel):
    question: str
    model: Optional[str] = "mimo"  # 可选: mimo, claude
    conversation_id: Optional[int] = None

class ChatResponse(BaseModel):
    question: str
    answer: str
    references: list[str]
    conversation_id: int

class ConversationCreate(BaseModel):
    title: Optional[str] = None

class ConversationResponse(BaseModel):
    id: int
    title: str
    created_at: datetime

class MessageResponse(BaseModel):
    id: int
    question: str
    answer: str
    created_at: datetime
