import pytest
from backend.app.services.job_matcher import job_matcher

def test_skill_overlap_calculation():
    resume_skills = ["Python", "SQL", "FastAPI", "Docker"]
    jd_text = "Looking for an engineer with Python, SQL, Docker, and Kubernetes experience."
    
    res = job_matcher.match_resume_to_jd(
        resume_id=1,
        resume_text="Built APIs with FastAPI, Docker, SQL, and Python.",
        resume_skills=resume_skills,
        job_description=jd_text
    )
    
    assert "Python" in res["matching_skills"]
    assert "SQL" in res["matching_skills"]
    assert "Docker" in res["matching_skills"]
    assert "Kubernetes" in res["missing_skills"]
    assert res["match_percentage"] > 50.0
