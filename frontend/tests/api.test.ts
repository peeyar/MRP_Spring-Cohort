import { describe, it, expect, vi, beforeEach } from "vitest";
import axios from "axios";
import { analyzeConnections, fetchDetails } from "../src/api";
import type { AnalyzeResponse, CompanyResult, LLMDetails, Preferences } from "../src/types";

vi.mock("axios", () => ({
  default: {
    post: vi.fn(),
  },
}));

const mockedPost = vi.mocked(axios.post);

const mockPreferences: Preferences = {
  target_role: "software engineer",
  location: "San Francisco",
  company_type: "startup",
};

const mockAnalyzeResponse: AnalyzeResponse = {
  parsing_summary: {
    total_rows: 2,
    valid_connections: 2,
    excluded_rows: 0,
    exclusion_reasons: [],
    unique_companies: 2,
  },
  results: [
    {
      company_name: "Acme Corp",
      contact_name: "Alice Smith",
      contact_title: "Software Engineer",
      contact_url: "https://linkedin.com/in/alice",
      contact_email: "alice@acme.com",
      path_label: "Warm Path",
      score: 85,
      contact_count: 1,
    },
  ],
};

const mockCompanyResult: CompanyResult = mockAnalyzeResponse.results[0];

const mockLLMDetails: LLMDetails = {
  explanation: "Great technical match.",
  next_action: "Send a LinkedIn message.",
  outreach_draft: "Hi Alice, I would love to connect.",
};

beforeEach(() => {
  vi.clearAllMocks();
});

// ── analyzeConnections ────────────────────────────────────────────────────────

describe("analyzeConnections", () => {
  it("posts to /api/analyze with FormData and returns response data", async () => {
    mockedPost.mockResolvedValueOnce({ data: mockAnalyzeResponse });

    const file = new File(["csv content"], "connections.csv", { type: "text/csv" });
    const result = await analyzeConnections(file, mockPreferences);

    expect(mockedPost).toHaveBeenCalledOnce();
    const [url, formData] = mockedPost.mock.calls[0];
    expect(url).toBe("http://localhost:8000/api/analyze");
    expect(formData).toBeInstanceOf(FormData);
    expect(result).toEqual(mockAnalyzeResponse);
  });

  it("includes file and preferences in FormData", async () => {
    mockedPost.mockResolvedValueOnce({ data: mockAnalyzeResponse });

    const file = new File(["csv"], "test.csv");
    await analyzeConnections(file, mockPreferences);

    const formData = mockedPost.mock.calls[0][1] as FormData;
    expect(formData.get("file")).toBe(file);
    expect(formData.get("preferences")).toBe(JSON.stringify(mockPreferences));
  });

  it("propagates axios errors", async () => {
    mockedPost.mockRejectedValueOnce(new Error("Network Error"));

    const file = new File(["csv"], "test.csv");
    await expect(analyzeConnections(file, mockPreferences)).rejects.toThrow("Network Error");
  });
});

// ── fetchDetails ──────────────────────────────────────────────────────────────

describe("fetchDetails", () => {
  it("posts to /api/details with company_result and preferences", async () => {
    mockedPost.mockResolvedValueOnce({ data: mockLLMDetails });

    const result = await fetchDetails(mockCompanyResult, mockPreferences);

    expect(mockedPost).toHaveBeenCalledOnce();
    const [url, body] = mockedPost.mock.calls[0];
    expect(url).toBe("http://localhost:8000/api/details");
    expect(body).toEqual({
      company_result: mockCompanyResult,
      preferences: mockPreferences,
    });
    expect(result).toEqual(mockLLMDetails);
  });

  it("returns explanation, next_action, and outreach_draft", async () => {
    mockedPost.mockResolvedValueOnce({ data: mockLLMDetails });

    const result = await fetchDetails(mockCompanyResult, mockPreferences);

    expect(result.explanation).toBe("Great technical match.");
    expect(result.next_action).toBe("Send a LinkedIn message.");
    expect(result.outreach_draft).toBe("Hi Alice, I would love to connect.");
  });

  it("propagates axios errors", async () => {
    mockedPost.mockRejectedValueOnce(new Error("Timeout"));

    await expect(fetchDetails(mockCompanyResult, mockPreferences)).rejects.toThrow("Timeout");
  });
});
