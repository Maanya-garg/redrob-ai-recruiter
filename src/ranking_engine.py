"""
Ranking Engine Module
Aggregates scoring metrics, applies weights, handles streaming pipeline,
and ranks candidates for the recruitment search query.
"""

import json
from typing import Dict, Any, Generator, List

from src.config import SCORING_WEIGHTS
from src.profile_builder import CandidateProfileBuilder, CandidateProfile
from src.feature_extractor import FeatureExtractor
from src.jd_parser import JobRequirements
from src.technical_score import TechnicalScoreCalculator
from src.career_score import CareerScoreCalculator
from src.behaviour_score import BehaviourScoreCalculator
from src.risk_score import RiskScoreCalculator


class RankingEngine:

    @staticmethod
    def score_candidate(candidate_json: Dict[str, Any], jd: JobRequirements) -> Dict[str, Any]:
        """
        Parses a single candidate's JSON, extracts features, calculates
        all sub-scores, aggregates them, and returns a rich scoring profile.
        """
        # 1. Parse JSON to structured CandidateProfile
        profile = CandidateProfileBuilder.build(candidate_json)

        # 2. Extract semantic features
        features = FeatureExtractor.extract(profile)

        # 3. Calculate sub-scores
        tech_breakdown = TechnicalScoreCalculator.calculate(profile, features, jd)
        career_breakdown = CareerScoreCalculator.calculate(profile, features, jd)
        behaviour_breakdown = BehaviourScoreCalculator.calculate(profile, features, jd)
        risk_breakdown = RiskScoreCalculator.calculate(profile, features, jd)

        # Extract primary scores
        s_tech = tech_breakdown["score"]
        s_career = career_breakdown["score"]
        s_behaviour = behaviour_breakdown["score"]
        s_risk = risk_breakdown["score"]

        # 4. Aggregation formula
        w = SCORING_WEIGHTS
        composite_score = (
            (w["technical"] * s_tech) +
            (w["career"] * s_career) +
            (w["behaviour"] * s_behaviour) -
            (w["risk"] * s_risk)
        )

        # Clamp final score between 0.0 and 100.0
        final_score = max(0.0, min(100.0, composite_score))

        # Check for critical blockers (Priority 2 - Gating requirements before scoring)
        is_blocked = False
        blocker_reasons = []

        # Blocker 1: Expected salary exceeds budget by 50%
        expected_salary_min = profile.behavioral_signals.expected_salary_range_inr_lpa.get("min", 0.0)
        if jd.salary_budget_max_lpa and expected_salary_min > (jd.salary_budget_max_lpa * 1.5):
            is_blocked = True
            blocker_reasons.append(
                f"Salary expectation ({expected_salary_min} LPA) severely exceeds budget ({jd.salary_budget_max_lpa} LPA)"
            )

        # Blocker 2: Location mismatch for strictly non-remote roles without willingness to relocate
        if jd.preferred_work_mode in ["onsite", "hybrid"]:
            candidate_loc_lower = profile.location.lower()
            in_target_location = any(
                loc.lower() in candidate_loc_lower for loc in jd.target_locations
            )
            if not in_target_location and not profile.behavioral_signals.willing_to_relocate:
                is_blocked = True
                blocker_reasons.append(
                    f"Candidate location ({profile.location}) is outside target area and unwilling to relocate"
                )

        # Blocker 3: Missing Core Required Skills (No overlap with JD required skills)
        if jd.required_skills:
            candidate_skill_names = {s.name.strip().lower() for s in profile.skills}
            jd_req_skills_clean = {s.strip().lower() for s in jd.required_skills}
            overlap = candidate_skill_names.intersection(jd_req_skills_clean)
            if len(overlap) == 0:
                is_blocked = True
                blocker_reasons.append("Missing mandatory core skills required for this job description")

        # Blocker 4: Missing Mandatory Experience (Tolerance buffer of 1.5 years)
        if profile.years_experience < (jd.min_years_experience - 1.5):
            is_blocked = True
            blocker_reasons.append(
                f"Candidate has only {profile.years_experience} years of experience, failing to meet the minimum required {jd.min_years_experience} years"
            )

        # Blocker 5: Technical Score below Threshold (S_tech < 50.0)
        if s_tech < 50.0:
            is_blocked = True
            blocker_reasons.append(f"Technical score of {s_tech:.1f} falls below the required threshold of 50.0")

        # Blocker 6: High Risk Candidate (S_risk > 60.0)
        if s_risk > 60.0:
            is_blocked = True
            blocker_reasons.append(f"Candidate risk score of {s_risk:.1f} exceeds the threshold of 60.0")

        # Blocker 7: Lacks specific semantic domain features required by the JD
        if "retrieval_search" in jd.required_features and features.retrieval_search < 0.15:
            is_blocked = True
            blocker_reasons.append("Lacks required hands-on experience in Search Infrastructure / Retrieval Systems")
        if "ranking_systems" in jd.required_features and features.ranking_systems < 0.15:
            is_blocked = True
            blocker_reasons.append("Lacks required hands-on experience in Ranking Pipelines / LTR")

        return {
            "candidate_id": profile.candidate_id,
            "name": profile.anonymized_name,
            "headline": profile.headline,
            "current_role": profile.current_role,
            "current_company": profile.current_company,
            "years_experience": profile.years_experience,
            "final_score": round(final_score, 2),
            "is_blocked": is_blocked,
            "blocker_reasons": blocker_reasons,
            "sub_scores": {
                "technical": tech_breakdown,
                "career": career_breakdown,
                "behaviour": behaviour_breakdown,
                "risk": risk_breakdown
            },
            "profile": profile,
            "extracted_features": features
        }

    @staticmethod
    def stream_score_candidates(
        file_path: str,
        jd: JobRequirements
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Streams candidates from a JSONL file one-by-one to conserve memory.
        """
        with open(file_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    candidate_json = json.loads(line)
                    scored_profile = RankingEngine.score_candidate(candidate_json, jd)
                    yield scored_profile
                except Exception as e:
                    # Gracefully skip corrupted JSON lines while logging error context
                    print(f"Error parsing line {line_num} in candidates database: {e}")
                    continue
