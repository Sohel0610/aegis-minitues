import { useState, useEffect } from "react";
import {
  Activity,
  Users,
  TrendingDown,
  TrendingUp,
  Search,
  ArrowUpRight,
  ArrowDownRight,
  Loader2,
  AlertCircle,
} from "lucide-react";
import { useInsiderTradingFilters } from "@/contexts/InsiderTradingFilterContext";
import InsiderTradingFilterBar from "@/components/InsiderTradingFilterBar";

// ── Color palette (same as outside design) ────────────────────────
const C = {
  bg: "#F8FAFB",
  card: "#FFFFFF",
  border: "rgba(0,0,0,0.08)",
  borderStrong: "rgba(0,0,0,0.12)",
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
interface InsiderTradingSummary {
  total_companies: number;
  total_investors: number;
  total_shares: number;
  net_investors_change: number;
  net_shares_change: number;
  added_count: number;
  removed_count: number;
  changed_count: number;
  unchanged_count: number;
}

interface InsiderRecord {
  pangir: string;
  name: string;
  email: string;
  position_latest: number;
  position_older: number;
  position_difference: number;
  status: string;
  source?: string;
  company?: string;
  batch?: string;
  depository?: string;
}

interface EnhancedInsiderTradingDetails {
  summary: InsiderTradingSummary;
  top_new_investors: InsiderRecord[];
  top_exits: InsiderRecord[];
  top_buyers: InsiderRecord[];
  top_sellers: InsiderRecord[];
}

// ── Tab config ────────────────────────────────────────────────────
const tabConfig = [
  { id: "new" as const, label: "New Investors", color: C.green },
  { id: "exits" as const, label: "Exits", color: C.red },
  { id: "buyers" as const, label: "Top Buyers", color: C.blue },
  { id: "sellers" as const, label: "Top Sellers", color: C.amber },
];

// ── Component ─────────────────────────────────────────────────────
const EnhancedInsiderTradingAnalytics = () => {
  const { filters, buildQuery } = useInsiderTradingFilters();
  const [activeTab, setActiveTab] = useState<"new" | "exits" | "buyers" | "sellers">("new");
  const [details, setDetails] = useState<EnhancedInsiderTradingDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  // Refetch whenever global filters change
  useEffect(() => {
    fetchData();
  }, [filters.company, filters.batch, filters.depository]);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const qs = buildQuery();
      const res = await fetch(`/api/insider-trading/enhanced-details${qs}`);
      if (!res.ok) throw new Error("Failed to fetch data");
      const data: EnhancedInsiderTradingDetails = await res.json();
      setDetails(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load data");
    } finally {
      setLoading(false);
    }
  };

  // Display helpers
  const displayName = (record: InsiderRecord) => {
    const name = record.name?.trim();
    const pan = record.pangir?.trim();
    const panPattern = /^[A-Z]{5}\d{4}[A-Z]$/i;
    if (!name || name === pan || panPattern.test(name) || name === "unavailable") return "N/A";
    return name;
  };

  const displaySource = (record: InsiderRecord) => {
    if (record.company) {
      return `${record.company}${record.depository ? ` — ${record.depository}` : ""}`;
    }
    return record.source || "N/A";
  };

  // ── Loading / Error states ──────────────────────────────────────
  if (loading) {
    return (
      <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: C.bg, fontFamily: "Adani, sans-serif" }}>
        <div style={{ textAlign: "center" }}>
          <Loader2 size={40} color={C.orange} style={{ animation: "spin 1s linear infinite", marginBottom: 12 }} />
          <p style={{ color: C.text, fontSize: 14 }}>Loading analytics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: C.bg, fontFamily: "Adani, sans-serif" }}>
        <div style={{ textAlign: "center", maxWidth: 400 }}>
          <AlertCircle size={40} color={C.red} style={{ marginBottom: 12 }} />
          <h2 style={{ fontSize: 18, fontWeight: 600, color: C.text, marginBottom: 8 }}>Error Loading Analytics</h2>
          <p style={{ fontSize: 14, color: C.sub, marginBottom: 16 }}>{error}</p>
          <button onClick={fetchData} style={{ padding: "8px 18px", borderRadius: 8, background: C.orange, color: "#fff", border: "none", cursor: "pointer", fontSize: 13, fontWeight: 600, fontFamily: "Adani" }}>Retry</button>
        </div>
      </div>
    );
  }

  const s = details?.summary;

  // Get active table data
  const tableData: InsiderRecord[] = (() => {
    if (!details) return [];
    switch (activeTab) {
      case "new": return details.top_new_investors || [];
      case "exits": return details.top_exits || [];
      case "buyers": return details.top_buyers || [];
      case "sellers": return details.top_sellers || [];
      default: return [];
    }
  })();

  const filtered = tableData.filter((r) =>
    (r.name?.toLowerCase() || "").includes(search.toLowerCase()) ||
    (r.pangir?.toLowerCase() || "").includes(search.toLowerCase())
  );

  return (
    <div style={{ padding: "28px 32px", background: C.bg, minHeight: "100%", fontFamily: "Adani, sans-serif" }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 24 }}>
        <div style={{ width: 46, height: 46, borderRadius: 13, background: "linear-gradient(135deg, #0057B8, #003087)", display: "flex", alignItems: "center", justifyContent: "center", boxShadow: "0 4px 18px rgba(0,87,184,0.4)", flexShrink: 0 }}>
          <Activity size={22} color="#fff" strokeWidth={2.5} />
        </div>
        <div>
          <h1 style={{ color: C.text, margin: 0, fontSize: 20, fontWeight: 700 }}>Insider Trading Insight</h1>
          <p style={{ color: C.sub, margin: "3px 0 0", fontSize: 13 }}>Comprehensive analysis of insider trading activities</p>
        </div>
      </div>

      {/* Global filter bar */}
      <InsiderTradingFilterBar />

      {/* Key Metrics */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 7, marginBottom: 12 }}>
          <div style={{ width: 3, height: 18, borderRadius: 3, background: C.orange }} />
          <span style={{ fontSize: 13, color: C.text, fontWeight: 700, letterSpacing: "0.01em" }}>Key Metrics</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5 mb-6">
          {[
            {
              label: "Total Investors",
              value: s?.total_investors?.toLocaleString() || "0",
              sub: `${(s?.net_investors_change ?? 0) >= 0 ? "+" : ""}${s?.net_investors_change ?? 0} vs last period`,
              icon: Users,
              color: C.blue,
              trend: (s?.net_investors_change ?? 0) >= 0 ? "up" : "down",
            },
            {
              label: "Net Investor Change",
              value: `${((s?.added_count ?? 0) - (s?.removed_count ?? 0)) >= 0 ? "+" : ""}${(s?.added_count ?? 0) - (s?.removed_count ?? 0)}`,
              sub: "vs last period",
              icon: TrendingDown,
              color: C.red,
              trend: ((s?.added_count ?? 0) - (s?.removed_count ?? 0)) >= 0 ? "up" : "down",
            },
            {
              label: "Modified Positions",
              value: s?.changed_count?.toLocaleString() || "0",
              sub: "positions modified",
              icon: Activity,
              color: C.amber,
              trend: "neutral" as const,
            },
          ].map((m) => {
            const Icon = m.icon;
            return (
              <div key={m.label} style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: "18px 20px", display: "flex", gap: 14, alignItems: "center", position: "relative", overflow: "hidden", boxShadow: "0 1px 3px rgba(0,0,0,0.05)" }}>
                <div style={{ position: "absolute", bottom: -14, right: -14, width: 60, height: 60, borderRadius: "50%", background: `${m.color}15`, filter: "blur(10px)" }} />
                <div style={{ width: 44, height: 44, borderRadius: 11, background: `${m.color}14`, border: `1px solid ${m.color}28`, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                  <Icon size={20} color={m.color} strokeWidth={2} />
                </div>
                <div>
                  <div style={{ fontSize: 24, color: C.text, fontWeight: 700, letterSpacing: "-0.03em", lineHeight: 1.1 }}>{m.value}</div>
                  <div style={{ fontSize: 12, color: C.sub, fontWeight: 500 }}>{m.label}</div>
                  <div style={{ fontSize: 11, color: m.trend === "down" ? C.red : m.trend === "up" ? C.green : C.amber, marginTop: 2, fontWeight: 600 }}>{m.sub}</div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Movement Analysis */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 7, marginBottom: 12 }}>
          <div style={{ width: 3, height: 18, borderRadius: 3, background: C.blue }} />
          <span style={{ fontSize: 13, color: C.text, fontWeight: 700 }}>Movement Analysis</span>
        </div>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3.5 mb-6">
          {[
            { label: "New Investors", value: s?.added_count?.toLocaleString() || "0", color: C.green, icon: TrendingUp },
            { label: "Full Exits", value: s?.removed_count?.toLocaleString() || "0", color: C.red, icon: TrendingDown },
            { label: "Modified", value: s?.changed_count?.toLocaleString() || "0", color: C.amber, icon: Activity },
            { label: "Unchanged", value: s?.unchanged_count?.toLocaleString() || "0", color: C.muted, icon: Users },
          ].map((m) => {
            const Icon = m.icon;
            return (
              <div key={m.label} style={{ background: `${m.color}0D`, border: `1px solid ${m.color}28`, borderRadius: 12, padding: 18 }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 10 }}>
                  <Icon size={16} color={m.color} strokeWidth={2} />
                </div>
                <div style={{ fontSize: 22, color: m.color, fontWeight: 700, letterSpacing: "-0.02em", lineHeight: 1.1 }}>{m.value}</div>
                <div style={{ fontSize: 11, color: C.muted, marginTop: 4, fontWeight: 500 }}>{m.label}</div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Detailed Analysis Table */}
      <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 14, overflow: "hidden", boxShadow: "0 1px 3px rgba(0,0,0,0.05)" }}>
        <div style={{ padding: "16px 20px", borderBottom: `1px solid ${C.border}`, display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 12, background: "linear-gradient(90deg, rgba(0,87,184,0.05) 0%, transparent 100%)" }}>
          <div>
            <div style={{ fontSize: 14, color: C.text, fontWeight: 700 }}>Detailed Analysis</div>
            <div style={{ fontSize: 12, color: C.sub, marginTop: 2 }}>Top 15 movers in insider trading activities</div>
          </div>
          <div style={{ display: "flex", gap: 6 }}>
            {tabConfig.map((t) => (
              <button
                key={t.id}
                onClick={() => { setActiveTab(t.id); setSearch(""); }}
                style={{
                  padding: "7px 14px",
                  borderRadius: 8,
                  border: "none",
                  cursor: "pointer",
                  fontSize: 12,
                  fontWeight: 700,
                  fontFamily: "Adani",
                  background: activeTab === t.id ? t.color : "rgba(255,255,255,0.05)",
                  color: activeTab === t.id ? "#fff" : C.muted,
                  boxShadow: activeTab === t.id ? `0 4px 14px ${t.color}44` : "none",
                  transition: "all 0.18s",
                }}
              >
                {t.label} ({(() => {
                  if (!details) return 0;
                  switch (t.id) {
                    case "new": return details.top_new_investors?.length ?? 0;
                    case "exits": return details.top_exits?.length ?? 0;
                    case "buyers": return details.top_buyers?.length ?? 0;
                    case "sellers": return details.top_sellers?.length ?? 0;
                    default: return 0;
                  }
                })()})
              </button>
            ))}
          </div>
        </div>

        <div style={{ padding: "10px 20px", borderBottom: `1px solid ${C.border}`, display: "flex", alignItems: "center", gap: 8, background: C.bg }}>
          <Search size={14} color={C.muted} />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by PAN or name…"
            style={{ background: "transparent", border: "none", outline: "none", fontSize: 13, color: C.text, flex: 1, fontFamily: "Adani" }}
          />
          {search && (
            <button onClick={() => setSearch("")} style={{ background: "transparent", border: "none", cursor: "pointer", color: C.muted, fontSize: 16 }}>×</button>
          )}
        </div>

        <div style={{ overflowX: "hidden" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", tableLayout: "fixed" }}>
            <thead>
              <tr style={{ background: "rgba(0,87,184,0.04)" }}>
                {["PAN/GIR", "Name", "Pos. Older", "Pos. Latest", "Difference", "Email", "Source"].map((h) => (
                  <th key={h} style={{ padding: "10px 8px", textAlign: ["Pos. Older", "Pos. Latest", "Difference"].includes(h) ? "right" : "left", fontSize: 9, color: "#334155", textTransform: "uppercase", letterSpacing: "0.05em", fontWeight: 700, whiteSpace: "nowrap", borderBottom: `1px solid ${C.border}`, overflow: "hidden", textOverflow: "ellipsis" }}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.length > 0 ? (
                filtered.map((r, i) => (
                  <tr key={r.pangir || i} style={{ borderBottom: `1px solid ${C.border}`, background: i % 2 === 0 ? "#FFFFFF" : C.bg, cursor: "pointer" }}>
                    <td style={{ padding: "10px 8px", fontSize: 11, color: C.blue, fontFamily: "monospace", fontWeight: 700, whiteSpace: "nowrap" }}>{r.pangir?.trim() || "N/A"}</td>
                    <td style={{ padding: "10px 8px", fontSize: 11, color: C.text, maxWidth: 160, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{displayName(r)}</td>
                    <td style={{ padding: "10px 8px", fontSize: 11, color: C.sub, textAlign: "right", whiteSpace: "nowrap" }}>{(r.position_older ?? 0).toLocaleString()}</td>
                    <td style={{ padding: "10px 8px", fontSize: 11, color: C.text, fontWeight: 700, textAlign: "right", whiteSpace: "nowrap" }}>{(r.position_latest ?? 0).toLocaleString()}</td>
                    <td style={{ padding: "10px 8px", textAlign: "right", whiteSpace: "nowrap" }}>
                      <span style={{ fontSize: 11, fontWeight: 800, color: (r.position_difference ?? 0) >= 0 ? C.green : C.red, display: "inline-flex", alignItems: "center", gap: 2 }}>
                        {(r.position_difference ?? 0) >= 0 ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}
                        {(r.position_difference ?? 0) >= 0 ? "+" : ""}{(r.position_difference ?? 0).toLocaleString()}
                      </span>
                    </td>
                    <td style={{ padding: "10px 8px", fontSize: 10, color: C.muted, maxWidth: 140, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{r.email?.trim() || "N/A"}</td>
                    <td style={{ padding: "10px 8px", fontSize: 10, color: C.muted, maxWidth: 140, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{displaySource(r)}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} style={{ padding: 40, textAlign: "center", color: C.muted, fontSize: 13 }}>
                    No records match your search
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        <div style={{ padding: "12px 20px", borderTop: `1px solid ${C.border}`, display: "flex", justifyContent: "space-between", alignItems: "center", background: C.bg }}>
          <span style={{ fontSize: 12, color: C.muted }}>Showing {filtered.length} of {tableData.length} records</span>
        </div>
      </div>
    </div>
  );
};

export default EnhancedInsiderTradingAnalytics;
