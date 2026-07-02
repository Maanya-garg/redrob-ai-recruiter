import React, { useState, useMemo } from "react";
import { Search, Filter, ArrowUpDown, ChevronLeft, ChevronRight, Download, CheckCircle, AlertTriangle, XOctagon } from "lucide-react";
import { RankResponse, ScoredProfile } from "../types";

interface RankingResultsProps {
  results: RankResponse;
  onSelectCandidate: (candidateId: string) => void;
  addToast: (msg: string, type: "success" | "error" | "info") => void;
}

export default function RankingResults({
  results,
  onSelectCandidate,
  addToast
}: RankingResultsProps) {
  const [search, setSearch] = useState("");
  const [recFilter, setRecFilter] = useState("all");
  const [minExp, setMinExp] = useState<number | "">("");
  const [sortBy, setSortBy] = useState<"final_score" | "technical" | "career" | "behaviour" | "risk" | "years_experience">("final_score");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  
  // Pagination
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  // Filters & Sorting
  const filteredCandidates = useMemo(() => {
    let list = [...results.candidates];

    // Search
    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter(
        (c) =>
          c.name.toLowerCase().includes(q) ||
          c.headline.toLowerCase().includes(q) ||
          c.current_role.toLowerCase().includes(q) ||
          c.current_company.toLowerCase().includes(q) ||
          c.candidate_id.toLowerCase().includes(q)
      );
    }

    // Recommendation Filter
    if (recFilter !== "all") {
      list = list.filter((c) => {
        const rec = (c as any).recommendation || c.explanation?.recommendation || "";
        const recLower = rec.toLowerCase();
        if (recFilter === "strong") return recLower.includes("strong hire");
        if (recFilter === "interview") return recLower.includes("interview");
        if (recFilter === "potential") return recLower.includes("potential");
        if (recFilter === "hold") return recLower.includes("hold");
        if (recFilter === "notrelevant") return recLower.includes("not relevant");
        return true;
      });
    }

    // Experience Filter
    if (minExp !== "") {
      list = list.filter((c) => c.years_experience >= minExp);
    }

    // Sorting
    list.sort((a, b) => {
      let valA: number;
      let valB: number;

      if (sortBy === "final_score") {
        valA = a.final_score;
        valB = b.final_score;
      } else if (sortBy === "years_experience") {
        valA = a.years_experience;
        valB = b.years_experience;
      } else {
        // Sub-scores
        valA = a.sub_scores[sortBy]?.score || 0;
        valB = b.sub_scores[sortBy]?.score || 0;
      }

      if (valA < valB) return sortOrder === "asc" ? -1 : 1;
      if (valA > valB) return sortOrder === "asc" ? 1 : -1;
      return 0;
    });

    return list;
  }, [results, search, recFilter, minExp, sortBy, sortOrder]);

  // Paginated List
  const paginatedCandidates = useMemo(() => {
    const start = (page - 1) * pageSize;
    return filteredCandidates.slice(start, start + pageSize);
  }, [filteredCandidates, page, pageSize]);

  const totalPages = Math.ceil(filteredCandidates.length / pageSize) || 1;

  const handleSort = (field: typeof sortBy) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortBy(field);
      setSortOrder("desc");
    }
    setPage(1);
  };

  // CSV Downloader
  const handleExportCSV = () => {
    try {
      const headers = [
        "Rank", "Candidate ID", "Name", "Headline", "Current Role", "Current Company",
        "Years Experience", "Final Score", "Technical Score", "Career Score",
        "Behaviour Score", "Risk Score", "Status", "Blocker Reason"
      ];
      
      const rows = filteredCandidates.map((c, idx) => {
        const rec = (c as any).recommendation || c.explanation?.recommendation || "Not Relevant";
        const blocker = "";
        return [
          idx + 1, c.candidate_id, c.name, c.headline, c.current_role, c.current_company,
          c.years_experience, c.final_score, c.sub_scores.technical.score, c.sub_scores.career.score,
          c.sub_scores.behaviour.score, c.sub_scores.risk.score, rec, blocker
        ];
      });

      const csvContent = [headers, ...rows]
        .map((r) => r.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(","))
        .join("\n");

      const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.setAttribute("href", url);
      link.setAttribute("download", `ranked_candidates_${Date.now()}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      addToast("Successfully exported candidate rankings CSV!", "success");
    } catch {
      addToast("Failed to export rankings CSV", "error");
    }
  };

  const getBadgeClass = (score: number) => {
    if (score >= 80.0) return "bg-green-950/40 text-green-400 border border-green-500/30";
    if (score >= 65.0) return "bg-blue-950/40 text-blue-400 border border-blue-500/30";
    if (score >= 50.0) return "bg-yellow-950/40 text-yellow-400 border border-yellow-500/30";
    return "bg-slate-900 text-slate-400 border border-slate-700";
  };

  const getRecommendationBadge = (scored: ScoredProfile) => {
    const rec = (scored as any).recommendation || scored.explanation?.recommendation || "";
    const recLower = rec.toLowerCase();

    if (recLower.includes("strong hire")) {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-green-950/50 text-green-400 border border-green-500/20">
          <CheckCircle className="w-3 h-3" /> Strong Hire
        </span>
      );
    }
    if (recLower.includes("interview")) {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-950/50 text-blue-400 border border-blue-500/20">
          <CheckCircle className="w-3 h-3" /> Interview
        </span>
      );
    }
    if (recLower.includes("potential")) {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-yellow-950/50 text-yellow-400 border border-yellow-500/20">
          <AlertTriangle className="w-3 h-3" /> Potential Hire
        </span>
      );
    }
    if (recLower.includes("hold")) {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-orange-950/50 text-orange-400 border border-orange-500/20">
          <AlertTriangle className="w-3 h-3" /> Hold
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-900 text-slate-300 border border-slate-700">
        <XOctagon className="w-3 h-3" /> Not Relevant
      </span>
    );
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold font-display text-white">Ranking Results</h1>
          <p className="text-muted-foreground text-sm">
            Top matches sorted by composite score, using custom weights and soft parameters.
          </p>
        </div>
        <button
          onClick={handleExportCSV}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-bold shadow-lg hover:shadow-indigo-500/20 transition-all active:scale-95"
        >
          <Download className="w-4 h-4" /> Export CSV
        </button>
      </div>

      {/* Toolbar / Filters */}
      <div className="p-4 rounded-xl glass border border-white/5 grid grid-cols-1 md:grid-cols-4 gap-4 items-center">
        {/* Search */}
        <div className="relative md:col-span-2">
          <Search className="w-4 h-4 text-muted-foreground absolute left-3.5 top-1/2 transform -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            placeholder="Search candidates by name, company, or skills..."
            className="w-full pl-10 pr-4 py-2 bg-black/30 border border-white/5 focus:border-indigo-500/40 rounded-lg text-sm focus:outline-none text-slate-200"
          />
        </div>

        {/* Filter Recommendation */}
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-muted-foreground" />
          <select
            value={recFilter}
            onChange={(e) => { setRecFilter(e.target.value); setPage(1); }}
            className="flex-1 p-2 bg-black/30 border border-white/5 focus:border-indigo-500/40 rounded-lg text-xs font-semibold focus:outline-none text-slate-300"
          >
            <option value="all">All Recommendations</option>
            <option value="strong">⭐ Strong Hire</option>
            <option value="interview">✅ Interview</option>
            <option value="potential">🟡 Potential Hire</option>
            <option value="hold">🟠 Hold</option>
            <option value="notrelevant">⚪ Not Relevant</option>
          </select>
        </div>

        {/* Min Experience */}
        <div>
          <input
            type="number"
            value={minExp}
            onChange={(e) => { setMinExp(e.target.value === "" ? "" : parseFloat(e.target.value)); setPage(1); }}
            placeholder="Min experience (years)"
            className="w-full p-2 bg-black/30 border border-white/5 focus:border-indigo-500/40 rounded-lg text-xs focus:outline-none text-center text-slate-300"
          />
        </div>
      </div>

      {/* Table Card */}
      <div className="overflow-x-auto rounded-xl glass border border-white/5 shadow-xl">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-white/10 bg-black/25 text-xs text-muted-foreground font-semibold uppercase tracking-wider">
              <th className="px-6 py-4">Rank</th>
              <th className="px-6 py-4 cursor-pointer hover:text-white" onClick={() => handleSort("final_score")}>
                Candidate <ArrowUpDown className="w-3 h-3 inline ml-1" />
              </th>
              <th className="px-6 py-4 cursor-pointer hover:text-white text-center" onClick={() => handleSort("final_score")}>
                Score <ArrowUpDown className="w-3 h-3 inline ml-1" />
              </th>
              <th className="px-6 py-4 cursor-pointer hover:text-white text-center" onClick={() => handleSort("technical")}>
                Tech <ArrowUpDown className="w-3 h-3 inline ml-1" />
              </th>
              <th className="px-6 py-4 cursor-pointer hover:text-white text-center" onClick={() => handleSort("career")}>
                Career <ArrowUpDown className="w-3 h-3 inline ml-1" />
              </th>
              <th className="px-6 py-4 cursor-pointer hover:text-white text-center" onClick={() => handleSort("behaviour")}>
                Behav <ArrowUpDown className="w-3 h-3 inline ml-1" />
              </th>
              <th className="px-6 py-4 cursor-pointer hover:text-white text-center" onClick={() => handleSort("risk")}>
                Risk <ArrowUpDown className="w-3 h-3 inline ml-1" />
              </th>
              <th className="px-6 py-4 text-center">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5 text-sm">
            {paginatedCandidates.length > 0 ? (
              paginatedCandidates.map((c, index) => {
                const globalRank = (page - 1) * pageSize + index + 1;
                return (
                  <tr
                    key={c.candidate_id}
                    onClick={() => onSelectCandidate(c.candidate_id)}
                    className="hover:bg-indigo-500/5 cursor-pointer transition-colors group"
                  >
                    <td className="px-6 py-4 text-muted-foreground font-bold">
                      #{globalRank}
                    </td>
                    <td className="px-6 py-4">
                      <div className="space-y-0.5">
                        <div className="font-bold text-white group-hover:text-indigo-400 transition-colors">
                          {c.name}
                        </div>
                        <div className="text-xs text-muted-foreground truncate max-w-xs md:max-w-md">
                          {c.headline || `${c.current_role} at ${c.current_company}`}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <span className={`px-2.5 py-1 rounded-lg font-bold text-xs ${getBadgeClass(c.final_score)}`}>
                        {c.final_score.toFixed(1)}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-center text-slate-300">
                      {c.sub_scores.technical.score.toFixed(0)}
                    </td>
                    <td className="px-6 py-4 text-center text-slate-300">
                      {c.sub_scores.career.score.toFixed(0)}
                    </td>
                    <td className="px-6 py-4 text-center text-slate-300">
                      {c.sub_scores.behaviour.score.toFixed(0)}
                    </td>
                    <td className="px-6 py-4 text-center text-red-400/80">
                      {c.sub_scores.risk.score.toFixed(0)}
                    </td>
                    <td className="px-6 py-4 text-center">
                      {getRecommendationBadge(c)}
                    </td>
                  </tr>
                );
              })
            ) : (
              <tr>
                <td colSpan={8} className="px-6 py-12 text-center text-muted-foreground">
                  No candidates match your search query or filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <div className="flex justify-between items-center text-xs text-muted-foreground pt-4">
        <div className="flex items-center gap-2">
          <span>Show:</span>
          <select
            value={pageSize}
            onChange={(e) => { setPageSize(parseInt(e.target.value)); setPage(1); }}
            className="p-1 bg-black/40 border border-white/10 rounded focus:outline-none"
          >
            <option value={10}>10 rows</option>
            <option value={25}>25 rows</option>
            <option value={50}>50 rows</option>
          </select>
          <span>of {filteredCandidates.length} applicants</span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setPage(Math.max(1, page - 1))}
            disabled={page === 1}
            className="p-1.5 rounded bg-white/5 border border-white/10 hover:bg-white/10 disabled:opacity-30 disabled:pointer-events-none transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <span>Page {page} of {totalPages}</span>
          <button
            onClick={() => setPage(Math.min(totalPages, page + 1))}
            disabled={page === totalPages}
            className="p-1.5 rounded bg-white/5 border border-white/10 hover:bg-white/10 disabled:opacity-30 disabled:pointer-events-none transition-colors"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
