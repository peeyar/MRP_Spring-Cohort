import { useState, useRef } from "react";
import type {
  CompanyResult,
  LLMDetails,
  ParsingSummary as ParsingSummaryType,
  Preferences,
} from "./types";
import { fetchDetails } from "./api";

/* ── Upload Area ── */

export function UploadArea({
  onFileSelect,
}: {
  onFileSelect: (file: File) => void;
}) {
  const [fileName, setFileName] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);

  const handleFile = (f: File) => {
    setFileName(f.name);
    onFileSelect(f);
  };

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragOver(false);
        const f = e.dataTransfer.files?.[0];
        if (f) handleFile(f);
      }}
      style={{
        border: `2px dashed ${dragOver ? "#818cf8" : "#cbd5e1"}`,
        borderRadius: 12,
        padding: "24px 20px",
        textAlign: "center",
        marginBottom: 20,
        background: dragOver ? "#eef2ff" : "#f8fafc",
        transition: "all 0.2s ease",
        cursor: "pointer",
        position: "relative",
      }}
    >
      <input
        id="csv-upload"
        type="file"
        accept=".csv"
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) handleFile(f);
        }}
        style={{ position: "absolute", inset: 0, opacity: 0, cursor: "pointer" }}
      />
      <div style={{ fontSize: 28, marginBottom: 6 }}>📄</div>
      {fileName ? (
        <p style={{ margin: 0, fontSize: 14, color: "#16a34a", fontWeight: 600 }}>
          ✓ {fileName}
        </p>
      ) : (
        <>
          <p style={{ margin: "0 0 2px", fontSize: 14, fontWeight: 600, color: "#334155" }}>
            Drop your LinkedIn CSV here or click to browse
          </p>
          <p style={{ margin: 0, fontSize: 12, color: "#94a3b8" }}>
            Export from LinkedIn → Settings → Data Privacy → Get a copy of your data
          </p>
        </>
      )}
    </div>
  );
}


/* ── Preferences Form ── */

export function PreferencesForm({
  onSubmit,
  loading,
}: {
  onSubmit: (prefs: Preferences, file: File) => void;
  loading: boolean;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [targetRole, setTargetRole] = useState("");
  const [location, setLocation] = useState("");
  const [companyType, setCompanyType] = useState<Preferences["company_type"]>("any");

  const canSubmit = !!file && targetRole.trim().length > 0 && !loading;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !targetRole.trim()) return;
    onSubmit(
      { target_role: targetRole.trim(), location: location.trim(), company_type: companyType },
      file
    );
  };

  const inputStyle: React.CSSProperties = {
    padding: "10px 14px",
    borderRadius: 10,
    border: "1px solid #e2e8f0",
    fontSize: 14,
    outline: "none",
    transition: "border-color 0.2s, box-shadow 0.2s",
    width: "100%",
    boxSizing: "border-box",
    background: "#fff",
  };

  const labelStyle: React.CSSProperties = {
    fontSize: 13,
    fontWeight: 600,
    color: "#475569",
    marginBottom: 6,
    display: "block",
  };

  return (
    <form onSubmit={handleSubmit}>
      <UploadArea onFileSelect={setFile} />

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16, marginBottom: 20 }}>
        <div>
          <label htmlFor="target-role" style={labelStyle}>Target Role *</label>
          <input
            id="target-role"
            type="text"
            placeholder="e.g. software engineer"
            value={targetRole}
            onChange={(e) => setTargetRole(e.target.value)}
            style={inputStyle}
            onFocus={(e) => { e.currentTarget.style.borderColor = "#818cf8"; e.currentTarget.style.boxShadow = "0 0 0 3px rgba(129,140,248,0.15)"; }}
            onBlur={(e) => { e.currentTarget.style.borderColor = "#e2e8f0"; e.currentTarget.style.boxShadow = "none"; }}
          />
        </div>
        <div>
          <label htmlFor="location" style={labelStyle}>Location</label>
          <input
            id="location"
            type="text"
            placeholder="e.g. Seattle"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            style={inputStyle}
            onFocus={(e) => { e.currentTarget.style.borderColor = "#818cf8"; e.currentTarget.style.boxShadow = "0 0 0 3px rgba(129,140,248,0.15)"; }}
            onBlur={(e) => { e.currentTarget.style.borderColor = "#e2e8f0"; e.currentTarget.style.boxShadow = "none"; }}
          />
        </div>
        <div>
          <label htmlFor="company-type" style={labelStyle}>Company Type</label>
          <select
            id="company-type"
            value={companyType}
            onChange={(e) => setCompanyType(e.target.value as Preferences["company_type"])}
            style={{ ...inputStyle, cursor: "pointer", appearance: "auto" }}
          >
            <option value="any">Any</option>
            <option value="startup">Startup</option>
            <option value="mid-size">Mid-size</option>
            <option value="enterprise">Enterprise</option>
          </select>
        </div>
      </div>

      <button
        type="submit"
        disabled={!canSubmit}
        style={{
          width: "100%",
          padding: "12px 24px",
          fontSize: 15,
          fontWeight: 600,
          background: canSubmit
            ? "linear-gradient(135deg, #6366f1, #8b5cf6)"
            : "#cbd5e1",
          color: "#fff",
          border: "none",
          borderRadius: 12,
          cursor: canSubmit ? "pointer" : "not-allowed",
          transition: "all 0.2s ease",
          boxShadow: canSubmit ? "0 2px 8px rgba(99,102,241,0.3)" : "none",
          letterSpacing: "0.01em",
        }}
        onMouseEnter={(e) => { if (canSubmit) e.currentTarget.style.transform = "translateY(-1px)"; }}
        onMouseLeave={(e) => { e.currentTarget.style.transform = "none"; }}
      >
        {loading ? "Analyzing..." : "🔍 Analyze My Network"}
      </button>
    </form>
  );
}


/* ── Parsing Summary ── */

export function ParsingSummaryBar({ summary }: { summary: ParsingSummaryType }) {
  const stats = [
    { label: "Rows", value: summary.total_rows, color: "#6366f1" },
    { label: "Valid", value: summary.valid_connections, color: "#16a34a" },
    { label: "Excluded", value: summary.excluded_rows, color: "#f59e0b" },
    { label: "Companies", value: summary.unique_companies, color: "#8b5cf6" },
  ];

  return (
    <div style={{
      display: "grid",
      gridTemplateColumns: "repeat(4, 1fr)",
      gap: 12,
      marginBottom: 24,
    }}>
      {stats.map((s) => (
        <div key={s.label} style={{
          background: "#fff",
          borderRadius: 12,
          padding: "14px 16px",
          textAlign: "center",
          boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
          border: "1px solid rgba(226,232,240,0.7)",
        }}>
          <div style={{ fontSize: 24, fontWeight: 800, color: s.color, lineHeight: 1.2 }}>{s.value}</div>
          <div style={{ fontSize: 12, color: "#94a3b8", fontWeight: 500, marginTop: 2 }}>{s.label}</div>
        </div>
      ))}
    </div>
  );
}

/* ── Path Label Badge ── */

const LABEL_STYLES: Record<string, { bg: string; color: string; border: string }> = {
  "Warm Path": { bg: "#dcfce7", color: "#15803d", border: "#bbf7d0" },
  "Stretch Path": { bg: "#fef9c3", color: "#a16207", border: "#fde68a" },
  Explore: { bg: "#f1f5f9", color: "#64748b", border: "#e2e8f0" },
};

function PathBadge({ label }: { label: string }) {
  const s = LABEL_STYLES[label] ?? LABEL_STYLES["Explore"];
  return (
    <span style={{
      background: s.bg,
      color: s.color,
      border: `1px solid ${s.border}`,
      padding: "3px 12px",
      borderRadius: 20,
      fontSize: 12,
      fontWeight: 600,
      whiteSpace: "nowrap",
    }}>
      {label}
    </span>
  );
}

/* ── Score Pill ── */

function ScorePill({ score }: { score: number }) {
  const hue = score >= 70 ? 142 : score >= 40 ? 45 : 220;
  return (
    <div style={{
      width: 44, height: 44, borderRadius: "50%",
      display: "flex", alignItems: "center", justifyContent: "center",
      background: `hsl(${hue}, 70%, 96%)`,
      border: `2px solid hsl(${hue}, 60%, 80%)`,
      fontWeight: 800, fontSize: 15,
      color: `hsl(${hue}, 60%, 35%)`,
      flexShrink: 0,
    }}>
      {score}
    </div>
  );
}


/* ── Company Result Card (expandable) ── */

function CompanyResultCard({
  result,
  preferences,
  cachedDetails,
  onCacheDetails,
}: {
  result: CompanyResult;
  preferences: Preferences | null;
  cachedDetails: LLMDetails | undefined;
  onCacheDetails: (key: string, details: LLMDetails) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const [details, setDetails] = useState<LLMDetails | null>(cachedDetails ?? null);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [copied, setCopied] = useState(false);

  const cacheKey = result.contact_url;

  const handleToggle = async () => {
    if (expanded) {
      setExpanded(false);
      return;
    }
    setExpanded(true);

    if (details || cachedDetails) {
      if (cachedDetails && !details) setDetails(cachedDetails);
      return;
    }

    if (!preferences) return;

    setLoadingDetails(true);
    try {
      const d = await fetchDetails(result, preferences);
      setDetails(d);
      onCacheDetails(cacheKey, d);
    } catch {
      setDetails({
        explanation: "Relevance based on your preferences.",
        next_action: "Reach out via LinkedIn message.",
        outreach_draft: `Hi ${result.contact_name}, I noticed we're connected on LinkedIn. Would you be open to a quick chat?`,
      });
    } finally {
      setLoadingDetails(false);
    }
  };

  const handleCopy = async () => {
    if (!details) return;
    try {
      await navigator.clipboard.writeText(details.outreach_draft);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      const ta = document.createElement("textarea");
      ta.value = details.outreach_draft;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div style={{
      background: "#fff",
      borderRadius: 14,
      padding: "18px 22px",
      marginBottom: 12,
      boxShadow: expanded
        ? "0 4px 16px rgba(0,0,0,0.06)"
        : "0 1px 3px rgba(0,0,0,0.04)",
      border: expanded ? "1px solid #c7d2fe" : "1px solid rgba(226,232,240,0.7)",
      transition: "all 0.2s ease",
      cursor: "pointer",
    }}
      onMouseEnter={(e) => { if (!expanded) e.currentTarget.style.boxShadow = "0 2px 8px rgba(0,0,0,0.06)"; }}
      onMouseLeave={(e) => { if (!expanded) e.currentTarget.style.boxShadow = "0 1px 3px rgba(0,0,0,0.04)"; }}
    >
      <div onClick={handleToggle}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12 }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
              <span style={{ fontSize: 17, fontWeight: 700, color: "#0f172a" }}>{result.company_name}</span>
              <span style={{ color: "#94a3b8", fontSize: 13 }}>
                {result.contact_count} contact{result.contact_count !== 1 ? "s" : ""}
              </span>
              <span style={{ color: "#c4c9d4", fontSize: 11, userSelect: "none" }}>
                {expanded ? "▲" : "▼"}
              </span>
            </div>
            <div style={{ fontSize: 14, color: "#475569", display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
              <a
                href={result.contact_url}
                target="_blank"
                rel="noopener noreferrer"
                style={{ color: "#6366f1", textDecoration: "none", fontWeight: 500 }}
                onClick={(e) => e.stopPropagation()}
              >
                {result.contact_name}
              </a>
              <span style={{ color: "#cbd5e1" }}>·</span>
              <span style={{ color: "#64748b" }}>{result.contact_title}</span>
              {result.contact_email && (
                <>
                  <span style={{ color: "#cbd5e1" }}>·</span>
                  <span style={{ color: "#94a3b8", fontSize: 13 }}>✉ {result.contact_email}</span>
                </>
              )}
            </div>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 12, flexShrink: 0 }}>
            <PathBadge label={result.path_label} />
            <ScorePill score={result.score} />
          </div>
        </div>
      </div>

      {expanded && (
        <div style={{
          marginTop: 16,
          paddingTop: 16,
          borderTop: "1px solid #f1f5f9",
        }}>
          {loadingDetails ? (
            <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "12px 0", color: "#94a3b8" }}>
              <span style={{
                display: "inline-block", width: 16, height: 16,
                border: "2px solid #e2e8f0", borderTopColor: "#6366f1",
                borderRadius: "50%", animation: "spin 0.8s linear infinite",
              }} />
              <span style={{ fontSize: 14 }}>Generating insights...</span>
            </div>
          ) : details ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              <DetailSection icon="💡" title="Why relevant" text={details.explanation} />
              <DetailSection icon="🎯" title="Next action" text={details.next_action} />
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                  <span style={{ fontSize: 13, fontWeight: 600, color: "#475569" }}>✉️ Outreach draft</span>
                  <button
                    onClick={(e) => { e.stopPropagation(); handleCopy(); }}
                    style={{
                      padding: "5px 14px",
                      fontSize: 12,
                      fontWeight: 600,
                      background: copied ? "#dcfce7" : "#f1f5f9",
                      color: copied ? "#15803d" : "#475569",
                      border: `1px solid ${copied ? "#bbf7d0" : "#e2e8f0"}`,
                      borderRadius: 8,
                      cursor: "pointer",
                      transition: "all 0.2s ease",
                    }}
                  >
                    {copied ? "✓ Copied" : "📋 Copy"}
                  </button>
                </div>
                <p style={{
                  margin: 0, fontSize: 14, color: "#334155", lineHeight: 1.6,
                  background: "#f8fafc", padding: "14px 16px", borderRadius: 10,
                  border: "1px solid #f1f5f9", whiteSpace: "pre-wrap",
                }}>
                  {details.outreach_draft}
                </p>
              </div>
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}

function DetailSection({ icon, title, text }: { icon: string; title: string; text: string }) {
  return (
    <div>
      <span style={{ fontSize: 13, fontWeight: 600, color: "#475569" }}>{icon} {title}</span>
      <p style={{ margin: "4px 0 0", fontSize: 14, color: "#334155", lineHeight: 1.6 }}>{text}</p>
    </div>
  );
}


/* ── Results List ── */

const PAGE_SIZE = 25;

export function ResultsList({
  results,
  preferences,
}: {
  results: CompanyResult[];
  preferences: Preferences | null;
}) {
  const [showCount, setShowCount] = useState(PAGE_SIZE);
  const detailsCacheRef = useRef<Record<string, LLMDetails>>({});

  const handleCacheDetails = (key: string, details: LLMDetails) => {
    detailsCacheRef.current[key] = details;
  };

  if (results.length === 0) {
    return (
      <div style={{
        textAlign: "center",
        padding: "48px 24px",
        background: "#fff",
        borderRadius: 16,
        border: "1px solid rgba(226,232,240,0.7)",
        boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
      }}>
        <div style={{ fontSize: 40, marginBottom: 12 }}>🔍</div>
        <p style={{ fontSize: 17, fontWeight: 600, color: "#334155", margin: "0 0 6px" }}>
          No matching companies found
        </p>
        <p style={{ fontSize: 14, color: "#94a3b8", margin: 0, maxWidth: 360, marginLeft: "auto", marginRight: "auto" }}>
          All connections were excluded (e.g., missing company info) or none matched your criteria. Try a different CSV or adjust your preferences.
        </p>
      </div>
    );
  }

  const visible = results.slice(0, showCount);

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
        <span style={{ fontSize: 14, fontWeight: 600, color: "#475569" }}>
          {results.length} {results.length === 1 ? "company" : "companies"} ranked
        </span>
        <span style={{ fontSize: 12, color: "#94a3b8" }}>
          Click a card to expand details
        </span>
      </div>
      {visible.map((r, i) => {
        const cacheKey = r.contact_url;
        return (
          <CompanyResultCard
            key={`${r.company_name}-${i}`}
            result={r}
            preferences={preferences}
            cachedDetails={detailsCacheRef.current[cacheKey]}
            onCacheDetails={handleCacheDetails}
          />
        );
      })}
      {showCount < results.length && (
        <button
          onClick={() => setShowCount((c) => c + PAGE_SIZE)}
          style={{
            display: "block",
            margin: "16px auto 0",
            padding: "10px 32px",
            fontSize: 14,
            fontWeight: 600,
            background: "#fff",
            color: "#6366f1",
            border: "1px solid #e2e8f0",
            borderRadius: 10,
            cursor: "pointer",
            transition: "all 0.2s ease",
          }}
          onMouseEnter={(e) => { e.currentTarget.style.background = "#f8fafc"; e.currentTarget.style.borderColor = "#c7d2fe"; }}
          onMouseLeave={(e) => { e.currentTarget.style.background = "#fff"; e.currentTarget.style.borderColor = "#e2e8f0"; }}
        >
          Show More ({results.length - showCount} remaining)
        </button>
      )}
    </div>
  );
}

/* ── Loading Indicator ── */

export function LoadingIndicator() {
  return (
    <div style={{
      textAlign: "center",
      padding: "48px 24px",
      background: "#fff",
      borderRadius: 16,
      border: "1px solid rgba(226,232,240,0.7)",
      boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
    }}>
      <div style={{
        display: "inline-block", width: 36, height: 36,
        border: "3px solid #e2e8f0", borderTopColor: "#6366f1",
        borderRadius: "50%", animation: "spin 0.8s linear infinite",
        marginBottom: 14,
      }} />
      <p style={{ margin: 0, fontSize: 15, fontWeight: 500, color: "#475569" }}>
        Analyzing your network...
      </p>
      <p style={{ margin: "6px 0 0", fontSize: 13, color: "#94a3b8" }}>
        Parsing, grouping, and ranking your connections. First load may take a few seconds.
      </p>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}

/* ── Error Alert ── */

export function ErrorAlert({
  message,
  onDismiss,
}: {
  message: string;
  onDismiss: () => void;
}) {
  return (
    <div
      role="alert"
      style={{
        background: "#fef2f2",
        border: "1px solid #fecaca",
        color: "#991b1b",
        padding: "14px 18px",
        borderRadius: 12,
        marginBottom: 20,
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        fontSize: 14,
        boxShadow: "0 1px 3px rgba(239,68,68,0.08)",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <span style={{ fontSize: 18 }}>⚠️</span>
        <span>{message}</span>
      </div>
      <button
        onClick={onDismiss}
        aria-label="Dismiss error"
        style={{
          background: "none",
          border: "none",
          color: "#dc2626",
          cursor: "pointer",
          fontSize: 16,
          padding: "4px 8px",
          borderRadius: 6,
          transition: "background 0.15s",
        }}
        onMouseEnter={(e) => { e.currentTarget.style.background = "rgba(220,38,38,0.08)"; }}
        onMouseLeave={(e) => { e.currentTarget.style.background = "none"; }}
      >
        ✕
      </button>
    </div>
  );
}
