from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.chat_summary.service import ChatSummaryService, ChatSummaryDTO
from app.chat_summary.repository import ChatRepository

router = APIRouter(prefix="/api/chat", tags=["Chat Summary"])

def _svc(db: Session = Depends(get_db)):
    return ChatSummaryService(ChatRepository(db))

@router.get("/{room_id}/unread/summary", response_model=ChatSummaryDTO)
def summarize_chat(room_id: int,
                   viewer_id: int,
                   svc: ChatSummaryService = Depends(_svc)):
    return svc.handle(room_id, viewer_id)

