import pytest
import pymupdf as fitz
from backend.app.services.pdf_parser import PDFParser, PDFParsingError

def create_sample_pdf_bytes(content: str = "Sample Resume\nPython, SQL, AWS") -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), content)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes

def test_pdf_extraction_success():
    pdf_bytes = create_sample_pdf_bytes("John Doe\nSoftware Engineer\nSkills: Python, FastAPI, Docker")
    raw, cleaned, page_count = PDFParser.extract_text_from_bytes(pdf_bytes)
    
    assert page_count == 1
    assert "John Doe" in cleaned
    assert "FastAPI" in cleaned

def test_pdf_extraction_empty_bytes():
    with pytest.raises(PDFParsingError):
        PDFParser.extract_text_from_bytes(b"")

def test_pdf_extraction_corrupt_bytes():
    with pytest.raises(PDFParsingError):
        PDFParser.extract_text_from_bytes(b"Not A Real PDF Content at all")
