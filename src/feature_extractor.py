"""
Feature Extractor Module
Evidence-based semantic signal extraction.
Rewards candidates who BUILT systems; discounts candidates who merely list keywords.

Key upgrades:
- Action verb detection (built, designed, deployed, architected, shipped...)
- Semantic synonyms: FAISS→vector_search, Elasticsearch→retrieval, etc.
- Negative signal detection: "learning", "exploring", "tutorial" reduce scores
- production_evidence_score across the whole profile
- domain_depth_score for target-domain specialisation
"""

from dataclasses import dataclass
import datetime
import re
from typing import List, Set

from src.config import SERVICE_COMPANIES
from src.profile_builder import CandidateProfile


# ---------------------------------------------------------------------------
# Builder verbs — indicate the candidate BUILT/SHIPPED something
# ---------------------------------------------------------------------------
BUILDER_VERBS: Set[str] = {
    "built", "build", "designed", "design", "architected", "architect",
    "shipped", "deploy", "deployed", "launched", "launch", "implemented",
    "implement", "developed", "develop", "scaled", "scale", "owned", "own",
    "led", "lead", "created", "create", "delivered", "deliver", "engineered",
    "productionized", "maintained", "maintain", "orchestrated", "drove",
}

# Weak signals — indicate studying, not doing
WEAK_SIGNALS: Set[str] = {
    "learning", "exploring", "studying", "coursework", "tutorial",
    "beginner", "understanding", "familiar", "exposure", "toy",
    "personal project", "side project", "hobby", "academic",
}

# ---------------------------------------------------------------------------
# Technology keyword groups with semantic synonyms
# ---------------------------------------------------------------------------
FEATURE_KEYWORDS: dict = {
    "production_ml": [
        # Core
        "production ml", "productionize", "mlops", "model serving",
        "inference pipeline", "model deployment", "deploy model",
        # Tools
        "kubeflow", "mlflow", "tfx", "sagemaker", "triton", "bentoml",
        "ray serve", "seldon", "torchserve",
        # Infrastructure
        "docker", "kubernetes", "k8s", "cicd", "monitoring", "latency",
        "throughput", "quantization", "onnx", "torchscript",
        # LLM fine-tuning (strong production signal)
        "fine-tun", "fine tuning", "finetuning", "lora", "qlora", "peft",
        "rlhf", "instruction tuning",
    ],
    "retrieval_search": [
        # Core concepts
        "retrieval", "information retrieval", "dense retrieval",
        "hybrid search", "hybrid retrieval", "semantic search",
        "lexical search", "search infrastructure", "search quality",
        "query understanding", "candidate matching", "marketplace search",
        # Tools (direct and synonyms)
        "elasticsearch", "opensearch", "solr", "lucene", "meilisearch",
        "bm25", "inverted index", "bi-encoder", "cross-encoder",
        # Synonyms
        "search system", "search engine", "search pipeline",
    ],
    "recommendation_systems": [
        "recommendation", "recommender", "recsys", "collaborative filtering",
        "matrix factorization", "personalization", "candidate generation",
        "two-tower", "ctr prediction", "click-through rate",
        "deep & wide", "factorization machines", "session-based",
        "als", "item embeddings", "user embeddings",
    ],
    "ranking_systems": [
        "learning to rank", "ltr", "ranking model", "ranking pipeline",
        "scoring function", "re-ranking", "reranking",
        "pairwise ranking", "listwise ranking", "pointwise ranking",
        "ndcg", "mrr", "map@k", "mean average precision",
        "mean reciprocal rank", "normalized discounted",
        "ads ranking", "marketplace ranking",
        "xgboost", "lightgbm", "catboost",
    ],
    "vector_databases": [
        "vector database", "vector db", "vector search", "similarity search",
        "nearest neighbor", "approximate nearest neighbor", "ann",
        "hnsw", "faiss", "milvus", "pinecone", "weaviate", "qdrant",
        "chromadb", "pgvector", "vespa",
    ],
    "embeddings": [
        "embeddings", "embedding", "dense vectors", "representation learning",
        "vectorization", "sentence transformers", "sentence-transformers",
        "sentence embeddings", "text embedding", "text-embedding",
        "bert", "roberta", "glove", "fasttext", "word2vec",
        "bge", "e5", "openai embeddings",
        "bi-encoder", "cross-encoder",
    ],
    "leadership": [
        "team lead", "tech lead", "architect", "manager", "managing",
        "led a team", "managed a team", "mentored", "coached",
        "director", "vp", "head of", "principal", "engineering lead",
        "staff engineer", "senior staff",
    ],
    "product_indicators": [
        "saas", "product-based", "b2b", "b2c", "marketplace",
        "daily active users", "monthly active users", "churn", "retention",
        "user growth", "a/b testing", "metrics-driven", "product scaling",
        "microservices", "scaling platform",
    ],
    "open_source": [
        "open-source", "open source", "contributed to", "contributor",
        "github project", "maintained library", "public repository",
        "pull request", "prs accepted", "maintainer",
    ],
}


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

        job_descs = [j.description.lower() for j in profile.career_history]
        job_titles = [j.role.lower() for j in profile.career_history]

        all_text = " ".join([headline, summary] + job_titles + job_descs)

        # Evaluation metrics — strong ranking/retrieval proxy
        eval_metrics = {
            "ndcg", "mrr", "map@k", "mean reciprocal rank",
            "normalized discounted cumulative gain", "mean average precision",
        }
        has_eval_metrics = any(m in all_text for m in eval_metrics)

        def compute_evidence_score(keywords: List[str], domain_name: str) -> float:
            """
            Evidence-based scoring:
              Skill entry                   → +0.25 each (max 0.50)
              Text mention (neutral)        → +0.08 each
              Builder verb + keyword in same sentence → +0.20 per job
              Weak signal (tutorial/learning) → −0.10
              Eval metrics (ranking/retrieval domains) → +0.15
            """
            skill_score = 0.0
            for kw in keywords:
                if any(kw in sk for sk in skills_set):
                    skill_score = min(0.50, skill_score + 0.25)

            text_score = 0.0
            for kw in keywords:
                if kw in all_text:
                    text_score = min(0.40, text_score + 0.08)

            # Builder bonus: scan each job description for co-occurrence of
            # keyword + builder verb in the same sentence
            builder_score = 0.0
            for desc in job_descs:
                sentences = re.split(r"[.!\n]", desc)
                for sent in sentences:
                    if not any(kw in sent for kw in keywords):
                        continue
                    words = set(sent.split())
                    if words & BUILDER_VERBS:
                        builder_score += 0.20
                    elif words & WEAK_SIGNALS:
                        builder_score -= 0.10

            builder_score = max(0.0, min(0.40, builder_score))

            # Evaluation metrics bonus for ranking/retrieval domains
            metric_bonus = 0.0
            if has_eval_metrics and domain_name in ("ranking_systems", "retrieval_search"):
                metric_bonus = 0.15

            return min(1.0, skill_score + text_score + builder_score + metric_bonus)

        production_ml = compute_evidence_score(FEATURE_KEYWORDS["production_ml"], "production_ml")
        retrieval_search = compute_evidence_score(FEATURE_KEYWORDS["retrieval_search"], "retrieval_search")
        recommendation_systems = compute_evidence_score(FEATURE_KEYWORDS["recommendation_systems"], "recommendation_systems")
        ranking_systems = compute_evidence_score(FEATURE_KEYWORDS["ranking_systems"], "ranking_systems")
        vector_databases = compute_evidence_score(FEATURE_KEYWORDS["vector_databases"], "vector_databases")
        embeddings = compute_evidence_score(FEATURE_KEYWORDS["embeddings"], "embeddings")

        # ---------------------------------------------------------------
        # Leadership
        # ---------------------------------------------------------------
        lead_kws = FEATURE_KEYWORDS["leadership"]
        lead_skill = min(0.50, sum(0.25 for kw in lead_kws if any(kw in sk for sk in skills_set)))
        lead_text = min(0.30, sum(0.10 for kw in lead_kws if kw in all_text))
        lead_patterns = [r"\blead\b", r"\bmanager\b", r"\bdirector\b", r"\bvp\b",
                         r"\barchitect\b", r"\bchief\b", r"\bhead\b", r"\bprincipal\b"]
        lead_title_matches = sum(
            1 for t in job_titles if any(re.search(p, t) for p in lead_patterns)
        )
        leadership = min(1.0, lead_skill + lead_text + min(0.40, lead_title_matches * 0.20))

        # ---------------------------------------------------------------
        # Product company vs services-only
        # ---------------------------------------------------------------
        has_history = len(profile.career_history) > 0
        all_service = True if has_history else False
        has_large_product = False
        product_accum = 0.0

        for job in profile.career_history:
            company_clean = job.company.lower().strip()
            company_base = re.sub(
                r"\b(inc|pvt|ltd|corp|co|corporation|private|limited|llc)\b", "",
                company_clean,
            ).strip()

            is_service = (
                company_clean in SERVICE_COMPANIES
                or company_base in SERVICE_COMPANIES
                or "services" in company_clean
                or "consulting" in company_clean
            )
            if not is_service:
                all_service = False
                if job.company_size in ("501-1000", "1001-5000", "5001-10000", "10001+"):
                    has_large_product = True

            desc = job.description.lower()
            prod_hits = sum(1 for kw in FEATURE_KEYWORDS["product_indicators"] if kw in desc)
            product_accum += min(1.0, prod_hits / 3.0)

        if has_history:
            product_company = 0.8 * (product_accum / len(profile.career_history))
            if has_large_product:
                product_company = min(1.0, product_company + 0.30)
            product_company = min(1.0, max(0.0, product_company))
            services_only = 1.0 if all_service else 0.0
        else:
            product_company = 0.0
            services_only = 0.0

        # ---------------------------------------------------------------
        # Open source
        # ---------------------------------------------------------------
        os_hits = sum(1 for kw in FEATURE_KEYWORDS["open_source"] if kw in all_text)
        github = profile.behavioral_signals.github_activity_score
        os_score = min(0.60, os_hits * 0.20)
        if github > 20.0:
            os_score = min(1.0, os_score + 0.40)
        elif github > 0.0:
            os_score = min(1.0, os_score + 0.20)
        open_source = os_score

        # ---------------------------------------------------------------
        # Candidate activity
        # ---------------------------------------------------------------
        activity = 0.0
        last_active = profile.behavioral_signals.last_active_date
        try:
            ref = datetime.date(2026, 7, 1)
            if last_active:
                delta = (ref - datetime.date.fromisoformat(last_active)).days
                if delta <= 30:
                    activity += 0.60
                elif delta <= 90:
                    activity += 0.40
                elif delta <= 180:
                    activity += 0.20
        except Exception:
            activity += 0.30

        activity += 0.40 * (profile.behavioral_signals.profile_completeness_score / 100.0)
        if profile.behavioral_signals.open_to_work_flag:
            activity = min(1.0, activity + 0.20)
        candidate_activity = min(1.0, max(0.0, activity))

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
            candidate_activity=candidate_activity,
        )
