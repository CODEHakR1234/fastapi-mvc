# app/pdf_summary/service.py
import io
import PyPDF2
from pydantic import BaseModel
from openai import OpenAI               # ✅ 새 SDK
from app.pdf_summary.repository import NoteRepository

client = OpenAI()  # OPENAI_API_KEY 환경변수를 자동 사용

class NoteSummaryDTO(BaseModel):
    note_id: int
    summary: str

class PdfSummaryService:
    def __init__(self, repo: NoteRepository):
        self.repo = repo

    def handle(self, note_id: int, file_bytes: bytes) -> NoteSummaryDTO:
        # 1) PDF 파일 저장
        self.repo.save_pdf(note_id, file_bytes)

        # 2) PDF 텍스트 추출 (앞 1.2만 자만 사용해 프롬프트 길이 제한)
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        text   = "\n".join(p.extract_text() or "" for p in reader.pages)[:12000]

        # 3) GPT-3.5-Turbo 호출 — ✅ 새 SDK 형식
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            temperature=0.3,
            max_tokens=256,
            messages=[
                {"role": "system",
                 "content": "You are a helpful assistant that outputs concise Korean summaries."},
                {"role": "user",
                 "content": f"다음 글을 5문장 이하로 요약하세요:\n\n{text}"}
            ],
        )
        summary = response.choices[0].message.content.strip()

        # 4) DB에 요약 저장
        self.repo.update_summary(note_id, summary)
        return NoteSummaryDTO(note_id=note_id, summary=summary)

