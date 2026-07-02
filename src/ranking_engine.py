"""
Ranking Engine Module
Evidence-based recruiter decision engine.
- Dynamic scoring weights inferred from JD role_type.
- No hard binary rejection gates: all signals reduce confidence gradually.
- Produces hiring_confidence (0-100%) alongside composite score.
"""

import json
from typing import Dict, Any, Generator, List

from src.profile_builder import CandidateProfileBuilder, CandidateProfile
from src.feature_extractor import FeatureExtractor
from src.jd_parser import JobRequirements
from src.technical_score import TechnicalScoreCalculator
from src.career_score import CareerScoreCalculator
from src.behaviour_score import BehaviourScoreCalculator
from src.risk_score import RiskScoreCalculator


# ---------------------------------------------------------------------------
# Dynamic weights by role type
# ---------------------------------------------------------------------------
ROLE_WEIGHTS = {
    "research":   {"technical": 0.55, "career": 0.20, "behaviour": 0.15, "risk": 0.10},
    "startup":    {"technical": 0.40, "career": 0.20, "behaviour": 0.25, "risk": 0.15},
    "leadership": {"technical": 0.30, "career": 0.35, "behaviour": 0.20, "risk": 0.15},
    "platform":   {"technical": 0.45, "career": 0.25, "behaviour": 0.15, "risk": 0.15},
    "default":    {"technical": 0.50, "career": 0.25, "behaviour": 0.10, "risk": 0.15},
}


def _get_weights(jd: JobRequirements) -> Dict[str, float]:
    return ROLE_WEIGHTS.get(getattr(jd, "role_type", "default"), ROLE_WEIGHTS["default"])


class RankingEngine:

    @staticmethod
    def score_candidate(candidate_json: Dict[str, Any], jd: JobRequirements) -> Dict[str, Any]:
        """
        Parses a candidate JSON, extracts features, calculates all sub-scores,
        aggregates using JD-driven dynamic weights, and returns a rich scoring
        profile including hiring_confidence and soft risk signals.
        """
        # 1. Build profile
        profile = CandidateProfileBuilder.build(candidate_json)

        # 2. Extract semantic features
        features = FeatureExtractor.extract(profile)

        # 3. Sub-scores
        tech_breakdown = TechnicalScoreCalculator.calculate(profile, features, jd)
        career_breakdown = CareerScoreCalculator.calculate(profile, features, jd)
        behaviour_breakdown = BehaviourScoreCalculator.calculate(profile, features, jd)
        risk_breakdown = RiskScoreCalculator.calculate(profile, features, jd)

        s_tech = tech_breakdown["score"]
        s_career = career_breakdown["score"]
        s_behaviour = behaviour_breakdown["score"]
        s_risk = risk_breakdown["score"]

        # 4. Dynamic weights from role_type
        w = _get_weights(jd)

        composite = (
            (w["technical"]  * s_tech) +
            (w["career"]     * s_career) +
            (w["behaviour"]  * s_behaviour) -
            (w["risk"]       * s_risk)
        )
        final_score = max(0.0, min(100.0, composite))

        # ---------------------------------------------------------------
        # 5. Soft confidence penalties (replace hard gates)
        #    Each signal REDUCES hiring_confidence instead of rejecting.
        # ---------------------------------------------------------------
        confidence_start = final_score
        confidence_penalties = []

        # Salary severely over budget (>50%)
        expected_min = profile.behavioral_signals.expected_salary_range_inr_lpa.get("min", 0.0)
        if jd.salary_budget_max_lpa and expected_min > (jd.salary_budget_max_lpa * 1.5):
            confidence_start -= 15.0
            confidence_penalties.append(
                f"Salary expectation ({expected_min} LPA) significantly exceeds budget "
                f"({jd.salary_budget_max_lpa} LPA)"
            )

        # Location mismatch for restricted roles
        if jd.preferred_work_mode in ["onsite", "hybrid"] and jd.target_locations:
            candidate_loc_lower = profile.location.lower()
            in_target = any(loc.lower() in candidate_loc_lower for loc in jd.target_locations)
            if not in_target and not profile.behavioral_signals.willing_to_relocate:
                confidence_start -= 10.0
                confidence_penalties.append(
                    f"Location mismatch: {profile.location} (unwilling to relocate)"
                )

        # Experience well below minimum (>2 years short)
        exp_gap = jd.min_years_experience - profile.years_experience
        if exp_gap > 2.0:
            confidence_start -= min(20.0, exp_gap * 5.0)
            confidence_penalties.append(
                f"Experience gap: {profile.years_experience:.1f} yrs vs {jd.min_years_experience:.0f}+ required"
            )

        # Missing core required skills (no overlap at all)
        if jd.required_skills:
            candidate_skill_names = {s.name.strip().lower() for s in profile.skills}
            jd_req_clean = {s.strip().lower() for s in jd.required_skills[:15]}  # top 15 only
            overlap = candidate_skill_names & jd_req_clean
            if len(overlap) == 0:
                confidence_start -= 12.0
                confidence_penalties.append("No overlap with core required skills")

        # Very weak technical score
        if s_tech < 30.0:
            confidence_start -= 15.0
            confidence_penalties.append(f"Very low technical alignment ({s_tech:.0f}/100)")

        # Very high risk
        if s_risk > 70.0:
            confidence_start -= 10.0
            confidence_penalties.append(f"Elevated risk score ({s_risk:.0f}/100)")

        # Wrong domain — consulting/services-only
        if features.services_only >= 0.9 and s_tech < 50.0:
            confidence_start -= 8.0
            confidence_penalties.append("Services-only background with low technical match")

        hiring_confidence = max(0.0, min(100.0, confidence_start))

        # ---------------------------------------------------------------
        # 6. Decision label from hiring_confidence
        # ---------------------------------------------------------------
        if hiring_confidence >= 85.0:
            decision = "Strong Hire"
        elif hiring_confidence >= 70.0:
            decision = "Interview"
        elif hiring_confidence >= 55.0:
            decision = "Potential Hire"
        elif hiring_confidence >= 40.0:
            decision = "Hold"
        elif hiring_confidence >= 20.0:
            decision = "Reject"
        else:
            decision = "Not Relevant"

        # Legacy compat: is_blocked = True for Reject / Not Relevant
        is_blocked = hiring_confidence < 40.0
        blocker_reasons = confidence_penalties if is_blocked else []

        return {
            "candidate_id": profile.candidate_id,
            "name": profile.anonymized_name,
            "headline": profile.headline,
            "current_role": profile.current_role,
            "current_company": profile.current_company,
            "years_experience": profile.years_experience,
            "final_score": round(final_score, 2),
            "hiring_confidence": round(hiring_confidence, 2),
            "decision": decision,
            "is_blocked": is_blocked,
            "blocker_reasons": blocker_reasons,
            "confidence_penalties": confidence_penalties,
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
        """Streams candidates from a JSONL file, scoring each one."""
        with open(file_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    candidate_json = json.loads(line)
                    yield RankingEngine.score_candidate(candidate_json, jd)
                except Exception as e:
                    print(f"[RankingEngine] Error on line {line_num}: {e}")
                    continue
