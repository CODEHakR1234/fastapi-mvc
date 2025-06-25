from sqlalchemy import Column, Integer, Text, Boolean, Index
from app.database import Base

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id       = Column(Integer, primary_key=True)
    room_id  = Column(Integer, index=True)
    user_id  = Column(Integer)
    content  = Column(Text)
    is_read  = Column(Boolean, default=False)

Index("idx_room_read", ChatMessage.room_id, ChatMessage.is_read)

