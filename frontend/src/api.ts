
import { RankResponse, ScoredProfile, JobRequirements } from "./types";

const API_BASE =
  (import.meta as any).env?.VITE_API_URL || "http://localhost:8000";
export async function checkBackendHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/api/health`);
    if (!res.ok) return false;
    const data = await res.json();
    return data.status === "ok";
  } catch {
    return false;
  }
}

export async function getCurrentJD(): Promise<{ markdown: string; requirements: JobRequirements }> {
  const res = await fetch(`${API_BASE}/api/jd`);
  if (!res.ok) {
    throw new Error("Failed to fetch current Job Description");
  }
  return res.json();
}

export async function uploadJDFile(file: File): Promise<{ status: string; message: string }> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/api/upload-jd`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to upload Job Description file");
  }
  return res.json();
}

export async function uploadCandidatesFile(file: File): Promise<{ status: string; message: string }> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/api/upload-candidates`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to upload candidates database");
  }
  return res.json();
}

export async function runRanking(
  jdText?: string,
  useSample: boolean = true,
  candidateLimit: number = 500
): Promise<RankResponse> {
  const res = await fetch(`${API_BASE}/api/rank`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      jd_text: jdText || null,
      use_sample: useSample,
      candidate_limit: candidateLimit,
    }),
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to execute ranking engine");
  }
  return res.json();
}

export async function getCandidateDetails(candidateId: string): Promise<ScoredProfile> {
  const res = await fetch(`${API_BASE}/api/candidates/${candidateId}`);
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || `Failed to fetch details for candidate ${candidateId}`);
  }
  return res.json();
}
