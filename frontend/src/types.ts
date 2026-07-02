export interface SkillEntry {
  name: string;
  proficiency: string;
  endorsements: number;
  duration_months: number;
}

export interface EducationEntry {
  institution: string;
  degree: string;
  field_of_study: string;
  start_year: number | null;
  end_year: number | null;
  grade: string | null;
  tier: string;
}

export interface JobEntry {
  company: string;
  role: string;
  description: string;
  start_date: string;
  end_date: string | null;
  duration_months: number;
  is_current: boolean;
  industry: string;
  company_size: string;
}

export interface CertificationEntry {
  name: string;
  issuer: string;
  year: number | null;
}

export interface LanguageEntry {
  language: string;
  proficiency: string;
}

export interface RedrobSignals {
  profile_completeness_score: number;
  signup_date: string;
  last_active_date: string;
  open_to_work_flag: boolean;
  profile_views_received_30d: number;
  applications_submitted_30d: number;
  recruiter_response_rate: number;
  avg_response_time_hours: number;
  skill_assessment_scores: Record<string, number>;
  connection_count: number;
  endorsements_received: number;
  notice_period_days: number;
  expected_salary_range_inr_lpa: { min: number; max: number };
  preferred_work_mode: string;
  willing_to_relocate: boolean;
  github_activity_score: number;
  search_appearance_30d: number;
  saved_by_recruiters_30d: number;
  interview_completion_rate: number;
  offer_acceptance_rate: number;
  verified_email: boolean;
  verified_phone: boolean;
  linkedin_connected: boolean;
}

export interface CandidateProfile {
  candidate_id: string;
  anonymized_name: string;
  headline: string;
  summary: string;
  current_role: string;
  current_company: string;
  current_company_size: string;
  current_industry: string;
  location: string;
  country: string;
  years_experience: number;
  skills: SkillEntry[];
  education: EducationEntry[];
  certifications: CertificationEntry[];
  languages: LanguageEntry[];
  career_history: JobEntry[];
  behavioral_signals: RedrobSignals;
}

export interface ExtractedFeatures {
  production_ml: number;
  retrieval_search: number;
  recommendation_systems: number;
  ranking_systems: number;
  vector_databases: number;
  embeddings: number;
  leadership: number;
  product_company: number;
  services_only: number;
  open_source: number;
  candidate_activity: number;
}

export interface SubScoreBreakdown {
  score: number;
  [key: string]: any;
}

export interface TechnicalScoreDetails extends SubScoreBreakdown {
  role_alignment: number;
  feature_alignment: number;
  skill_alignment: number;
  assessment_boost: number;
  certification_boost: number;
  matched_features: Record<string, number>;
}

export interface CareerScoreDetails extends SubScoreBreakdown {
  experience_match: number;
  domain_alignment?: number;
  stability_index: number;
  title_progression: number;
  prestige_rating: number;
  company_prestige: number;
  education_prestige: number;
}

export interface BehaviourScoreDetails extends SubScoreBreakdown {
  responsiveness: number;
  profile_integrity: number;
  activity_level: number;
  response_rate: number;
  response_speed: number;
}

export interface RiskScoreDetails extends SubScoreBreakdown {
  notice_period_risk: number;
  ghosting_risk: number;
  renege_risk: number;
  salary_risk: number;
  location_risk: number;
}

export interface SubScores {
  technical: TechnicalScoreDetails;
  career: CareerScoreDetails;
  behaviour: BehaviourScoreDetails;
  risk: RiskScoreDetails;
}

export interface ScoredProfile {
  candidate_id: string;
  name: string;
  headline: string;
  current_role: string;
  current_company: string;
  years_experience: number;
  final_score: number;
  hiring_confidence?: number;
  decision?: string;
  is_blocked: boolean;
  blocker_reasons: string[];
  sub_scores: SubScores;
  profile: CandidateProfile;
  extracted_features: ExtractedFeatures;
  explanation?: {
    strengths: string[];
    weaknesses: string[];
    recommendation: string;
    hiring_confidence?: number;
    recruiter_reasoning?: string;
    missing_requirements?: string[];
    potential_risks?: string[];
  };
}

export interface JobRequirements {
  title: string;
  min_years_experience: number;
  required_skills: string[];
  preferred_skills: string[];
  required_education_degrees: string[];
  required_education_fields: string[];
  salary_budget_max_lpa: number | null;
  preferred_work_mode: string;
  target_locations: string[];
  required_features: string[];
  mandatory_requirements: string[];
  behavioural_expectations: string[];
}

export interface RankResponse {
  processed_count: number;
  unblocked_count: number;
  blocked_count: number;
  elapsed_time: number;
  candidates: ScoredProfile[];
  jd: JobRequirements;
}
