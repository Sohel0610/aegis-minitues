import { useState, useEffect } from "react";
import {
  Database,
  Search,
  Plus,
  Minus,
  RefreshCw,
  ArrowUpDown,
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
  orange: "#0066B3",
  blue: "#4DA6FF",
  green: "#00C98A",
  red: "#6366F1",
  amber: "#F7941D",
  text: "#1E293B",
  sub: "#64748B",
  muted: "#94A3B8",
};

const depStyle: Record<string, { bg: string; color: string; border: string }> = {
  CDSL: { bg: "rgba(0,87,184,0.08)", color: "#0057B8", border: "rgba(0,87,184,0.25)" },
  NSDL: { bg: "rgba(0,201,138,0.08)", color: "#00C98A", border: "rgba(0,201,138,0.25)" },
  Physical: { bg: "rgba(247,148,29,0.08)", color: "#F7941D", border: "rgba(247,148,29,0.25)" },
  PHY: { bg: "rgba(247,148,29,0.08)", color: "#F7941D", border: "rgba(247,148,29,0.25)" },
};

// ── Types (unchanged) ─────────────────────────────────────────────
interface SummaryRow {
  id?: number;
  company: string;
  batch: string;
  depository: string;
  added: number;
  removed: number;
  changed: number;
  unchanged: number;
  total: number;
  empty_pangir_latest?: number;
  empty_pangir_older?: number;
}

// ── Component ─────────────────────────────────────────────────────
const InsiderTradingDataSource = () => {
  const { filters, buildQuery } = useInsiderTradingFilters();
  const [summaryRows, setSummaryRows] = useState<SummaryRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [sortField, setSortField] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  // Refetch whenever global filters change
  useEffect(() => {
    fetchData();
  }, [filters.company, filters.batch, filters.depository]);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const qs = buildQuery();
      const res = await fetch(`/api/insider-trading/summary/detail${qs}`);
      if (!res.ok) throw new Error("Failed to fetch summary data");
      const data = await res.json();
      setSummaryRows(data.summary || []);
    } catch (err) {
      console.error("Error fetching data:", err);
      setError(err instanceof Error ? err.message : "Failed to load data");
    } finally {
      setLoading(false);
    }
  };

  const filteredRows = summaryRows.filter(
    (row) =>
      row.company.toLowerCase().includes(searchTerm.toLowerCase()) ||
      row.batch.toLowerCase().includes(searchTerm.toLowerCase()) ||
      row.depository.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const sorted = sortField
    ? [...filteredRows].sort((a, b) =>
        sortDir === "asc"
          ? (a as any)[sortField] - (b as any)[sortField]
          : (b as any)[sortField] - (a as any)[sortField]
      )
    : filteredRows;

  const handleSort = (f: string) => {
    setSortField(f);
    setSortDir(sortField === f && sortDir === "desc" ? "asc" : "desc");
  };

  // Aggregate totals
  const totals = filteredRows.reduce(
    (acc, r) => ({
      added: acc.added + (r.added || 0),
      removed: acc.removed + (r.removed || 0),
      changed: acc.changed + (r.changed || 0),
      unchanged: acc.unchanged + (r.unchanged || 0),
      total: acc.total + (r.total || 0),
    }),
    { added: 0, removed: 0, changed: 0, unchanged: 0, total: 0 }
  );

  const statCards = [
    { label: "Total Records", value: totals.total, color: C.text, accent: "#4DA6FF", icon: null },
    { label: "Added", value: totals.added, color: C.green, accent: C.green, icon: Plus },
    { label: "Removed", value: totals.removed, color: C.red, accent: C.red, icon: Minus },
    { label: "Changed", value: totals.changed, color: C.amber, accent: C.amber, icon: RefreshCw },
    { label: "Unchanged", value: totals.unchanged, color: C.sub, accent: C.sub, icon: null },
  ];

  // ── Loading / Error states ──────────────────────────────────────
  if (loading) {
    return (
      <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: C.bg, fontFamily: "Adani, sans-serif" }}>
        <div style={{ textAlign: "center" }}>
          <Loader2 size={40} color={C.orange} style={{ animation: "spin 1s linear infinite", marginBottom: 12 }} />
          <p style={{ color: C.text, fontSize: 14 }}>Loading data sources...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: C.bg, fontFamily: "Adani, sans-serif" }}>
        <div style={{ textAlign: "center", maxWidth: 400 }}>
          <AlertCircle size={40} color={C.red} style={{ marginBottom: 12 }} />
          <h2 style={{ fontSize: 18, fontWeight: 600, color: C.text, marginBottom: 8 }}>Error Loading Data</h2>
          <p style={{ fontSize: 14, color: C.sub, marginBottom: 16 }}>{error}</p>
          <button onClick={fetchData} style={{ padding: "8px 18px", borderRadius: 8, background: C.orange, color: "#fff", border: "none", cursor: "pointer", fontSize: 13, fontWeight: 600, fontFamily: "Adani" }}>Retry</button>
        </div>
      </div>
    );
  }

  return (
    <div style={{ padding: "28px 32px", background: C.bg, minHeight: "100%", fontFamily: "Adani, sans-serif" }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 24 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <div style={{ width: 46, height: 46, borderRadius: 13, background: "linear-gradient(135deg, #00C98A, #007A54)", display: "flex", alignItems: "center", justifyContent: "center", boxShadow: "0 4px 18px rgba(0,201,138,0.35)", flexShrink: 0 }}>
            <Database size={22} color="#fff" strokeWidth={2.5} />
          </div>
          <div>
            <h1 style={{ color: C.text, margin: 0, fontSize: 20, fontWeight: 700 }}>Data Sources</h1>
            <p style={{ color: C.sub, margin: "3px 0 0", fontSize: 13 }}>Summary of insider trading data per company, batch, and depository</p>
          </div>
        </div>
      </div>

      {/* Global filter bar */}
      <InsiderTradingFilterBar />

      {/* Stat Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3.5 mb-6">
        {statCards.map((s) => {
          const Icon = s.icon;
          return (
            <div key={s.label} style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: "18px 20px", position: "relative", overflow: "hidden", boxShadow: "0 1px 3px rgba(0,0,0,0.05)" }}>
              <div style={{ position: "absolute", top: -15, right: -15, width: 55, height: 55, borderRadius: "50%", background: `${s.accent}12`, filter: "blur(12px)" }} />
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
                <span style={{ fontSize: 10, color: C.muted, textTransform: "uppercase", letterSpacing: "0.08em", fontWeight: 700 }}>{s.label}</span>
                {Icon && <Icon size={14} color={s.color} />}
              </div>
              <div style={{ fontSize: 22, color: s.color, fontWeight: 800, letterSpacing: "-0.03em" }}>{s.value.toLocaleString()}</div>
            </div>
          );
        })}
      </div>

      {/* Table */}
      <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 14, overflow: "hidden", boxShadow: "0 1px 3px rgba(0,0,0,0.05)" }}>
        <div style={{ padding: "16px 20px", borderBottom: `1px solid ${C.border}`, display: "flex", justifyContent: "space-between", alignItems: "center", background: "linear-gradient(90deg, rgba(0,201,138,0.04) 0%, transparent 100%)" }}>
          <div>
            <div style={{ fontSize: 14, color: C.text, fontWeight: 700 }}>Company Summary</div>
            <div style={{ fontSize: 12, color: C.sub, marginTop: 2 }}>{sorted.length} summary rows found</div>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 7, padding: "8px 14px", borderRadius: 8, background: C.bg, border: `1px solid ${C.border}` }}>
            <Search size={13} color={C.muted} />
            <input
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search companies…"
              style={{ background: "transparent", border: "none", outline: "none", fontSize: 12, color: C.text, width: 160, fontFamily: "Adani" }}
            />
          </div>
        </div>


        <div style={{ overflowX: "auto", width: "100%" }}>
          <table style={{ width: "100%", minWidth: "900px", borderCollapse: "collapse" }}>

            <thead>
              <tr style={{ background: "rgba(0,87,184,0.04)" }}>
                {[
                  { h: "Company", f: null },
                  { h: "Batch", f: null },
                  { h: "Depository", f: null },
                  { h: "Total", f: "total" },
                  { h: "Added", f: "added" },
                  { h: "Removed", f: "removed" },
                  { h: "Changed", f: "changed" },
                  { h: "Unchanged", f: "unchanged" },
                ].map(({ h, f }) => (
                  <th
                    key={h}
                    onClick={() => f && handleSort(f)}
                    style={{
                      padding: "10px 8px",
                      textAlign: ["Total", "Added", "Removed", "Changed", "Unchanged"].includes(h) ? "right" : "left",
                      fontSize: 9,
                      color: sortField === f ? C.orange : "#334155",
                      textTransform: "uppercase",
                      letterSpacing: "0.05em",
                      fontWeight: 700,
                      cursor: f ? "pointer" : "default",
                      whiteSpace: "nowrap",
                      borderBottom: `1px solid ${C.border}`,
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                    }}
                  >
                    <span style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
                      {h} {f && <ArrowUpDown size={10} />}
                    </span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sorted.length > 0 ? (
                sorted.map((r, i) => {
                  const d = depStyle[r.depository] || depStyle.Physical || depStyle.PHY;
                  return (
                    <tr key={i} style={{ borderBottom: `1px solid ${C.border}`, background: i % 2 === 0 ? "#FFFFFF" : C.bg }}>

                      <td style={{ padding: "10px 8px", fontSize: 12, color: C.text, fontWeight: 600, whiteSpace: "nowrap" }}>{r.company}</td>
                      <td style={{ padding: "10px 8px", fontSize: 11, color: C.sub, whiteSpace: "nowrap" }}>{r.batch}</td>

                      <td style={{ padding: "10px 8px" }}>
                        <span style={{ fontSize: 10, padding: "2px 8px", borderRadius: 12, background: d?.bg, color: d?.color, border: `1px solid ${d?.border}`, fontWeight: 700 }}>{r.depository}</span>
                      </td>
                      <td style={{ padding: "10px 8px", fontSize: 12, color: C.text, fontWeight: 800, textAlign: "right" }}>{r.total?.toLocaleString()}</td>
                      <td style={{ padding: "10px 8px", fontSize: 11, color: C.green, fontWeight: 700, textAlign: "right" }}>{r.added?.toLocaleString()}</td>
                      <td style={{ padding: "10px 8px", fontSize: 11, color: C.red, fontWeight: 700, textAlign: "right" }}>{r.removed?.toLocaleString()}</td>
                      <td style={{ padding: "10px 8px", fontSize: 11, color: C.amber, fontWeight: 700, textAlign: "right" }}>{r.changed?.toLocaleString()}</td>
                      <td style={{ padding: "10px 8px", fontSize: 11, color: C.sub, textAlign: "right" }}>{r.unchanged?.toLocaleString()}</td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={8} style={{ padding: 40, textAlign: "center", color: C.muted, fontSize: 13 }}>
                    No summary data available for the selected filters
                  </td>
                </tr>
              )}
            </tbody>
            {sorted.length > 0 && (
              <tfoot>
                <tr style={{ borderTop: `2px solid ${C.border}`, background: "rgba(0,87,184,0.04)" }}>
                  <td style={{ padding: "13px 16px", fontSize: 13, color: C.orange, fontWeight: 800 }}>Total</td>
                  <td colSpan={2} />
                  <td style={{ padding: "13px 16px", fontSize: 13, color: C.text, fontWeight: 800, textAlign: "right" }}>{totals.total.toLocaleString()}</td>
                  <td style={{ padding: "13px 16px", fontSize: 12, color: C.green, fontWeight: 800, textAlign: "right" }}>{totals.added.toLocaleString()}</td>
                  <td style={{ padding: "13px 16px", fontSize: 12, color: C.red, fontWeight: 800, textAlign: "right" }}>{totals.removed.toLocaleString()}</td>
                  <td style={{ padding: "13px 16px", fontSize: 12, color: C.amber, fontWeight: 800, textAlign: "right" }}>{totals.changed.toLocaleString()}</td>
                  <td style={{ padding: "13px 16px", fontSize: 12, color: C.sub, fontWeight: 800, textAlign: "right" }}>{totals.unchanged.toLocaleString()}</td>
                </tr>
              </tfoot>
            )}
          </table>
        </div>
      </div>
    </div>
  );
};

export default InsiderTradingDataSource;
