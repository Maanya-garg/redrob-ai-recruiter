"""
Risk Score Calculator Module
Calculates S_risk (0-100) where higher values indicate higher risks for recruitment,
focusing on notice period delay, interview ghosting rate, offer reneges, and non-linear salary mismatch.
"""

from typing import Dict, Any

from src.profile_builder import CandidateProfile
from src.feature_extractor import ExtractedFeatures
from src.jd_parser import JobRequirements


class RiskScoreCalculator:

    @staticmethod
    def calculate(
        profile: CandidateProfile,
        extracted_features: ExtractedFeatures,
        jd: JobRequirements
    ) -> Dict[str, Any]:
        """
        Calculates S_risk and returns breakdown metrics.
        """
        signals = profile.behavioral_signals

        # 1. Notice Period Risk (30% weight)
        notice_days = signals.notice_period_days
        if notice_days <= 30:
            notice_risk = 0.0
        elif notice_days <= 60:
            notice_risk = 50.0
        else:
            notice_risk = 100.0

        # 2. Interview Ghosting Risk (30% weight)
        ghost_risk = (1.0 - signals.interview_completion_rate) * 100.0

        # 3. Offer Reneging / Acceptance Risk (20% weight)
        oar = signals.offer_acceptance_rate
        if oar < 0.0:
            renege_risk = 15.0
        else:
            renege_risk = (1.0 - oar) * 100.0

        # 4. Non-Linear Salary Mismatch Risk (20% weight - reduced penalty for minor mismatches)
        salary_risk = 0.0
        min_expected_salary = signals.expected_salary_range_inr_lpa.get("min", 0.0)
        budget_max = jd.salary_budget_max_lpa

        if budget_max and min_expected_salary > 0.0:
            if min_expected_salary > budget_max:
                excess_pct = (min_expected_salary - budget_max) / budget_max
                if excess_pct <= 0.10:
                    # Minor mismatch (within 10% target buffer range), low risk penalty
                    salary_risk = excess_pct * 100.0  # max 10.0 points
                elif excess_pct <= 0.30:
                    # Moderate mismatch (10% to 30%), scales from 10 to 50
                    salary_risk = 10.0 + ((excess_pct - 0.10) / 0.20) * 40.0
                else:
                    # Large mismatch (> 30%), scales from 50 to 100
                    salary_risk = min(100.0, 50.0 + ((excess_pct - 0.30) / 0.20) * 50.0)

        # 5. Location/Relocation Risk
        location_risk = 0.0
        is_mode_restricted = jd.preferred_work_mode in ["onsite", "hybrid"]
        
        if is_mode_restricted:
            candidate_loc_lower = profile.location.lower()
            in_target_location = any(
                loc.lower() in candidate_loc_lower for loc in jd.target_locations
            )
            
            if not in_target_location and not signals.willing_to_relocate:
                location_risk = 80.0

        # Base aggregated score
        base_risk_score = (
            (0.30 * notice_risk) +
            (0.30 * ghost_risk) +
            (0.20 * renege_risk) +
            (0.20 * salary_risk)
        )

        final_risk_score = max(base_risk_score, location_risk)

        return {
            "score": round(final_risk_score, 2),
            "notice_period_risk": round(notice_risk, 2),
            "ghosting_risk": round(ghost_risk, 2),
            "renege_risk": round(renege_risk, 2),
            "salary_risk": round(salary_risk, 2),
            "location_risk": round(location_risk, 2)
        }
