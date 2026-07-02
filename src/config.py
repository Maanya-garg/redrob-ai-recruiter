"""
Configuration settings for the Redrob AI Recruiter Ranking Engine.
"""

# Legacy fallback weights — overridden at runtime by ROLE_WEIGHTS in ranking_engine.py
# based on jd.role_type (research / startup / leadership / platform / default)
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

# Company size prestige — intentionally flattened to avoid over-rewarding brand names.
# Domain alignment in career_score.py is the primary differentiator instead.
COMPANY_SIZE_PRESTIGE_WEIGHTS = {
    "10001+": 0.90,
    "5001-10000": 0.85,
    "1001-5000": 0.80,
    "501-1000": 0.78,
    "201-500": 0.75,
    "51-200": 0.72,
    "11-50": 0.70,
    "1-10": 0.68,
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

# NOTE: FEATURE_KEYWORDS has been moved to src/feature_extractor.py
# to keep all evidence-based keyword logic co-located with the extractor.
# Import from there if needed: from src.feature_extractor import FEATURE_KEYWORDS
