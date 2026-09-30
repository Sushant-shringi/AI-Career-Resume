import pytest
from backend.app.services.skill_extractor import extract_skills_from_text, categorize_skills

def test_extract_skills_precision():
    sample_text = "Built an automated ETL pipeline using Python, PySpark, AWS Lambda, PostgreSQL, and Docker. Implemented RAG search with ChromaDB."
    skills = extract_skills_from_text(sample_text)
    
    assert "Python" in skills
    assert "PySpark" in skills
    assert "AWS Lambda" in skills
    assert "PostgreSQL" in skills
    assert "Docker" in skills
    assert "RAG" in skills
    assert "ChromaDB" in skills
    assert "Java" not in skills

def test_categorize_skills():
    skills = ["Python", "PostgreSQL", "Docker", "PyTorch", "ETL"]
    categorized = categorize_skills(skills)
    
    assert "Programming Languages" in categorized
    assert "Python" in categorized["Programming Languages"]
    assert "Databases & Storage" in categorized
    assert "PostgreSQL" in categorized["Databases & Storage"]
