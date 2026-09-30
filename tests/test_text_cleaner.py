import pytest
from backend.app.services.text_cleaner import clean_text, chunk_text

def test_clean_text_normalizes_ligatures_and_spaces():
    raw = "Experienced in \ufb01nancial ETL and \u2022 building data pipelines.   Multiple   spaces.\n\n\n\nNext line."
    cleaned = clean_text(raw)
    assert "financial" in cleaned
    assert "- building data pipelines." in cleaned
    assert "   " not in cleaned
    assert "\n\n\n" not in cleaned

def test_chunk_text_empty():
    assert chunk_text("") == []

def test_chunk_text_short():
    short = "Simple short resume text."
    chunks = chunk_text(short, chunk_size=100)
    assert len(chunks) == 1
    assert chunks[0] == short

def test_chunk_text_overlap():
    long_text = "First paragraph about AWS and Python data engineering pipelines.\n\nSecond paragraph with SQL and PostgreSQL databases.\n\nThird paragraph describing machine learning with PyTorch and ChromaDB."
    chunks = chunk_text(long_text, chunk_size=80, chunk_overlap=20)
    assert len(chunks) >= 2
