"""
Behaviour Score Calculator Module
Calculates S_behaviour (0-100) based on recruiter responsiveness,
profile completeness/verification, and candidate activity/demand signals.
"""

from typing import Dict, Any
import math

from src.profile_builder import CandidateProfile
from src.feature_extractor import ExtractedFeatures
from src.jd_parser import JobRequirements


class BehaviourScoreCalculator:

    @staticmethod
    def calculate(
        profile: CandidateProfile,
        extracted_features: ExtractedFeatures,
        jd: JobRequirements
    ) -> Dict[str, Any]:
        """
        Calculates S_behaviour and returns breakdown metrics.
        """
        signals = profile.behavioral_signals

        # 1. Recruiter Responsiveness (40% weight)
        response_rate_score = signals.recruiter_response_rate * 100.0
        
        # Scale average response time: 0-2 hours = 100 pts, >168 hours (1 week) = 0 pts
        resp_time = signals.avg_response_time_hours
        if resp_time <= 2.0:
            response_time_score = 100.0
        elif resp_time >= 168.0:
            response_time_score = 0.0
        else:
            # Linear scaling in between
            ratio = (resp_time - 2.0) / (168.0 - 2.0)
            response_time_score = (1.0 - ratio) * 100.0

        responsiveness_score = (0.70 * response_rate_score) + (0.30 * response_time_score)

        # 2. Profile Completeness & Identity Verification (30% weight)
        completeness_base = signals.profile_completeness_score
        
        # Add boosts for verification features
        verification_boost = 0.0
        if signals.verified_email:
            verification_boost += 10.0
        if signals.verified_phone:
            verification_boost += 10.0
        if signals.linkedin_connected:
            verification_boost += 10.0

        profile_integrity_score = min(100.0, completeness_base + verification_boost)

        # 3. Platform Activity & Demand (30% weight)
        work_flag_score = 100.0 if signals.open_to_work_flag else 50.0
        
        # Logarithmic scaling for views and searches received (normalizes extreme values)
        views = signals.profile_views_received_30d
        views_score = min(100.0, (math.log1p(views) / math.log1p(50)) * 100.0)

        searches = signals.search_appearance_30d
        search_score = min(100.0, (math.log1p(searches) / math.log1p(500)) * 100.0)

        activity_score = (0.50 * work_flag_score) + (0.25 * views_score) + (0.25 * search_score)

        # Aggregate weighted behavior score
        final_behaviour_score = (
            (0.40 * responsiveness_score) +
            (0.30 * profile_integrity_score) +
            (0.30 * activity_score)
        )

        return {
            "score": round(final_behaviour_score, 2),
            "responsiveness": round(responsiveness_score, 2),
            "profile_integrity": round(profile_integrity_score, 2),
            "activity_level": round(activity_score, 2),
            "response_rate": round(response_rate_score, 2),
            "response_speed": round(response_time_score, 2)
        }
