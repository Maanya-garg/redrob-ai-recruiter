import React, { useMemo } from "react";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, PieChart, Pie, Cell, Legend } from "recharts";
import { RankResponse } from "../types";

interface AnalyticsProps {
  results: RankResponse;
}

const COLORS = ["#10b981", "#6366f1", "#f59e0b", "#64748b", "#ef4444"];

export default function Analytics({ results }: AnalyticsProps) {
  const { candidates } = results;

  // 1. Score Distribution
  const scoreData = useMemo(() => {
    const bins = {
      "0-50 (Reject/Low)": 0,
      "50-65 (Consider)": 0,
      "65-80 (Hire)": 0,
      "80-100 (Strong)": 0
    };

    candidates.forEach((c) => {
      if (c.is_blocked) return; // skip blocked
      const score = c.final_score;
      if (score >= 80) bins["80-100 (Strong)"]++;
      else if (score >= 65) bins["65-80 (Hire)"]++;
      else if (score >= 50) bins["50-65 (Consider)"]++;
      else bins["0-50 (Reject/Low)"]++;
    });

    return Object.entries(bins).map(([name, count]) => ({ name, count }));
  }, [candidates]);

  // 2. Recommendation Breakdown (Pie Chart)
  const recommendationData = useMemo(() => {
    const counts = {
      "Strong Hire": 0,
      "Hire": 0,
      "Consider": 0,
      "Reject": 0,
      "Blocked": 0
    };

    candidates.forEach((c) => {
      if (c.is_blocked) {
        counts["Blocked"]++;
        return;
      }
      const rec = c.explanation?.recommendation || "";
      if (rec.includes("STRONG HIRE")) counts["Strong Hire"]++;
      else if (rec.includes("HIRE")) counts["Hire"]++;
      else if (rec.includes("CONSIDER")) counts["Consider"]++;
      else counts["Reject"]++;
    });

    return Object.entries(counts)
      .map(([name, value]) => ({ name, value }))
      .filter((d) => d.value > 0);
  }, [candidates]);

  // 3. Top Skills Distribution
  const skillsData = useMemo(() => {
    const counts: Record<string, number> = {};
    candidates.forEach((c) => {
      c.profile.skills.forEach((s) => {
        const name = s.name.trim().toLowerCase();
        counts[name] = (counts[name] || 0) + 1;
      });
    });

    return Object.entries(counts)
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10); // top 10 skills
  }, [candidates]);

  // 4. Experience Ranges
  const experienceData = useMemo(() => {
    const bins = {
      "0-2 Years": 0,
      "2-5 Years": 0,
      "5-8 Years": 0,
      "8+ Years": 0
    };

    candidates.forEach((c) => {
      const exp = c.years_experience;
      if (exp >= 8) bins["8+ Years"]++;
      else if (exp >= 5) bins["5-8 Years"]++;
      else if (exp >= 2) bins["2-5 Years"]++;
      else bins["0-2 Years"]++;
    });

    return Object.entries(bins).map(([name, count]) => ({ name, count }));
  }, [candidates]);

  // 5. Common Company Origins
  const companyData = useMemo(() => {
    const counts: Record<string, number> = {};
    candidates.forEach((c) => {
      if (c.current_company) {
        const comp = c.current_company.trim();
        counts[comp] = (counts[comp] || 0) + 1;
      }
    });

    return Object.entries(counts)
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 8); // top 8 companies
  }, [candidates]);

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold font-display text-white">Ranking Analytics</h1>
        <p className="text-muted-foreground text-sm">
          Telemetry statistics, skills distribution, and experience metrics computed across ranked applicants.
        </p>
      </div>

      {/* Grid Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Recommendation Breakdown Pie */}
        <div className="p-6 rounded-2xl glass-card flex flex-col items-center">
          <h2 className="text-base font-bold font-display text-white mb-6 self-start">Hiring Recommendation Mix</h2>
          <div className="w-full h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={recommendationData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {recommendationData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ backgroundColor: "rgba(10, 10, 18, 0.95)", borderColor: "rgba(255, 255, 255, 0.1)", borderRadius: "8px" }}
                  itemStyle={{ color: "#fff" }}
                />
                <Legend verticalAlign="bottom" height={36} wrapperStyle={{ fontSize: "11px" }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Score Distribution Bar */}
        <div className="p-6 rounded-2xl glass-card">
          <h2 className="text-base font-bold font-display text-white mb-6">Candidate Score Distribution</h2>
          <div className="w-full h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={scoreData} margin={{ left: -20 }}>
                <XAxis dataKey="name" stroke="#64748b" fontSize={10} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={10} tickLine={false} />
                <Tooltip 
                  cursor={{ fill: "rgba(99, 102, 241, 0.05)" }}
                  contentStyle={{ backgroundColor: "rgba(10, 10, 18, 0.95)", borderColor: "rgba(255, 255, 255, 0.1)", borderRadius: "8px" }}
                  itemStyle={{ color: "#fff" }}
                />
                <Bar dataKey="count" fill="url(#indigoGrad)" radius={[4, 4, 0, 0]}>
                  {scoreData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fillOpacity={0.85} />
                  ))}
                </Bar>
                <defs>
                  <linearGradient id="indigoGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#8b5cf6" />
                    <stop offset="100%" stopColor="#4f46e5" />
                  </linearGradient>
                </defs>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Top Technical Skills */}
        <div className="p-6 rounded-2xl glass-card">
          <h2 className="text-base font-bold font-display text-white mb-6">Top 10 Applicant Skills</h2>
          <div className="w-full h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={skillsData} layout="vertical" margin={{ left: -10 }}>
                <XAxis type="number" stroke="#64748b" fontSize={10} tickLine={false} />
                <YAxis dataKey="name" type="category" stroke="#64748b" fontSize={10} tickLine={false} width={80} />
                <Tooltip 
                  cursor={{ fill: "rgba(99, 102, 241, 0.05)" }}
                  contentStyle={{ backgroundColor: "rgba(10, 10, 18, 0.95)", borderColor: "rgba(255, 255, 255, 0.1)", borderRadius: "8px" }}
                  itemStyle={{ color: "#fff" }}
                />
                <Bar dataKey="count" fill="url(#violetGrad)" radius={[0, 4, 4, 0]} />
                <defs>
                  <linearGradient id="violetGrad" x1="0" y1="0" x2="1" y2="0">
                    <stop offset="0%" stopColor="#4f46e5" />
                    <stop offset="100%" stopColor="#ec4899" />
                  </linearGradient>
                </defs>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Experience ranges */}
        <div className="p-6 rounded-2xl glass-card">
          <h2 className="text-base font-bold font-display text-white mb-6">Years of Experience Mix</h2>
          <div className="w-full h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={experienceData} margin={{ left: -20 }}>
                <XAxis dataKey="name" stroke="#64748b" fontSize={10} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={10} tickLine={false} />
                <Tooltip 
                  cursor={{ fill: "rgba(99, 102, 241, 0.05)" }}
                  contentStyle={{ backgroundColor: "rgba(10, 10, 18, 0.95)", borderColor: "rgba(255, 255, 255, 0.1)", borderRadius: "8px" }}
                  itemStyle={{ color: "#fff" }}
                />
                <Bar dataKey="count" fill="url(#cyanGrad)" radius={[4, 4, 0, 0]} />
                <defs>
                  <linearGradient id="cyanGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#06b6d4" />
                    <stop offset="100%" stopColor="#0284c7" />
                  </linearGradient>
                </defs>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Company distribution */}
        <div className="p-6 rounded-2xl glass-card lg:col-span-2">
          <h2 className="text-base font-bold font-display text-white mb-6">Applicant Employer Origin (Top 8 Companies)</h2>
          <div className="w-full h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={companyData} margin={{ left: -20 }}>
                <XAxis dataKey="name" stroke="#64748b" fontSize={10} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={10} tickLine={false} />
                <Tooltip 
                  cursor={{ fill: "rgba(99, 102, 241, 0.05)" }}
                  contentStyle={{ backgroundColor: "rgba(10, 10, 18, 0.95)", borderColor: "rgba(255, 255, 255, 0.1)", borderRadius: "8px" }}
                  itemStyle={{ color: "#fff" }}
                />
                <Bar dataKey="count" fill="url(#multiGrad)" radius={[4, 4, 0, 0]} />
                <defs>
                  <linearGradient id="multiGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#ec4899" />
                    <stop offset="100%" stopColor="#8b5cf6" />
                  </linearGradient>
                </defs>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

      </div>
    </div>
  );
}
