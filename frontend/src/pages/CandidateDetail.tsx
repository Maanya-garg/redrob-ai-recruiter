import React, { useState } from "react";
import { ArrowLeft, CheckCircle2, AlertTriangle, XOctagon, Briefcase, GraduationCap, Award, Languages, Activity, ShieldAlert, Cpu } from "lucide-react";
import { ScoredProfile } from "../types";

interface CandidateDetailProps {
  candidate: ScoredProfile;
  onBack: () => void;
}

export default function CandidateDetail({ candidate, onBack }: CandidateDetailProps) {
  const [activeTab, setActiveTab] = useState<"summary" | "experience" | "behavior">("summary");
  
  const { profile, sub_scores, explanation, is_blocked, blocker_reasons, final_score, extracted_features } = candidate;

  // Render a beautiful SVG circular progress ring for the overall score
  const renderScoreRing = (score: number, label: string, size = 120, strokeWidth = 10, color = "rgb(99, 102, 241)") => {
    const radius = (size - strokeWidth) / 2;
    const circumference = radius * 2 * Math.PI;
    const strokeDashoffset = circumference - (score / 100) * circumference;

    return (
      <div className="flex flex-col items-center justify-center space-y-2">
        <div className="relative" style={{ width: size, height: size }}>
          <svg className="transform -rotate-90 w-full h-full">
            {/* Background Circle */}
            <circle
              cx={size / 2}
              cy={size / 2}
              r={radius}
              className="stroke-white/5 fill-transparent"
              strokeWidth={strokeWidth}
            />
            {/* Foreground Progress */}
            <circle
              cx={size / 2}
              cy={size / 2}
              r={radius}
              className="transition-all duration-500 ease-out fill-transparent"
              strokeWidth={strokeWidth}
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              stroke={color}
              strokeLinecap="round"
            />
          </svg>
          {/* Inner Text */}
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-2xl font-extrabold font-display text-white">{score.toFixed(0)}</span>
            <span className="text-[10px] text-muted-foreground font-semibold uppercase tracking-wider">/100</span>
          </div>
        </div>
        <span className="text-xs font-bold text-slate-300">{label}</span>
      </div>
    );
  };

  const getSubscoreColor = (score: number) => {
    if (score >= 80) return "rgb(34, 197, 94)"; // Green
    if (score >= 65) return "rgb(99, 102, 241)"; // Indigo
    if (score >= 50) return "rgb(234, 179, 8)"; // Yellow
    return "rgb(239, 68, 68)"; // Red
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Back Header */}
      <button
        onClick={onBack}
        className="inline-flex items-center gap-1.5 text-xs font-semibold text-indigo-400 hover:text-indigo-300 transition-colors py-1.5 px-3 rounded-lg bg-white/5 border border-white/5 hover:border-white/10 active:scale-95"
      >
        <ArrowLeft className="w-3.5 h-3.5" /> Back to Results
      </button>

      {/* Hero Profile Header */}
      <div className="p-6 rounded-2xl glass border border-white/5 flex flex-col md:flex-row justify-between items-start md:items-center gap-6 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/5 rounded-full blur-3xl -z-10"></div>
        
        <div className="space-y-2">
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-extrabold font-display text-white">{profile.anonymized_name}</h1>
            <span className="text-xs font-bold text-muted-foreground bg-white/5 border border-white/10 px-2 py-0.5 rounded-lg font-mono">
              {profile.candidate_id}
            </span>
          </div>
          <p className="text-indigo-400 font-semibold text-sm md:text-base">{profile.headline}</p>
          <p className="text-xs text-muted-foreground">
            📍 {profile.location}, {profile.country} | 💼 {profile.years_experience} years experience
          </p>
        </div>

        {/* Circular Overall Score Display */}
        <div className="flex-shrink-0 self-center">
          {renderScoreRing(
            is_blocked ? 0.0 : final_score, 
            is_blocked ? "Blocked" : "Overall Fit", 
            130, 
            12, 
            is_blocked ? "rgb(239, 68, 68)" : getSubscoreColor(final_score)
          )}
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column: Sub-scores & Explanations */}
        <div className="space-y-6 lg:col-span-1">
          {/* Subscores Grid */}
          <div className="p-5 rounded-2xl glass-card space-y-4">
            <h2 className="text-lg font-bold font-display text-white border-b border-white/10 pb-2">Subscore Breakdowns</h2>
            <div className="grid grid-cols-2 gap-4">
              {renderScoreRing(sub_scores.technical.score, "Technical", 90, 8, getSubscoreColor(sub_scores.technical.score))}
              {renderScoreRing(sub_scores.career.score, "Career Fit", 90, 8, getSubscoreColor(sub_scores.career.score))}
              {renderScoreRing(sub_scores.behaviour.score, "Behaviour", 90, 8, getSubscoreColor(sub_scores.behaviour.score))}
              {renderScoreRing(sub_scores.risk.score, "Risk Score", 90, 8, "rgb(239, 68, 68)")}
            </div>
          </div>

          {/* Core Recruiter Verdict */}
          <div className="p-5 rounded-2xl glass-card space-y-3">
            <h3 className="text-xs uppercase font-bold tracking-wider text-muted-foreground">Recruiter Decision</h3>
            <div className="p-4 rounded-xl bg-black/45 border border-white/5 space-y-2">
              <div className="text-sm font-bold text-white flex items-center gap-1.5">
                {is_blocked ? (
                  <span className="text-red-400 flex items-center gap-1"><XOctagon className="w-4 h-4" /> Reject</span>
                ) : explanation?.recommendation.includes("STRONG HIRE") ? (
                  <span className="text-green-400 flex items-center gap-1"><CheckCircle2 className="w-4 h-4" /> Strong Hire</span>
                ) : explanation?.recommendation.includes("HIRE") ? (
                  <span className="text-indigo-400 flex items-center gap-1"><CheckCircle2 className="w-4 h-4" /> Hire</span>
                ) : explanation?.recommendation.includes("CONSIDER") ? (
                  <span className="text-yellow-400 flex items-center gap-1"><AlertTriangle className="w-4 h-4" /> Consider</span>
                ) : (
                  <span className="text-red-400 flex items-center gap-1"><XOctagon className="w-4 h-4" /> Reject</span>
                )}
              </div>
              <p className="text-xs text-slate-300 italic">
                {explanation?.recommendation || "Needs detailed evaluations."}
              </p>
            </div>
          </div>
        </div>

        {/* Right Columns: Structured Tabs Detail */}
        <div className="lg:col-span-2 space-y-6">
          {/* Navigation Tabs */}
          <div className="flex border-b border-white/10 text-sm">
            <button
              onClick={() => setActiveTab("summary")}
              className={`pb-3.5 px-4 font-bold border-b-2 transition-all ${
                activeTab === "summary" 
                  ? "border-indigo-500 text-indigo-400" 
                  : "border-transparent text-muted-foreground hover:text-white"
              }`}
            >
              Profile Summary & Strengths
            </button>
            <button
              onClick={() => setActiveTab("experience")}
              className={`pb-3.5 px-4 font-bold border-b-2 transition-all ${
                activeTab === "experience" 
                  ? "border-indigo-500 text-indigo-400" 
                  : "border-transparent text-muted-foreground hover:text-white"
              }`}
            >
              Work & Education History
            </button>
            <button
              onClick={() => setActiveTab("behavior")}
              className={`pb-3.5 px-4 font-bold border-b-2 transition-all ${
                activeTab === "behavior" 
                  ? "border-indigo-500 text-indigo-400" 
                  : "border-transparent text-muted-foreground hover:text-white"
              }`}
            >
              Recruiting Telemetry & Skills
            </button>
          </div>

          {/* Tab 1: Profile Summary & Strengths */}
          {activeTab === "summary" && (
            <div className="space-y-6 animate-fade-in">
              {/* About summary */}
              <div className="p-5 rounded-xl glass border border-white/5 space-y-2">
                <h3 className="text-sm font-bold text-white flex items-center gap-1.5">
                  <Cpu className="w-4 h-4 text-indigo-400" /> Professional Summary
                </h3>
                <p className="text-sm text-slate-300 leading-relaxed font-sans">
                  {profile.summary}
                </p>
              </div>

              {/* Strengths & Weaknesses list */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Strengths */}
                <div className="p-5 rounded-xl bg-green-950/20 border border-green-500/10 space-y-3">
                  <h4 className="text-sm font-bold text-green-400 flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4" /> Hiring Strengths
                  </h4>
                  <ul className="space-y-2 text-xs text-slate-300 list-disc list-inside">
                    {explanation?.strengths.map((str, idx) => (
                      <li key={idx} className="leading-relaxed">{str}</li>
                    ))}
                  </ul>
                </div>

                {/* Weaknesses */}
                <div className="p-5 rounded-xl bg-red-950/20 border border-red-500/10 space-y-3">
                  <h4 className="text-sm font-bold text-red-400 flex items-center gap-1.5">
                    <ShieldAlert className="w-4 h-4" /> Risks & Warning flags
                  </h4>
                  <ul className="space-y-2 text-xs text-slate-300 list-disc list-inside">
                    {explanation?.weaknesses.map((weak, idx) => (
                      <li key={idx} className="leading-relaxed">{weak}</li>
                    ))}
                    {is_blocked && blocker_reasons.map((br, idx) => (
                      <li key={`br-${idx}`} className="text-red-400 font-bold leading-relaxed">{br}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}

          {/* Tab 2: Work & Education Timeline */}
          {activeTab === "experience" && (
            <div className="space-y-8 animate-fade-in">
              {/* Career History timeline */}
              <div className="space-y-4">
                <h3 className="text-sm font-bold text-white flex items-center gap-1.5 border-b border-white/5 pb-2">
                  <Briefcase className="w-4 h-4 text-indigo-400" /> Career History
                </h3>
                <div className="relative pl-6 border-l-2 border-white/10 space-y-6">
                  {profile.career_history.map((job, idx) => (
                    <div key={idx} className="relative space-y-1">
                      {/* Timeline dot */}
                      <div className="absolute -left-[31px] top-1.5 w-4 h-4 rounded-full bg-indigo-500 border-4 border-slate-950"></div>
                      
                      <div className="flex justify-between items-start">
                        <div>
                          <h4 className="font-bold text-white text-sm">{job.role}</h4>
                          <div className="text-xs text-indigo-400 font-semibold">
                            {job.company} &middot; <span className="text-muted-foreground font-normal">{job.company_size} employees</span>
                          </div>
                        </div>
                        <span className="text-[10px] bg-white/5 px-2 py-0.5 rounded text-muted-foreground font-mono">
                          {job.start_date} to {job.end_date || "Present"} ({job.duration_months} mo)
                        </span>
                      </div>
                      <p className="text-xs text-slate-300 leading-relaxed font-sans pt-1">
                        {job.description}
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Education section */}
              <div className="space-y-4">
                <h3 className="text-sm font-bold text-white flex items-center gap-1.5 border-b border-white/5 pb-2">
                  <GraduationCap className="w-4 h-4 text-purple-400" /> Education history
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {profile.education.map((edu, idx) => (
                    <div key={idx} className="p-4 rounded-xl bg-white/5 border border-white/5 space-y-1.5">
                      <div className="flex justify-between items-start">
                        <span className="text-xs font-bold text-white">{edu.degree} in {edu.field_of_study}</span>
                        <span className="text-[10px] bg-indigo-500/10 text-indigo-400 font-bold px-1.5 py-0.5 rounded uppercase">
                          {edu.tier.replace("_", " ")}
                        </span>
                      </div>
                      <div className="text-xs text-muted-foreground font-medium">{edu.institution}</div>
                      {edu.grade && (
                        <div className="text-[10px] text-slate-400">Grade: <span className="text-white font-bold">{edu.grade}</span></div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Tab 3: Recruiting Telemetry & Skills */}
          {activeTab === "behavior" && (
            <div className="space-y-8 animate-fade-in">
              {/* Telemetry and behavior stats */}
              <div className="space-y-4">
                <h3 className="text-sm font-bold text-white flex items-center gap-1.5 border-b border-white/5 pb-2">
                  <Activity className="w-4 h-4 text-indigo-400" /> Engagement Telemetry
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="p-4 rounded-xl bg-white/5 border border-white/5 text-center space-y-1">
                    <span className="text-muted-foreground text-[10px] uppercase font-bold tracking-wider">Notice Period</span>
                    <div className="text-base font-extrabold text-white">{profile.behavioral_signals.notice_period_days} Days</div>
                  </div>
                  <div className="p-4 rounded-xl bg-white/5 border border-white/5 text-center space-y-1">
                    <span className="text-muted-foreground text-[10px] uppercase font-bold tracking-wider">Interview Attendance</span>
                    <div className="text-base font-extrabold text-white">{(profile.behavioral_signals.interview_completion_rate * 100).toFixed(0)}%</div>
                  </div>
                  <div className="p-4 rounded-xl bg-white/5 border border-white/5 text-center space-y-1">
                    <span className="text-muted-foreground text-[10px] uppercase font-bold tracking-wider">Salary Demand</span>
                    <div className="text-base font-extrabold text-white">{profile.behavioral_signals.expected_salary_range_inr_lpa.min} LPA</div>
                  </div>
                  <div className="p-4 rounded-xl bg-white/5 border border-white/5 text-center space-y-1">
                    <span className="text-muted-foreground text-[10px] uppercase font-bold tracking-wider">Response Speed</span>
                    <div className="text-base font-extrabold text-white">{profile.behavioral_signals.avg_response_time_hours.toFixed(1)} Hrs</div>
                  </div>
                </div>
              </div>

              {/* Skills breakdown */}
              <div className="space-y-4">
                <h3 className="text-sm font-bold text-white flex items-center gap-1.5 border-b border-white/5 pb-2">
                  <Award className="w-4 h-4 text-pink-400" /> Technical Skills & Endorsements
                </h3>
                <div className="flex flex-wrap gap-2.5">
                  {profile.skills.map((s, idx) => (
                    <div
                      key={idx}
                      className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 border border-white/5 hover:border-white/10 transition-colors"
                    >
                      <span className="text-xs font-bold text-white">{s.name}</span>
                      <span className="text-[10px] text-indigo-400 font-semibold capitalize font-mono">
                        {s.proficiency}
                      </span>
                      {s.endorsements > 0 && (
                        <span className="text-[9px] px-1 bg-white/10 text-slate-300 rounded font-bold font-mono">
                          +{s.endorsements}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Certifications and Languages */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Languages */}
                <div className="p-5 rounded-xl bg-white/5 border border-white/5 space-y-3">
                  <h4 className="text-xs uppercase font-extrabold text-muted-foreground tracking-wider flex items-center gap-1.5">
                    <Languages className="w-4 h-4 text-indigo-400" /> Spoken Languages
                  </h4>
                  <div className="space-y-2">
                    {profile.languages.map((l, idx) => (
                      <div key={idx} className="flex justify-between items-center text-xs">
                        <span className="font-bold text-white">{l.language}</span>
                        <span className="text-muted-foreground capitalize">{l.proficiency}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Certifications */}
                <div className="p-5 rounded-xl bg-white/5 border border-white/5 space-y-3">
                  <h4 className="text-xs uppercase font-extrabold text-muted-foreground tracking-wider flex items-center gap-1.5">
                    <Award className="w-4 h-4 text-pink-400" /> Credentials
                  </h4>
                  <div className="space-y-2.5">
                    {profile.certifications.length > 0 ? (
                      profile.certifications.map((c, idx) => (
                        <div key={idx} className="text-xs leading-relaxed">
                          <div className="font-bold text-white">{c.name}</div>
                          <div className="text-muted-foreground text-[10px]">{c.issuer} {c.year ? `(${c.year})` : ""}</div>
                        </div>
                      ))
                    ) : (
                      <span className="text-xs text-muted-foreground">No certifications listed.</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
