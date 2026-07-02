import React, { useState, useEffect } from "react";
import { UploadCloud, Sparkles, FileText, CheckCircle, Database, AlertCircle, Play } from "lucide-react";
import { runRanking, uploadJDFile, uploadCandidatesFile, getCurrentJD } from "../api";
import { RankResponse } from "../types";

interface DashboardProps {
  results: RankResponse | null;
  onRankingComplete: (data: RankResponse) => void;
  setLoading: (loading: boolean) => void;
  loading: boolean;
  addToast: (msg: string, type: "success" | "error" | "info") => void;
}

export default function Dashboard({
  results,
  onRankingComplete,
  setLoading,
  loading,
  addToast
}: DashboardProps) {
  const [jdText, setJdText] = useState("");
  const [useSample, setUseSample] = useState(true);
  const [limit, setLimit] = useState(500);
  const [jdFile, setJdFile] = useState<File | null>(null);
  const [candidatesFile, setCandidatesFile] = useState<File | null>(null);
  
  // Progress telemetry
  const [progressStep, setProgressStep] = useState(0);
  const [progressMsg, setProgressMsg] = useState("");

  useEffect(() => {
    // Fetch initial JD for default text (from data/job_description.md exactly)
    getCurrentJD()
      .then((data) => {
        setJdText(data.markdown);
      })
      .catch(() => {
        addToast("Failed to fetch initial job description requirements", "error");
      });
  }, [addToast]);

  const handleJdUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const file = e.target.files[0];
    setJdFile(file);
    
    // Read local file contents for the editor view
    const reader = new FileReader();
    reader.onload = (event) => {
      if (event.target?.result) {
        setJdText(event.target.result as string);
      }
    };
    reader.readAsText(file);

    try {
      await uploadJDFile(file);
      addToast("Job Description markdown saved to backend", "success");
    } catch (err: any) {
      addToast(err.message || "Failed to upload JD", "error");
    }
  };

  const handleCandidatesUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const file = e.target.files[0];
    setCandidatesFile(file);

    try {
      addToast("Uploading database file... Please wait.", "info");
      await uploadCandidatesFile(file);
      setUseSample(false); // Default to full dataset since they just uploaded one
      addToast("Candidate database file saved to backend successfully", "success");
    } catch (err: any) {
      addToast(err.message || "Failed to upload candidates", "error");
    }
  };

  const handleRunRank = async () => {
    setLoading(true);
    setProgressStep(1);
    setProgressMsg("Parsing job description markdown requirements...");

    setTimeout(async () => {
      setProgressStep(2);
      setProgressMsg("Scanning and streaming candidate database profiles...");
      
      setTimeout(async () => {
        setProgressStep(3);
        setProgressMsg("Extracting semantic signal features & builder actions...");
        
        setTimeout(async () => {
          setProgressStep(4);
          setProgressMsg("Running composite scoring and filtering models...");
          
          try {
            const rankedResults = await runRanking(undefined, useSample, limit);
            setProgressStep(5);
            setProgressMsg("Aggregating rankings and compiling explanations...");
            
            setTimeout(() => {
              onRankingComplete(rankedResults);
              addToast(`Successfully ranked ${rankedResults.candidates.length} candidates in ${rankedResults.elapsed_time}s!`, "success");
              setLoading(false);
              setProgressStep(0);
              setProgressMsg("");
            }, 500);
          } catch (err: any) {
            addToast(err.message || "Error running ranking engine", "error");
            setLoading(false);
            setProgressStep(0);
            setProgressMsg("");
          }
        }, 600);
      }, 700);
    }, 600);
  };

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Hero Header */}
      <div className="relative p-8 overflow-hidden rounded-2xl glass border border-white/10 flex flex-col md:flex-row justify-between items-center gap-6">
        <div className="absolute top-0 right-0 w-80 h-80 bg-indigo-500/10 rounded-full blur-3xl -z-10"></div>
        <div className="absolute bottom-0 left-0 w-80 h-80 bg-purple-500/10 rounded-full blur-3xl -z-10"></div>
        
        <div className="space-y-3 text-center md:text-left max-w-2xl">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            <Sparkles className="w-3.5 h-3.5" /> Redrob Challenge Edition
          </div>
          <h1 className="text-4xl font-extrabold tracking-tight font-display text-transparent bg-clip-text bg-gradient-to-r from-white via-indigo-200 to-purple-400">
            Intelligent Candidate Discovery & Ranking
          </h1>
          <p className="text-muted-foreground text-sm md:text-base">
            Upload hiring requirements and applicant datasets. Our semantic engine parses technical backgrounds, calculates career progression indices, evaluates platform responsiveness, and lists recruiters' blockers.
          </p>
        </div>
        
        <button
          onClick={handleRunRank}
          disabled={loading}
          className="flex items-center justify-center gap-2.5 px-8 py-4 rounded-xl bg-gradient-to-r from-indigo-600 via-indigo-500 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-bold shadow-lg hover:shadow-indigo-500/25 transition-all duration-300 disabled:opacity-50 disabled:pointer-events-none group transform active:scale-95"
        >
          <Play className="w-5 h-5 fill-white group-hover:scale-110 transition-transform" />
          Rank Candidates
        </button>
      </div>

      {/* Stats Cards (Priority 4 - Recruiter Friendly UI / No Developer Filenames) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-6 rounded-xl glass border border-white/5 space-y-4">
          <div className="flex justify-between items-center">
            <span className="text-muted-foreground text-xs uppercase tracking-wider font-semibold">Job Role & AI Status</span>
            <FileText className="w-5 h-5 text-indigo-400" />
          </div>
          <div className="space-y-1">
            <div className="text-lg font-bold font-display text-white truncate">
              {results ? results.jd.title : (jdFile ? jdFile.name.replace(/\.[^/.]+$/, "") : "Awaiting Job Description")}
            </div>
            <div className="text-xs text-green-400 flex items-center gap-1">
              <CheckCircle className="w-3.5 h-3.5" /> AI Matching: {results ? "Calibrated & Active" : "Pending Calibration"}
            </div>
          </div>
        </div>

        <div className="p-6 rounded-xl glass border border-white/5 space-y-4">
          <div className="flex justify-between items-center">
            <span className="text-muted-foreground text-xs uppercase tracking-wider font-semibold">Candidate Pool Indexed</span>
            <Database className="w-5 h-5 text-purple-400" />
          </div>
          <div className="space-y-1">
            <div className="text-lg font-bold font-display truncate text-white">
              {useSample ? "Pre-loaded Talent Pool" : "Uploaded Candidate Registry"}
            </div>
            <div className="text-xs text-indigo-300">
              Total Profiles Indexed: {results ? `${results.candidates.length} candidates` : "0 candidates"}
            </div>
          </div>
        </div>

        <div className="p-6 rounded-xl glass border border-white/5 space-y-4">
          <div className="flex justify-between items-center">
            <span className="text-muted-foreground text-xs uppercase tracking-wider font-semibold">Semantic Ranking Engine</span>
            <Sparkles className="w-5 h-5 text-pink-400" />
          </div>
          <div className="space-y-2">
            <div className="text-sm font-semibold flex items-center justify-between text-white">
              <span>Builder Verb Scans:</span>
              <span className="text-indigo-400">{results ? "Enabled" : "Awaiting activation"}</span>
            </div>
            <div className="text-xs text-muted-foreground">
              Weights: Tech 50% | Career 25% | Behav 10% | Risk 15%
            </div>
          </div>
        </div>
      </div>

      {/* Progress Telemetry */}
      {loading && progressStep > 0 && (
        <div className="p-6 rounded-xl glass-card border border-indigo-500/20 space-y-3">
          <div className="flex justify-between items-center text-sm font-semibold">
            <span className="text-indigo-300 flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-indigo-500 animate-ping"></span>
              {progressMsg}
            </span>
            <span>{Math.round((progressStep / 5) * 100)}%</span>
          </div>
          <div className="w-full h-2 bg-white/5 rounded-full overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 rounded-full transition-all duration-300"
              style={{ width: `${(progressStep / 5) * 100}%` }}
            ></div>
          </div>
        </div>
      )}

      {/* Data Upload Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* JD Section */}
        <div className="p-6 rounded-2xl glass-card space-y-4 flex flex-col">
          <div className="flex justify-between items-center border-b border-white/10 pb-3">
            <h2 className="text-xl font-bold font-display text-white">Target Job Description</h2>
            <label className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-xs font-semibold cursor-pointer border border-white/10 transition-colors">
              <UploadCloud className="w-3.5 h-3.5 text-indigo-400" />
              Upload Markdown
              <input type="file" accept=".md,.txt" onChange={handleJdUpload} className="hidden" />
            </label>
          </div>
          <textarea
            value={jdText}
            onChange={(e) => setJdText(e.target.value)}
            placeholder="# Write or paste your Markdown Job Description here..."
            className="flex-1 w-full min-h-[350px] p-4 bg-black/35 rounded-xl border border-white/5 focus:border-indigo-500/40 text-sm font-mono focus:outline-none focus:ring-1 focus:ring-indigo-500/40 resize-y text-slate-300"
          ></textarea>
        </div>

        {/* Database Upload Section */}
        <div className="p-6 rounded-2xl glass-card space-y-6 flex flex-col justify-between">
          <div className="space-y-4">
            <div className="border-b border-white/10 pb-3">
              <h2 className="text-xl font-bold font-display text-white">Candidate Database Config</h2>
            </div>
            
            {/* Upload Area */}
            <div className="border-2 border-dashed border-white/10 hover:border-indigo-500/35 rounded-xl p-8 text-center bg-black/15 transition-all duration-300 relative group">
              <input 
                type="file" 
                accept=".jsonl,.json" 
                onChange={handleCandidatesUpload} 
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer" 
              />
              <div className="space-y-3 pointer-events-none">
                <div className="w-12 h-12 rounded-full bg-indigo-500/10 text-indigo-400 flex items-center justify-center mx-auto group-hover:scale-110 transition-transform">
                  <UploadCloud className="w-6 h-6" />
                </div>
                <div className="space-y-1">
                  <p className="text-sm font-semibold text-white">Upload Candidates JSONL file</p>
                  <p className="text-xs text-muted-foreground">Drag and drop or click to browse (supports large databases up to 500MB)</p>
                </div>
              </div>
            </div>

            {/* Toggle Configuration */}
            <div className="space-y-4 pt-4">
              <div className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/5">
                <div className="space-y-0.5">
                  <div className="text-sm font-bold text-white">Use Sample Hackathon Dataset</div>
                  <div className="text-xs text-muted-foreground">Runs the scoring engine over the default sample database. Useful for rapid trials.</div>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={useSample}
                    onChange={(e) => setUseSample(e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-600"></div>
                </label>
              </div>

              {!useSample && (
                <div className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/5 animate-fade-in">
                  <div className="space-y-0.5">
                    <div className="text-sm font-bold text-white">Candidate Processing Limit</div>
                    <div className="text-xs text-muted-foreground">Sets maximum lines processed to optimize performance in web environments.</div>
                  </div>
                  <input
                    type="number"
                    value={limit}
                    onChange={(e) => setLimit(parseInt(e.target.value) || 100)}
                    min={50}
                    max={5000}
                    className="w-24 p-2 bg-black/45 rounded-lg border border-white/10 text-center font-semibold focus:outline-none focus:border-indigo-500/50"
                  />
                </div>
              )}
            </div>
          </div>

          <div className="p-4 rounded-xl bg-indigo-500/5 border border-indigo-500/10 flex gap-3 text-xs text-indigo-300 mt-6">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <p>
              <strong>Recruiter Tip:</strong> Standard keywords can be easily fake-listed. The system utilizes deterministic signal extraction, evaluating the candidate's career descriptions for action verbs (e.g. <em>deployed</em>, <em>scaled</em>, <em>architected</em>) near system concepts to verify real building experience.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
