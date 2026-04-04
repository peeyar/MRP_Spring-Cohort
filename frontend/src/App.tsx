import { useEffect, useState } from "react";
import { analyzeConnections } from "./api";
import {
  ErrorAlert,
  LoadingIndicator,
  ParsingSummaryBar,
  PreferencesForm,
  ResultsList,
} from "./components";
import type { AnalyzeResponse, Preferences } from "./types";

export default function App() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<AnalyzeResponse | null>(null);
  const [lastPrefs, setLastPrefs] = useState<Preferences | null>(null);

  useEffect(() => {
    const backendUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
    fetch(`${backendUrl}/health`).catch(() => {
      // Ignore warm-up failures; real requests will still handle errors normally
    });
  }, []);

  const handleSubmit = async (prefs: Preferences, file: File) => {
    setLoading(true);
    setError(null);
    setData(null);
    setLastPrefs(prefs);

    try {
      const result = await analyzeConnections(file, prefs);
      setData(result);
    } catch (err: unknown) {
      if (
        err &&
        typeof err === "object" &&
        "response" in err &&
        (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
      ) {
        setError(
          (err as { response: { data: { detail: string } } }).response.data.detail
        );
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("An unexpected error occurred. Please check that the backend is running and try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: "100vh",
      background: "linear-gradient(135deg, #f0f4ff 0%, #faf5ff 50%, #fff1f2 100%)",
      fontFamily: "'Inter', system-ui, -apple-system, sans-serif",
    }}>
      {/* Header */}
      <header style={{
        background: "rgba(255,255,255,0.8)",
        backdropFilter: "blur(12px)",
        borderBottom: "1px solid rgba(226,232,240,0.6)",
        padding: "16px 0",
        position: "sticky",
        top: 0,
        zIndex: 10,
      }}>
        <div style={{ maxWidth: 860, margin: "0 auto", padding: "0 24px", display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontSize: 20, fontWeight: 700, color: "#1e293b", letterSpacing: "-0.02em" }}>WarmPath</span>
          <span style={{ fontSize: 11, fontWeight: 600, color: "#8b5cf6", background: "#ede9fe", padding: "2px 8px", borderRadius: 6, marginLeft: 4 }}>Beta</span>
        </div>
      </header>

      <main style={{ maxWidth: 860, margin: "0 auto", padding: "32px 24px 64px" }}>
        {/* Hero */}
        <div style={{ marginBottom: 32, textAlign: "center" }}>
          <h1 style={{
            fontSize: 32, fontWeight: 800, color: "#0f172a", margin: "0 0 8px",
            letterSpacing: "-0.03em", lineHeight: 1.2,
          }}>
            Turn connections into referrals
          </h1>
          <p style={{ color: "#64748b", fontSize: 16, margin: 0, maxWidth: 520, marginLeft: "auto", marginRight: "auto", lineHeight: 1.5 }}>
            Upload your LinkedIn CSV, enter your target role, and discover your best referral opportunities — ranked, labeled, and ready for outreach.
          </p>
        </div>

        {/* Upload + Preferences Card */}
        <div style={{
          background: "#fff",
          borderRadius: 16,
          padding: "28px 32px",
          boxShadow: "0 1px 3px rgba(0,0,0,0.04), 0 4px 12px rgba(0,0,0,0.03)",
          border: "1px solid rgba(226,232,240,0.7)",
          marginBottom: 28,
        }}>
          <PreferencesForm onSubmit={handleSubmit} loading={loading} />
        </div>

        {error && <ErrorAlert message={error} onDismiss={() => setError(null)} />}

        {loading && <LoadingIndicator />}

        {data && !loading && (
          <>
            <ParsingSummaryBar summary={data.parsing_summary} />
            <ResultsList results={data.results} preferences={lastPrefs} />
          </>
        )}
      </main>
    </div>
  );
}
