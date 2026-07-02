import { useState, useEffect } from "react";
import { LayoutDashboard, BarChart3, Info, Sun, Moon, AlertTriangle, CheckCircle, Flame, FileSpreadsheet, Sparkles } from "lucide-react";
import { checkBackendHealth, getCandidateDetails, runRanking } from "./api";
import { RankResponse, ScoredProfile } from "./types";

import Dashboard from "./pages/Dashboard";
import RankingResults from "./pages/RankingResults";
import CandidateDetail from "./pages/CandidateDetail";
import Analytics from "./pages/Analytics";
import AboutSystem from "./pages/AboutSystem";

interface Toast {
  id: number;
  message: string;
  type: "success" | "error" | "info";
}

export default function App() {
  const [currentTab, setCurrentTab] = useState<"dashboard" | "results" | "analytics" | "about">("dashboard");
  const [results, setResults] = useState<RankResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedCandidateId, setSelectedCandidateId] = useState<string | null>(null);
  const [selectedCandidate, setSelectedCandidate] = useState<ScoredProfile | null>(null);
  
  // Theme state
  const [theme, setTheme] = useState<"dark" | "light">("dark");

  // Telemetry Health check
  const [backendAlive, setBackendAlive] = useState(true);
  
  // Toast notifications state
  const [toasts, setToasts] = useState<Toast[]>([]);

  // Startup mount effects: checks health and triggers initial ranking run
  useEffect(() => {
    checkBackendHealth().then((alive) => {
      setBackendAlive(alive);
      if (alive) {
        setLoading(true);
        runRanking(undefined, true, 500)
          .then((data) => {
            setResults(data);
            setLoading(false);
          })
          .catch(() => {
            setLoading(false);
          });
      } else {
        addToast("Backend server is offline! Please start server.py first.", "error");
      }
    });
  }, []);

  // Sync theme to document body
  useEffect(() => {
    const root = window.document.documentElement;
    if (theme === "dark") {
      root.classList.add("dark");
    } else {
      root.classList.remove("dark");
    }
  }, [theme]);

  // Load detailed profile for selected candidate from backend cache
  useEffect(() => {
    if (selectedCandidateId) {
      getCandidateDetails(selectedCandidateId)
        .then((profile) => {
          setSelectedCandidate(profile);
        })
        .catch((err) => {
          addToast(err.message || "Failed to fetch candidate details", "error");
          setSelectedCandidateId(null);
        });
    } else {
      setSelectedCandidate(null);
    }
  }, [selectedCandidateId]);

  const addToast = (message: string, type: Toast["type"]) => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  };

  const removeToast = (id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  const handleRankingComplete = (data: RankResponse) => {
    setResults(data);
    setCurrentTab("results");
    setSelectedCandidateId(null);
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-800 dark:text-slate-100 transition-colors duration-300">
      
      {/* Background Ambient Glows */}
      <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-indigo-500/10 rounded-full blur-[120px] pointer-events-none -z-10 dark:block hidden"></div>
      <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-purple-500/10 rounded-full blur-[120px] pointer-events-none -z-10 dark:block hidden"></div>

      {/* Global Toast Container */}
      <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-3 max-w-sm w-full">
        {toasts.map((t) => (
          <div
            key={t.id}
            onClick={() => removeToast(t.id)}
            className={`p-4 rounded-xl shadow-2xl border flex items-center justify-between gap-3 cursor-pointer animate-fade-in transition-all hover:scale-[1.02] ${
              t.type === "success"
                ? "bg-green-500/10 dark:bg-green-950/80 border-green-500/30 text-green-700 dark:text-green-300"
                : t.type === "error"
                ? "bg-red-500/10 dark:bg-red-950/80 border-red-500/30 text-red-700 dark:text-red-300"
                : "bg-indigo-500/10 dark:bg-indigo-950/80 border-indigo-500/30 text-indigo-700 dark:text-indigo-300"
            }`}
          >
            <div className="text-sm font-semibold">{t.message}</div>
            <button className="text-xs font-bold opacity-60 hover:opacity-100">&times;</button>
          </div>
        ))}
      </div>

      {/* Health Check Alert Header */}
      {!backendAlive && (
        <div className="bg-red-600 dark:bg-red-950/80 text-white border-b border-red-500/30 p-2.5 text-center text-xs font-bold flex items-center justify-center gap-1.5 animate-pulse">
          <AlertTriangle className="w-4 h-4" /> 
          Backend Connection Failed: The FastAPI server at localhost:8000 is offline. Please run the server (python server.py) to parse candidates.
        </div>
      )}

      {/* Main Navbar */}
      <header className="sticky top-0 z-40 w-full glass border-b border-slate-200 dark:border-white/5 transition-all">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          {/* Logo */}
          <div className="flex items-center gap-2.5 cursor-pointer" onClick={() => { setCurrentTab("dashboard"); setSelectedCandidateId(null); }}>
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-purple-600 text-white flex items-center justify-center shadow-lg shadow-indigo-500/20 group hover:scale-105 transition-all duration-300">
              <Flame className="w-5 h-5 fill-white group-hover:rotate-12 transition-transform" />
            </div>
            <div>
              <span className="font-extrabold text-lg tracking-tight font-display text-white">REDROB</span>
              <span className="text-xs font-bold text-indigo-400 block -mt-1 tracking-wider uppercase font-mono">Recruiter AI</span>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center gap-1.5 p-1 rounded-xl bg-white/5 border border-white/5">
            <button
              onClick={() => { setCurrentTab("dashboard"); setSelectedCandidateId(null); }}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-bold transition-all ${
                currentTab === "dashboard"
                  ? "bg-indigo-600 text-white shadow-md shadow-indigo-500/10"
                  : "text-muted-foreground hover:text-white hover:bg-white/5"
              }`}
            >
              <LayoutDashboard className="w-3.5 h-3.5" /> Dashboard
            </button>
            <button
              onClick={() => { setCurrentTab("results"); setSelectedCandidateId(null); }}
              disabled={!results}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-bold transition-all ${
                !results ? "opacity-40 cursor-not-allowed" : ""
              } ${
                currentTab === "results"
                  ? "bg-indigo-600 text-white shadow-md shadow-indigo-500/10"
                  : "text-muted-foreground hover:text-white hover:bg-white/5"
              }`}
            >
              <FileSpreadsheet className="w-3.5 h-3.5" /> Rankings
            </button>
            <button
              onClick={() => { setCurrentTab("analytics"); setSelectedCandidateId(null); }}
              disabled={!results}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-bold transition-all ${
                !results ? "opacity-40 cursor-not-allowed" : ""
              } ${
                currentTab === "analytics"
                  ? "bg-indigo-600 text-white shadow-md shadow-indigo-500/10"
                  : "text-muted-foreground hover:text-white hover:bg-white/5"
              }`}
            >
              <BarChart3 className="w-3.5 h-3.5" /> Analytics
            </button>
            <button
              onClick={() => { setCurrentTab("about"); setSelectedCandidateId(null); }}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-bold transition-all ${
                currentTab === "about"
                  ? "bg-indigo-600 text-white shadow-md shadow-indigo-500/10"
                  : "text-muted-foreground hover:text-white hover:bg-white/5"
              }`}
            >
              <Info className="w-3.5 h-3.5" /> Pipeline specs
            </button>
          </nav>

          {/* Right Action buttons */}
          <div className="flex items-center gap-3">
            {/* Theme Toggle */}
            <button
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
              className="p-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-muted-foreground hover:text-white border border-white/5 hover:border-white/10 active:scale-95 transition-all"
            >
              {theme === "dark" ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </button>
            
            {results && (
              <div className="hidden lg:flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-green-500/10 text-green-400 border border-green-500/20 text-xs font-bold">
                <CheckCircle className="w-3.5 h-3.5" /> Scored {results.candidates.length} Profiles
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        
        {/* If candidate details are requested */}
        {selectedCandidateId && selectedCandidate ? (
          <CandidateDetail
            candidate={selectedCandidate}
            onBack={() => setSelectedCandidateId(null)}
          />
        ) : selectedCandidateId && !selectedCandidate ? (
          /* Loading skeletons for candidate details page */
          <div className="space-y-6 animate-pulse">
            <div className="h-8 w-32 bg-white/5 rounded-lg"></div>
            <div className="h-32 bg-white/5 rounded-2xl"></div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="h-80 bg-white/5 rounded-2xl md:col-span-1"></div>
              <div className="h-80 bg-white/5 rounded-2xl md:col-span-2"></div>
            </div>
          </div>
        ) : (
          /* Normal Tab routing */
          <>
            {currentTab === "dashboard" && (
              <Dashboard
                results={results}
                onRankingComplete={handleRankingComplete}
                setLoading={setLoading}
                loading={loading}
                addToast={addToast}
              />
            )}
            {currentTab === "results" && results && (
              <RankingResults
                results={results}
                onSelectCandidate={setSelectedCandidateId}
                addToast={addToast}
              />
            )}
            {currentTab === "analytics" && results && (
              <Analytics results={results} />
            )}
            {currentTab === "about" && (
              <AboutSystem />
            )}
          </>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 dark:border-white/5 py-8 mt-12 text-center text-xs text-muted-foreground font-semibold">
        <div className="flex items-center justify-center gap-1">
          <Sparkles className="w-3.5 h-3.5 text-indigo-400" /> Powered by Redrob AI Core Engine &middot; Hackathon Recruiter UI Edition
        </div>
      </footer>

    </div>
  );
}
