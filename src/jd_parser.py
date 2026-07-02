"""
Job Description (JD) Parser Module
Full-document semantic scanner that works with ANY JD format.

Strategy:
  1. Extract metadata (title, company, experience) using regex patterns.
  2. Try section-aware extraction for both Redrob custom headings
     ("Things you absolutely need") AND standard markdown headings
     ("## Required Skills").
  3. Always run a full-document technology scan as a safety net — this
     catches every technology mentioned anywhere in the document, regardless
     of section structure.
  4. Infer role_type from vocabulary to enable dynamic scoring weights.
"""

from dataclasses import dataclass, field
import re
from typing import List, Optional, Tuple


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class JobRequirements:
    title: str = ""
    min_years_experience: float = 0.0
    required_skills: List[str] = field(default_factory=list)
    preferred_skills: List[str] = field(default_factory=list)
    required_education_degrees: List[str] = field(default_factory=list)
    required_education_fields: List[str] = field(default_factory=list)
    salary_budget_max_lpa: Optional[float] = None
    preferred_work_mode: str = "flexible"
    target_locations: List[str] = field(default_factory=list)
    required_features: List[str] = field(default_factory=list)
    mandatory_requirements: List[str] = field(default_factory=list)
    behavioural_expectations: List[str] = field(default_factory=list)
    # New fields for intelligent scoring
    role_type: str = "default"          # research | startup | leadership | platform | default
    hiring_signals: List[str] = field(default_factory=list)
    disqualifiers: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Technology vocabulary with synonym normalisation
# ---------------------------------------------------------------------------

# Map every surface form → canonical name
TECH_SYNONYM_MAP = {
    # Python ecosystem
    "python": "python",
    "pytorch": "pytorch",
    "tensorflow": "tensorflow",
    "keras": "keras",
    "scikit-learn": "scikit-learn",
    "sklearn": "scikit-learn",
    "numpy": "numpy",
    "pandas": "pandas",
    "sql": "sql",
    "spark": "spark",
    "airflow": "airflow",
    # Embeddings / representations
    "embeddings": "embeddings",
    "embedding": "embeddings",
    "dense vectors": "embeddings",
    "vectorization": "embeddings",
    "representation learning": "embeddings",
    "sentence transformers": "sentence transformers",
    "sentence-transformers": "sentence transformers",
    "sentence transformer": "sentence transformers",
    "bge": "bge",
    "e5": "e5",
    "openai embeddings": "openai embeddings",
    "openai embedding": "openai embeddings",
    "text embedding": "embeddings",
    "text-embedding": "embeddings",
    "bert": "bert",
    "roberta": "roberta",
    "word2vec": "word2vec",
    "glove": "glove",
    "fasttext": "fasttext",
    "bi-encoder": "embeddings",
    "cross-encoder": "embeddings",
    # Retrieval / search
    "retrieval": "retrieval",
    "information retrieval": "information retrieval",
    "dense retrieval": "retrieval",
    "sparse retrieval": "retrieval",
    "hybrid search": "hybrid retrieval",
    "hybrid retrieval": "hybrid retrieval",
    "semantic search": "retrieval",
    "lexical search": "retrieval",
    "search infrastructure": "retrieval",
    "search quality": "retrieval",
    "query understanding": "retrieval",
    "candidate matching": "retrieval",
    "marketplace search": "retrieval",
    "elasticsearch": "elasticsearch",
    "opensearch": "opensearch",
    "solr": "solr",
    "lucene": "lucene",
    "bm25": "bm25",
    "inverted index": "retrieval",
    "meilisearch": "retrieval",
    # Vector databases
    "vector databases": "vector databases",
    "vector database": "vector databases",
    "vector db": "vector databases",
    "vector search": "vector databases",
    "pinecone": "pinecone",
    "milvus": "milvus",
    "weaviate": "weaviate",
    "qdrant": "qdrant",
    "faiss": "faiss",
    "chromadb": "chromadb",
    "chroma": "chromadb",
    "pgvector": "pgvector",
    "ann": "vector databases",
    "nearest neighbor": "vector databases",
    "approximate nearest neighbor": "vector databases",
    "hnsw": "vector databases",
    "similarity search": "vector databases",
    # Ranking / LTR
    "ranking": "ranking",
    "learning to rank": "learning to rank",
    "ltr": "learning to rank",
    "ndcg": "ndcg",
    "mrr": "mrr",
    "map@k": "map",
    "mean average precision": "map",
    "mean reciprocal rank": "mrr",
    "normalized discounted cumulative gain": "ndcg",
    "re-ranking": "ranking",
    "reranking": "ranking",
    "scoring function": "ranking",
    "ranking model": "ranking",
    "pairwise ranking": "ranking",
    "listwise ranking": "ranking",
    "pointwise ranking": "ranking",
    "ads ranking": "ranking",
    "marketplace ranking": "ranking",
    "xgboost": "xgboost",
    "lightgbm": "lightgbm",
    "catboost": "catboost",
    # Recommendation systems
    "recommendation systems": "recommendation systems",
    "recommendation system": "recommendation systems",
    "recommendation": "recommendation systems",
    "recommendations": "recommendation systems",
    "recommender": "recommendation systems",
    "recommender system": "recommendation systems",
    "recsys": "recommendation systems",
    "collaborative filtering": "recommendation systems",
    "matrix factorization": "recommendation systems",
    "personalization": "recommendation systems",
    "candidate generation": "recommendation systems",
    "two-tower": "recommendation systems",
    "ctr prediction": "recommendation systems",
    "click-through rate": "recommendation systems",
    "deep & wide": "recommendation systems",
    "factorization machines": "recommendation systems",
    "session-based recommendation": "recommendation systems",
    # LLMs & fine-tuning
    "llm": "llms",
    "llms": "llms",
    "large language model": "llms",
    "large language models": "llms",
    "gpt": "llms",
    "fine tuning": "fine tuning",
    "fine-tuning": "fine tuning",
    "finetuning": "fine tuning",
    "llm fine tuning": "fine tuning",
    "llm fine-tuning": "fine tuning",
    "lora": "lora",
    "qlora": "qlora",
    "peft": "peft",
    "rlhf": "rlhf",
    "instruction tuning": "fine tuning",
    "parameter efficient": "peft",
    "parameter-efficient": "peft",
    # ML Infrastructure
    "distributed systems": "distributed systems",
    "distributed system": "distributed systems",
    "distributed training": "distributed systems",
    "mlops": "mlops",
    "kubeflow": "kubeflow",
    "mlflow": "mlflow",
    "model serving": "mlops",
    "inference pipeline": "mlops",
    "bentoml": "bentoml",
    "triton": "triton",
    "sagemaker": "sagemaker",
    "kubernetes": "kubernetes",
    "docker": "docker",
    "kafka": "kafka",
    "aws": "aws",
    # Evaluation
    "evaluation frameworks": "evaluation frameworks",
    "evaluation framework": "evaluation frameworks",
    "eval": "evaluation frameworks",
    "a/b testing": "evaluation frameworks",
    # Open source
    "open source": "open source",
    "open-source": "open source",
}

# Which canonical names map to which required_features bucket
FEATURE_BUCKETS = {
    "embeddings": ["embeddings", "sentence transformers", "bge", "e5", "openai embeddings",
                   "bert", "roberta", "word2vec", "glove", "fasttext"],
    "retrieval_search": ["retrieval", "information retrieval", "hybrid retrieval",
                         "elasticsearch", "opensearch", "solr", "lucene", "bm25"],
    "ranking_systems": ["ranking", "learning to rank", "ndcg", "mrr", "map",
                        "xgboost", "lightgbm", "catboost"],
    "vector_databases": ["vector databases", "pinecone", "milvus", "weaviate",
                         "qdrant", "faiss", "chromadb", "pgvector"],
    "recommendation_systems": ["recommendation systems", "collaborative filtering",
                                "matrix factorization", "personalization"],
    "production_ml": ["python", "pytorch", "tensorflow", "mlops", "distributed systems",
                      "fine tuning", "lora", "qlora", "peft", "sagemaker", "kubernetes"],
    "open_source": ["open source"],
}


def _word_boundary_search(term: str, text: str) -> bool:
    """Case-insensitive whole-word/phrase search."""
    if not term:
        return False
    # For multi-word phrases just do substring search (already lowered)
    if " " in term or "-" in term:
        return term in text
    return bool(re.search(rf"\b{re.escape(term)}\b", text))


def _extract_tech_from_text(text_lower: str) -> List[str]:
    """Scan text and return list of canonical technology names found."""
    found = []
    for surface, canonical in TECH_SYNONYM_MAP.items():
        if _word_boundary_search(surface, text_lower):
            found.append(canonical)
    return list(dict.fromkeys(found))  # preserve order, deduplicate


# ---------------------------------------------------------------------------
# Section classifier
# ---------------------------------------------------------------------------

# Redrob custom headings + standard markdown headings, both mapped to bucket names
_SECTION_RULES: List[Tuple[str, str]] = [
    # Redrob custom sections
    ("things you absolutely need",              "required"),
    ("things you need",                         "required"),
    ("absolutely need",                         "required"),
    ("required skills and experience",          "required"),
    ("requirements",                            "required"),
    ("things we'd like you to have but won't reject", "preferred"),
    ("things we'd like you to have",            "preferred"),
    ("nice to have but won't reject",           "preferred"),
    ("nice to have",                            "preferred"),
    ("preferred skills",                        "preferred"),
    ("preferred skills and experience",         "preferred"),
    ("things we explicitly do not want",        "disqualifiers"),
    ("explicitly do not want",                  "disqualifiers"),
    ("things we do not want",                   "disqualifiers"),
    ("the vibe check",                          "behavioural"),
    ("vibe check",                              "behavioural"),
    ("how to read between the lines",           "behavioural"),
    ("read between the lines",                  "behavioural"),
    ("final note for participants",             "behavioural"),
    ("final note",                              "behavioural"),
    # Standard markdown headings
    ("## required",                             "required"),
    ("## must have",                            "required"),
    ("## preferred",                            "preferred"),
    ("## nice to have",                         "preferred"),
    ("## do not want",                          "disqualifiers"),
    ("## behavioural",                          "behavioural"),
    ("## culture",                              "behavioural"),
    ("## about you",                            "behavioural"),
]

# Additional "required" heading patterns (for headings like "## Required Skills", "## Experience Required", etc.)
_REQ_MD_PATTERNS = [
    re.compile(r"^#+\s*required", re.IGNORECASE),
    re.compile(r"^#+\s*must.have", re.IGNORECASE),
    re.compile(r"^#+\s*what you.ll bring", re.IGNORECASE),
    re.compile(r"^#+\s*what we.re looking for", re.IGNORECASE),
    re.compile(r"^#+\s*qualifications", re.IGNORECASE),
    re.compile(r"^#+\s*responsibilities", re.IGNORECASE),
]
_PREF_MD_PATTERNS = [
    re.compile(r"^#+\s*preferred", re.IGNORECASE),
    re.compile(r"^#+\s*nice.to.have", re.IGNORECASE),
    re.compile(r"^#+\s*bonus", re.IGNORECASE),
]
_DISQ_MD_PATTERNS = [
    re.compile(r"^#+\s*(do not want|don.t want|explicitly not|not looking for)", re.IGNORECASE),
]
_BEH_MD_PATTERNS = [
    re.compile(r"^#+\s*(behaviour|culture|vibe|who you are|about you|soft skill)", re.IGNORECASE),
]


def _classify_line_to_section(raw_line: str) -> Optional[str]:
    """Return the section bucket name if this line is a section header, else None."""
    # Strip leading bullet chars so "- Things you absolutely need" still matches
    cleaned = re.sub(r"^\s*[-•*+–—]\s*", "", raw_line).strip()
    # Remove markdown formatting but keep the # for heading detection
    cleaned_no_hash = re.sub(r"[*_:]", "", cleaned).strip().lower()

    # Rule-based match (longest match first for specificity)
    for keyword, bucket in _SECTION_RULES:
        if cleaned_no_hash == keyword or cleaned_no_hash.startswith(keyword):
            return bucket

    # Regex-based markdown heading match
    stripped = cleaned.strip()
    for pat in _REQ_MD_PATTERNS:
        if pat.match(stripped):
            return "required"
    for pat in _PREF_MD_PATTERNS:
        if pat.match(stripped):
            return "preferred"
    for pat in _DISQ_MD_PATTERNS:
        if pat.match(stripped):
            return "disqualifiers"
    for pat in _BEH_MD_PATTERNS:
        if pat.match(stripped):
            return "behavioural"

    return None


# ---------------------------------------------------------------------------
# Main parser
# ---------------------------------------------------------------------------

class JDParser:

    @staticmethod
    def parse_file(file_path: str) -> JobRequirements:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
        except FileNotFoundError:
            content = ""
        if not content or len(content) < 50:
            return JobRequirements(title="Pending Job Description Upload")
        return JDParser.parse_text(content)

    @staticmethod
    def parse_text(text: str) -> JobRequirements:
        reqs = JobRequirements()
        if not text or len(text.strip()) < 20:
            return reqs

        lines = text.split("\n")
        text_lower = text.lower()

        # ---------------------------------------------------------------
        # 1. Metadata extraction
        # ---------------------------------------------------------------
        job_title = ""
        company_name = ""
        experience_text = ""

        for line in lines:
            ls = line.strip()
            if not ls:
                continue
            # Job title
            m = re.search(r"(?i)(?:job title|job description|role|position)\s*:\s*(.+)", ls)
            if m and not job_title:
                job_title = m.group(1).strip()
                continue
            # Company
            m = re.search(r"(?i)(?:company|employer|organization)\s*:\s*(.+)", ls)
            if m and not company_name:
                company_name = m.group(1).strip()
                continue
            # Experience
            m = re.search(r"(?i)(?:experience required|min experience|years of experience)\s*:\s*(.+)", ls)
            if m and not experience_text:
                experience_text = m.group(1).strip()
                continue
            # H1 fallback title
            if ls.startswith("# ") and not job_title:
                job_title = re.sub(r"^#+\s*", "", ls).strip()

        # Format title
        if job_title and company_name:
            reqs.title = f"{job_title} at {company_name}"
        elif job_title:
            reqs.title = job_title
        else:
            # Scan first non-empty lines for title-like content
            for line in lines[:10]:
                ls = re.sub(r"^[#\-•*+]\s*", "", line).strip()
                if len(ls) > 5 and ":" not in ls:
                    reqs.title = ls
                    break
            if not reqs.title:
                reqs.title = "Senior AI Engineer"

        # ---------------------------------------------------------------
        # 2. Experience extraction (robust, handles en-dash, em-dash, +)
        # ---------------------------------------------------------------
        exp_search = experience_text if experience_text else text
        m = re.search(r"(\d+)\s*[–—\-]\s*\d+\s*years?", exp_search, re.IGNORECASE)
        if m:
            reqs.min_years_experience = float(m.group(1))
        else:
            m = re.search(r"(\d+)\+?\s*years?", exp_search, re.IGNORECASE)
            if m:
                reqs.min_years_experience = float(m.group(1))
            else:
                reqs.min_years_experience = 5.0

        # ---------------------------------------------------------------
        # 3. Section-aware extraction
        # ---------------------------------------------------------------
        bucket_lines: dict = {
            "required": [],
            "preferred": [],
            "disqualifiers": [],
            "behavioural": [],
        }
        current_bucket: Optional[str] = None

        BULLET_RE = re.compile(r"^\s*[-•*+–—]\s*(.+)$")

        for line in lines:
            ls = line.strip()
            if not ls:
                continue

            section = _classify_line_to_section(ls)
            if section:
                current_bucket = section
                continue

            if current_bucket and current_bucket in bucket_lines:
                bucket_lines[current_bucket].append(ls)

        # ---------------------------------------------------------------
        # 4. Full-document technology scan (catches everything regardless
        #    of whether sections were detected)
        # ---------------------------------------------------------------
        all_doc_techs = _extract_tech_from_text(text_lower)

        # Skills from required section bullets
        required_techs: List[str] = []
        for line in bucket_lines["required"]:
            m = BULLET_RE.match(line)
            content = m.group(1).strip() if m else line.strip()
            techs = _extract_tech_from_text(content.lower())
            required_techs.extend(techs)
            # Short raw skill items (< 40 chars without tech map hits) kept as-is
            if not techs and len(content) < 40:
                required_techs.append(content.lower())

        # Skills from preferred section bullets
        preferred_techs: List[str] = []
        for line in bucket_lines["preferred"]:
            m = BULLET_RE.match(line)
            content = m.group(1).strip() if m else line.strip()
            techs = _extract_tech_from_text(content.lower())
            preferred_techs.extend(techs)
            if not techs and len(content) < 40:
                preferred_techs.append(content.lower())

        # Merge section-based + full-doc scan
        # Section-detected required skills take priority; full-doc scan fills gaps
        if required_techs:
            reqs.required_skills = list(dict.fromkeys(required_techs))
        else:
            # No sections found — treat all full-doc techs as required
            reqs.required_skills = list(dict.fromkeys(all_doc_techs))

        if preferred_techs:
            reqs.preferred_skills = list(dict.fromkeys(preferred_techs))

        # Deduplicate across lists
        req_set = set(reqs.required_skills)
        reqs.preferred_skills = [s for s in reqs.preferred_skills if s not in req_set]

        # Add remaining full-doc techs not captured in either list into required
        for tech in all_doc_techs:
            if tech not in req_set and tech not in reqs.preferred_skills:
                reqs.required_skills.append(tech)
                req_set.add(tech)

        # ---------------------------------------------------------------
        # 5. Disqualifiers
        # ---------------------------------------------------------------
        for line in bucket_lines["disqualifiers"]:
            m = BULLET_RE.match(line)
            content = m.group(1).strip() if m else line.strip()
            if content:
                reqs.mandatory_requirements.append(content)
                reqs.disqualifiers.append(content)
        reqs.mandatory_requirements = list(dict.fromkeys(reqs.mandatory_requirements))
        reqs.disqualifiers = list(dict.fromkeys(reqs.disqualifiers))

        # Also scan for NOT-want language in full document
        not_want_patterns = [
            re.compile(r"(?:we do not want|do not want|explicitly not|won't consider|we won't accept|no experience in)\s+(.+?)(?:\.|$)", re.IGNORECASE),
        ]
        for pat in not_want_patterns:
            for m in pat.finditer(text):
                phrase = m.group(1).strip()
                if phrase and phrase not in reqs.disqualifiers:
                    reqs.disqualifiers.append(phrase)

        # ---------------------------------------------------------------
        # 6. Behavioural expectations
        # ---------------------------------------------------------------
        for line in bucket_lines["behavioural"]:
            m = BULLET_RE.match(line)
            content = m.group(1).strip() if m else line.strip()
            if content:
                reqs.behavioural_expectations.append(content)
        reqs.behavioural_expectations = list(dict.fromkeys([b for b in reqs.behavioural_expectations if b]))

        # ---------------------------------------------------------------
        # 7. Hiring signals (evidence of what builder experience is valued)
        # ---------------------------------------------------------------
        hiring_signal_patterns = [
            re.compile(r"(?:must have built|must have shipped|must have designed|must have deployed)\s+(.+?)(?:\.|$)", re.IGNORECASE),
            re.compile(r"(?:production experience with|hands-on experience with|proven experience building)\s+(.+?)(?:\.|$)", re.IGNORECASE),
            re.compile(r"(?:you have shipped|you have built|you have designed)\s+(.+?)(?:\.|$)", re.IGNORECASE),
        ]
        for pat in hiring_signal_patterns:
            for m in pat.finditer(text):
                phrase = m.group(1).strip()
                if phrase and phrase not in reqs.hiring_signals:
                    reqs.hiring_signals.append(phrase)

        # ---------------------------------------------------------------
        # 8. Required features (for FeatureExtractor alignment)
        # ---------------------------------------------------------------
        all_required = set(reqs.required_skills)
        for feature, tech_list in FEATURE_BUCKETS.items():
            if any(tech in all_required for tech in tech_list):
                reqs.required_features.append(feature)
            elif any(_word_boundary_search(tech, text_lower) for tech in tech_list):
                reqs.required_features.append(feature)
        reqs.required_features = list(dict.fromkeys(reqs.required_features))

        # ---------------------------------------------------------------
        # 9. Education
        # ---------------------------------------------------------------
        if re.search(r"\bphd\b|\bph\.d\b", text_lower):
            reqs.required_education_degrees.append("phd")
        if re.search(r"\bmaster\b|\bm\.s\b|\bm\.tech\b|\bmasters\b", text_lower):
            reqs.required_education_degrees.append("master")
        if re.search(r"\bbachelor\b|\bb\.s\b|\bb\.tech\b|\bb\.e\b", text_lower):
            reqs.required_education_degrees.append("bachelor")
        if re.search(r"\bcomputer science\b|\bcs\b", text_lower):
            reqs.required_education_fields.append("computer science")
        if re.search(r"\bstatistics\b|\bmathematics\b", text_lower):
            reqs.required_education_fields.append("statistics")

        # ---------------------------------------------------------------
        # 10. Salary
        # ---------------------------------------------------------------
        m = re.search(r"(\d+)\s*(?:–|—|-|to)?\s*(\d+)\s*lpa", text_lower)
        if m and m.group(2):
            reqs.salary_budget_max_lpa = float(m.group(2))
        else:
            m = re.search(r"budget\D*?(\d+)\s*lpa", text_lower)
            if m:
                reqs.salary_budget_max_lpa = float(m.group(1))

        # ---------------------------------------------------------------
        # 11. Locations and work mode
        # ---------------------------------------------------------------
        KNOWN_LOCS = {
            "toronto": "Toronto", "chennai": "Chennai",
            "bangalore": "Bangalore", "bengaluru": "Bangalore",
            "mumbai": "Mumbai", "hyderabad": "Hyderabad", "delhi": "Delhi",
        }
        for loc_lower, loc_display in KNOWN_LOCS.items():
            if re.search(rf"\b{loc_lower}\b", text_lower) and loc_display not in reqs.target_locations:
                reqs.target_locations.append(loc_display)

        if "remote" in text_lower:
            reqs.preferred_work_mode = "remote"
        elif "hybrid" in text_lower:
            reqs.preferred_work_mode = "hybrid"
        elif re.search(r"\bon.?site\b", text_lower):
            reqs.preferred_work_mode = "onsite"
        else:
            reqs.preferred_work_mode = "flexible"

        # ---------------------------------------------------------------
        # 12. Role type inference (drives dynamic scoring weights)
        # ---------------------------------------------------------------
        research_signals = ["paper", "publication", "arxiv", "research scientist", "phd", "academic"]
        startup_signals = ["startup", "seed stage", "series a", "early stage", "founding engineer", "equity", "0 to 1"]
        leadership_signals = ["engineering manager", "tech lead", "head of", "director", "vp of", "principal engineer"]
        platform_signals = ["platform", "infrastructure", "scale to", "millions of", "distributed system", "reliability"]

        role_scores = {
            "research": sum(1 for s in research_signals if s in text_lower),
            "startup": sum(1 for s in startup_signals if s in text_lower),
            "leadership": sum(1 for s in leadership_signals if s in text_lower),
            "platform": sum(1 for s in platform_signals if s in text_lower),
        }
        best_role = max(role_scores, key=role_scores.get)
        reqs.role_type = best_role if role_scores[best_role] >= 2 else "default"

        # ---------------------------------------------------------------
        # Validation log (printed once to confirm extraction worked)
        # ---------------------------------------------------------------
        print(f"[JDParser] title={reqs.title!r} exp={reqs.min_years_experience} "
              f"role_type={reqs.role_type!r} "
              f"required_skills={len(reqs.required_skills)} "
              f"preferred_skills={len(reqs.preferred_skills)} "
              f"required_features={reqs.required_features}")

        return reqs

    @staticmethod
    def get_default_requirements() -> JobRequirements:
        """
        Loads the saved JD from disk. Falls back to an empty placeholder if
        the file is absent or too short to be a real JD (< 50 chars).
        Uses an absolute path anchored to this file's location.
        """
        import os
        _src_dir = os.path.dirname(os.path.abspath(__file__))
        jd_path = os.path.normpath(os.path.join(_src_dir, "..", "data", "job_description.md"))
        if os.path.exists(jd_path):
            try:
                with open(jd_path, "r", encoding="utf-8") as f:
                    text = f.read().strip()
                if len(text) >= 50:
                    return JDParser.parse_text(text)
            except Exception:
                pass
        return JobRequirements(title="Pending Job Description Upload")
