from fastapi import FastAPI
from app.database import Base, engine
import app.models.note, app.models.chat
from app.pdf_summary.router import router as pdf_router
from app.chat_summary.router import router as chat_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Dual Summary API", version="1.0.0")
app.include_router(pdf_router)
app.include_router(chat_router)

