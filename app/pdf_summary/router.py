from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.pdf_summary.service import PdfSummaryService, NoteSummaryDTO
from app.pdf_summary.repository import NoteRepository

router = APIRouter(prefix="/api/pdf", tags=["PDF Summary"])

def _svc(db: Session = Depends(get_db)):
    return PdfSummaryService(NoteRepository(db))

@router.post("/notes/{note_id}/summary", response_model=NoteSummaryDTO)
def summarize_pdf(note_id: int,
                  file: UploadFile = File(...),
                  svc: PdfSummaryService = Depends(_svc)):
    return svc.handle(note_id, file.file.read())

