from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime, timezone
from database import Base

class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    question = Column(String(500), index=True)
    answer = Column(String(2000))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))