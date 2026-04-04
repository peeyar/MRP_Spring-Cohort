import axios from "axios";
import type { AnalyzeResponse, Preferences, CompanyResult, LLMDetails } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export async function analyzeConnections(
  file: File,
  preferences: Preferences
): Promise<AnalyzeResponse> {
  const form = new FormData();
  form.append("file", file);
  form.append("preferences", JSON.stringify(preferences));

  const res = await axios.post<AnalyzeResponse>(
    `${API_BASE}/api/analyze`,
    form
  );
  return res.data;
}

export async function fetchDetails(
  companyResult: CompanyResult,
  preferences: Preferences
): Promise<LLMDetails> {
  const res = await axios.post<LLMDetails>(
    `${API_BASE}/api/details`,
    { company_result: companyResult, preferences }
  );
  return res.data;
}