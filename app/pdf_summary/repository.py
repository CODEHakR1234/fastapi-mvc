from pathlib import Path
from sqlalchemy.orm import Session
from app.models.note import Note

class NoteRepository:
    def __init__(self, db: Session):
        self.db = db
        Path("uploads").mkdir(exist_ok=True)

    def save_pdf(self, note_id: int, file_bytes: bytes):
        path = Path("uploads") / f"note_{note_id}.pdf"
        path.write_bytes(file_bytes)
        note = self.db.query(Note).get(note_id) or Note(id=note_id, pdf_path=str(path))
        note.pdf_path = str(path)
        self.db.add(note); self.db.commit(); self.db.refresh(note)
        return note

    def update_summary(self, note_id: int, summary: str):
        note = self.db.query(Note).get(note_id)
        note.summary = summary
        self.db.commit()

