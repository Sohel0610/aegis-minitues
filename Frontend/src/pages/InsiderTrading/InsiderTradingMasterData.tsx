import { useState, useEffect } from "react";
import {
  Server,
  Search,
  CheckCircle,
  AlertTriangle,
  Clock,
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

const statusCfg: Record<string, { color: string; bg: string; border: string; icon: any; label: string }> = {
  ADDED: { color: C.green, bg: "rgba(0,201,138,0.1)", border: "rgba(0,201,138,0.25)", icon: CheckCircle, label: "Added" },
  REMOVED: { color: C.red, bg: "rgba(99,102,241,0.1)", border: "rgba(99,102,241,0.25)", icon: AlertTriangle, label: "Removed" },
  CHANGED: { color: C.amber, bg: "rgba(247,148,29,0.1)", border: "rgba(247,148,29,0.25)", icon: Clock, label: "Changed" },
  UNCHANGED: { color: C.muted, bg: "rgba(148,163,184,0.1)", border: "rgba(148,163,184,0.25)", icon: CheckCircle, label: "Unchanged" },
};

// ── Types (unchanged) ─────────────────────────────────────────────
interface InsiderRecord {
  id?: number;
  company?: string;
  batch?: string;
  depository?: string;
  pangir: string;
  name: string;
  email: string;
  position_latest: number;
  position_older: number;
  position_difference: number;
  status: string;
  source?: string;
}

interface RecordsResponse {
  records: InsiderRecord[];
  total: number;
  limit: number;
  offset: number;
}

const RECORDS_PER_PAGE = 15;

// ── Component ─────────────────────────────────────────────────────
const InsiderTradingMasterData = () => {
  const { filters, buildQuery } = useInsiderTradingFilters();
  const [records, setRecords] = useState<InsiderRecord[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [searchTerm, setSearchTerm] = useState("");
  const [counts, setCounts] = useState<Record<string, number>>({ ADDED: 0, REMOVED: 0, CHANGED: 0, UNCHANGED: 0, TOTAL: 0 });
  const [adaniOnly, setAdaniOnly] = useState(false);

  const [debouncedSearch, setDebouncedSearch] = useState("");

  // Debounce search input
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedSearch(searchTerm);
      setOffset(0);
    }, 400);
    return () => clearTimeout(handler);
  }, [searchTerm]);

  // Refetch whenever global filters or status changes
  useEffect(() => {
    setOffset(0);
    fetchCounts();
  }, [filters.company, filters.batch, filters.depository, adaniOnly]);

  useEffect(() => {
    fetchRecords();
  }, [filters.company, filters.batch, filters.depository, statusFilter, offset, debouncedSearch, adaniOnly]);

  const fetchCounts = async () => {
    try {
      const extra: Record<string, string | number | boolean> = {};
      if (adaniOnly) extra.adani_only = true;
      const qs = buildQuery(extra);
      const res = await fetch(`/api/insider-trading/counts${qs}`);
      if (res.ok) {
        const data = await res.json();
        setCounts(data);
      }
    } catch (err) {
      console.error("Error fetching counts:", err);
    }
  };

  const fetchRecords = async () => {
    try {
      setLoading(true);
      setError(null);

      const extra: Record<string, string | number | boolean> = { limit: RECORDS_PER_PAGE, offset };
      if (statusFilter) extra.status = statusFilter;
      if (debouncedSearch) extra.search = debouncedSearch;
      if (adaniOnly) extra.adani_only = true;

      const qs = buildQuery(extra);
      const res = await fetch(`/api/insider-trading/records${qs}`);
      if (!res.ok) throw new Error("Failed to fetch records");

      const data: RecordsResponse = await res.json();
      setRecords(data.records || []);
      setTotal(data.total || 0);
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

  const getStatusConfig = (status: string) => {
    return statusCfg[status?.toUpperCase()] || statusCfg.UNCHANGED;
  };

  // Backend already filters by search term, so we just use the returned records
  const displayedRecords = records;

  const totalPages = Math.ceil(total / RECORDS_PER_PAGE);
  const currentPage = Math.floor(offset / RECORDS_PER_PAGE) + 1;

  const statusButtons = [
    { key: "", label: "All", count: counts.TOTAL || 0 },
    { key: "ADDED", label: "Added", count: counts.ADDED || 0 },
    { key: "REMOVED", label: "Removed", count: counts.REMOVED || 0 },
    { key: "CHANGED", label: "Changed", count: counts.CHANGED || 0 },
    { key: "UNCHANGED", label: "Unchanged", count: counts.UNCHANGED || 0 },
  ];

  return (
    <div style={{ padding: "28px 32px", background: C.bg, minHeight: "100%", fontFamily: "Adani, sans-serif" }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 24 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <div style={{ width: 46, height: 46, borderRadius: 13, background: `linear-gradient(135deg, ${C.amber}, #b85c00)`, display: "flex", alignItems: "center", justifyContent: "center", boxShadow: "0 4px 18px rgba(247,148,29,0.35)", flexShrink: 0 }}>
            <Server size={22} color="#fff" strokeWidth={2.5} />
          </div>
          <div>
            <h1 style={{ color: C.text, margin: 0, fontSize: 20, fontWeight: 700 }}>Master Data</h1>
            <p style={{ color: C.sub, margin: "3px 0 0", fontSize: 13 }}>Individual shareholder records — showing {RECORDS_PER_PAGE} records per page</p>
          </div>
        </div>

      </div>

      {/* Global filter bar */}
      <InsiderTradingFilterBar />

      {/* Stat cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3.5 mb-6">
        {statusButtons.map((sb) => {
          const isActive = statusFilter === sb.key;
          const cfg = sb.key === "" ? { color: C.text, bg: C.card, border: C.border } : { color: statusCfg[sb.key]?.color || C.text, bg: statusCfg[sb.key]?.bg || C.card, border: statusCfg[sb.key]?.border || C.border };
          return (
            <button
              key={sb.key}
              onClick={() => { setStatusFilter(sb.key); setOffset(0); }}
              style={{
                background: isActive ? cfg.bg : C.card,
                border: `1px solid ${isActive ? cfg.border : C.border}`,
                borderRadius: 12,
                padding: "16px 18px",
                cursor: "pointer",
                textAlign: "left",
                transition: "all 0.15s",
                boxShadow: isActive ? "0 2px 8px rgba(0,0,0,0.08)" : "0 1px 3px rgba(0,0,0,0.05)",
                fontFamily: "Adani, sans-serif",
              }}
            >
              <div style={{ fontSize: 26, color: cfg.color, fontWeight: 800, letterSpacing: "-0.03em" }}>{sb.count.toLocaleString()}</div>
              <div style={{ fontSize: 11, color: C.muted, marginTop: 4, textTransform: "capitalize", fontWeight: 500 }}>
                {sb.key === "" ? "Total Records" : `${sb.label} Investors`}
              </div>
            </button>
          );
        })}
      </div>

      {/* Table */}
      <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 14, overflow: "hidden", boxShadow: "0 1px 3px rgba(0,0,0,0.05)" }}>
        <div style={{ padding: "14px 20px", borderBottom: `1px solid ${C.border}`, display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, flexWrap: "wrap", background: "linear-gradient(90deg, rgba(247,148,29,0.04) 0%, transparent 100%)" }}>
          <div style={{ display: "flex", gap: 5 }}>
            {statusButtons.map((sb) => {
              const isActive = statusFilter === sb.key;
              const cfg = sb.key === "" ? { color: C.sub } : { color: statusCfg[sb.key]?.color || C.sub };
              return (
                <button
                  key={sb.key}
                  onClick={() => { setStatusFilter(sb.key); setOffset(0); }}
                  style={{
                    padding: "5px 12px",
                    borderRadius: 7,
                    border: "none",
                    cursor: "pointer",
                    fontSize: 11,
                    fontWeight: 700,
                    fontFamily: "Adani",
                    background: isActive ? (sb.key === "" ? "rgba(255,255,255,0.1)" : statusCfg[sb.key]?.bg || "transparent") : "transparent",
                    color: cfg.color,
                    textTransform: "capitalize",
                  }}
                >
                  {sb.label}
                </button>
              );
            })}
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <button
              onClick={() => setAdaniOnly(!adaniOnly)}
              style={{
                display: "flex", alignItems: "center", gap: 6,
                padding: "7px 14px", borderRadius: 8, border: "none", cursor: "pointer",
                fontSize: 12, fontWeight: 700, fontFamily: "Adani, sans-serif",
                background: adaniOnly ? "linear-gradient(135deg, #0057B8, #003087)" : C.bg,
                color: adaniOnly ? "#fff" : C.text,
                border: adaniOnly ? "none" : `1px solid ${C.border}`,
                boxShadow: adaniOnly ? "0 4px 12px rgba(0,87,184,0.3)" : "none",
                transition: "all 0.2s"
              }}
            >
              <div style={{
                width: 16, height: 16, borderRadius: "50%", background: adaniOnly ? "#fff" : "transparent",
                border: adaniOnly ? "none" : `2px solid ${C.sub}`, display: "flex", alignItems: "center", justifyContent: "center"
              }}>
                {adaniOnly && <div style={{ width: 8, height: 8, borderRadius: "50%", background: "#0057B8" }} />}
              </div>
              Adani Employees Only
            </button>
            <div style={{ display: "flex", alignItems: "center", gap: 7, padding: "7px 14px", borderRadius: 8, background: C.bg, border: `1px solid ${C.border}` }}>
              <Search size={13} color={C.muted} />
              <input
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search by PAN or name…"
                style={{ background: "transparent", border: "none", outline: "none", fontSize: 12, color: C.text, width: 200, fontFamily: "Adani" }}
              />
            </div>
          </div>
        </div>

        {loading ? (
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", padding: "60px 0" }}>
            <Loader2 size={32} color={C.orange} style={{ animation: "spin 1s linear infinite" }} />
            <span style={{ marginLeft: 12, color: C.sub, fontSize: 14 }}>Loading records...</span>
          </div>
        ) : error ? (
          <div style={{ textAlign: "center", padding: "40px 0" }}>
            <AlertCircle size={32} color={C.red} style={{ marginBottom: 8 }} />
            <p style={{ color: C.red, fontSize: 13, marginBottom: 12 }}>{error}</p>
            <button onClick={fetchRecords} style={{ padding: "6px 16px", borderRadius: 7, border: `1px solid ${C.border}`, background: C.card, cursor: "pointer", fontSize: 12, fontFamily: "Adani", color: C.text }}>Retry</button>
          </div>
        ) : (
          <div style={{ overflowX: "auto", width: "100%" }}>
            <table style={{ width: "100%", minWidth: "1000px", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ background: "rgba(0,87,184,0.04)" }}>
                  {["PAN/GIR", "Name", "Pos. Older", "Pos. Latest", "Difference", "Status", "Company", "Depository"].map((h) => (
                    <th key={h} style={{ padding: "10px 8px", textAlign: ["Pos. Older", "Pos. Latest", "Difference"].includes(h) ? "right" : "left", fontSize: 9, color: "#334155", textTransform: "uppercase", letterSpacing: "0.05em", fontWeight: 700, whiteSpace: "nowrap", borderBottom: `1px solid ${C.border}` }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {displayedRecords.length > 0 ? (
                  displayedRecords.map((r, i) => {
                    const cfg = getStatusConfig(r.status);
                    const Icon = cfg.icon;
                    return (
                      <tr key={r.pangir || i} style={{ borderBottom: `1px solid ${C.border}`, background: i % 2 === 0 ? "#FFFFFF" : C.bg }}>
                        <td style={{ padding: "10px 8px", fontSize: 11, color: C.blue, fontFamily: "monospace", fontWeight: 700, whiteSpace: "nowrap" }}>{r.pangir?.trim() || "N/A"}</td>
                        <td style={{ padding: "10px 8px", fontSize: 11, color: C.text, whiteSpace: "nowrap" }}>{displayName(r)}</td>
                        <td style={{ padding: "10px 8px", fontSize: 11, color: C.sub, textAlign: "right" }}>{(r.position_older ?? 0).toLocaleString()}</td>
                        <td style={{ padding: "10px 8px", fontSize: 11, color: C.text, fontWeight: 700, textAlign: "right" }}>{(r.position_latest ?? 0).toLocaleString()}</td>
                        <td style={{ padding: "10px 8px", textAlign: "right" }}>
                          <span style={{ fontSize: 11, fontWeight: 700, color: (r.position_difference ?? 0) > 0 ? C.green : (r.position_difference ?? 0) < 0 ? C.red : C.muted }}>
                            {(r.position_difference ?? 0) > 0 ? "+" : ""}{(r.position_difference ?? 0).toLocaleString()}
                          </span>
                        </td>
                        <td style={{ padding: "10px 8px" }}>
                          <span style={{ display: "inline-flex", alignItems: "center", gap: 4, fontSize: 10, padding: "2px 7px", borderRadius: 12, background: cfg.bg, color: cfg.color, border: `1px solid ${cfg.border}`, fontWeight: 700, whiteSpace: "nowrap" }}>
                            <Icon size={10} />{cfg.label}
                          </span>
                        </td>
                        <td style={{ padding: "10px 8px", fontSize: 10, color: C.muted, whiteSpace: "nowrap" }}>{r.company || "—"}</td>
                        <td style={{ padding: "10px 8px", fontSize: 10, color: C.muted, whiteSpace: "nowrap" }}>{r.depository || "—"}</td>
                      </tr>
                    );
                  })
                ) : (
                  <tr>
                    <td colSpan={8} style={{ padding: 40, textAlign: "center", color: C.muted, fontSize: 13 }}>No records found</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {!loading && !error && total > RECORDS_PER_PAGE && (
          <div style={{ padding: "12px 20px", borderTop: `1px solid ${C.border}`, display: "flex", justifyContent: "space-between", alignItems: "center", background: C.bg }}>
            <span style={{ fontSize: 12, color: C.muted }}>
              Showing {offset + 1}–{Math.min(offset + RECORDS_PER_PAGE, total)} of {total.toLocaleString()} records
            </span>
            <div style={{ display: "flex", gap: 5 }}>
              <button
                disabled={offset === 0}
                onClick={() => setOffset(Math.max(0, offset - RECORDS_PER_PAGE))}
                style={{
                  padding: "6px 14px", borderRadius: 6, border: `1px solid ${C.border}`,
                  cursor: offset === 0 ? "default" : "pointer", fontSize: 12, fontFamily: "Adani",
                  background: C.card, color: offset === 0 ? C.muted : C.text, fontWeight: 600,
                  opacity: offset === 0 ? 0.5 : 1,
                }}
              >
                Previous
              </button>
              <button
                disabled={offset + RECORDS_PER_PAGE >= total}
                onClick={() => setOffset(offset + RECORDS_PER_PAGE)}
                style={{
                  padding: "6px 14px", borderRadius: 6, border: `1px solid ${C.border}`,
                  cursor: offset + RECORDS_PER_PAGE >= total ? "default" : "pointer", fontSize: 12, fontFamily: "Adani",
                  background: C.card, color: offset + RECORDS_PER_PAGE >= total ? C.muted : C.text, fontWeight: 600,
                  opacity: offset + RECORDS_PER_PAGE >= total ? 0.5 : 1,
                }}
              >
                Next
              </button>
            </div>
          </div>
        )}

        {/* Footer when not paginating */}
        {!loading && !error && total <= RECORDS_PER_PAGE && (
          <div style={{ padding: "12px 20px", borderTop: `1px solid ${C.border}`, display: "flex", justifyContent: "space-between", alignItems: "center", background: C.bg }}>
            <span style={{ fontSize: 12, color: C.muted }}>Showing {displayedRecords.length} of {total} records</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default InsiderTradingMasterData;