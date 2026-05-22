import { useState, useEffect } from "react";
import {
  Loader2,
  AlertCircle,
  RefreshCw,
  CheckCircle,
  HelpCircle,
  ShieldAlert,
  UserCheck,
  FileSpreadsheet,
  Award,
  AlertTriangle,
  Search,
} from "lucide-react";

// ── Color palette (same as all other pages) ───────────────────────
const C = {
  bg: "#F8FAFB",
  card: "#FFFFFF",
  border: "rgba(0,0,0,0.08)",
  orange: "#0066B3",
  blue: "#4DA6FF",
  green: "#00C98A",
  red: "#6366F1",
  amber: "#F7941D",
  text: "#1E293B",
  sub: "#64748B",
  muted: "#94A3B8",
};

// ── Types (unchanged) ─────────────────────────────────────────────
interface SummaryMetrics {
  total_declarations: number;
  total_holdings: number;
  total_preclearances: number;
  unsanctioned_trades_count: number;
  volume_breaches_count: number;
  holding_discrepancies_count: number;
}

interface ViolationRecord {
  shareholder_name?: string;
  pan?: string;
  company_name?: string;
  shares_traded?: number;
  batch_name?: string;
  transaction_date?: string;
  employee_name?: string;
  employee_email?: string;
  approved_volume?: number;
  excess_volume?: number;
  ritm_number?: string;
  declarant_name?: string;
  relationship?: string;
  declared_quantity?: number;
  depository_quantity?: number;
  difference?: number;
  phase?: string;
  fiscal_year?: string;
}

interface SyncStep {
  step: string;
  status: string;
  detail: string;
}

interface SyncResult {
  message: string;
  api_fetched: boolean;
  new_records_from_api: number;
  steps: SyncStep[];
}

// ── Tab config ────────────────────────────────────────────────────
const tabConfig = [
  { id: "UNSANCTIONED" as const, label: "Unsanctioned Trades", color: C.red, tooltip: "Trades executed without prior pre-clearance approval" },
  { id: "VOLUME_BREACH" as const, label: "Volume Breaches", color: C.amber, tooltip: "Trades exceeding the approved pre-clearance volume" },
  { id: "HOLDING_MISMATCH" as const, label: "Holding Discrepancies", color: "#D97706", tooltip: "Mismatch between declared holdings and depository records" },
];

// ── Component ─────────────────────────────────────────────────────
const ServiceNowReconciliation = () => {
  const [activeTab, setActiveTab] = useState<"UNSANCTIONED" | "VOLUME_BREACH" | "HOLDING_MISMATCH">("UNSANCTIONED");
  const [summary, setSummary] = useState<SummaryMetrics | null>(null);
  const [violations, setViolations] = useState<ViolationRecord[]>([]);
  const [loadingSummary, setLoadingSummary] = useState(true);
  const [loadingViolations, setLoadingViolations] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [syncPhase, setSyncPhase] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [syncResult, setSyncResult] = useState<SyncResult | null>(null);
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    fetchSummary();
  }, []);

  useEffect(() => {
    fetchViolations();
  }, [activeTab]);

  const fetchSummary = async () => {
    try {
      setLoadingSummary(true);
      const res = await fetch("/api/servicenow/summary");
      if (!res.ok) throw new Error("Failed to fetch ServiceNow summary metadata");
      const data = await res.json();
      setSummary(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingSummary(false);
    }
  };

  const fetchViolations = async () => {
    try {
      setLoadingViolations(true);
      setError(null);
      const res = await fetch(`/api/servicenow/violations?type=${activeTab}&limit=100`);
      if (!res.ok) throw new Error("Failed to fetch violations records");
      const data = await res.json();
      setViolations(data.violations || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load violations details");
    } finally {
      setLoadingViolations(false);
    }
  };

  const handleSync = async () => {
    try {
      setSyncing(true);
      setSyncResult(null);
      setError(null);
      setSyncPhase("Connecting to ServiceNow API...");

      const res = await fetch("/api/servicenow/sync", { method: "POST" });

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || "Synchronization request failed");
      }

      const data: SyncResult = await res.json();
      setSyncResult(data);

      setSyncPhase("Refreshing dashboard...");
      await fetchSummary();
      await fetchViolations();

      setTimeout(() => {
        setSyncResult(null);
      }, 12000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to sync ServiceNow records");
    } finally {
      setSyncing(false);
      setSyncPhase("");
    }
  };

  const getTabCount = (tabId: string) => {
    if (!summary) return 0;
    switch (tabId) {
      case "UNSANCTIONED": return summary.unsanctioned_trades_count ?? 0;
      case "VOLUME_BREACH": return summary.volume_breaches_count ?? 0;
      case "HOLDING_MISMATCH": return summary.holding_discrepancies_count ?? 0;
      default: return 0;
    }
  };

  // KPI card data
  const kpiCards = [
    { label: "Declarations", value: summary?.total_declarations ?? 0, sub: "Submitted Forms", color: C.blue, icon: FileSpreadsheet },
    { label: "Holdings Declared", value: summary?.total_holdings ?? 0, sub: "Position Lines", color: C.green, icon: Award },
    { label: "Pre-clearances", value: summary?.total_preclearances ?? 0, sub: "Buy/Sell Applications", color: C.orange, icon: CheckCircle },
    { label: "Unsanctioned Trades", value: summary?.unsanctioned_trades_count ?? 0, sub: "No Pre-clearance", color: C.red, icon: AlertTriangle },
    { label: "Volume Breaches", value: summary?.volume_breaches_count ?? 0, sub: "Over approved limit", color: C.amber, icon: AlertCircle },
    { label: "Holding Mismatches", value: summary?.holding_discrepancies_count ?? 0, sub: "Form vs Depository", color: "#D97706", icon: RefreshCw },
  ];

  // Filter violations based on search term
  const filteredViolations = violations.filter((record) => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return (
      (record.shareholder_name || "").toLowerCase().includes(term) ||
      (record.employee_name || "").toLowerCase().includes(term) ||
      (record.declarant_name || "").toLowerCase().includes(term) ||
      (record.pan || "").toLowerCase().includes(term) ||
      (record.company_name || "").toLowerCase().includes(term)
    );
  });

  // Table headers per tab
  const getHeaders = () => {
    switch (activeTab) {
      case "UNSANCTIONED":
        return ["Insider Shareholder", "PAN", "Company", "Employee / Owner", "Traded Qty", "Batch Period", "Date"];
      case "VOLUME_BREACH":
        return ["Insider Shareholder", "PAN", "Company", "Employee / Owner", "Traded Vol", "Approved Vol", "Excess Vol", "RITM Ticket", "Date"];
      case "HOLDING_MISMATCH":
        return ["Employee Name", "Declared Shareholder", "Relationship", "PAN", "Company", "Declared Qty", "Depository Qty", "Difference", "Ticket", "Period"];
    }
  };

  return (
    <div style={{ padding: "28px 24px", background: C.bg, minHeight: "100%", fontFamily: "Adani, sans-serif", maxWidth: "100%", boxSizing: "border-box" }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 24 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <div style={{ width: 46, height: 46, borderRadius: 13, background: "linear-gradient(135deg, #6366F1, #4F46E5)", display: "flex", alignItems: "center", justifyContent: "center", boxShadow: "0 4px 18px rgba(99,102,241,0.35)", flexShrink: 0 }}>
            <ShieldAlert size={22} color="#fff" strokeWidth={2.5} />
          </div>
          <div>
            <h1 style={{ color: C.text, margin: 0, fontSize: 20, fontWeight: 700 }}>ServiceNow PIT Compliance</h1>
            <p style={{ color: C.sub, margin: "3px 0 0", fontSize: 13 }}>Compare ServiceNow employee disclosures & pre-clearance approvals against depository trade logs</p>
          </div>
        </div>
      </div>

      {/* Error banner */}
      {error && (
        <div style={{ marginBottom: 20, padding: "12px 16px", background: "rgba(247,148,29,0.08)", border: "1px solid rgba(247,148,29,0.25)", borderRadius: 10, display: "flex", alignItems: "center", gap: 10 }}>
          <AlertCircle size={18} color={C.red} style={{ flexShrink: 0 }} />
          <span style={{ fontSize: 13, color: C.red, fontWeight: 500 }}>{error}</span>
        </div>
      )}

      {/* Sync result banner */}
      {syncResult && (
        <div style={{ marginBottom: 20, padding: "12px 16px", background: "rgba(0,201,138,0.08)", border: "1px solid rgba(0,201,138,0.25)", borderRadius: 10, display: "flex", alignItems: "center", gap: 10 }}>
          <CheckCircle size={18} color={C.green} style={{ flexShrink: 0 }} />
          <div>
            <div style={{ fontSize: 13, color: C.green, fontWeight: 600 }}>{syncResult.message}</div>
            <div style={{ fontSize: 11, color: C.sub, marginTop: 2 }}>
              {syncResult.new_records_from_api} new records fetched from API
            </div>
          </div>
        </div>
      )}

      {/* KPI Cards */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 7, marginBottom: 12 }}>
          <div style={{ width: 3, height: 18, borderRadius: 3, background: C.orange }} />
          <span style={{ fontSize: 13, color: C.text, fontWeight: 700 }}>Compliance Overview</span>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3.5 mb-6">
          {kpiCards.map((kpi) => {
            const Icon = kpi.icon;
            const isAlert = ["Unsanctioned Trades", "Volume Breaches", "Holding Mismatches"].includes(kpi.label);
            return (
              <div key={kpi.label} style={{
                background: isAlert ? `${kpi.color}0D` : C.card,
                border: `1px solid ${isAlert ? `${kpi.color}28` : C.border}`,
                borderRadius: 12, padding: "18px 16px", position: "relative", overflow: "hidden",
                boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
              }}>
                <div style={{ position: "absolute", top: -15, right: -15, width: 50, height: 50, borderRadius: "50%", background: `${kpi.color}12`, filter: "blur(12px)" }} />
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                  <span style={{ fontSize: 9, color: C.muted, textTransform: "uppercase", letterSpacing: "0.08em", fontWeight: 700 }}>{kpi.label}</span>
                  <Icon size={14} color={kpi.color} />
                </div>
                <div style={{ fontSize: 22, color: isAlert ? kpi.color : C.text, fontWeight: 800, letterSpacing: "-0.03em" }}>
                  {loadingSummary ? "..." : kpi.value.toLocaleString()}
                </div>
                <div style={{ fontSize: 10, color: C.muted, marginTop: 3 }}>{kpi.sub}</div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Compliance Check Details Table */}
      <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 14, overflow: "hidden", boxShadow: "0 1px 3px rgba(0,0,0,0.05)" }}>
        <div style={{ padding: "16px 20px", borderBottom: `1px solid ${C.border}`, display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 12, background: "linear-gradient(90deg, rgba(99,102,241,0.04) 0%, transparent 100%)" }}>
          <div>
            <div style={{ fontSize: 14, color: C.text, fontWeight: 700 }}>Compliance Check Details</div>
            <div style={{ fontSize: 12, color: C.sub, marginTop: 2 }}>Select a violation type to inspect matched records and discrepancies</div>
          </div>
<<<<<<< HEAD
          <div style={{ display: "flex", gap: 6 }}>
            {tabConfig.map((t) => (
              <button
                key={t.id}
                onClick={() => setActiveTab(t.id)}
                title={t.tooltip}
                style={{
                  padding: "7px 14px", borderRadius: 8, border: "none", cursor: "pointer",
                  fontSize: 12, fontWeight: 700, fontFamily: "Adani",
                  background: activeTab === t.id ? t.color : "rgba(255,255,255,0.05)",
                  color: activeTab === t.id ? "#fff" : C.muted,
                  boxShadow: activeTab === t.id ? `0 4px 14px ${t.color}44` : "none",
                  transition: "all 0.18s",
                }}
              >
                {t.label} ({getTabCount(t.id)})
              </button>
            ))}
=======
          <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
            <div style={{ display: "flex", gap: 6 }}>
              {tabConfig.map((t) => (
                <button
                  key={t.id}
                  onClick={() => setActiveTab(t.id)}
                  title={t.tooltip}
                  style={{
                    padding: "7px 14px", borderRadius: 8, border: "none", cursor: "pointer",
                    fontSize: 12, fontWeight: 700, fontFamily: "Adani",
                    background: activeTab === t.id ? t.color : "rgba(255,255,255,0.05)",
                    color: activeTab === t.id ? "#fff" : C.muted,
                    boxShadow: activeTab === t.id ? `0 4px 14px ${t.color}44` : "none",
                    transition: "all 0.18s",
                  }}
                >
                  {t.label} ({getTabCount(t.id)})
                </button>
              ))}
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 7, padding: "6px 12px", borderRadius: 8, background: C.bg, border: `1px solid ${C.border}` }}>
              <Search size={13} color={C.muted} />
              <input
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search by name or PAN…"
                style={{ background: "transparent", border: "none", outline: "none", fontSize: 12, color: C.text, width: 180, fontFamily: "Adani" }}
              />
            </div>
>>>>>>> 223947e (insider)
          </div>
        </div>

        {loadingViolations ? (
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "60px 0" }}>
            <Loader2 size={32} color={C.orange} style={{ animation: "spin 1s linear infinite", marginBottom: 8 }} />
            <p style={{ color: C.sub, fontSize: 13 }}>Calculating compliance metrics...</p>
          </div>
        ) : (
<<<<<<< HEAD
          <div style={{ overflowX: "hidden" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", tableLayout: "fixed" }}>
=======
          <div style={{ overflowX: "auto", width: "100%" }}>
            <table style={{ width: "100%", minWidth: "1200px", borderCollapse: "collapse" }}>
>>>>>>> 223947e (insider)
              <thead>
                <tr style={{ background: "rgba(0,87,184,0.04)" }}>
                  {getHeaders().map((h) => (
                    <th key={h} style={{
                      padding: "10px 8px", textAlign: "left", fontSize: 9,
                      color: "#334155", textTransform: "uppercase", letterSpacing: "0.05em",
                      fontWeight: 700, whiteSpace: "nowrap", borderBottom: `1px solid ${C.border}`,
                      overflow: "hidden", textOverflow: "ellipsis",
                    }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filteredViolations.length > 0 ? (
                  filteredViolations.map((record, index) => (
                    <tr key={index} style={{ borderBottom: `1px solid ${C.border}`, background: index % 2 === 0 ? "#FFFFFF" : C.bg }}>
                      {activeTab === "UNSANCTIONED" && (
                        <>
<<<<<<< HEAD
                          <td style={{ padding: "10px 8px", fontSize: 11, color: C.text, fontWeight: 600, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{record.shareholder_name}</td>
                          <td style={{ padding: "10px 8px", fontSize: 11, color: C.blue, fontFamily: "monospace", fontWeight: 700 }}>{record.pan}</td>
                          <td style={{ padding: "10px 8px", fontSize: 11, color: C.text, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{record.company_name}</td>
                          <td style={{ padding: "10px 8px" }}>
                            <div style={{ fontSize: 11, color: C.text, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{record.employee_name}</div>
                            <div style={{ fontSize: 9, color: C.muted, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{record.employee_email}</div>
=======
                          <td style={{ padding: "10px 8px", fontSize: 11, color: C.text, fontWeight: 600, whiteSpace: "nowrap" }}>{record.shareholder_name}</td>
                          <td style={{ padding: "10px 8px", fontSize: 11, color: C.blue, fontFamily: "monospace", fontWeight: 700 }}>{record.pan}</td>
                          <td style={{ padding: "10px 8px", fontSize: 11, color: C.text, whiteSpace: "nowrap" }}>{record.company_name}</td>
                          <td style={{ padding: "10px 8px" }}>
                            <div style={{ fontSize: 11, color: C.text, whiteSpace: "nowrap" }}>{record.employee_name}</div>
                            <div style={{ fontSize: 9, color: C.muted, whiteSpace: "nowrap" }}>{record.employee_email}</div>
>>>>>>> 223947e (insider)
                          </td>
                          <td style={{ padding: "10px 8px", fontSize: 11, color: C.red, fontWeight: 800 }}>
                            {record.shares_traded && record.shares_traded > 0 ? "+" : ""}{record.shares_traded?.toLocaleString()}
                          </td>
<<<<<<< HEAD
                          <td style={{ padding: "10px 8px", fontSize: 10, color: C.muted, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{record.batch_name}</td>
=======
                          <td style={{ padding: "10px 8px", fontSize: 10, color: C.muted, whiteSpace: "nowrap" }}>{record.batch_name}</td>
>>>>>>> 223947e (insider)
                          <td style={{ padding: "10px 8px", fontSize: 10, color: C.muted, whiteSpace: "nowrap" }}>{record.transaction_date}</td>
                        </>
                      )}
                      {activeTab === "VOLUME_BREACH" && (
                        <>
<<<<<<< HEAD
                          <td style={{ padding: "10px 8px", fontSize: 11, color: C.text, fontWeight: 600, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{record.shareholder_name}</td>
                          <td style={{ padding: "10px 8px", fontSize: 11, color: C.blue, fontFamily: "monospace", fontWeight: 700 }}>{record.pan}</td>
                          <td style={{ padding: "10px 8px", fontSize: 11, color: C.text, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{record.company_name}</td>
                          <td style={{ padding: "10px 8px" }}>
                            <div style={{ fontSize: 11, color: C.text, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{record.employee_name}</div>
                            <div style={{ fontSize: 9, color: C.muted, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{record.employee_email}</div>
=======
                          <td style={{ padding: "10px 8px", fontSize: 11, color: C.text, fontWeight: 600, whiteSpace: "nowrap" }}>{record.shareholder_name}</td>
                          <td style={{ padding: "10px 8px", fontSize: 11, color: C.blue, fontFamily: "monospace", fontWeight: 700 }}>{record.pan}</td>
                          <td style={{ padding: "10px 8px", fontSize: 11, color: C.text, whiteSpace: "nowrap" }}>{record.company_name}</td>
                          <td style={{ padding: "10px 8px" }}>
                            <div style={{ fontSize: 11, color: C.text, whiteSpace: "nowrap" }}>{record.employee_name}</div>
                            <div style={{ fontSize: 9, color: C.muted, whiteSpace: "nowrap" }}>{record.employee_email}</div>
>>>>>>> 223947e (insider)
                          </td>
                          <td style={{ padding: "10px 8px", fontSize: 11, color: C.text, fontWeight: 700 }}>{record.shares_traded?.toLocaleString()}</td>
                          <td style={{ padding: "10px 8px", fontSize: 11, color: C.sub }}>{record.approved_volume?.toLocaleString()}</td>
                          <td style={{ padding: "10px 8px", fontSize: 11, color: C.red, fontWeight: 800 }}>+{record.excess_volume?.toLocaleString()}</td>
                          <td style={{ padding: "10px 8px", fontSize: 11, color: C.orange, fontFamily: "monospace", fontWeight: 700 }}>{record.ritm_number}</td>
                          <td style={{ padding: "10px 8px", fontSize: 10, color: C.muted, whiteSpace: "nowrap" }}>{record.transaction_date}</td>
                        </>
                      )}
                      {activeTab === "HOLDING_MISMATCH" && (
                        <>
                          <td style={{ padding: "10px 8px" }}>
<<<<<<< HEAD
                            <div style={{ fontSize: 11, color: C.text, fontWeight: 600, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{record.employee_name}</div>
                            <div style={{ fontSize: 9, color: C.muted, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{record.employee_email}</div>
                          </td>
                          <td style={{ padding: "10px 8px", fontSize: 11, color: C.text, fontWeight: 600, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{record.declarant_name}</td>
                          <td style={{ padding: "10px 8px", fontSize: 10, color: C.sub, textTransform: "capitalize" }}>{record.relationship}</td>
                          <td style={{ padding: "10px 8px", fontSize: 11, color: C.blue, fontFamily: "monospace", fontWeight: 700 }}>{record.pan}</td>
                          <td style={{ padding: "10px 8px", fontSize: 10, color: C.text, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{record.company_name}</td>
=======
                            <div style={{ fontSize: 11, color: C.text, fontWeight: 600, whiteSpace: "nowrap" }}>{record.employee_name}</div>
                            <div style={{ fontSize: 9, color: C.muted, whiteSpace: "nowrap" }}>{record.employee_email}</div>
                          </td>
                          <td style={{ padding: "10px 8px", fontSize: 11, color: C.text, fontWeight: 600, whiteSpace: "nowrap" }}>{record.declarant_name}</td>
                          <td style={{ padding: "10px 8px", fontSize: 10, color: C.sub, textTransform: "capitalize" }}>{record.relationship}</td>
                          <td style={{ padding: "10px 8px", fontSize: 11, color: C.blue, fontFamily: "monospace", fontWeight: 700 }}>{record.pan}</td>
                          <td style={{ padding: "10px 8px", fontSize: 10, color: C.text, whiteSpace: "nowrap" }}>{record.company_name}</td>
>>>>>>> 223947e (insider)
                          <td style={{ padding: "10px 8px", fontSize: 11, color: C.sub }}>{record.declared_quantity?.toLocaleString()}</td>
                          <td style={{ padding: "10px 8px", fontSize: 11, color: C.text, fontWeight: 700 }}>{record.depository_quantity?.toLocaleString()}</td>
                          <td style={{ padding: "10px 8px", fontSize: 11, color: C.amber, fontWeight: 800 }}>
                            {record.difference && record.difference > 0 ? "+" : ""}{record.difference?.toLocaleString()}
                          </td>
                          <td style={{ padding: "10px 8px", fontSize: 11, color: C.orange, fontFamily: "monospace", fontWeight: 700 }}>{record.ritm_number}</td>
                          <td style={{ padding: "10px 8px", fontSize: 10, color: C.muted, whiteSpace: "nowrap" }}>
                            {record.fiscal_year} — {record.phase}
                          </td>
                        </>
                      )}
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={10} style={{ padding: "60px 0", textAlign: "center" }}>
                      <UserCheck size={40} color={C.green} style={{ margin: "0 auto 8px", opacity: 0.55 }} />
                      <h4 style={{ fontSize: 14, fontWeight: 700, color: C.text, marginBottom: 4 }}>Compliance Clear</h4>
                      <p style={{ fontSize: 12, color: C.muted, maxWidth: 320, margin: "0 auto" }}>
                        No active {activeTab.toLowerCase().replace("_", " ")} violations detected in the database records.
                      </p>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        <div style={{ padding: "12px 20px", borderTop: `1px solid ${C.border}`, display: "flex", justifyContent: "space-between", alignItems: "center", background: C.bg }}>
          <span style={{ fontSize: 12, color: C.muted }}>Showing {filteredViolations.length} records</span>
          <span style={{ fontSize: 11, color: C.muted }}>🔒 SEBI PIT Compliance Audit</span>
        </div>
      </div>
    </div>
  );
};

export default ServiceNowReconciliation;
