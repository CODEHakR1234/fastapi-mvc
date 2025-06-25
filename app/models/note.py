from sqlalchemy import Column, Integer, String, Text
from app.database import Base

class Note(Base):
    __tablename__ = "notes"
    id       = Column(Integer, primary_key=True)
    pdf_path = Column(String, nullable=False)
    summary  = Column(Text)

