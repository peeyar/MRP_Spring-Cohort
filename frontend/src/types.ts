/** Matches backend response models exactly. */

export interface ExcludedRow {
  row_number: number;
  reason: string;
}

export interface ParsingSummary {
  total_rows: number;
  valid_connections: number;
  excluded_rows: number;
  exclusion_reasons: ExcludedRow[];
  unique_companies: number;
}

export interface CompanyResult {
  company_name: string;
  contact_name: string;
  contact_title: string;
  contact_url: string;
  contact_email: string | null;
  path_label: "Warm Path" | "Stretch Path" | "Explore";
  score: number;
  contact_count: number;
}

export interface AnalyzeResponse {
  parsing_summary: ParsingSummary;
  results: CompanyResult[];
}

export interface Preferences {
  target_role: string;
  location: string;
  company_type: "startup" | "mid-size" | "enterprise" | "any";
}

export interface LLMDetails {
  explanation: string;
  next_action: string;
  outreach_draft: string;
}

export interface AuthUser {
  id: string;
  email: string | undefined;
}
