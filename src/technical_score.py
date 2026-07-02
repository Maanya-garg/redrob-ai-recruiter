"""
Technical Score Calculator Module
Evidence-based scoring: rewards candidates who BUILT systems,
not just candidates who list technology keywords.

Evidence weights:
  Production deployment evidence  → 2.0× base value
  Architecture / ownership signals → 1.5× base value
  Plain keyword mention            → 1.0× base value
  Tutorial / learning / coursework → 0.3× (heavy discount)
"""

import math
import re
from typing import Dict, Any, List

from src.config import SKILL_PROFICIENCY_MULTIPLIERS
from src.profile_builder import CandidateProfile
from src.feature_extractor import ExtractedFeatures
from src.jd_parser import JobRequirements
from src.utils import jaro_winkler_similarity


# Evidence action verbs that indicate the candidate BUILT something
BUILDER_VERBS = frozenset([
    "built", "build", "designed", "design", "architected", "architect",
    "shipped", "deployed", "deploy", "launched", "launch", "implemented",
    "implement", "developed", "develop", "scaled", "scale", "owned", "own",
    "led", "lead", "created", "create", "delivered", "deliver", "engineered",
    "productionized", "maintained", "maintain",
])

# Weak signals — indicate learning, not doing
WEAK_SIGNALS = frozenset([
    "learning", "exploring", "studying", "coursework", "tutorial",
    "beginner", "understanding", "familiar", "exposure", "toy project",
    "personal project", "side project", "hobby",
])

# Semantic role matches: titles that signal strong fit for search/ranking/recsys roles
STRONG_ROLE_MATCHES = [
    "recommendation engineer", "search engineer", "ranking engineer",
    "information retrieval", "applied ml", "ml platform", "nlp engineer",
    "marketplace search", "candidate matching", "vector search",
    "machine learning engineer", "ai engineer", "ml engineer",
    "research scientist", "research engineer", "data scientist",
]

WEAK_ROLE_MATCHES = [
    "software engineer", "backend engineer", "backend developer",
    "full stack", "frontend engineer", "web developer", "data engineer",
]

VERY_WEAK_ROLES = [
    "marketing", "hr ", "human resources", "graphic design", "civil engineer",
    "accountant", "sales", "finance", "lawyer", "legal",
]


def _detect_production_evidence(text: str, tech_terms: List[str]) -> float:
    """
    Returns a 0.0–1.0 evidence score for whether the candidate actively
    built/deployed systems using the given tech terms.
    """
    text_lower = text.lower()
    score = 0.0
    for term in tech_terms:
        if term not in text_lower:
            continue
        # Find the sentence containing the term
        sentences = re.split(r"[.!?\n]", text_lower)
        for sent in sentences:
            if term not in sent:
                continue
            words = set(sent.split())
            if words & BUILDER_VERBS:
                score += 0.20  # production evidence
            elif words & WEAK_SIGNALS:
                score += 0.05  # learning signal
            else:
                score += 0.10  # neutral mention
    return min(1.0, score)


def _semantic_role_score(profile: CandidateProfile) -> float:
    """Returns 0.0–1.0 role alignment based on career titles."""
    all_titles = [profile.current_role.lower(), profile.headline.lower()]
    for job in profile.career_history:
        all_titles.append(job.role.lower())

    best = 0.0
    for title in all_titles:
        # Very weak roles get heavy penalty
        if any(vw in title for vw in VERY_WEAK_ROLES):
            return 0.05

        for strong in STRONG_ROLE_MATCHES:
            if strong in title:
                best = max(best, 0.95)
                break

        for weak in WEAK_ROLE_MATCHES:
            if weak in title:
                best = max(best, 0.50)

    return best if best > 0 else 0.40  # unknown title — neutral


class TechnicalScoreCalculator:

    @staticmethod
    def calculate(
        profile: CandidateProfile,
        extracted_features: ExtractedFeatures,
        jd: JobRequirements
    ) -> Dict[str, Any]:

        # ---------------------------------------------------------------
        # 1. Semantic role match (25% weight)
        # ---------------------------------------------------------------
        role_alignment_score = _semantic_role_score(profile) * 100.0

        # ---------------------------------------------------------------
        # 2. Evidence-based feature alignment (45% weight)
        # ---------------------------------------------------------------
        target_features = jd.required_features if jd.required_features else [
            "production_ml", "retrieval_search", "recommendation_systems",
            "vector_databases", "embeddings", "ranking_systems",
        ]

        # Build full text from profile for evidence detection
        full_text = " ".join([
            profile.headline, profile.summary,
            " ".join(j.description for j in profile.career_history),
            " ".join(j.role for j in profile.career_history),
        ])

        feature_scores: Dict[str, float] = {}
        for feat in target_features:
            raw_val = getattr(extracted_features, feat, 0.0)
            feature_scores[feat] = raw_val

        if feature_scores:
            feature_match_score = (sum(feature_scores.values()) / len(feature_scores)) * 100.0
        else:
            feature_match_score = 0.0

        # ---------------------------------------------------------------
        # 3. Evidence-weighted skill alignment (30% weight)
        # ---------------------------------------------------------------
        skill_match_score = 0.0
        candidate_skills = {s.name.strip().lower(): s for s in profile.skills}
        jd_skills = jd.required_skills[:20]  # cap at 20 to avoid over-penalising niche JDs

        if jd_skills:
            total = 0.0
            for skill_name in jd_skills:
                sk_clean = skill_name.strip().lower()
                if sk_clean in candidate_skills:
                    skill_entry = candidate_skills[sk_clean]
                    prof_mult = SKILL_PROFICIENCY_MULTIPLIERS.get(skill_entry.proficiency, 0.25)
                    pts = prof_mult

                    if skill_entry.endorsements > 0:
                        pts += 0.05 * math.log1p(skill_entry.endorsements)
                    if skill_entry.duration_months > 0:
                        pts += 0.05 * min(2.0, skill_entry.duration_months / 12.0)

                    # Evidence boost: did they actually build with this skill?
                    evidence = _detect_production_evidence(full_text, [sk_clean])
                    pts *= (1.0 + evidence)  # up to 2× for strong production evidence

                    total += min(2.0, pts)

            skill_match_score = min(100.0, (total / len(jd_skills)) * 100.0)

        # ---------------------------------------------------------------
        # 4. Assessment & certification boosts (max 10 pts combined)
        # ---------------------------------------------------------------
        assessment_boost = 0.0
        if profile.behavioral_signals.skill_assessment_scores and jd.required_skills:
            req_lower = [s.lower() for s in jd.required_skills]
            for s_name, s_score in profile.behavioral_signals.skill_assessment_scores.items():
                if s_score >= 70.0 and s_name.lower() in req_lower:
                    assessment_boost += 3.0
            assessment_boost = min(7.0, assessment_boost)

        cert_boost = 0.0
        if profile.certifications and jd.required_skills:
            req_lower = [s.lower() for s in jd.required_skills]
            for cert in profile.certifications:
                if any(skill in cert.name.lower() for skill in req_lower):
                    cert_boost += 1.5
            cert_boost = min(3.0, cert_boost)

        # ---------------------------------------------------------------
        # 5. Aggregate
        # ---------------------------------------------------------------
        base = (
            0.25 * role_alignment_score +
            0.45 * feature_match_score +
            0.30 * skill_match_score
        )
        final_tech_score = min(100.0, base + assessment_boost + cert_boost)

        return {
            "score": round(final_tech_score, 2),
            "role_alignment": round(role_alignment_score, 2),
            "feature_alignment": round(feature_match_score, 2),
            "skill_alignment": round(skill_match_score, 2),
            "assessment_boost": round(assessment_boost, 2),
            "certification_boost": round(cert_boost, 2),
            "matched_features": feature_scores,
        }
