"""
Career Score Calculator Module
Calculates S_career (0-100) based on experience alignment, stability index,
vertical title progression, and prestige (employer brand size + school tier).
"""

from typing import Dict, Any
import re

from src.config import (
    COMPANY_SIZE_PRESTIGE_WEIGHTS,
    EDUCATION_TIER_MULTIPLIERS,
    EXPERIENCE_UNDER_PENALTY,
    STABILITY_MIN_TENURE_MONTHS,
    STABILITY_PENALTY_MAX
)
from src.profile_builder import CandidateProfile
from src.feature_extractor import ExtractedFeatures
from src.jd_parser import JobRequirements


class CareerScoreCalculator:

    @staticmethod
    def calculate(
        profile: CandidateProfile,
        extracted_features: ExtractedFeatures,
        jd: JobRequirements
    ) -> Dict[str, Any]:
        """
        Calculates S_career and returns breakdown metrics.
        """
        # 1. Experience Match (35% weight)
        exp_score = 100.0
        exp_diff = jd.min_years_experience - profile.years_experience
        if exp_diff > 0:
            exp_score = max(0.0, 100.0 - (exp_diff * EXPERIENCE_UNDER_PENALTY))

        # 2. Stability Index / Job Hopping (25% weight)
        stability_score = 100.0
        job_count = len(profile.career_history)
        
        if job_count > 0:
            total_months = sum(j.duration_months for j in profile.career_history)
            if total_months == 0:
                total_months = int(profile.years_experience * 12)
                
            avg_tenure_months = total_months / job_count
            
            if avg_tenure_months >= STABILITY_MIN_TENURE_MONTHS:
                stability_score = 100.0
            else:
                ratio = avg_tenure_months / STABILITY_MIN_TENURE_MONTHS
                penalty = (1.0 - ratio) * STABILITY_PENALTY_MAX
                stability_score = max(0.0, 100.0 - penalty)
        else:
            if profile.years_experience > 0:
                stability_score = 90.0
            else:
                stability_score = 100.0

        # 3. Career title progression (15% weight)
        progression_score = 75.0
        
        if job_count >= 2:
            rank_map = {
                "intern": 1,
                "trainee": 1,
                "junior": 2,
                "associate": 3,
                "mid": 4,
                "developer": 4,
                "engineer": 4,
                "senior": 5,
                "lead": 6,
                "principal": 7,
                "architect": 7,
                "manager": 8,
                "director": 9,
                "vp": 10,
                "chief": 10,
                "head": 10
            }

            def get_title_rank(role_title: str) -> int:
                role_lower = role_title.lower()
                for kw, rank in sorted(rank_map.items(), key=lambda x: -len(x[0])):
                    if kw in role_lower:
                        return rank
                return 4

            try:
                sorted_jobs = sorted(
                    profile.career_history,
                    key=lambda x: x.start_date if x.start_date else "1970-01-01"
                )
                first_job_rank = get_title_rank(sorted_jobs[0].role)
                latest_job_rank = get_title_rank(sorted_jobs[-1].role)
                
                if latest_job_rank > first_job_rank:
                    progression_score = 100.0
                elif latest_job_rank == first_job_rank:
                    progression_score = 80.0
                else:
                    progression_score = 50.0
            except Exception:
                progression_score = 75.0

        # 4. Brand Prestige & School Tier (25% weight)
        # 4a. Company prestige (max 100)
        company_scores = []
        for job in profile.career_history:
            # Set high default of 0.75 (so candidates with unlisted company size aren't penalized)
            size_score = COMPANY_SIZE_PRESTIGE_WEIGHTS.get(job.company_size, 0.75)
            # Product company gets a boost
            is_product = 1.0 - getattr(extracted_features, "services_only", 0.0)
            if is_product > 0.5:
                size_score = min(1.0, size_score + 0.2)
            company_scores.append(size_score * 100.0)
            
        company_prestige_score = sum(company_scores) / len(company_scores) if company_scores else 75.0

        # 4b. Education prestige (max 100)
        edu_scores = []
        for edu in profile.education:
            edu_scores.append(EDUCATION_TIER_MULTIPLIERS.get(edu.tier, 0.2) * 100.0)
            
        education_prestige_score = max(edu_scores) if edu_scores else 50.0  # default neutral score

        # Combine prestige metrics
        prestige_score = (0.50 * company_prestige_score) + (0.50 * education_prestige_score)

        # Aggregate weighted career score
        final_career_score = (
            (0.35 * exp_score) +
            (0.25 * stability_score) +
            (0.15 * progression_score) +
            (0.25 * prestige_score)
        )

        return {
            "score": round(final_career_score, 2),
            "experience_match": round(exp_score, 2),
            "stability_index": round(stability_score, 2),
            "title_progression": round(progression_score, 2),
            "prestige_rating": round(prestige_score, 2),
            "company_prestige": round(company_prestige_score, 2),
            "education_prestige": round(education_prestige_score, 2)
        }
