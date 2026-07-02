"""
Career Score Calculator Module
Calculates S_career (0-100) using:
- Semantic domain trajectory (not just experience years)
- Role alignment: correct domain raises score, wrong domain applies penalty
- Product vs services background
- Stability and progression
"""

import re
from typing import Dict, Any, List

from src.config import (
    COMPANY_SIZE_PRESTIGE_WEIGHTS,
    EDUCATION_TIER_MULTIPLIERS,
    EXPERIENCE_UNDER_PENALTY,
    STABILITY_MIN_TENURE_MONTHS,
    STABILITY_PENALTY_MAX,
)
from src.profile_builder import CandidateProfile
from src.feature_extractor import ExtractedFeatures
from src.jd_parser import JobRequirements


# ---------------------------------------------------------------------------
# Domain classification helpers
# ---------------------------------------------------------------------------

# Roles in the target domain (search, ranking, recommendations, retrieval)
TARGET_DOMAIN_ROLES = [
    "recommendation engineer", "search engineer", "ranking engineer",
    "information retrieval", "ir engineer", "applied ml", "ml engineer",
    "machine learning engineer", "ai engineer", "nlp engineer",
    "ml platform", "ml infrastructure", "research scientist", "research engineer",
    "data scientist", "marketplace search", "candidate matching",
    "vector search", "applied scientist",
]

# Roles adjacent to the domain — some value, partial credit
ADJACENT_DOMAIN_ROLES = [
    "software engineer", "backend engineer", "data engineer",
    "systems engineer", "platform engineer", "full stack",
]

# Wrong domain — heavy penalty regardless of AI keywords
WRONG_DOMAIN_ROLES = [
    "marketing", "human resources", "hr manager", "graphic design",
    "civil engineer", "mechanical engineer", "accountant", "finance",
    "lawyer", "legal counsel", "sales", "business development",
    "recruiter", "project manager", "scrum master", "agile coach",
    "computer vision only", "robotics engineer", "speech recognition",
]

# Product-type company keywords (boosts career score)
PRODUCT_COMPANY_SIGNALS = [
    "saas", "product-based", "b2b", "b2c", "marketplace", "platform",
    "daily active users", "monthly active users", "retention", "churn",
    "a/b testing", "user growth", "microservices", "scaling platform",
]


def _classify_role(title: str) -> str:
    """Returns 'target', 'adjacent', 'wrong', or 'unknown'."""
    t = title.lower()
    if any(wr in t for wr in WRONG_DOMAIN_ROLES):
        return "wrong"
    if any(td in t for td in TARGET_DOMAIN_ROLES):
        return "target"
    if any(ad in t for ad in ADJACENT_DOMAIN_ROLES):
        return "adjacent"
    return "unknown"


def _domain_alignment_bonus(profile: CandidateProfile) -> float:
    """
    Returns a domain alignment score (0.0–1.0).
    Target domain roles → high score.
    Wrong domain roles  → penalty.
    """
    all_roles = [profile.current_role, profile.headline]
    for job in profile.career_history:
        all_roles.append(job.role)

    target_count = 0
    wrong_count = 0
    adjacent_count = 0

    for role in all_roles:
        cls = _classify_role(role)
        if cls == "target":
            target_count += 1
        elif cls == "wrong":
            wrong_count += 1
        elif cls == "adjacent":
            adjacent_count += 1

    total = len(all_roles)
    if total == 0:
        return 0.5

    if wrong_count / total >= 0.6:
        return 0.10  # mostly wrong domain — heavy penalty
    if target_count >= 2:
        return min(1.0, 0.70 + target_count * 0.05)
    if target_count == 1:
        return 0.65
    if adjacent_count >= 2:
        return 0.50
    return 0.40


class CareerScoreCalculator:

    @staticmethod
    def calculate(
        profile: CandidateProfile,
        extracted_features: ExtractedFeatures,
        jd: JobRequirements
    ) -> Dict[str, Any]:

        # ---------------------------------------------------------------
        # 1. Experience match (30% weight)
        # ---------------------------------------------------------------
        exp_score = 100.0
        exp_diff = jd.min_years_experience - profile.years_experience
        if exp_diff > 0:
            exp_score = max(0.0, 100.0 - (exp_diff * EXPERIENCE_UNDER_PENALTY))

        # ---------------------------------------------------------------
        # 2. Domain alignment (25% weight — NEW, replaces raw prestige)
        # ---------------------------------------------------------------
        domain_score = _domain_alignment_bonus(profile) * 100.0

        # ---------------------------------------------------------------
        # 3. Job stability (20% weight)
        # ---------------------------------------------------------------
        stability_score = 100.0
        job_count = len(profile.career_history)
        if job_count > 0:
            total_months = sum(j.duration_months for j in profile.career_history)
            if total_months == 0:
                total_months = int(profile.years_experience * 12)
            avg_tenure = total_months / job_count
            if avg_tenure >= STABILITY_MIN_TENURE_MONTHS:
                stability_score = 100.0
            else:
                ratio = avg_tenure / STABILITY_MIN_TENURE_MONTHS
                stability_score = max(0.0, 100.0 - (1.0 - ratio) * STABILITY_PENALTY_MAX)
        else:
            stability_score = 90.0 if profile.years_experience > 0 else 100.0

        # ---------------------------------------------------------------
        # 4. Title progression (10% weight)
        # ---------------------------------------------------------------
        progression_score = 75.0
        if job_count >= 2:
            rank_map = {
                "intern": 1, "trainee": 1, "junior": 2, "associate": 3,
                "mid": 4, "developer": 4, "engineer": 4, "senior": 5,
                "lead": 6, "principal": 7, "architect": 7, "manager": 8,
                "director": 9, "vp": 10, "chief": 10, "head": 10,
            }

            def get_rank(role: str) -> int:
                r = role.lower()
                for kw, rank in sorted(rank_map.items(), key=lambda x: -len(x[0])):
                    if kw in r:
                        return rank
                return 4

            try:
                sorted_jobs = sorted(
                    profile.career_history,
                    key=lambda x: x.start_date or "1970-01-01"
                )
                first_rank = get_rank(sorted_jobs[0].role)
                last_rank = get_rank(sorted_jobs[-1].role)
                if last_rank > first_rank:
                    progression_score = 100.0
                elif last_rank == first_rank:
                    progression_score = 80.0
                else:
                    progression_score = 50.0
            except Exception:
                progression_score = 75.0

        # ---------------------------------------------------------------
        # 5. Product company & education prestige (15% weight)
        # ---------------------------------------------------------------
        company_scores: List[float] = []
        for job in profile.career_history:
            size_score = COMPANY_SIZE_PRESTIGE_WEIGHTS.get(job.company_size, 0.70)
            # Boost for product-type companies
            desc_lower = job.description.lower()
            product_signals = sum(1 for sig in PRODUCT_COMPANY_SIGNALS if sig in desc_lower)
            if product_signals >= 2:
                size_score = min(1.0, size_score + 0.15)
            company_scores.append(size_score * 100.0)
        company_prestige = sum(company_scores) / len(company_scores) if company_scores else 70.0

        edu_scores: List[float] = []
        for edu in profile.education:
            edu_scores.append(EDUCATION_TIER_MULTIPLIERS.get(edu.tier, 0.20) * 100.0)
        education_prestige = max(edu_scores) if edu_scores else 50.0

        prestige_score = 0.50 * company_prestige + 0.50 * education_prestige

        # ---------------------------------------------------------------
        # 6. Aggregate
        # ---------------------------------------------------------------
        final_career_score = (
            0.30 * exp_score +
            0.25 * domain_score +
            0.20 * stability_score +
            0.10 * progression_score +
            0.15 * prestige_score
        )
        final_career_score = max(0.0, min(100.0, final_career_score))

        return {
            "score": round(final_career_score, 2),
            "experience_match": round(exp_score, 2),
            "domain_alignment": round(domain_score, 2),
            "stability_index": round(stability_score, 2),
            "title_progression": round(progression_score, 2),
            "prestige_rating": round(prestige_score, 2),
            "company_prestige": round(company_prestige, 2),
            "education_prestige": round(education_prestige, 2),
        }
