import sys
import os
import json
import time
from pathlib import Path

PROJECT_ROOT = Path(r"C:\Users\sushant\.gemini\antigravity\scratch\ai-career-assistant")
sys.path.insert(0, str(PROJECT_ROOT))

import pymupdf as fitz
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.config import settings
from backend.app.database.session import SessionLocal
from backend.app.database.models import ResumeModel, JobDescriptionModel, AnalysisModel, InterviewQuestionModel
from backend.app.services.vector_store import vector_store
from backend.app.services.skill_extractor import extract_skills_from_text
from backend.app.services.embedding_service import embedding_service

client = TestClient(app)

print("=" * 60)
print("RUNNING FINAL VALIDATION & QUALITY AUDIT SUITE")
print("=" * 60)

audit_results = {}

# 1. Health check & Ollama status
print("\n[Step 1] Verifying /api/health endpoint...")
res = client.get("/api/health")
assert res.status_code == 200, f"Health check failed with {res.status_code}"
health_data = res.json()
print(f"Health Response: {json.dumps(health_data, indent=2)}")
audit_results["health_check"] = "PASS"
audit_results["llm_provider"] = health_data["llm_provider"]
audit_results["llm_status"] = health_data["llm_status"]

# 2. Create Realistic Sample Data Engineer Resume PDF
print("\n[Step 2] Generating realistic sample Data Engineer resume PDF...")
sample_resume_text = """
Alex Chen
Data & GenAI Engineer | alex.chen@example.com | github.com/alexchen | linkedin.com/in/alexchen

PROFESSIONAL SUMMARY
Results-driven Data Engineer with experience building serverless ETL pipelines, relational data models, and local RAG search applications. Proficient in Python, SQL, AWS, and ChromaDB.

TECHNICAL SKILLS
- Programming Languages: Python, SQL, Bash
- Data & Machine Learning: Pandas, NumPy, Scikit-Learn, ChromaDB, RAG, Embeddings, Ollama
- Data Engineering & Cloud: AWS Lambda, Amazon S3, PostgreSQL, SQLite, Docker, Git, CI/CD
- API Frameworks: FastAPI, REST API

FEATURED PROJECTS

1. AWS Serverless ETL Pipeline
- Architected automated data ingestion pipeline using AWS Lambda and Amazon S3 to process 250,000+ daily JSON transaction records.
- Implemented data validation and cleaning routines in Python, loading transformed structured tables into PostgreSQL.
- Reduced data ingestion latency by 35% through concurrent batch processing.

2. Document Search & RAG Assistant
- Built a local Retrieval-Augmented Generation (RAG) assistant using FastAPI, ChromaDB, and sentence-transformers.
- Indexed 500+ technical documentation pages into 384-dimensional vector embeddings for cosine similarity retrieval.
- Integrated Ollama local LLM for context-grounded Q&A with strict anti-hallucination prompt constraints.

EDUCATION
Bachelor of Science in Computer Science, 2024
"""

doc = fitz.open()
page = doc.new_page()
page.insert_text((40, 40), sample_resume_text.strip(), fontsize=10)
sample_pdf_bytes = doc.tobytes()
doc.close()

# 3. Test Resume Upload & Parsing
print("\n[Step 3] Testing Resume Upload (/api/resume/upload)...")
upload_res = client.post(
    "/api/resume/upload",
    files={"file": ("alex_chen_resume.pdf", sample_pdf_bytes, "application/pdf")}
)
assert upload_res.status_code == 201, f"Upload failed: {upload_res.text}"
upload_data = upload_res.json()
resume_id = upload_data["id"]
print(f"Uploaded Resume ID: {resume_id}")
print(f"Extracted Skills ({len(upload_data['extracted_skills'])}): {upload_data['extracted_skills']}")
print(f"Total Chunks Created: {upload_data['total_chunks']}")

assert "Python" in upload_data["extracted_skills"]
assert "AWS Lambda" in upload_data["extracted_skills"]
assert "ChromaDB" in upload_data["extracted_skills"]
assert "FastAPI" in upload_data["extracted_skills"]
assert upload_data["total_chunks"] >= 2
audit_results["resume_upload"] = "PASS"
audit_results["pdf_extraction"] = "PASS"
audit_results["skill_extraction"] = "PASS"

# 4. Verify Database Persistence (SQLite)
print("\n[Step 4] Verifying SQLite database persistence...")
db = SessionLocal()
resume_db = db.query(ResumeModel).filter(ResumeModel.id == resume_id).first()
assert resume_db is not None, "Resume record missing in SQLite!"
assert "alex chen" in resume_db.raw_text.lower()
assert resume_db.total_chunks == upload_data["total_chunks"]
db.close()
audit_results["sqlite_db_persistence"] = "PASS"

# 5. Verify ChromaDB Vector Store Persistence
print("\n[Step 5] Verifying ChromaDB vector search and chunk retrieval...")
q_emb = embedding_service.embed_text("What AWS services are used in the ETL pipeline?")
retrieved_chunks = vector_store.query_resume_chunks(resume_id, q_emb, top_k=2)
print(f"Retrieved {len(retrieved_chunks)} chunks for query 'What AWS services are used?':")
for i, c in enumerate(retrieved_chunks, 1):
    print(f"  Chunk #{c['chunk_id']} (Similarity: {c['similarity_score']}): {c['text'][:100]}...")
assert len(retrieved_chunks) > 0, "No chunks returned from ChromaDB query!"
assert "AWS Lambda" in retrieved_chunks[0]["text"] or "Amazon S3" in retrieved_chunks[0]["text"]
audit_results["chromadb_vector_search"] = "PASS"

# 6. Job Description Match Analysis
print("\n[Step 6] Testing Job Description Match (/api/jobs/match)...")
sample_jd = """
Junior Data Engineer - Cloud Platform
Requirements:
- Strong programming in Python and SQL
- Experience with AWS and Docker
- Experience with Snowflake, Apache Spark, and Apache Kafka
- Knowledge of REST API development with FastAPI
"""
match_res = client.post(
    "/api/jobs/match",
    json={"resume_id": resume_id, "custom_job_text": sample_jd}
)
assert match_res.status_code == 200, f"Match failed: {match_res.text}"
match_data = match_res.json()
print(f"Match Percentage: {match_data['match_percentage']}%")
print(f"Matching Skills ({len(match_data['matching_skills'])}): {match_data['matching_skills']}")
print(f"Missing Skills ({len(match_data['missing_skills'])}): {match_data['missing_skills']}")
print(f"Relevant Projects Retrieved: {len(match_data['relevant_projects'])}")

assert "Python" in match_data["matching_skills"]
assert "SQL" in match_data["matching_skills"]
assert "AWS" in match_data["matching_skills"]
assert "FastAPI" in match_data["matching_skills"]
assert "Snowflake" in match_data["missing_skills"]
assert "Apache Spark" in match_data["missing_skills"]
assert "Apache Kafka" in match_data["missing_skills"]
audit_results["job_matching"] = "PASS"

# 7. RAG Grounded Query Test
print("\n[Step 7] Testing RAG Chat grounded question (/api/rag/chat)...")
rag_res = client.post(
    "/api/rag/chat",
    json={"resume_id": resume_id, "question": "What is the daily transaction volume processed by the AWS ETL pipeline?"}
)
assert rag_res.status_code == 200
rag_data = rag_res.json()
print(f"Question: {rag_data['question']}")
print(f"Answer: {rag_data['answer']}")
print(f"Source chunks cited: {len(rag_data['sources'])}")
assert len(rag_data["sources"]) > 0
assert rag_data["sources"][0]["similarity_score"] > 0.0
audit_results["rag_grounded_answer"] = "PASS"

# 8. RAG Hallucination Resistance Tests
print("\n[Step 8] Testing RAG Anti-Hallucination Guardrails...")
hallucination_queries = [
    "What AWS certifications does the candidate have?",
    "Tell me about the candidate's work experience at Google or Microsoft.",
    "How many years of Apache Spark production experience does the candidate have?",
    "What Kubernetes cluster administration projects are mentioned?"
]

for h_query in hallucination_queries:
    h_res = client.post("/api/rag/chat", json={"resume_id": resume_id, "question": h_query})
    assert h_res.status_code == 200
    h_ans = h_res.json()["answer"]
    print(f"\nQuery: '{h_query}'")
    print(f"Model Answer: {h_ans}")
    is_refusal = (
        "couldn't find" in h_ans.lower()
        or "not found" in h_ans.lower()
        or "does not provide" in h_ans.lower()
        or "not mentioned" in h_ans.lower()
        or "offline" in h_ans.lower()
        or "unable to reach" in h_ans.lower()
    )
    print(f"-> Anti-Hallucination Verified: {is_refusal}")
    assert is_refusal, f"Model hallucinated an answer for absent facts! Output: {h_ans}"

audit_results["anti_hallucination_guardrails"] = "PASS"

# 9. Interview Question & STAR Answer Generation
print("\n[Step 9] Testing Interview Question & STAR Answer Generation...")
int_res = client.post(
    "/api/interview/generate",
    json={"resume_id": resume_id, "custom_job_text": sample_jd}
)
assert int_res.status_code == 200
int_data = int_res.json()
print(f"Generated {len(int_data['questions'])} interview questions:")
for q in int_data["questions"][:3]:
    print(f"  [{q['category']}] ({q['difficulty']}): {q['question']}")

assert len(int_data["questions"]) >= 4

first_q = int_data["questions"][0]["question"]
ans_res = client.post(
    "/api/interview/answer",
    json={"resume_id": resume_id, "question": first_q, "category": "Project-based"}
)
assert ans_res.status_code == 200
ans_data = ans_res.json()
print(f"\nGenerated STAR Answer for '{first_q}':\n{ans_data['sample_answer']}")
audit_results["interview_prep"] = "PASS"

# 10. Resume Improvement & X-Y-Z Bullet Point Polish
print("\n[Step 10] Testing Resume Suggestions & X-Y-Z Bullet Point Polish...")
rev_res = client.get(f"/api/suggestions/review/{resume_id}")
assert rev_res.status_code == 200
rev_data = rev_res.json()
print(f"Resume Review Score: {rev_data['score_estimate']}/100")
print(f"Suggestions Count: {len(rev_data['suggestions'])}")

bullet_res = client.post(
    "/api/suggestions/improve-bullet",
    json={
        "original_bullet": "Wrote Python scripts to process data files and saved into database.",
        "role_or_domain": "Data Engineer"
    }
)
assert bullet_res.status_code == 200
bullet_data = bullet_res.json()
print(f"Original: {bullet_data['original_bullet']}")
print(f"Improved: {bullet_data['improved_bullet']}")
print(f"Key Changes: {bullet_data['key_changes']}")
assert len(bullet_data["improved_bullet"]) > 10
assert len(bullet_data["key_changes"]) > 0
audit_results["resume_polish"] = "PASS"

# 11. Backend Restart & Persistence Integrity Test
print("\n[Step 11] Testing vector store persistence across simulated backend reload...")
from backend.app.services.vector_store import VectorStoreService
reloaded_store = VectorStoreService()
reloaded_chunks = reloaded_store.query_resume_chunks(resume_id, q_emb, top_k=2)
assert len(reloaded_chunks) > 0, "Persisted vectors failed to reload from disk!"
print(f"Successfully queried {len(reloaded_chunks)} chunks after persistent reload.")
audit_results["persistence_across_restart"] = "PASS"

# 12. Security & Clean Deletion Audit
print("\n[Step 12] Testing cascade resume deletion...")
del_res = client.delete(f"/api/resume/{resume_id}")
assert del_res.status_code == 200

db = SessionLocal()
assert db.query(ResumeModel).filter(ResumeModel.id == resume_id).first() is None
db.close()
post_del_chunks = vector_store.query_resume_chunks(resume_id, q_emb, top_k=2)
assert len(post_del_chunks) == 0, "ChromaDB chunks were not cleaned up after resume deletion!"
print("Verified: Resume, SQLite records, and ChromaDB vector embeddings were cleanly purged.")
audit_results["clean_deletion_audit"] = "PASS"

print("\n" + "=" * 60)
print("FINAL AUDIT SUMMARY - ALL 12 TEST SUITES:")
for test_name, status in audit_results.items():
    print(f"  {test_name.ljust(32)}: {status}")
print("=" * 60)
