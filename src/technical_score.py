"""
Technical Score Calculator Module
Calculates S_tech (0-100) by combining Jaro-Winkler title alignment,
extracted semantic feature matching, and structured skill profiling.
"""

import math
from typing import Dict, Any

from src.config import SKILL_PROFICIENCY_MULTIPLIERS
from src.profile_builder import CandidateProfile
from src.feature_extractor import ExtractedFeatures
from src.jd_parser import JobRequirements
from src.utils import jaro_winkler_similarity


class TechnicalScoreCalculator:

    @staticmethod
    def calculate(
        profile: CandidateProfile,
        extracted_features: ExtractedFeatures,
        jd: JobRequirements
    ) -> Dict[str, Any]:
        """
        Calculates S_tech and returns a breakdown of scores.
        """
        # 1. Role Title Alignment (20% weight - reduced to prioritize system building capabilities)
        title_scores = []
        title_scores.append(jaro_winkler_similarity(profile.current_role, jd.title))
        title_scores.append(jaro_winkler_similarity(profile.headline, jd.title))
        for job in profile.career_history:
            title_scores.append(jaro_winkler_similarity(job.role, jd.title))
            
        role_alignment_score = max(title_scores) * 100.0 if title_scores else 0.0

        # 2. Extracted Features Matching (50% weight - increased to reward system builders)
        feature_match_score = 0.0
        target_features = jd.required_features if jd.required_features else [
            "production_ml", "retrieval_search", "recommendation_systems",
            "vector_databases", "embeddings"
        ]

        matched_features = {}
        for feature in target_features:
            val = getattr(extracted_features, feature, 0.0)
            matched_features[feature] = val
            feature_match_score += val

        if target_features:
            feature_match_score = (feature_match_score / len(target_features)) * 100.0
        else:
            feature_match_score = 0.0

        # 3. Explicit Skill Alignment (30% weight)
        skill_match_score = 0.0
        candidate_skills_dict = {s.name: s for s in profile.skills}
        
        total_skills_to_match = len(jd.required_skills)
        if total_skills_to_match > 0:
            total_score = 0.0
            for skill_name in jd.required_skills:
                skill_name_clean = skill_name.strip().lower()
                if skill_name_clean in candidate_skills_dict:
                    skill_entry = candidate_skills_dict[skill_name_clean]
                    prof_mult = SKILL_PROFICIENCY_MULTIPLIERS.get(skill_entry.proficiency, 0.25)
                    skill_pts = prof_mult * 1.0
                    
                    if skill_entry.endorsements > 0:
                        skill_pts += 0.1 * math.log1p(skill_entry.endorsements)
                    
                    if skill_entry.duration_months > 0:
                        skill_pts += 0.1 * min(2.0, skill_entry.duration_months / 12.0)
                    
                    total_score += min(1.5, skill_pts)
            
            skill_match_score = min(100.0, (total_score / total_skills_to_match) * 100.0)
        else:
            skill_match_score = 0.0

        # 4. Assessment verification boost (max 10 points)
        assessment_boost = 0.0
        assessment_scores = profile.behavioral_signals.skill_assessment_scores
        if assessment_scores:
            verified_high_scores = sum(
                1 for s_name, s_score in assessment_scores.items()
                if s_score >= 70.0 and s_name.lower() in [s.lower() for s in jd.required_skills]
            )
            assessment_boost = min(10.0, verified_high_scores * 5.0)

        # 5. Certifications boost (max 5 points)
        cert_boost = 0.0
        if profile.certifications and jd.required_skills:
            relevant_certs = 0
            for cert in profile.certifications:
                cert_name_lower = cert.name.lower()
                if any(skill in cert_name_lower for skill in jd.required_skills):
                    relevant_certs += 1
            cert_boost = min(5.0, relevant_certs * 2.5)

        # Aggregate weighted base score: 20% Title similarity + 50% Semantic Features + 30% Explicit Skills
        base_score = (
            (0.20 * role_alignment_score) +
            (0.50 * feature_match_score) +
            (0.30 * skill_match_score)
        )

        final_tech_score = min(100.0, base_score + assessment_boost + cert_boost)

        return {
            "score": round(final_tech_score, 2),
            "role_alignment": round(role_alignment_score, 2),
            "feature_alignment": round(feature_match_score, 2),
            "skill_alignment": round(skill_match_score, 2),
            "assessment_boost": round(assessment_boost, 2),
            "certification_boost": round(cert_boost, 2),
            "matched_features": matched_features
        }
