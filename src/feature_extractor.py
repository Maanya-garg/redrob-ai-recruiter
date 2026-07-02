"""
Feature Extractor Module
Extracts semantic candidate signals (production ML, search, recommendations, leadership, etc.)
using recruiter-focused heuristics (e.g. system builder verb scanning and evaluation metrics).
"""

from dataclasses import dataclass
import datetime
import re
from typing import List, Set

from src.config import FEATURE_KEYWORDS, SERVICE_COMPANIES
from src.profile_builder import CandidateProfile


@dataclass
class ExtractedFeatures:
    production_ml: float = 0.0
    retrieval_search: float = 0.0
    recommendation_systems: float = 0.0
    ranking_systems: float = 0.0
    vector_databases: float = 0.0
    embeddings: float = 0.0
    leadership: float = 0.0
    product_company: float = 0.0
    services_only: float = 0.0
    open_source: float = 0.0
    candidate_activity: float = 0.0


class FeatureExtractor:

    @staticmethod
    def extract(profile: CandidateProfile) -> ExtractedFeatures:
        skills_set = {s.name.strip().lower() for s in profile.skills}
        headline = profile.headline.lower()
        summary = profile.summary.lower()
        
        job_titles = []
        job_descriptions = []
        for job in profile.career_history:
            job_titles.append(job.role.lower())
            job_descriptions.append(job.description.lower())
        
        all_text = " ".join([
            headline,
            summary,
            " ".join(job_titles),
            " ".join(job_descriptions)
        ])

        # Recruiter reasoning: check for action verbs of building/deploying systems
        action_verbs = {
            "build", "built", "design", "designed", "implement", "implemented", "architect", 
            "architected", "scale", "scaled", "deploy", "deployed", "train", "trained", 
            "tune", "tuned", "optimize", "optimized", "develop", "developed", "own", "owned", 
            "lead", "led", "create", "created", "integrate", "integrated", "launch", "launched"
        }

        # Check for specific search/ranking evaluation metrics (NDCG, MRR, MAP)
        eval_metrics = {"ndcg", "mrr", "map", "mean reciprocal rank", "normalized discounted cumulative gain"}
        has_eval_metrics = any(metric in all_text for metric in eval_metrics)

        def compute_recruiter_score(keywords: List[str], domain_name: str) -> float:
            # 1. Base keyword match (skills + text count)
            matches = 0
            for kw in keywords:
                if kw in skills_set:
                    matches += 2.0  # Explicit skill is highly relevant
                if kw in all_text:
                    matches += 1.0

            base_score = 0.0
            if matches >= 4.0:
                base_score = 0.8
            elif matches > 0:
                base_score = (matches / 4.0) * 0.8

            # 2. Builder Reward: Did the candidate actively BUILD/DEPLOY these systems?
            # We look for action verbs in descriptions that mention the domain keywords
            builder_bonus = 0.0
            for job in profile.career_history:
                desc = job.description.lower()
                # Check if this job description mentions the keyword and an action verb
                has_kw = any(kw in desc for kw in keywords)
                has_action = any(verb in desc for verb in action_verbs)
                
                if has_kw and has_action:
                    builder_bonus += 0.15  # 15% boost for every job where they actively built it

            # 3. Specific Evaluation Metric Boost
            metric_boost = 0.0
            if has_eval_metrics and domain_name in ["ranking_systems", "retrieval_search"]:
                metric_boost = 0.15

            return min(1.0, base_score + builder_bonus + metric_boost)

        # Calculate scores
        production_ml = compute_recruiter_score(FEATURE_KEYWORDS["production_ml"], "production_ml")
        retrieval_search = compute_recruiter_score(FEATURE_KEYWORDS["retrieval_search"], "retrieval_search")
        recommendation_systems = compute_recruiter_score(FEATURE_KEYWORDS["recommendation_systems"], "recommendation_systems")
        ranking_systems = compute_recruiter_score(FEATURE_KEYWORDS["ranking_systems"], "ranking_systems")
        vector_databases = compute_recruiter_score(FEATURE_KEYWORDS["vector_databases"], "vector_databases")
        embeddings = compute_recruiter_score(FEATURE_KEYWORDS["embeddings"], "embeddings")

        # 4. Leadership Score
        leadership_kw_score = 0.0
        lead_kws = FEATURE_KEYWORDS["leadership"]
        for kw in lead_kws:
            if kw in skills_set:
                leadership_kw_score += 0.4
            if kw in all_text:
                leadership_kw_score += 0.2
        
        leadership_kw_score = min(0.8, leadership_kw_score)

        # Check titles for manager/lead roles
        leadership_title_match = 0
        lead_patterns = [r"\blead\b", r"\bmanager\b", r"\bdirector\b", r"\bvp\b", r"\barchitect\b", r"\bchief\b", r"\bhead\b"]
        for title in job_titles:
            if any(re.search(pattern, title) for pattern in lead_patterns):
                leadership_title_match += 1
        
        leadership = max(leadership_kw_score, min(1.0, leadership_title_match / 2.0))

        # 5. Product-Company vs Services-Only Background
        has_history = len(profile.career_history) > 0
        all_service = True if has_history else False
        has_large_product = False
        product_score_accum = 0.0

        for job in profile.career_history:
            company_clean = job.company.lower().strip()
            company_base = re.sub(r"\b(inc|pvt|ltd|corp|co|corporation|private|limited|llc)\b", "", company_clean).strip()
            
            is_service = False
            if company_clean in SERVICE_COMPANIES or company_base in SERVICE_COMPANIES:
                is_service = True
            elif "services" in company_clean or "consulting" in company_clean:
                is_service = True
            
            if not is_service:
                all_service = False
                if job.company_size in ["501-1000", "1001-5000", "5001-10000", "10001+"]:
                    has_large_product = True
            
            desc = job.description.lower()
            product_desc_matches = sum(1 for kw in FEATURE_KEYWORDS["product_indicators"] if kw in desc)
            if product_desc_matches > 0:
                product_score_accum += min(1.0, product_desc_matches / 3.0)

        if has_history:
            product_company = 0.8 * (product_score_accum / len(profile.career_history))
            if has_large_product:
                product_company = min(1.0, product_company + 0.3)
            product_company = min(1.0, max(0.0, product_company))
            services_only = 1.0 if all_service else 0.0
        else:
            product_company = 0.0
            services_only = 0.0

        # 6. Open Source Score
        os_matches = sum(1 for kw in FEATURE_KEYWORDS["open_source"] if kw in all_text)
        github_act = profile.behavioral_signals.github_activity_score
        os_score = min(1.0, os_matches / 2.0)
        if github_act > 20.0:
            os_score = min(1.0, os_score + 0.4)
        elif github_act > 0.0:
            os_score = min(1.0, os_score + 0.2)
        
        open_source = os_score

        # 7. Candidate Activity Score
        activity_score = 0.0
        last_active_str = profile.behavioral_signals.last_active_date
        
        try:
            ref_date = datetime.date(2026, 7, 1)
            if last_active_str:
                active_date = datetime.date.fromisoformat(last_active_str)
                days_diff = (ref_date - active_date).days
                if days_diff <= 30:
                    activity_score += 0.6
                elif days_diff <= 90:
                    activity_score += 0.4
                elif days_diff <= 180:
                    activity_score += 0.2
        except Exception:
            activity_score += 0.3

        activity_score += 0.4 * (profile.behavioral_signals.profile_completeness_score / 100.0)
        if profile.behavioral_signals.open_to_work_flag:
            activity_score = min(1.0, activity_score + 0.2)
            
        candidate_activity = min(1.0, max(0.0, activity_score))

        return ExtractedFeatures(
            production_ml=production_ml,
            retrieval_search=retrieval_search,
            recommendation_systems=recommendation_systems,
            ranking_systems=ranking_systems,
            vector_databases=vector_databases,
            embeddings=embeddings,
            leadership=leadership,
            product_company=product_company,
            services_only=services_only,
            open_source=open_source,
            candidate_activity=candidate_activity
        )
