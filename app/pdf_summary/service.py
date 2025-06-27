# app/pdf_summary/service.py
import io
import PyPDF2
from pydantic import BaseModel
from openai import OpenAI               # ✅ 새 SDK
from app.pdf_summary.repository import NoteRepository
import platform
from PIL import Image, ImageOps
import fitz
import pytesseract
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.chains.summarize import load_summarize_chain
from langchain.chains import LLMChain
from langchain.schema.runnable import Runnable, RunnableLambda

client = OpenAI()  # OPENAI_API_KEY 환경변수를 자동 사용

class NoteSummaryDTO(BaseModel):
    note_id: int
    summary: str

class PdfSummaryService:
    def __init__(self, repo: NoteRepository, tesseract_cmd=None, ocr_lang='kor+eng'):
        self.repo = repo
        self.parser = PDFParser(tesseract_cmd=tesseract_cmd, ocr_lang=ocr_lang)

    def handle(self, note_id: int, file_bytes: bytes) -> NoteSummaryDTO:
        # 1) PDF 파일 저장
        note = self.repo.save_pdf(note_id, file_bytes)
        pdf_path = note.pdf_path

        # 2) 전체 체인 실행 (파싱→map_reduce 요약→번역)
        chain = get_full_chain(self.parser)
        result = chain.invoke(pdf_path)
        summary = result["text"] if isinstance(result, dict) and "text" in result else str(result)

        # 3) DB에 요약 저장
        self.repo.update_summary(note_id, summary)
        return NoteSummaryDTO(note_id=note_id, summary=summary)

class PDFParser:
    def __init__(self, tesseract_cmd=None, ocr_lang='kor+eng'):
        self.tesseract_cmd = tesseract_cmd
        self.ocr_lang = ocr_lang
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    def read(self, pdf_path):
        doc = fitz.open(pdf_path)
        is_text = sum(1 for p in doc if p.get_text().strip()) / len(doc) >= 0.3
        doc.close()
        return self._read_text(pdf_path) if is_text else self._read_ocr(pdf_path)

    def _read_text(self, path):
        doc = fitz.open(path)
        pages = [p.get_text() for p in doc]
        doc.close()
        return pages

    def _read_ocr(self, path):
        doc = fitz.open(path)
        texts = []
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(dpi=300)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            gray = ImageOps.grayscale(img)
            bw = gray.point(lambda x: 0 if x < 180 else 255, '1')
            text = pytesseract.image_to_string(img, lang=self.ocr_lang)
            texts.append(text)
        doc.close()
        return texts


# ✅ LangChain PDF 파서 체인
class PDFParseChain(Runnable):
    def __init__(self, parser: PDFParser):
        self.parser = parser

    def invoke(self, pdf_path: str, config=None, **kwargs) -> list[str]:
        return self.parser.read(pdf_path)


# ✅ 요약 체인 생성
def get_summary_chain():
    llm = ChatOpenAI(model="gpt-3.5-turbo")
    return load_summarize_chain(llm, chain_type="map_reduce")


# ✅ 번역 체인 생성
def get_translation_chain():
    llm = ChatOpenAI(model="gpt-3.5-turbo")
    prompt = PromptTemplate.from_template(
        """다음 영문 요약을 자연스럽고 간결한 한국어로 번역해줘:

{text}

번역:"""
    )
    return LLMChain(llm=llm, prompt=prompt)


# ✅ 전체 체인 연결
def get_full_chain(parser: PDFParser) -> Runnable:
    pdf_chain = PDFParseChain(parser)

    def pages_to_documents(pages: list[str]) -> list[Document]:
        return [Document(page_content=t, metadata={"page": i+1}) for i, t in enumerate(pages)]

    def split_documents(docs: list[Document]) -> list[Document]:
        return RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100).split_documents(docs)

    summary_chain = get_summary_chain()
    translation_chain = get_translation_chain()
    wrap_text_input = RunnableLambda(lambda x: {"text": x})

    return (
        pdf_chain
        | pages_to_documents
        | split_documents
        | summary_chain
        | wrap_text_input
        | translation_chain
    )