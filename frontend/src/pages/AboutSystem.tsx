import React from "react";
import { Info, Cpu, Award, ShieldAlert, HeartHandshake, Compass } from "lucide-react";

export default function AboutSystem() {
  return (
    <div className="space-y-8 animate-fade-in text-slate-300 max-w-4xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold font-display text-white flex items-center gap-2">
          <Info className="w-8 h-8 text-indigo-400" /> About the Ranking Engine
        </h1>
        <p className="text-muted-foreground text-sm">
          Technical specifications, scoring formulas, and recruiter reasoning heuristics.
        </p>
      </div>

      {/* Architecture Overview */}
      <div className="p-6 rounded-2xl glass-card space-y-4">
        <h2 className="text-lg font-bold font-display text-white flex items-center gap-2 border-b border-white/10 pb-2">
          <Cpu className="w-5 h-5 text-indigo-400" /> System Architecture
        </h2>
        <p className="text-sm leading-relaxed">
          The Redrob Recruiter system utilizes a <strong>Streaming Pipeline</strong> architecture designed to process hundreds of thousands of candidate profiles memory-efficiently. Rather than loading the database into RAM, the engine streams candidate objects line-by-line from a JSONL file, deserializing and computing scoring metrics in real-time.
        </p>
        <p className="text-sm leading-relaxed">
          Before scoring, a <strong>Feature Extractor</strong> runs semantic rule-based models on each candidate to infer domain qualifications (e.g. Production ML, RecSys, Search Infrastructure, Vector DBs, MLOps, Leadership). It scans job descriptions and resumes for action-oriented descriptions, looking for semantic verbs (e.g. <em>deployed</em>, <em>designed</em>, <em>optimized</em>) adjacent to concepts to verify hands-on builder experience rather than just skill listings.
        </p>
      </div>

      {/* Primary Scoring Formula */}
      <div className="p-6 rounded-2xl glass-card space-y-4 bg-indigo-500/5 border-indigo-500/10">
        <h2 className="text-lg font-bold font-display text-white flex items-center gap-2 border-b border-indigo-500/15 pb-2">
          <Compass className="w-5 h-5 text-indigo-400" /> Primary Ranking Equation
        </h2>
        <p className="text-sm">
          The ranking engine aggregates multiple dimensions of fit into a single composite rank score. The formula is defined as:
        </p>
        
        {/* LaTeX block formula */}
        <div className="py-6 px-4 my-2 rounded-xl bg-black/45 text-center text-white border border-white/5 font-mono text-sm overflow-x-auto">
          {"S_{final} = 0.50 \\cdot S_{tech} + 0.25 \\cdot S_{career} + 0.10 \\cdot S_{behaviour} - 0.15 \\cdot S_{risk}"}
        </div>
        
        <p className="text-xs text-muted-foreground italic">
          Note: S_final is clamped strictly between 0.0 and 100.0. A high notice period, ghosting history, or budget mismatch increases S_risk, causing a negative deduction to the final score.
        </p>
      </div>

      {/* Scoring Modules Breakdown */}
      <div className="space-y-6">
        <h2 className="text-lg font-bold font-display text-white border-b border-white/10 pb-2">Scoring Modules Specifications</h2>
        
        {/* Tech Score */}
        <div className="p-5 rounded-xl glass border border-white/5 space-y-3">
          <h3 className="text-sm font-extrabold text-green-400 flex items-center gap-2">
            <Award className="w-4 h-4" /> Technical Score (S_tech)
          </h3>
          <p className="text-xs text-slate-300">
            Measures matching title strings, semantic capabilities, and skill proficiencies. Weight: <strong>50%</strong> of final score.
          </p>
          <ul className="list-disc list-inside text-xs text-slate-400 space-y-1.5 pl-2">
            <li><strong>Role Title Alignment (20%)</strong>: Cosine/Jaro-Winkler similarity matching current title/headline against the JD target.</li>
            <li><strong>Extracted Features Match (50%)</strong>: Matches inferred candidate signals (built recsys, optimized search, MLOps) against JD requirements. Includes a <em>Builder Boost</em> (+15% per job) for descriptive action verbs.</li>
            <li><strong>Explicit Skills (30%)</strong>: Matches profile skills list, weighted by proficiency multipliers (Expert=1.0, Beginner=0.25) and log-scaled endorsements.</li>
            <li><strong>Assessment Verification Boost (+10 max)</strong>: Positive points for passing objective platform tests with a score &gt;= 70.</li>
            <li><strong>Certifications Boost (+5 max)</strong>: Positive points for relevant industry credentials.</li>
          </ul>
        </div>

        {/* Career Score */}
        <div className="p-5 rounded-xl glass border border-white/5 space-y-3">
          <h3 className="text-sm font-extrabold text-indigo-400 flex items-center gap-2">
            <Cpu className="w-4 h-4" /> Career Score (S_career)
          </h3>
          <p className="text-xs text-slate-300">
            Evaluates professional trajectory, company/major prestige, and employment tenure. Weight: <strong>25%</strong> of final score.
          </p>
          <ul className="list-disc list-inside text-xs text-slate-400 space-y-1.5 pl-2">
            <li><strong>Experience Match (35%)</strong>: Compares candidate years of experience against the JD minimum target. Deducts 15 points per year under requirement.</li>
            <li><strong>Job Stability Index (25%)</strong>: Evaluates candidate tenure frequency. Penalizes job changes occurring at less than 1.5 year intervals.</li>
            <li><strong>Career Title Progression (15%)</strong>: Evaluates chronological job histories for vertical hierarchy movements (e.g. developer to senior to architect).</li>
            <li><strong>Employer & Academic Prestige (25%)</strong>: Aggregates weights from school tiers (Tier-1 to Tier-4) and prior employer company sizes (flattened weights of 0.65 to 1.0 to avoid startup penalties).</li>
          </ul>
        </div>

        {/* Behaviour Score */}
        <div className="p-5 rounded-xl glass border border-white/5 space-y-3">
          <h3 className="text-sm font-extrabold text-yellow-500 flex items-center gap-2">
            <HeartHandshake className="w-4 h-4" /> Behaviour Score (S_behaviour)
          </h3>
          <p className="text-xs text-slate-300">
            Measures responsiveness metrics and verified platform engagement. Weight: <strong>10%</strong> of final score.
          </p>
          <ul className="list-disc list-inside text-xs text-slate-400 space-y-1.5 pl-2">
            <li><strong>Recruiter Responsiveness (40%)</strong>: Matches communication response rates and speeds (0-2 hours = 100, &gt;168 hours = 0).</li>
            <li><strong>Profile Completeness & Verifications (30%)</strong>: Profile completeness score + boosts for email, phone, and LinkedIn verifications.</li>
            <li><strong>Platform Activity & Demand (30%)</strong>: Open-to-work flag + log-normalized monthly profile views and search appearances.</li>
          </ul>
        </div>

        {/* Risk Score */}
        <div className="p-5 rounded-xl glass border border-white/5 space-y-3">
          <h3 className="text-sm font-extrabold text-red-500 flex items-center gap-2">
            <ShieldAlert className="w-4 h-4" /> Risk & Blocker Score (S_risk)
          </h3>
          <p className="text-xs text-slate-300">
            Measures candidate risk metrics and flags block conditions. Weight: <strong>15%</strong> (subtracted) of final score.
          </p>
          <ul className="list-disc list-inside text-xs text-slate-400 space-y-1.5 pl-2">
            <li><strong>Notice Period Risk (30%)</strong>: Penalizes notice periods &gt; 60 days (extremely high risk for urgent project fills).</li>
            <li><strong>Interview Ghosting Risk (30%)</strong>: Risk score = (100 - interview attendance rate), identifying flakiness.</li>
            <li><strong>Offer Acceptance Risk (20%)</strong>: Evaluates historical propensity to decline or accept offers.</li>
            <li><strong>Non-Linear Salary Mismatch (20%)</strong>: Soft non-linear curve. Under 10% mismatch gets minor penalty; scales up to 100 risk score only for extreme mismatch (&gt;30% budget excess).</li>
            <li><strong>Relocation Blockers</strong>: Candidates located in different cities with no willingness to relocate are flagged as high risk for strictly hybrid/onsite roles.</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
