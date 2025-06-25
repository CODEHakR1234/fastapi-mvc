# app/chat_summary/service.py
import os
from pydantic import BaseModel
from openai import OpenAI                      # ✅ 새 SDK
from app.chat_summary.repository import ChatRepository

client = OpenAI()   # OPENAI_API_KEY 환경변수를 자동 사용

class ChatSummaryDTO(BaseModel):
    room_id: int
    unread: int
    summary: str

class ChatSummaryService:
    def __init__(self, repo: ChatRepository):
        self.repo = repo

    def handle(self, room_id: int, viewer_id: int) -> ChatSummaryDTO:
        # 1) 안 읽은 메시지 가져오기
        msgs = self.repo.unread(room_id, viewer_id)
        if not msgs:
            return ChatSummaryDTO(room_id=room_id, unread=0,
                                  summary="(읽지 않은 메시지가 없습니다)")

        # 2) 프롬프트용 텍스트 생성
        chat_text = "\n".join(f"{m.user_id}: {m.content}" for m in msgs)

        # 3) GPT-3.5-Turbo 호출 (신 SDK 형식)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            temperature=0.3,
            max_tokens=256,
            messages=[
                {"role": "system",
                 "content": "You are a helpful assistant that outputs concise Korean summaries."},
                {"role": "user",
                 "content": f"다음 대화를 5문장 이하로 요약하세요:\n\n{chat_text}"}
            ],
        )
        summary = response.choices[0].message.content.strip()

        # 4) 읽음 처리 및 DTO 반환
        self.repo.mark_read(msgs)
        return ChatSummaryDTO(room_id=room_id, unread=len(msgs), summary=summary)

