import { useState, useEffect } from "react";
import {
  Server,
  Search,
  CheckCircle,
  AlertTriangle,
  Loader2,
  AlertCircle,
} from "lucide-react";

// ── Color palette ────────────────────────
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
  COMPLIANT:        { color: C.green, bg: "rgba(0,201,138,0.1)",  border: "rgba(0,201,138,0.25)",  icon: CheckCircle,   label: "Compliant" },
  UNSANCTIONED:     { color: C.red,   bg: "rgba(99,102,241,0.1)", border: "rgba(99,102,241,0.25)", icon: AlertTriangle, label: "Unsanctioned" },
  VOLUME_BREACH:    { color: C.amber, bg: "rgba(247,148,29,0.1)", border: "rgba(247,148,29,0.25)", icon: AlertTriangle, label: "Volume Breach" },
  HOLDING_MISMATCH: { color: C.amber, bg: "rgba(247,148,29,0.1)", border: "rgba(247,148,29,0.25)", icon: AlertTriangle, label: "Mismatch" },
};

// ── Types ─────────────────────────────────────────────
interface ServiceNowRecord {
  id: number;
  pan_card: string;
  declared_name: string;
  source_type: string;
  declared_qty: number;
  shareholder_name: string;
  shareholder_company: string;
  shareholder_position: number;
  position_difference: number;
  computed_status: string;
}

interface RecordsResponse {
  records: ServiceNowRecord[];
  count: number;
}

const RECORDS_PER_PAGE = 15;

// ── Component ─────────────────────────────────────────────────────
const ServiceNowMasterData = () => {
  const [records, setRecords] = useState<ServiceNowRecord[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [batches, setBatches] = useState<string[]>([]);
  const [selectedBatch, setSelectedBatch] = useState<string>("");
  const [showUnchanged, setShowUnchanged] = useState<boolean>(false);

  useEffect(() => {
    fetchBatches();
  }, []);

  const fetchBatches = async () => {
    try {
      const res = await fetch("/api/servicenow/batches");
      if (res.ok) {
        const data = await res.json();
        setBatches(data.batches || []);
      }
    } catch (err) {
      console.error("Failed to fetch batches", err);
    }
  };

  // Debounce search input
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedSearch(searchTerm);
      setOffset(0);
    }, 400);
    return () => clearTimeout(handler);
  }, [searchTerm]);

  useEffect(() => {
    fetchRecords();
  }, [offset, debouncedSearch, selectedBatch, showUnchanged]);

  const fetchRecords = async () => {
    try {
      setLoading(true);
      setError(null);

      const qs = new URLSearchParams({
        limit: RECORDS_PER_PAGE.toString(),
        offset: offset.toString()
      });
      if (debouncedSearch) qs.append("search", debouncedSearch);
      if (selectedBatch) qs.append("batch", selectedBatch);
      if (showUnchanged) qs.append("show_unchanged", "true");

      const res = await fetch(`/api/servicenow/all-records?${qs.toString()}`);
      if (!res.ok) throw new Error("Failed to fetch records");

      const data: RecordsResponse = await res.json();
      setRecords(data.records || []);
      setTotal(data.count || 0);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load data");
    } finally {
      setLoading(false);
    }
  };

  const getStatusConfig = (status: string) => {
    return statusCfg[status?.toUpperCase()] || statusCfg.COMPLIANT;
  };

  return (
    <div style={{ padding: "28px 32px", background: C.bg, minHeight: "100%", fontFamily: "Adani, sans-serif" }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 24 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <div style={{ width: 46, height: 46, borderRadius: 13, background: `linear-gradient(135deg, ${C.blue}, #004488)`, display: "flex", alignItems: "center", justifyContent: "center", boxShadow: "0 4px 18px rgba(77,166,255,0.35)", flexShrink: 0 }}>
            <Server size={22} color="#fff" strokeWidth={2.5} />
          </div>
          <div>
            <h1 style={{ color: C.text, margin: 0, fontSize: 20, fontWeight: 700 }}>ServiceNow Audit Log</h1>
            <p style={{ color: C.sub, margin: "3px 0 0", fontSize: 13 }}>Complete list of all ServiceNow declarations and pre-clearances.</p>
          </div>
        </div>
      </div>

      {/* Table */}
      <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 14, overflow: "hidden", boxShadow: "0 1px 3px rgba(0,0,0,0.05)" }}>
        <div style={{ padding: "14px 20px", borderBottom: `1px solid ${C.border}`, display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, flexWrap: "wrap", background: "linear-gradient(90deg, rgba(77,166,255,0.04) 0%, transparent 100%)" }}>
          <div style={{ fontWeight: 600, color: C.text, fontSize: 14 }}>
            Total Records: {total.toLocaleString()}
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 7, padding: "7px 14px", borderRadius: 8, background: C.bg, border: `1px solid ${C.border}` }}>
              <Search size={13} color={C.muted} />
              <input
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search by PAN or name…"
                style={{ background: "transparent", border: "none", outline: "none", fontSize: 12, color: C.text, width: 200, fontFamily: "Adani" }}
              />
            </div>
            
            {/* Batch Filter Dropdown */}
            {batches.length > 0 && (
              <div style={{ display: "flex", alignItems: "center", gap: 7, padding: "7px 14px", borderRadius: 8, background: C.bg, border: `1px solid ${C.border}` }}>
                <select
                  value={selectedBatch}
                  onChange={(e) => { setSelectedBatch(e.target.value); setOffset(0); }}
                  style={{ background: "transparent", border: "none", outline: "none", fontSize: 12, color: C.text, fontFamily: "Adani", cursor: "pointer" }}
                >
                  <option value="">All Batches</option>
                  {batches.map(b => (
                    <option key={b} value={b}>{b}</option>
                  ))}
                </select>
              </div>
            )}
            {/* Show Unchanged Toggle */}
            <label style={{ display: "flex", alignItems: "center", gap: 6, cursor: "pointer", fontSize: 13, color: C.text, fontWeight: 500, fontFamily: "Adani" }}>
              <input
                type="checkbox"
                checked={showUnchanged}
                onChange={(e) => { setShowUnchanged(e.target.checked); setOffset(0); }}
                style={{ cursor: "pointer", accentColor: C.orange }}
              />
              Show Unchanged
            </label>
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
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ background: "rgba(0,87,184,0.04)" }}>
                  {["PAN", "Employee Name", "Source", "Batch", "Declared", "Actual", "Diff", "Status", "Company"].map((h) => (
                    <th key={h} style={{ padding: "10px 16px", textAlign: ["Declared", "Actual", "Diff"].includes(h) ? "right" : "left", fontSize: 10, color: "#334155", textTransform: "uppercase", letterSpacing: "0.07em", fontWeight: 700, whiteSpace: "nowrap", borderBottom: `1px solid ${C.border}` }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {records.length > 0 ? (
                  records.map((r, i) => {
                    const cfg = getStatusConfig(r.computed_status);
                    const Icon = cfg.icon;
                    return (
                      <tr key={r.id || i} style={{ borderBottom: `1px solid ${C.border}`, background: i % 2 === 0 ? "#FFFFFF" : C.bg }}>
                        <td style={{ padding: "12px 16px", fontSize: 12, color: C.blue, fontFamily: "monospace", fontWeight: 700, whiteSpace: "nowrap" }}>{r.pan_card?.trim() || "N/A"}</td>
                        <td style={{ padding: "10px 16px" }}>
                          <div style={{ fontSize: 12, color: C.text, fontWeight: 600, maxWidth: 200, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                            {r.declared_name || "—"}
                          </div>
                          <div style={{ fontSize: 10, color: C.sub, marginTop: 2, maxWidth: 200, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                            {r.shareholder_name || "—"}
                          </div>
                        </td>
                        <td style={{ padding: "12px 16px", fontSize: 11, color: C.muted, textTransform: "capitalize" }}>{r.source_type}</td>
                        <td style={{ padding: "12px 16px", fontSize: 11, color: C.sub, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{r.batch_name || "—"}</td>
                        <td style={{ padding: "12px 16px", fontSize: 12, color: C.sub, textAlign: "right" }}>
                          {(r.declared_qty ?? 0).toLocaleString()}
                        </td>
                        <td style={{ padding: "12px 16px", fontSize: 12, color: C.text, fontWeight: 700, textAlign: "right" }}>
                          {r.source_type === 'preclearance' 
                            ? Math.abs(r.position_difference ?? 0).toLocaleString() 
                            : (r.shareholder_position ?? 0).toLocaleString()}
                        </td>
                        <td style={{ padding: "12px 16px", textAlign: "right" }}>
                          {r.source_type === 'preclearance' ? (
                            (() => {
                              const diff = Math.abs(r.position_difference ?? 0) - (r.declared_qty ?? 0);
                              return (
                                <span style={{ fontSize: 12, fontWeight: 700, color: diff > 0 ? C.red : C.muted }}>
                                  {diff > 0 ? "+" : ""}{diff.toLocaleString()}
                                </span>
                              );
                            })()
                          ) : (
                            <span style={{ fontSize: 12, fontWeight: 700, color: (r.position_difference ?? 0) > 0 ? C.green : (r.position_difference ?? 0) < 0 ? C.red : C.muted }}>
                              {(r.position_difference ?? 0) > 0 ? "+" : ""}{(r.position_difference ?? 0).toLocaleString()}
                            </span>
                          )}
                        </td>
                        <td style={{ padding: "12px 16px" }}>
                          <span style={{ display: "inline-flex", alignItems: "center", gap: 5, fontSize: 11, padding: "3px 9px", borderRadius: 12, background: cfg.bg, color: cfg.color, border: `1px solid ${cfg.border}`, fontWeight: 700, whiteSpace: "nowrap" }}>
                            <Icon size={11} />{cfg.label}
                          </span>
                        </td>
                        <td style={{ padding: "12px 16px", fontSize: 11, color: C.muted, maxWidth: 180, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{r.shareholder_company || "—"}</td>
                      </tr>
                    );
                  })
                ) : (
                  <tr>
                    <td colSpan={9} style={{ padding: 40, textAlign: "center", color: C.muted, fontSize: 13 }}>No records found</td>
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
      </div>
    </div>
  );
};

export default ServiceNowMasterData;
