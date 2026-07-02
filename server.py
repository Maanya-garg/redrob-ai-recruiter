"""
FastAPI Server Wrapper for Redrob AI Recruiter Ranking Engine.
Connects the React frontend to the real Python ranking modules.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os
import time
from typing import List, Optional

# Import the existing backend engine modules
from src.jd_parser import JDParser, JobRequirements
from src.profile_builder import CandidateProfileBuilder
from src.ranking_engine import RankingEngine
from src.reason_generator import ReasonGenerator

app = FastAPI(title="Redrob AI Recruiter API", version="1.0.0")

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Anchor all paths to the directory containing this file so they are
# correct regardless of the working directory uvicorn is started from.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
SAMPLE_CANDIDATES_PATH = os.path.join(DATA_DIR, "sample_candidates.json")
FULL_CANDIDATES_PATH = os.path.join(DATA_DIR, "candidates.jsonl")
JD_PATH = os.path.join(DATA_DIR, "job_description.md")

print("[STARTUP] server.py loaded from:", __file__)
print("[STARTUP] BASE_DIR:", BASE_DIR)
print("[STARTUP] JD_PATH:", JD_PATH)

# Cache to store last scored results for details query
SCORED_CACHE = {}


class RankRequest(BaseModel):
    jd_text: Optional[str] = None
    use_sample: bool = True
    candidate_limit: int = 500


def get_initial_default_jd_markdown() -> str:
    """Returns the default commercial-grade Job Description for Senior AI/ML Engineer."""
    return """# Senior AI & Machine Learning Engineer

We are seeking a Senior AI & Machine Learning Engineer to join our team and build high-performance search and recommendation systems.

## Required Experience
- Minimum 5 years of relevant professional experience.

## Required Skills
- Python
- NLP
- PyTorch
- SQL
- Spark
- Airflow

## Preferred Skills
- Weights & Biases
- LoRA
- BentoML
- Milvus
- AWS
- Docker

## Target Education
- Degrees: Master, Bachelor
- Fields: Computer Science, Statistics

## Target Budget
- Max salary: 35 LPA

## Work Mode
- Mode: Hybrid
- Locations: Toronto, Chennai, Bangalore

## Mandatory Requirements
- Candidate must have at least 1 core required skill (Python, NLP, PyTorch).
- Technical Score must be at least 50/100 to pass first round.
- Years of Experience must not be less than 3 years.

## Behavioural Expectations
- Candidate must be highly responsive to recruiter outreach on the platform.
- A verified email address and LinkedIn connection is preferred.
"""


@app.get("/api/health")
def health():
    return {"status": "ok", "timestamp": time.time()}


@app.post("/api/upload-jd")
async def upload_jd(file: UploadFile = File(...)):
    os.makedirs(DATA_DIR, exist_ok=True)

    print("========== UPLOAD DEBUG ==========")
    print("ABS PATH:", os.path.abspath(JD_PATH))
    print("Filename:", file.filename)

    content = await file.read()
    jd_str = content.decode("utf-8")

    print("Bytes received:", len(content))
    print("First 500 chars:")
    print(repr(jd_str[:500]))
    print("==================================")

    # Guard: reject payloads that are obviously not a real JD
    # (e.g. the Swagger UI default placeholder "string" is only 6 bytes)
    if len(jd_str.strip()) < 50:
        print("UPLOAD REJECTED: content too short to be a real JD (", len(jd_str.strip()), "chars)")
        raise HTTPException(
            status_code=400,
            detail=f"Uploaded content is too short ({len(jd_str.strip())} chars). Please upload a valid markdown job description."
        )

    with open(JD_PATH, "w", encoding="utf-8") as f:
        f.write(jd_str)

    # Immediately read back to confirm the write succeeded
    print("AFTER WRITE – reading back:")
    with open(JD_PATH, "r", encoding="utf-8") as f:
        print(repr(f.read()[:500]))

    return {
        "status": "success",
        "message": "Job description uploaded successfully"
    }
@app.post("/api/upload-candidates")
async def upload_candidates(file: UploadFile = File(...)):
    """Uploads a JSONL database of candidates to data/candidates.jsonl."""
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        # Save candidates database file
        with open(FULL_CANDIDATES_PATH, "wb") as f:
            while content := await file.read(1024 * 1024):  # 1MB chunks
                f.write(content)
        return {"status": "success", "message": "Candidates file uploaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to save candidates file: {e}")


@app.get("/api/jd")
def get_current_jd():
    """Gets the currently saved JD or returns the default fallback JD."""
    os.makedirs(DATA_DIR, exist_ok=True)
    text = ""
    if os.path.exists(JD_PATH):
        with open(JD_PATH, "r", encoding="utf-8") as f:
            text = f.read().strip()

    # Treat obviously corrupted / placeholder content as absent
    # (e.g. Swagger default "string" is only 6 bytes)
    if len(text) < 50:
        text = ""

    if not text:
        text = get_initial_default_jd_markdown()
        with open(JD_PATH, "w", encoding="utf-8") as f:
            f.write(text)

    print("========== SERVER DEBUG [GET /api/jd] ==========")
    print("ABS PATH:", os.path.abspath(JD_PATH))
    print("FILE EXISTS:", os.path.exists(JD_PATH))
    print("FILE SIZE:", os.path.getsize(JD_PATH), "bytes")
    print("TEXT LENGTH:", len(text))
    print("FIRST 500 CHARACTERS:")
    print(repr(text[:500]))
    print("================================================")
    jd = JDParser.parse_text(text)
    
    jd_resp = {
        "title": jd.title,
        "min_years_experience": jd.min_years_experience,
        "required_skills": jd.required_skills,
        "preferred_skills": jd.preferred_skills,
        "required_education_degrees": jd.required_education_degrees,
        "required_education_fields": jd.required_education_fields,
        "salary_budget_max_lpa": jd.salary_budget_max_lpa,
        "preferred_work_mode": jd.preferred_work_mode,
        "target_locations": jd.target_locations,
        "required_features": jd.required_features,
        "mandatory_requirements": jd.mandatory_requirements,
        "behavioural_expectations": jd.behavioural_expectations
    }
    
    return {
        "markdown": text,
        "requirements": jd_resp
    }


@app.post("/api/rank")
def rank_candidates(req: RankRequest):
    """
    Executes the ranking pipeline using the saved JD and candidates.
    Supports streaming and limit variables.
    """
    global SCORED_CACHE
    start_time = time.time()
    
    # 1. Parse Job Description
    if req.jd_text:
        text_for_parse = req.jd_text
        print("========== SERVER DEBUG [POST /api/rank – jd_text branch] ==========")
        print("TEXT LENGTH:", len(text_for_parse))
        print("FIRST 500 CHARACTERS:")
        print(repr(text_for_parse[:500]))
        print("====================================================================")
        jd = JDParser.parse_text(text_for_parse)
        # Also persist it
        with open(JD_PATH, "w", encoding="utf-8") as f:
            f.write(text_for_parse)
    else:
        text = ""
        if os.path.exists(JD_PATH):
            with open(JD_PATH, "r", encoding="utf-8") as f:
                text = f.read().strip()
        
        if not text:
            text = get_initial_default_jd_markdown()
            with open(JD_PATH, "w", encoding="utf-8") as f:
                f.write(text)

        print("========== SERVER DEBUG [POST /api/rank – file branch] ==========")
        print("JD_PATH:", JD_PATH)
        print("TEXT LENGTH:", len(text))
        print("FIRST 500 CHARACTERS:")
        print(repr(text[:500]))
        print("=================================================================")
        jd = JDParser.parse_text(text)

    # 2. Collect Candidates List to Score
    candidates_to_score = []
    
    if req.use_sample:
        # Use sample candidates
        if os.path.exists(SAMPLE_CANDIDATES_PATH):
            with open(SAMPLE_CANDIDATES_PATH, "r", encoding="utf-8") as f:
                candidates_to_score = json.load(f)
        else:
            # Fallback check
            raise HTTPException(status_code=404, detail="Sample candidates file not found")
    else:
        # Stream from full candidates.jsonl file up to limit
        if os.path.exists(FULL_CANDIDATES_PATH):
            with open(FULL_CANDIDATES_PATH, "r", encoding="utf-8") as f:
                for idx, line in enumerate(f):
                    if idx >= req.candidate_limit:
                        break
                    line_strip = line.strip()
                    if line_strip:
                        try:
                            candidates_to_score.append(json.loads(line_strip))
                        except Exception:
                            continue
        else:
            # Fallback to sample if full candidates.jsonl doesn't exist yet
            if os.path.exists(SAMPLE_CANDIDATES_PATH):
                with open(SAMPLE_CANDIDATES_PATH, "r", encoding="utf-8") as f:
                    candidates_to_score = json.load(f)
            else:
                raise HTTPException(status_code=404, detail="No candidate files found to rank")

    # 3. Score all candidates using the RankingEngine
    scored_candidates = []
    blocked_count = 0
    unblocked_count = 0

    for cand_json in candidates_to_score:
        try:
            scored = RankingEngine.score_candidate(cand_json, jd)
            explanation = ReasonGenerator.generate(scored, jd)
            
            # Pack explanation inside candidate profile
            scored["explanation"] = {
                "strengths": explanation.strengths,
                "weaknesses": explanation.weaknesses,
                "recommendation": explanation.recommendation
            }
            
            if scored["is_blocked"]:
                blocked_count += 1
            else:
                unblocked_count += 1
                
            scored_candidates.append(scored)
        except Exception as e:
            print(f"Error ranking candidate: {e}")
            continue

    # Sort scored candidates: unblocked first, sorted descending by final score
    scored_candidates.sort(key=lambda x: (not x["is_blocked"], x["final_score"]), reverse=True)

    # Cache result sets for candidate profile detail fetches
    SCORED_CACHE = {c["candidate_id"]: c for c in scored_candidates}

    elapsed_time = time.time() - start_time

    # Construct requirements response JSON
    jd_resp = {
        "title": jd.title,
        "min_years_experience": jd.min_years_experience,
        "required_skills": jd.required_skills,
        "preferred_skills": jd.preferred_skills,
        "required_education_degrees": jd.required_education_degrees,
        "required_education_fields": jd.required_education_fields,
        "salary_budget_max_lpa": jd.salary_budget_max_lpa,
        "preferred_work_mode": jd.preferred_work_mode,
        "target_locations": jd.target_locations,
        "required_features": jd.required_features,
        "mandatory_requirements": jd.mandatory_requirements,
        "behavioural_expectations": jd.behavioural_expectations
    }

    # Clean Pydantic/Dataclass objects for output serialization
    serialized_candidates = []
    for sc in scored_candidates:
        profile = sc["profile"]
        serialized_candidates.append({
            "candidate_id": sc["candidate_id"],
            "name": sc["name"],
            "headline": sc["headline"],
            "current_role": sc["current_role"],
            "current_company": sc["current_company"],
            "years_experience": sc["years_experience"],
            "final_score": sc["final_score"],
            "is_blocked": sc["is_blocked"],
            "blocker_reasons": sc["blocker_reasons"],
            "sub_scores": sc["sub_scores"],
            "explanation": sc["explanation"],
            "extracted_features": {
                "production_ml": sc["extracted_features"].production_ml,
                "retrieval_search": sc["extracted_features"].retrieval_search,
                "recommendation_systems": sc["extracted_features"].recommendation_systems,
                "ranking_systems": sc["extracted_features"].ranking_systems,
                "vector_databases": sc["extracted_features"].vector_databases,
                "embeddings": sc["extracted_features"].embeddings,
                "leadership": sc["extracted_features"].leadership,
                "product_company": sc["extracted_features"].product_company,
                "services_only": sc["extracted_features"].services_only,
                "open_source": sc["extracted_features"].open_source,
                "candidate_activity": sc["extracted_features"].candidate_activity
            },
            "profile": {
                "candidate_id": profile.candidate_id,
                "anonymized_name": profile.anonymized_name,
                "headline": profile.headline,
                "summary": profile.summary,
                "current_role": profile.current_role,
                "current_company": profile.current_company,
                "current_company_size": profile.current_company_size,
                "current_industry": profile.current_industry,
                "location": profile.location,
                "country": profile.country,
                "years_experience": profile.years_experience,
                "skills": [
                    {
                        "name": s.name,
                        "proficiency": s.proficiency,
                        "endorsements": s.endorsements,
                        "duration_months": s.duration_months
                    } for s in profile.skills
                ],
                "education": [
                    {
                        "institution": e.institution,
                        "degree": e.degree,
                        "field_of_study": e.field_of_study,
                        "start_year": e.start_year,
                        "end_year": e.end_year,
                        "grade": e.grade,
                        "tier": e.tier
                    } for e in profile.education
                ],
                "certifications": [
                    {
                        "name": cert.name,
                        "issuer": cert.issuer,
                        "year": cert.year
                    } for cert in profile.certifications
                ],
                "languages": [
                    {
                        "language": lang.language,
                        "proficiency": lang.proficiency
                    } for lang in profile.languages
                ],
                "career_history": [
                    {
                        "company": job.company,
                        "role": job.role,
                        "description": job.description,
                        "start_date": job.start_date,
                        "end_date": job.end_date,
                        "duration_months": job.duration_months,
                        "is_current": job.is_current,
                        "industry": job.industry,
                        "company_size": job.company_size
                    } for job in profile.career_history
                ],
                "behavioral_signals": {
                    "profile_completeness_score": profile.behavioral_signals.profile_completeness_score,
                    "signup_date": profile.behavioral_signals.signup_date,
                    "last_active_date": profile.behavioral_signals.last_active_date,
                    "open_to_work_flag": profile.behavioral_signals.open_to_work_flag,
                    "profile_views_received_30d": profile.behavioral_signals.profile_views_received_30d,
                    "applications_submitted_30d": profile.behavioral_signals.applications_submitted_30d,
                    "recruiter_response_rate": profile.behavioral_signals.recruiter_response_rate,
                    "avg_response_time_hours": profile.behavioral_signals.avg_response_time_hours,
                    "skill_assessment_scores": profile.behavioral_signals.skill_assessment_scores,
                    "connection_count": profile.behavioral_signals.connection_count,
                    "endorsements_received": profile.behavioral_signals.endorsements_received,
                    "notice_period_days": profile.behavioral_signals.notice_period_days,
                    "expected_salary_range_inr_lpa": profile.behavioral_signals.expected_salary_range_inr_lpa,
                    "preferred_work_mode": profile.behavioral_signals.preferred_work_mode,
                    "willing_to_relocate": profile.behavioral_signals.willing_to_relocate,
                    "github_activity_score": profile.behavioral_signals.github_activity_score,
                    "search_appearance_30d": profile.behavioral_signals.search_appearance_30d,
                    "saved_by_recruiters_30d": profile.behavioral_signals.saved_by_recruiters_30d,
                    "interview_completion_rate": profile.behavioral_signals.interview_completion_rate,
                    "offer_acceptance_rate": profile.behavioral_signals.offer_acceptance_rate,
                    "verified_email": profile.behavioral_signals.verified_email,
                    "verified_phone": profile.behavioral_signals.verified_phone,
                    "linkedin_connected": profile.behavioral_signals.linkedin_connected
                }
            }
        })

    return {
        "processed_count": len(candidates_to_score),
        "unblocked_count": unblocked_count,
        "blocked_count": blocked_count,
        "elapsed_time": round(elapsed_time, 3),
        "candidates": serialized_candidates,
        "jd": jd_resp
    }


@app.get("/api/candidates/{candidate_id}")
def get_candidate_details(candidate_id: str):
    """Fetches details of a specific candidate from the cache."""
    if candidate_id not in SCORED_CACHE:
        raise HTTPException(
            status_code=404, 
            detail=f"Candidate {candidate_id} details not found. Please run the ranking process first."
        )
    return SCORED_CACHE[candidate_id]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
