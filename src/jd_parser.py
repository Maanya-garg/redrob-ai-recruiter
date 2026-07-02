"""
Job Description (JD) Parser Module
Parses real Redrob Hackathon Job Descriptions using regex, Unicode bullets,
and case-insensitive semantic pattern matching.
"""

from dataclasses import dataclass, field
import re
from typing import List, Optional


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


class JDParser:

    @staticmethod
    def parse_file(file_path: str) -> JobRequirements:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
        except FileNotFoundError:
            content = ""

        if not content:
            return JobRequirements(title="Pending Job Description Upload")

        return JDParser.parse_text(content)

    @staticmethod
    def parse_text(text: str) -> JobRequirements:
        print("ENTERED JDParser.parse_text()")
        print("TOTAL TEXT LENGTH:", len(text))
        lines = text.split("\n")
        print("TOTAL LINES:", len(lines))
        print("FIRST 20 LINES:")
        for i, line in enumerate(lines[:20]):
            print(i, repr(line))
        reqs = JobRequirements()
        text_lower = text.lower()

        # Specific section header mappings to prevent accidental matching on bullet points
        sections_map = {
            "absolutely_need": [
                "things you absolutely need",
                "things you need",
                "absolutely need",
                "required skills and experience"
            ],
            "nice_to_have": [
                "things we'd like you to have but won't reject you for",
                "things we'd like you to have",
                "nice to have but won't reject",
                "preferred skills and experience",
                "nice to have"
            ],
            "explicitly_not_want": [
                "things we explicitly do not want",
                "explicitly do not want",
                "things we do not want"
            ],
            "vibe_check": [
                "the vibe check",
                "vibe check"
            ],
            "read_between_lines": [
                "how to read between the lines",
                "read between the lines"
            ]
        }

        def classify_section(line: str) -> Optional[str]:
            # Clean bullet prefixes (•, -, *, +, etc.) first so we can parse bulleted headers
            line_clean = re.sub(r"^\s*(?:[•\-\*\+–—]|\d+\.)\s*", "", line)
            # Strip markdown formatting and colons
            line_clean = re.sub(r"[#\*_:]", "", line_clean).strip().lower()
            
            for sec_name, keywords in sections_map.items():
                for kw in keywords:
                    if line_clean == kw or line_clean.startswith(kw):
                        return sec_name
            return None

        # 1. Parse Metadata (Job Title, Company, Experience)
        job_title = ""
        company_name = ""
        experience_text = ""

        current_section = "general"
        section_lines = {
            "absolutely_need": [],
            "nice_to_have": [],
            "explicitly_not_want": [],
            "vibe_check": [],
            "read_between_lines": []
        }

        # Track metadata directly
        for line in lines:
            line_strip = line.strip()
            print("[DEBUG LINE]", repr(line))
            if not line_strip:
                continue

            # Classify current section
            classified = classify_section(line_strip)
            print(f"[DEBUG] classify_section({repr(line_strip)!r}) -> {classified!r}  (current={current_section!r})")
            if classified:
                current_section = classified
                continue
            elif line_strip.startswith("#") and current_section == "general":
                # Use H1 header as fallback job title
                if not job_title:
                    job_title = re.sub(r"[#\*_]", "", line_strip).strip()
                continue

            # Meta-field scans
            title_match = re.search(r"(?i)(?:job title|job description|role|position)\s*:\s*(.+)", line_strip)
            if title_match:
                job_title = title_match.group(1).strip()
                continue

            company_match = re.search(r"(?i)(?:company|employer|organization)\s*:\s*(.+)", line_strip)
            if company_match:
                company_name = company_match.group(1).strip()
                continue

            exp_match = re.search(r"(?i)(?:experience required|experience|min experience)\s*:\s*(.+)", line_strip)
            if exp_match:
                experience_text = exp_match.group(1).strip()
                continue

            if current_section in section_lines:
                print(f"[DEBUG] Appending to section {current_section!r}: {repr(line_strip)}")
                section_lines[current_section].append(line_strip)

        # DEBUG: dump all collected section lines
        print("[DEBUG] section_lines after loop:")
        import json
        for sec_key, sec_vals in section_lines.items():
            print(f"  [{sec_key}] ({len(sec_vals)} lines):")
            for v in sec_vals:
                print(f"    {repr(v)}")

        # 2. Format Job Title incorporating Company if present
        if job_title and company_name:
            reqs.title = f"{job_title} at {company_name}"
        elif job_title:
            reqs.title = job_title
        else:
            reqs.title = "Senior AI Engineer"

        # 3. Parse Experience Range (Robust Unicode & Phrase Matcher)
        # Matches formats: 5–9 years, 5-9 years, 5 to 9 years, 5+ years, 5 years
        # Handles standard dash (-), unicode en-dash (–), em-dash (—)
        exp_search_text = experience_text if experience_text else text
        exp_match = re.search(r"(\d+)\s*(?:\-|–|—|to|\+)\s*(?:\d+)?\s*years?", exp_search_text, re.IGNORECASE)
        if exp_match:
            try:
                reqs.min_years_experience = float(exp_match.group(1))
            except ValueError:
                reqs.min_years_experience = 5.0  # Safe default if parsing fails
        else:
            # Fallback to single count
            fallback_match = re.search(r"(\d+)\s*years?", exp_search_text, re.IGNORECASE)
            if fallback_match:
                try:
                    reqs.min_years_experience = float(fallback_match.group(1))
                except ValueError:
                    reqs.min_years_experience = 5.0
            else:
                reqs.min_years_experience = 5.0  # Hackathon standard default

        # 4. Map Target Locations and Work Mode
        KNOWN_LOCATIONS = ["toronto", "chennai", "bangalore", "bengaluru"]
        for loc in KNOWN_LOCATIONS:
            if re.search(rf"\b{loc}\b", text_lower):
                # Standardize Bengaluru to Bangalore
                loc_name = "Bangalore" if loc in ["bangalore", "bengaluru"] else loc.capitalize()
                reqs.target_locations.append(loc_name)
        reqs.target_locations = list(dict.fromkeys(reqs.target_locations))

        if "remote" in text_lower:
            reqs.preferred_work_mode = "remote"
        elif "hybrid" in text_lower:
            reqs.preferred_work_mode = "hybrid"
        elif "onsite" in text_lower or "on-site" in text_lower:
            reqs.preferred_work_mode = "onsite"
        else:
            reqs.preferred_work_mode = "flexible"

        # 5. Extract Skills (Bullet Points & Paragraphs Scans)
        # We check for unicode bullets, en/em dashes, plusses, stars, hyphens, and list numbers
        bullet_pattern = r"^\s*(?:[•\-\*\+–—]|\d+\.)\s*(.+)$"

        KNOWN_TECH = [
            "python", "embeddings", "embedding", "sentence transformers", "sentence transformer",
            "openai embeddings", "openai embedding", "bge", "e5", "retrieval", "retrievals",
            "hybrid retrieval", "hybrid retrievals", "ranking", "rankings", "learning to rank",
            "vector databases", "vector database", "vector db", "vector search",
            "pinecone", "weaviate", "qdrant", "milvus", "faiss", "opensearch",
            "ndcg", "mrr", "map", "llms", "llm", "fine tuning", "fine-tuning",
            "lora", "qlora", "peft", "distributed systems", "distributed system",
            "recommendation systems", "recommendation system", "recsys",
            "evaluation frameworks", "evaluation framework", "eval", "evaluation",
            "pytorch", "sql", "spark", "airflow", "weights & biases", "bentoml", "aws", "docker", "fastapi"
        ]

        TECH_NORMALIZATION = {
            "embedding": "embeddings",
            "embeddings": "embeddings",
            "openai embedding": "openai embeddings",
            "openai embeddings": "openai embeddings",
            "sentence transformer": "sentence transformers",
            "sentence transformers": "sentence transformers",
            "retrievals": "retrieval",
            "retrieval": "retrieval",
            "hybrid retrievals": "hybrid retrieval",
            "hybrid retrieval": "hybrid retrieval",
            "rankings": "ranking",
            "ranking": "ranking",
            "vector database": "vector databases",
            "vector databases": "vector databases",
            "vector db": "vector databases",
            "vector search": "vector databases",
            "llms": "llms",
            "llm": "llms",
            "fine-tuning": "fine tuning",
            "fine tuning": "fine tuning",
            "distributed system": "distributed systems",
            "distributed systems": "distributed systems",
            "recommendation system": "recommendation systems",
            "recommendation systems": "recommendation systems",
            "recsys": "recommendation systems",
            "evaluation framework": "evaluation frameworks",
            "evaluation frameworks": "evaluation frameworks",
            "open-source": "open source",
            "open source": "open source"
        }

        def check_tech_presence(tech: str, text_line: str) -> bool:
            tech_clean = tech.lower()
            line_clean = text_line.lower()
            if "&" in tech_clean or "+" in tech_clean or "-" in tech_clean:
                return tech_clean in line_clean
            return bool(re.search(rf"\b{re.escape(tech_clean)}\b", line_clean))

        # Check required skills from absolutely_need section
        for line in section_lines["absolutely_need"]:
            match_bullet = re.match(bullet_pattern, line)
            content = match_bullet.group(1).strip() if match_bullet else line.strip()
            
            # If bullet is short, treat it as a direct skill name
            if len(content) < 30:
                reqs.required_skills.append(content.lower())
            
            # Scan line for known technologies
            for tech_key, tech_val in TECH_NORMALIZATION.items():
                if check_tech_presence(tech_key, content):
                    reqs.required_skills.append(tech_val)
            for tech in KNOWN_TECH:
                if tech not in TECH_NORMALIZATION and check_tech_presence(tech, content):
                    reqs.required_skills.append(tech)

        # Check preferred skills from nice_to_have section
        for line in section_lines["nice_to_have"]:
            match_bullet = re.match(bullet_pattern, line)
            content = match_bullet.group(1).strip() if match_bullet else line.strip()
            
            if len(content) < 30:
                reqs.preferred_skills.append(content.lower())
            
            for tech_key, tech_val in TECH_NORMALIZATION.items():
                if check_tech_presence(tech_key, content):
                    reqs.preferred_skills.append(tech_val)
            for tech in KNOWN_TECH:
                if tech not in TECH_NORMALIZATION and check_tech_presence(tech, content):
                    reqs.preferred_skills.append(tech)

        # Remove duplicate skills and cleanup
        reqs.required_skills = list(dict.fromkeys([s.strip().lower() for s in reqs.required_skills if s.strip()]))
        reqs.preferred_skills = list(dict.fromkeys([s.strip().lower() for s in reqs.preferred_skills if s.strip()]))

        # Prevent overlap between required and preferred lists
        reqs.preferred_skills = [s for s in reqs.preferred_skills if s not in reqs.required_skills]

        # 6. Extract Disqualifiers (Things explicitly do NOT want)
        for line in section_lines["explicitly_not_want"]:
            match_bullet = re.match(bullet_pattern, line)
            content = match_bullet.group(1).strip() if match_bullet else line.strip()
            if content:
                reqs.mandatory_requirements.append(content)
        reqs.mandatory_requirements = list(dict.fromkeys([r.strip() for r in reqs.mandatory_requirements if r.strip()]))

        # 7. Extract Behavioural Expectations (Vibe Check, How to read between the lines)
        for sec in ["vibe_check", "read_between_lines"]:
            for line in section_lines[sec]:
                match_bullet = re.match(bullet_pattern, line)
                content = match_bullet.group(1).strip() if match_bullet else line.strip()
                if content:
                    reqs.behavioural_expectations.append(content)
        reqs.behavioural_expectations = list(dict.fromkeys([b.strip() for b in reqs.behavioural_expectations if b.strip()]))

        # 8. Parse Education (Simple keyword flags)
        if "phd" in text_lower or "ph.d" in text_lower:
            reqs.required_education_degrees.append("phd")
        if "master" in text_lower or "m.s" in text_lower or "m.tech" in text_lower:
            reqs.required_education_degrees.append("master")
        if "bachelor" in text_lower or "b.s" in text_lower or "b.tech" in text_lower or "b.e" in text_lower:
            reqs.required_education_degrees.append("bachelor")
        
        if "computer science" in text_lower or "cs" in text_lower:
            reqs.required_education_fields.append("computer science")
        if "statistics" in text_lower or "mathematics" in text_lower or "math" in text_lower:
            reqs.required_education_fields.append("statistics")

        # 9. Parse Salary Budget Max
        salary_match = re.search(r"(\d+)\s*(?:-|to)?\s*(\d+)\s*lpa", text_lower)
        if salary_match:
            reqs.salary_budget_max_lpa = float(salary_match.group(2))
        else:
            salary_single = re.search(r"budget\D*(\d+)\s*lpa", text_lower)
            if salary_single:
                reqs.salary_budget_max_lpa = float(salary_single.group(1))

        # 10. Generate Required Features for FeatureExtractor and RankingEngine
        features_map = {
            "embeddings": ["embeddings", "sentence transformers", "openai embeddings", "bge", "e5"],
            "retrieval_search": ["retrieval", "hybrid retrieval", "opensearch", "search"],
            "ranking_systems": ["ranking", "learning to rank", "ndcg", "mrr", "map"],
            "vector_databases": ["vector databases", "pinecone", "weaviate", "qdrant", "milvus", "faiss"],
            "production_ml": ["python", "pytorch", "distributed systems", "llms", "fine tuning", "lora", "qlora", "peft"],
            "recommendation_systems": ["recommendation systems"],
            "open_source": ["open source"],
            "leadership": ["leadership", "architect", "lead", "manage", "mentor"]
        }

        all_skills = reqs.required_skills + reqs.preferred_skills
        for feature, keywords in features_map.items():
            if any(kw in all_skills for kw in keywords):
                reqs.required_features.append(feature)
            elif any(check_tech_presence(kw, text) for kw in keywords):
                reqs.required_features.append(feature)
        reqs.required_features = list(dict.fromkeys(reqs.required_features))

        # Logging / Printing parsed output for platform validation
        print("--- PARSED JOB DESCRIPTION OUTPUT ---")
        print(f"Title: {reqs.title}")
        print(f"Experience: {reqs.min_years_experience}")
        print(f"Required Skills ({len(reqs.required_skills)}): {reqs.required_skills}")
        print(f"Preferred Skills ({len(reqs.preferred_skills)}): {reqs.preferred_skills}")
        print(f"Required Features ({len(reqs.required_features)}): {reqs.required_features}")
        print(f"Mandatory Requirements ({len(reqs.mandatory_requirements)}): {reqs.mandatory_requirements}")
        print(f"Behavioural Expectations ({len(reqs.behavioural_expectations)}): {reqs.behavioural_expectations}")
        print("-------------------------------------")

        return reqs

    @staticmethod
    def get_default_requirements() -> JobRequirements:
        """
        Dynamically loads the saved job description from the data directory to avoid hardcoded defaults.
        Uses an absolute path anchored to this file's location so it works regardless of cwd.
        """
        import os
        _src_dir = os.path.dirname(os.path.abspath(__file__))
        jd_path = os.path.join(_src_dir, "..", "data", "job_description.md")
        jd_path = os.path.normpath(jd_path)
        if os.path.exists(jd_path):
            try:
                with open(jd_path, "r", encoding="utf-8") as f:
                    text = f.read().strip()
                if len(text) >= 50:
                    return JDParser.parse_text(text)
            except Exception:
                pass
        return JobRequirements(title="Pending Job Description Upload")

