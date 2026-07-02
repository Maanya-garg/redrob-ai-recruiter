"""
Reason Generator Module
Generates human-readable, actionable recruitment feedback with candidate-specific strengths,
weaknesses, blockers, and recommendation decisions based on scores and signals.
"""

from dataclasses import dataclass
from typing import Dict, Any, List


@dataclass
class Explanation:
    strengths: List[str]
    weaknesses: List[str]
    recommendation: str


class ReasonGenerator:

    @staticmethod
    def generate(scored_cand: Dict[str, Any], jd: Any) -> Explanation:
        """
        Generates strengths, weaknesses, and a structured recommendation sentence.
        """
        strengths = []
        weaknesses = []

        sub_scores = scored_cand["sub_scores"]
        profile = scored_cand["profile"]
        features = scored_cand["extracted_features"]
        
        # 1. Candidate-Specific Strengths (Priority 5 - Recruiter Reasoning)
        # Title alignment check
        if sub_scores["technical"]["role_alignment"] >= 80.0:
            strengths.append(f"Role Alignment: Career history and title profile match standard '{jd.title}' expectations.")

        # Recommendation Systems
        if features.recommendation_systems >= 0.75:
            strengths.append("Recommendation Systems: Proven experience building RecSys pipelines (collaborative filtering, candidate generation).")

        # Search Infrastructure
        if features.retrieval_search >= 0.75:
            strengths.append("Search Infrastructure: Strong lexical and indexing search background (Elasticsearch, Solr, Lucene).")

        # Hybrid Retrieval
        if features.retrieval_search >= 0.60 and features.embeddings >= 0.60:
            strengths.append("Hybrid Retrieval: Combined experience matching dense vectors/embeddings with lexical text search queries.")

        # Vector Databases
        if features.vector_databases >= 0.70:
            strengths.append("Vector Databases: Practical experience indexing features using high-speed vector DBs (Milvus, Pinecone, FAISS).")

        # Ranking Pipelines
        if features.ranking_systems >= 0.75:
            strengths.append("Ranking Pipelines: Deep competence in learning-to-rank models (LTR, NDCG evaluation, re-ranking pipelines).")

        # Production LLM Systems
        has_llm_skill = any(
            kw in [s.name for s in profile.skills] or kw in profile.summary.lower()
            for kw in ["llm", "transformer", "fine-tune", "lora", "gpt", "rag"]
        )
        if features.production_ml >= 0.60 and has_llm_skill:
            strengths.append("Production LLM Systems: Hands-on experience optimizing and deploying large language models to production.")
        elif features.production_ml >= 0.75:
            strengths.append("MLOps / Production Serving: Practical experience orchestrating inference pipelines and containerized serving.")

        # Leadership
        if features.leadership >= 0.75:
            strengths.append("Technical Leadership: Background architecting systems, mentoring team members, and owning tech decisions.")

        # Open Source
        if features.open_source >= 0.70:
            strengths.append(f"Open Source Contributions: Public code activity (GitHub score: {profile.behavioral_signals.github_activity_score}).")

        # Career Progression
        if sub_scores["career"]["title_progression"] >= 90.0:
            strengths.append("Strong Career Progression: Upward title trajectory indicating consistent promotional growth.")

        # Product Company Experience
        if features.product_company >= 0.70:
            strengths.append("Product Company Experience: Career history shows background in SaaS or customer-facing scaling platforms.")

        # Experience threshold
        if sub_scores["career"]["experience_match"] >= 100.0:
            strengths.append(f"Tenure Fit: Meets experience guidelines with {profile.years_experience} years of industry practice.")
        elif sub_scores["career"]["stability_index"] >= 90.0:
            strengths.append("Career Stability: Long job tenures indicate commitment and stable career performance.")

        # Education
        if sub_scores["career"]["education_prestige"] >= 80.0:
            strengths.append("Academic Credentials: Degree from a tier-1/tier-2 academic institution.")

        # Behavioural Responsiveness
        if sub_scores["behaviour"]["responsiveness"] >= 85.0:
            strengths.append("Recruiter Responsiveness: Highly responsive to platform outreach with fast turnarounds.")

        if not strengths:
            strengths.append("Basic skill overlap with key recruiter targets.")

        # 2. Weaknesses / Risks Extraction (Recruiter-friendly reasons)
        if scored_cand["is_blocked"]:
            for blocker in scored_cand["blocker_reasons"]:
                weaknesses.append(f"BLOCKER: {blocker}")

        if sub_scores["career"]["experience_match"] < 60.0:
            weaknesses.append(f"Under-experienced: Candidate has only {profile.years_experience} years of experience (JD requests {jd.min_years_experience}+).")
        
        if sub_scores["career"]["stability_index"] < 60.0:
            weaknesses.append("Job Hopping: History of frequent transitions and short tenures.")

        if sub_scores["technical"]["score"] < 50.0:
            weaknesses.append("Technical score below threshold.")

        if sub_scores["risk"]["notice_period_risk"] >= 80.0:
            weaknesses.append(f"Onboarding Delay: Long notice period ({profile.behavioral_signals.notice_period_days} days) may delay hire.")
        if sub_scores["risk"]["ghosting_risk"] >= 50.0:
            weaknesses.append("Ghosting Risk: Candidate has a high rate of failing to attend scheduled interviews.")
        if sub_scores["risk"]["renege_risk"] >= 50.0:
            weaknesses.append("Renege Risk: Low offer acceptance rate indicates potential high risk of declining offers.")
        if sub_scores["risk"]["salary_risk"] >= 60.0:
            weaknesses.append(f"Salary Mismatch: Expected LPA ({profile.behavioral_signals.expected_salary_range_inr_lpa.get('min')} LPA) is above budget.")
        if sub_scores["risk"]["location_risk"] >= 80.0:
            weaknesses.append(f"Location Mismatch: Candidate located in {profile.location} is unwilling to relocate for an onsite/hybrid role.")

        # 3. Formulate Recommendation (Priority 2 & 5)
        final_score = scored_cand["final_score"]
        is_blocked = scored_cand["is_blocked"]

        # Recruiter Decision Hierarchy
        if is_blocked:
            recommendation = "REJECT: Does not satisfy JD requirements."
            # Append specific block reasons to weaknesses if not already there
            for blocker in scored_cand["blocker_reasons"]:
                if blocker not in weaknesses:
                    weaknesses.append(blocker)
        elif final_score < 55.0:
            recommendation = "REJECT: Technical score below threshold."
            weaknesses.append("Does not satisfy JD requirements.")
        elif final_score < 75.0:
            recommendation = "CONSIDER: Moderate technical match."
            # Check for missing elements and add standard Consider reasons
            if features.vector_databases < 0.60:
                weaknesses.append("Missing vector database production experience.")
        else:
            recommendation = "HIRE: Strong candidate satisfies hiring profile."
            # Add top hire positive markers
            if features.production_ml >= 0.70:
                strengths.append("Strong production ML experience.")
            if features.retrieval_search >= 0.70 and features.ranking_systems >= 0.70:
                strengths.append("Excellent retrieval and ranking background.")
            if features.embeddings >= 0.70:
                strengths.append("Matches required embeddings experience.")

        # Clean duplicate bullet points
        strengths = list(dict.fromkeys(strengths))
        weaknesses = list(dict.fromkeys(weaknesses))

        return Explanation(
            strengths=strengths,
            weaknesses=weaknesses,
            recommendation=recommendation
        )
