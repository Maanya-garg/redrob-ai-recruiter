"""
Reason Generator Module
Generates recruiter-grade, candidate-specific explanations.
Decision labels: Strong Hire | Interview | Potential Hire | Hold | Reject | Not Relevant
Each candidate receives a unique, evidence-based narrative.
"""

from dataclasses import dataclass
from typing import Dict, Any, List


@dataclass
class Explanation:
    strengths: List[str]
    weaknesses: List[str]
    recommendation: str
    hiring_confidence: float = 0.0
    recruiter_reasoning: str = ""
    missing_requirements: List[str] = None
    potential_risks: List[str] = None

    def __post_init__(self):
        if self.missing_requirements is None:
            self.missing_requirements = []
        if self.potential_risks is None:
            self.potential_risks = []


class ReasonGenerator:

    @staticmethod
    def generate(scored_cand: Dict[str, Any], jd: Any) -> Explanation:
        sub_scores = scored_cand["sub_scores"]
        profile = scored_cand["profile"]
        features = scored_cand["extracted_features"]
        final_score = scored_cand["final_score"]
        hiring_confidence = scored_cand.get("hiring_confidence", final_score)
        decision = scored_cand.get("decision", "Hold")

        strengths: List[str] = []
        missing: List[str] = []
        risks: List[str] = []

        # ---------------------------------------------------------------
        # STRENGTHS — evidence-based, candidate-specific
        # ---------------------------------------------------------------

        # Recommendation Systems — check for depth
        if features.recommendation_systems >= 0.80:
            strengths.append("Deep Recommendation Systems experience: built collaborative filtering, candidate generation, or two-tower models in production.")
        elif features.recommendation_systems >= 0.55:
            strengths.append("Solid Recommendation Systems background: RecSys pipeline exposure with measurable impact.")

        # Search / Retrieval — differentiate depth
        if features.retrieval_search >= 0.80:
            strengths.append("Strong Search Infrastructure: production-grade retrieval systems (Elasticsearch, OpenSearch, dense retrieval).")
        elif features.retrieval_search >= 0.55:
            strengths.append("Search & Retrieval exposure: has worked on lexical or dense retrieval systems.")

        # Hybrid retrieval
        if features.retrieval_search >= 0.55 and features.embeddings >= 0.55:
            strengths.append("Hybrid Retrieval: combined sparse + dense retrieval experience — aligns well with modern search stacks.")

        # Ranking
        if features.ranking_systems >= 0.80:
            strengths.append("Ranking Expertise: LTR pipelines, NDCG/MRR evaluation, production rankers. Rare and high-value.")
        elif features.ranking_systems >= 0.55:
            strengths.append("Ranking Systems familiarity: understands scoring functions and evaluation metrics.")

        # Vector databases
        if features.vector_databases >= 0.70:
            strengths.append("Vector Databases: hands-on with FAISS, Pinecone, Milvus, or Weaviate — production-ready vector search.")
        elif features.vector_databases >= 0.40:
            strengths.append("Familiar with vector search infrastructure.")

        # Embeddings / representations
        if features.embeddings >= 0.75:
            strengths.append("Embeddings & Representations: strong experience with sentence transformers, dense vectors, or fine-tuned encoders.")

        # Production ML — check LLM angle
        has_llm = any(
            kw in profile.summary.lower() or kw in " ".join(j.description.lower() for j in profile.career_history)
            for kw in ["llm", "transformer", "lora", "qlora", "peft", "fine-tun", "rag", "gpt"]
        )
        if features.production_ml >= 0.70 and has_llm:
            strengths.append("Production LLM Engineering: fine-tuned and served large language models at scale.")
        elif features.production_ml >= 0.70:
            strengths.append("Strong Production ML: MLOps, model serving, and inference pipeline experience.")
        elif features.production_ml >= 0.45:
            strengths.append("ML Engineering foundation: model training and deployment experience.")

        # Leadership signals
        if features.leadership >= 0.80:
            strengths.append(f"Technical Leadership: has led teams or architected systems — relevant for senior/staff-level hire.")
        elif features.leadership >= 0.55:
            strengths.append("Some leadership or mentorship signals in career history.")

        # Open source
        if features.open_source >= 0.70:
            strengths.append(f"Open Source Contributions (GitHub score: {profile.behavioral_signals.github_activity_score:.0f}) — demonstrates initiative and code quality.")

        # Domain alignment from career score
        domain_score = sub_scores["career"].get("domain_alignment", 50.0)
        if domain_score >= 85.0:
            strengths.append("Target Domain Fit: career titles directly match the Recommendation/Search/Ranking engineer profile.")
        elif domain_score >= 65.0:
            strengths.append("Adjacent Domain Background: career history shows proximity to the target search/ranking domain.")

        # Career progression
        if sub_scores["career"]["title_progression"] >= 90.0:
            strengths.append(f"Strong Career Progression: consistent upward trajectory over {profile.years_experience:.0f} years.")

        # Experience match
        if sub_scores["career"]["experience_match"] >= 100.0:
            strengths.append(f"Experience Match: {profile.years_experience:.0f} years meets the {jd.min_years_experience:.0f}+ year requirement.")

        # Product company
        if features.product_company >= 0.70:
            strengths.append("Product Company Background: built and scaled customer-facing systems — strong for platform roles.")

        # Responsiveness
        if sub_scores["behaviour"]["responsiveness"] >= 85.0:
            strengths.append("Highly Responsive: fast recruiter reply rate — low ghosting risk.")

        if not strengths:
            strengths.append("Basic skill overlap with target requirements.")

        # ---------------------------------------------------------------
        # MISSING REQUIREMENTS
        # ---------------------------------------------------------------
        jd_features = getattr(jd, "required_features", [])

        if "retrieval_search" in jd_features and features.retrieval_search < 0.35:
            missing.append("No production search/retrieval experience detected.")
        if "ranking_systems" in jd_features and features.ranking_systems < 0.35:
            missing.append("No learning-to-rank or ranking pipeline experience detected.")
        if "vector_databases" in jd_features and features.vector_databases < 0.30:
            missing.append("No hands-on vector database experience (Pinecone, Milvus, FAISS).")
        if "embeddings" in jd_features and features.embeddings < 0.30:
            missing.append("No embeddings or dense representation experience.")
        if "recommendation_systems" in jd_features and features.recommendation_systems < 0.30:
            missing.append("No recommendation system experience detected.")

        exp_gap = jd.min_years_experience - profile.years_experience
        if exp_gap > 1.0:
            missing.append(f"Under-experienced: {profile.years_experience:.0f} yrs vs {jd.min_years_experience:.0f}+ required.")

        # ---------------------------------------------------------------
        # POTENTIAL RISKS
        # ---------------------------------------------------------------
        if sub_scores["risk"]["notice_period_risk"] >= 80.0:
            risks.append(f"Long notice period ({profile.behavioral_signals.notice_period_days} days) — onboarding delay risk.")
        if sub_scores["risk"]["ghosting_risk"] >= 50.0:
            risks.append("Elevated interview ghosting risk based on platform history.")
        if sub_scores["risk"]["renege_risk"] >= 50.0:
            risks.append("Low offer acceptance rate — offer renege risk.")
        if sub_scores["risk"]["salary_risk"] >= 60.0:
            min_sal = profile.behavioral_signals.expected_salary_range_inr_lpa.get("min", 0)
            risks.append(f"Salary expectation ({min_sal} LPA) above budget.")
        if sub_scores["career"]["stability_index"] < 60.0:
            risks.append("Frequent job changes — average tenure below 18 months.")
        if features.services_only >= 0.9:
            risks.append("Consulting/services-only background — may lack product scaling experience.")

        # Domain risk
        domain_score = sub_scores["career"].get("domain_alignment", 50.0)
        if domain_score < 30.0:
            risks.append("Career history outside the target domain (search/ranking/recommendations).")

        # Confidence penalties from ranking engine
        for penalty in scored_cand.get("confidence_penalties", []):
            if penalty not in risks:
                risks.append(penalty)

        # ---------------------------------------------------------------
        # RECRUITER NARRATIVE
        # ---------------------------------------------------------------
        narrative_parts = []

        top_strength = strengths[0] if strengths else "Some relevant experience"
        top_risk = risks[0] if risks else None

        if decision == "Strong Hire":
            narrative_parts.append(
                f"Candidate demonstrates strong production-grade experience in the target domain. "
                f"{top_strength.split(':')[0]} is a clear differentiator."
            )
        elif decision == "Interview":
            narrative_parts.append(
                f"Solid candidate with relevant domain experience. {top_strength.split(':')[0]} "
                f"makes them worth a technical screen."
            )
        elif decision == "Potential Hire":
            narrative_parts.append(
                f"Moderate fit — has some relevant experience but gaps exist. "
                f"{missing[0] if missing else 'Experience depth could be stronger.'}"
            )
        elif decision == "Hold":
            narrative_parts.append(
                f"Marginal fit for this role. "
                f"{missing[0] if missing else 'Technical or domain signals are weak.'} "
                f"Consider for future openings with lower bar."
            )
        else:
            narrative_parts.append(
                f"Candidate profile does not sufficiently match the JD requirements. "
                f"{missing[0] if missing else 'Insufficient domain alignment.'}"
            )

        if top_risk:
            narrative_parts.append(f"Key risk: {top_risk}")

        narrative_parts.append(
            f"Hiring confidence: {hiring_confidence:.0f}% | "
            f"Technical: {sub_scores['technical']['score']:.0f} | "
            f"Career: {sub_scores['career']['score']:.0f}"
        )

        recruiter_reasoning = " ".join(narrative_parts)

        # ---------------------------------------------------------------
        # RECOMMENDATION LABEL
        # ---------------------------------------------------------------
        recommendation = f"{decision}: {_label_reason(decision, hiring_confidence, strengths, missing)}"

        return Explanation(
            strengths=list(dict.fromkeys(strengths)),
            weaknesses=missing + risks,
            recommendation=recommendation,
            hiring_confidence=round(hiring_confidence, 1),
            recruiter_reasoning=recruiter_reasoning,
            missing_requirements=list(dict.fromkeys(missing)),
            potential_risks=list(dict.fromkeys(risks)),
        )


def _label_reason(decision: str, confidence: float, strengths: List[str], missing: List[str]) -> str:
    """Generate a one-line reason for the decision label."""
    if decision == "Strong Hire":
        return strengths[0].split(":")[0] if strengths else "Exceptional domain fit."
    if decision == "Interview":
        return "Strong domain signals — recommend technical screen."
    if decision == "Potential Hire":
        return f"Moderate fit. {missing[0] if missing else 'Some gaps present.'}"
    if decision == "Hold":
        return f"Weak alignment. {missing[0] if missing else 'Insufficient evidence.'}"
    if decision == "Reject":
        return missing[0] if missing else "Does not meet minimum requirements."
    return "Profile outside target domain."
