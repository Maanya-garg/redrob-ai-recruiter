"""
Candidate Profile Builder
Parses the Redrob candidate JSON into a structured, type-safe CandidateProfile object.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class EducationEntry:
    institution: str
    degree: str = ""
    field_of_study: str = ""
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    grade: Optional[str] = None
    tier: str = "unknown"


@dataclass
class JobEntry:
    company: str
    role: str
    description: str = ""
    start_date: str = ""
    end_date: Optional[str] = None
    duration_months: int = 0
    is_current: bool = False
    industry: str = ""
    company_size: str = ""
    skills_used: List[str] = field(default_factory=list)


@dataclass
class SkillEntry:
    name: str
    proficiency: str = "beginner"
    endorsements: int = 0
    duration_months: int = 0


@dataclass
class CertificationEntry:
    name: str
    issuer: str = ""
    year: Optional[int] = None


@dataclass
class LanguageEntry:
    language: str
    proficiency: str = "basic"


@dataclass
class RedrobSignals:
    profile_completeness_score: float = 0.0
    signup_date: str = ""
    last_active_date: str = ""
    open_to_work_flag: bool = False
    profile_views_received_30d: int = 0
    applications_submitted_30d: int = 0
    recruiter_response_rate: float = 0.0
    avg_response_time_hours: float = 0.0
    skill_assessment_scores: Dict[str, float] = field(default_factory=dict)
    connection_count: int = 0
    endorsements_received: int = 0
    notice_period_days: int = 0
    expected_salary_range_inr_lpa: Dict[str, float] = field(default_factory=dict)
    preferred_work_mode: str = "flexible"
    willing_to_relocate: bool = False
    github_activity_score: float = -1.0
    search_appearance_30d: int = 0
    saved_by_recruiters_30d: int = 0
    interview_completion_rate: float = 0.0
    offer_acceptance_rate: float = -1.0
    verified_email: bool = False
    verified_phone: bool = False
    linkedin_connected: bool = False


@dataclass
class CandidateProfile:
    candidate_id: str
    anonymized_name: str
    headline: str
    summary: str
    current_role: str
    current_company: str
    current_company_size: str
    current_industry: str
    location: str
    country: str
    years_experience: float
    skills: List[SkillEntry] = field(default_factory=list)
    education: List[EducationEntry] = field(default_factory=list)
    certifications: List[CertificationEntry] = field(default_factory=list)
    languages: List[LanguageEntry] = field(default_factory=list)
    career_history: List[JobEntry] = field(default_factory=list)
    behavioral_signals: RedrobSignals = field(default_factory=RedrobSignals)


class CandidateProfileBuilder:

    @staticmethod
    def build(candidate_json: Dict[str, Any]) -> CandidateProfile:
        if not isinstance(candidate_json, dict):
            raise TypeError("Candidate must be a dictionary")

        profile = candidate_json.get("profile", {})
        candidate_id = str(
            candidate_json.get("candidate_id")
            or candidate_json.get("id")
            or ""
        )

        anonymized_name = str(profile.get("anonymized_name") or "")
        headline = str(profile.get("headline") or "")
        summary = str(profile.get("summary") or "")
        current_role = str(profile.get("current_title") or "")
        current_company = str(profile.get("current_company") or "")
        current_company_size = str(profile.get("current_company_size") or "")
        current_industry = str(profile.get("current_industry") or "")
        location = str(profile.get("location") or "")
        country = str(profile.get("country") or "")

        try:
            years_experience = float(profile.get("years_of_experience", 0.0))
        except (ValueError, TypeError):
            years_experience = 0.0

        # Parse skills
        skills = []
        raw_skills = candidate_json.get("skills", [])
        if isinstance(raw_skills, list):
            for skill in raw_skills:
                if isinstance(skill, dict):
                    name = skill.get("name")
                    if name:
                        try:
                            endorsements = int(skill.get("endorsements", 0))
                        except (ValueError, TypeError):
                            endorsements = 0
                        try:
                            duration = int(skill.get("duration_months", 0))
                        except (ValueError, TypeError):
                            duration = 0
                        skills.append(
                            SkillEntry(
                                name=str(name).strip().lower(),
                                proficiency=str(skill.get("proficiency", "beginner")).strip().lower(),
                                endorsements=endorsements,
                                duration_months=duration,
                            )
                        )
                elif isinstance(skill, str):
                    skills.append(SkillEntry(name=skill.strip().lower()))

        # Parse education
        education = []
        raw_education = candidate_json.get("education", [])
        if isinstance(raw_education, list):
            for edu in raw_education:
                if not isinstance(edu, dict):
                    continue
                education.append(
                    EducationEntry(
                        institution=str(edu.get("institution") or edu.get("school") or ""),
                        degree=str(edu.get("degree") or ""),
                        field_of_study=str(edu.get("field_of_study") or edu.get("major") or ""),
                        start_year=edu.get("start_year"),
                        end_year=edu.get("end_year"),
                        grade=edu.get("grade"),
                        tier=str(edu.get("tier") or "unknown").strip().lower(),
                    )
                )

        # Parse certifications (fixes the scoping bug)
        certifications = []
        raw_certifications = candidate_json.get("certifications", [])
        if isinstance(raw_certifications, list):
            for cert in raw_certifications:
                if isinstance(cert, dict):
                    name = cert.get("name")
                    if name:
                        certifications.append(
                            CertificationEntry(
                                name=str(name).strip(),
                                issuer=str(cert.get("issuer") or "").strip(),
                                year=cert.get("year"),
                            )
                        )
                elif isinstance(cert, str):
                    certifications.append(CertificationEntry(name=cert.strip()))

        # Parse languages
        languages = []
        raw_languages = candidate_json.get("languages", [])
        if isinstance(raw_languages, list):
            for lang in raw_languages:
                if isinstance(lang, dict):
                    language_name = lang.get("language") or lang.get("name")
                    if language_name:
                        languages.append(
                            LanguageEntry(
                                language=str(language_name).strip(),
                                proficiency=str(lang.get("proficiency", "basic")).strip().lower(),
                            )
                        )
                elif isinstance(lang, str):
                    languages.append(LanguageEntry(language=lang.strip()))

        # Parse career history
        career_history = []
        raw_history = candidate_json.get("career_history", [])
        if isinstance(raw_history, list):
            for job in raw_history:
                if not isinstance(job, dict):
                    continue
                
                try:
                    duration_months = int(job.get("duration_months", 0))
                except (ValueError, TypeError):
                    duration_months = 0

                is_current = bool(job.get("is_current", False))

                career_history.append(
                    JobEntry(
                        company=str(job.get("company") or job.get("organization") or ""),
                        role=str(job.get("role") or job.get("title") or ""),
                        description=str(job.get("description") or ""),
                        start_date=str(job.get("start_date") or ""),
                        end_date=str(job.get("end_date") or "") if job.get("end_date") else None,
                        duration_months=duration_months,
                        is_current=is_current,
                        industry=str(job.get("industry") or ""),
                        company_size=str(job.get("company_size") or ""),
                        skills_used=[],
                    )
                )

        # Parse behavioral signals
        raw_signals = (
            candidate_json.get("redrob_signals")
            or candidate_json.get("behavioral_signals")
            or candidate_json.get("behavioral")
            or {}
        )
        
        # Safely convert expected salary dict
        raw_salary = raw_signals.get("expected_salary_range_inr_lpa") or {}
        expected_salary = {"min": 0.0, "max": 0.0}
        if isinstance(raw_salary, dict):
            try:
                expected_salary["min"] = float(raw_salary.get("min", 0.0))
                expected_salary["max"] = float(raw_salary.get("max", 0.0))
            except (ValueError, TypeError):
                pass

        # Safely convert skill assessment scores
        raw_assessments = raw_signals.get("skill_assessment_scores") or {}
        assessments = {}
        if isinstance(raw_assessments, dict):
            for s_name, s_score in raw_assessments.items():
                try:
                    assessments[str(s_name)] = float(s_score)
                except (ValueError, TypeError):
                    pass

        signals = RedrobSignals(
            profile_completeness_score=float(raw_signals.get("profile_completeness_score", 0.0)),
            signup_date=str(raw_signals.get("signup_date") or ""),
            last_active_date=str(raw_signals.get("last_active_date") or ""),
            open_to_work_flag=bool(raw_signals.get("open_to_work_flag", False)),
            profile_views_received_30d=int(raw_signals.get("profile_views_received_30d", 0)),
            applications_submitted_30d=int(raw_signals.get("applications_submitted_30d", 0)),
            recruiter_response_rate=float(raw_signals.get("recruiter_response_rate", 0.0)),
            avg_response_time_hours=float(raw_signals.get("avg_response_time_hours", 0.0)),
            skill_assessment_scores=assessments,
            connection_count=int(raw_signals.get("connection_count", 0)),
            endorsements_received=int(raw_signals.get("endorsements_received", 0)),
            notice_period_days=int(raw_signals.get("notice_period_days", 0)),
            expected_salary_range_inr_lpa=expected_salary,
            preferred_work_mode=str(raw_signals.get("preferred_work_mode", "flexible")).strip().lower(),
            willing_to_relocate=bool(raw_signals.get("willing_to_relocate", False)),
            github_activity_score=float(raw_signals.get("github_activity_score", -1.0)),
            search_appearance_30d=int(raw_signals.get("search_appearance_30d", 0)),
            saved_by_recruiters_30d=int(raw_signals.get("saved_by_recruiters_30d", 0)),
            interview_completion_rate=float(raw_signals.get("interview_completion_rate", 0.0)),
            offer_acceptance_rate=float(raw_signals.get("offer_acceptance_rate", -1.0)),
            verified_email=bool(raw_signals.get("verified_email", False)),
            verified_phone=bool(raw_signals.get("verified_phone", False)),
            linkedin_connected=bool(raw_signals.get("linkedin_connected", False)),
        )

        # Infer current role/company if blank
        if not current_role and career_history:
            current_role = career_history[0].role
        if not current_company and career_history:
            current_company = career_history[0].company

        return CandidateProfile(
            candidate_id=candidate_id,
            anonymized_name=anonymized_name,
            headline=headline,
            summary=summary,
            current_role=current_role,
            current_company=current_company,
            current_company_size=current_company_size,
            current_industry=current_industry,
            location=location,
            country=country,
            years_experience=years_experience,
            skills=skills,
            education=education,
            certifications=certifications,
            languages=languages,
            career_history=career_history,
            behavioral_signals=signals,
        )