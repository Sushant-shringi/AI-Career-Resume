import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from tests.test_pdf_parser import create_sample_pdf_bytes

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "llm_provider" in data
    assert "embedding_model" in data

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert "Welcome" in response.json()["message"]

def test_upload_invalid_file_type():
    response = client.post(
        "/api/resume/upload",
        files={"file": ("resume.txt", b"Hello world", "text/plain")}
    )
    assert response.status_code == 400
    assert "Only PDF" in response.json()["detail"]

def test_upload_valid_pdf_and_list():
    pdf_bytes = create_sample_pdf_bytes("Alex Smith\nData Engineer\nSkills: Python, SQL, Pandas, AWS, Docker\nProjects: Built AWS ETL pipeline.")
    response = client.post(
        "/api/resume/upload",
        files={"file": ("alex_smith_resume.pdf", pdf_bytes, "application/pdf")}
    )
    assert response.status_code == 201
    upload_data = response.json()
    resume_id = upload_data["id"]
    assert "Python" in upload_data["extracted_skills"]
    assert upload_data["total_chunks"] >= 1

    # Test list endpoint
    list_res = client.get("/api/resume/list")
    assert list_res.status_code == 200
    resumes = list_res.json()
    assert any(r["id"] == resume_id for r in resumes)

    # Test get detail endpoint
    detail_res = client.get(f"/api/resume/{resume_id}")
    assert detail_res.status_code == 200
    assert "Alex Smith" in detail_res.json()["cleaned_text"]

def test_improve_bullet_point():
    response = client.post(
        "/api/suggestions/improve-bullet",
        json={"original_bullet": "Created a Python script to extract SQL database records.", "role_or_domain": "Data Engineer"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "improved_bullet" in data
    assert len(data["key_changes"]) > 0
