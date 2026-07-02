"""
Configuration settings for the Redrob AI Recruiter Ranking Engine.
"""

# Overall weights for the final composite rank score
# Technical score is prioritized (50%), followed by career prestige/fit, behavior, and risk.
SCORING_WEIGHTS = {
    "technical": 0.50,
    "career": 0.25,
    "behaviour": 0.10,
    "risk": 0.15,
}

# Skill proficiency multipliers to weigh experience depth
SKILL_PROFICIENCY_MULTIPLIERS = {
    "beginner": 0.25,
    "intermediate": 0.50,
    "advanced": 0.75,
    "expert": 1.00,
}

# Language proficiency multipliers
LANGUAGE_PROFICIENCY_MULTIPLIERS = {
    "basic": 0.25,
    "conversational": 0.50,
    "professional": 0.85,
    "native": 1.00,
}

# Education Institution Tier weights
EDUCATION_TIER_MULTIPLIERS = {
    "tier_1": 1.00,
    "tier_2": 0.80,
    "tier_3": 0.50,
    "tier_4": 0.30,
    "unknown": 0.20,
}

# Company size prestige scores - flattened to prevent extreme brand name bias
COMPANY_SIZE_PRESTIGE_WEIGHTS = {
    "10001+": 1.00,
    "5001-10000": 0.95,
    "1001-5000": 0.90,
    "501-1000": 0.85,
    "201-500": 0.80,
    "51-200": 0.75,
    "11-50": 0.70,
    "1-10": 0.65,
}

# Industry service tags to identify service-only backgrounds
SERVICE_COMPANIES = {
    "tcs", "tata consultancy services", "wipro", "infosys", "cognizant",
    "accenture", "capgemini", "hcl", "hcltech", "tech mahindra", "mindtree",
    "l&t", "larsen & toubro", "dxc", "ntt data", "ust", "infosys bpm", "wipro bpm"
}

# Threshold parameters for scoring and filtering
EXPERIENCE_UNDER_PENALTY = 15.0      # penalty points per year under required experience
STABILITY_MIN_TENURE_MONTHS = 18     # preferred average months per job (1.5 years)
STABILITY_PENALTY_MAX = 30           # maximum penalty for job hopping
MAX_NOTICE_PERIOD_DAYS = 90          # maximum notice period before severe risk penalty
MIN_INTERVIEW_COMPLETION_RATE = 0.75 # below this is flagged as high ghosting risk
MIN_OFFER_ACCEPTANCE_RATE = 0.50     # below this is flagged as offer renege risk

# Keywords dictionary for feature extraction, expanded with details from candidate profiles
FEATURE_KEYWORDS = {
    "production_ml": [
        "productionize", "production ml", "deploy", "mlops", "kubeflow", "mlflow", "tfx", 
        "inference pipeline", "model serving", "triton", "sagemaker", "monitoring",
        "latency", "throughput", "bentoml", "docker", "kubernetes", "k8s", "cicd",
        "quantization", "onnx", "torchscript", "model compression"
    ],
    "retrieval_search": [
        "elasticsearch", "solr", "lucene", "bm25", "retrieval", "hybrid search", "lexical search",
        "meilisearch", "opensearch", "information retrieval", "inverted index", "ranking function",
        "dense retrieval", "cross-encoder", "bi-encoder", "query understanding", "search quality"
    ],
    "recommendation_systems": [
        "recommender", "recommendation", "collaborative filtering", "matrix factorization",
        "recsys", "ctr prediction", "click-through rate", "personalization", "session-based recommendation",
        "als", "two-tower", "candidate generation", "deep & wide", "factorization machines"
    ],
    "ranking_systems": [
        "learning to rank", "ltr", "xgboost", "lightgbm", "catboost", "ranking model", "ndcg",
        "mrr", "map@k", "pairwise ranking", "listwise ranking", "scoring function", "re-ranking", "ranker"
    ],
    "vector_databases": [
        "milvus", "pinecone", "qdrant", "chromadb", "faiss", "weaviate", "vector search",
        "similarity search", "nearest neighbor", "ann search", "vector db", "pgvector", "hnsw"
    ],
    "embeddings": [
        "word2vec", "bert", "embeddings", "sentence embeddings", "dense retrieval", "vectorization",
        "sentence-transformers", "dense vectors", "representation learning", "text embedding",
        "roberta", "glove", "fasttext"
    ],
    "leadership": [
        "team lead", "tech lead", "architect", "manager", "led a team", "managed a team",
        "mentored", "coached", "director", "vp", "head of", "principal", "engineering lead"
    ],
    "product_indicators": [
        "saas", "product-based", "b2b", "b2c", "scaling platform", "daily active users",
        "monthly active users", "churn", "retention", "user growth", "a/b testing",
        "metrics-driven", "product scaling", "microservices architecture"
    ],
    "open_source": [
        "open-source", "open source", "contributed to", "contributor", "github project",
        "maintained library", "public repository", "git pull request", "prs accepted"
    ]
}
