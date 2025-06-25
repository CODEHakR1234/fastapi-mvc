from sqlalchemy.orm import Session
from app.models.chat import ChatMessage

class ChatRepository:
    def __init__(self, db: Session):
        self.db = db

    def unread(self, room_id: int, viewer_id: int):
        return (self.db.query(ChatMessage)
                .filter(ChatMessage.room_id == room_id,
                        ChatMessage.user_id != viewer_id,
                        ChatMessage.is_read == False)
                .all())

    def mark_read(self, msgs):
        for m in msgs: m.is_read = True
        self.db.commit()

