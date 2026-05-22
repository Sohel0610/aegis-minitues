import { useState, useEffect } from "react";
import {
  Loader2,
  Search,
  Contact,
  Inbox,
  Briefcase,
  Layers,
  Calendar,
  User,
  ArrowRight,
  ChevronLeft,
  ChevronRight,
  Filter,
  ChevronDown,
  ChevronUp
} from "lucide-react";

// ── Color palette ──
const C = {
  bg: "#F8FAFB",
  card: "#FFFFFF",
  border: "rgba(0,0,0,0.08)",
  orange: "#0066B3", // Corporate Adani Blue
  blue: "#4DA6FF",
  green: "#00C98A",
  red: "#6366F1",
  amber: "#F7941D",
  text: "#1E293B",
  sub: "#64748B",
  muted: "#94A3B8",
};

interface EmployeeLedgerItem {
  email: string;
  name: string;
  employee_code: string;
  designation: string;
  declarations_count: number;
  preclearances_count: number;
}

interface DeclarationDetail {
  ritm_number: string;
  declaration_date: string | null;
  phase: string | null;
  fiscal_year: string | null;
  state: string | null;
  holdings: Array<{
    name: string;
    relationship: string;
    pan_card: string;
    company_name: string;
    declared_quantity: number;
  }>;
}

interface PreclearanceDetail {
  ritm_number: string;
  phase: string | null;
  fiscal_year: string | null;
  state: string | null;
  details: Array<{
    name: string;
    relationship: string;
    pan_card: string;
    approved_quantity: number;
  }>;
}

interface EmployeeDetailResponse {
  email: string;
  declarations: DeclarationDetail[];
  preclearances: PreclearanceDetail[];
}

interface RawTicketItem {
  ticket_type: "Declaration" | "Pre-clearance";
  ritm_number: string;
  name: string;
  email: string;
  employee_code: string | null;
  designation: string | null;
  state: string | null;
  fiscal_year: string | null;
  phase: string | null;
  date: string | null;
}

const EmployeeComplianceLedger = () => {
  // Main Top-Level Tab State
  const [activeMainTab, setActiveMainTab] = useState<"AUDITED_LEDGER" | "RAW_FEED">("AUDITED_LEDGER");

  // ── Tab 1: Audited Ledger States ──
  const [employees, setEmployees] = useState<EmployeeLedgerItem[]>([]);
  const [selectedEmployee, setSelectedEmployee] = useState<EmployeeLedgerItem | null>(null);
  const [detailData, setDetailData] = useState<EmployeeDetailResponse | null>(null);
  const [ledgerSearch, setLedgerSearch] = useState("");
  const [loadingList, setLoadingList] = useState(true);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [detailTab, setDetailTab] = useState<"PRECLEARANCE" | "DECLARATION">("PRECLEARANCE");

  // ── Tab 2: Raw Feed States ──
  const [rawTickets, setRawTickets] = useState<RawTicketItem[]>([]);
  const [rawTotalCount, setRawTotalCount] = useState(0);
  const [rawSearch, setRawSearch] = useState("");
  const [rawFilterType, setRawFilterType] = useState<"ALL" | "DECLARATION" | "PRECLEARANCE">("ALL");
  const [rawPage, setRawPage] = useState(1);
  const [loadingRaw, setLoadingRaw] = useState(false);
  const limitPerPage = 20;

  // Raw feed row expansion states
  const [expandedRitm, setExpandedRitm] = useState<string | null>(null);
  const [ritmDetails, setRitmDetails] = useState<any>(null);
  const [loadingRitm, setLoadingRitm] = useState(false);

  const [error, setError] = useState<string | null>(null);

  // Fetch employee list for Audited Ledger when tab active & search changes
  useEffect(() => {
    if (activeMainTab === "AUDITED_LEDGER") {
      fetchEmployees();
    }
  }, [ledgerSearch, activeMainTab]);

  // Fetch selected employee details
  useEffect(() => {
    if (activeMainTab === "AUDITED_LEDGER" && selectedEmployee) {
      fetchEmployeeDetails(selectedEmployee.email);
    } else {
      setDetailData(null);
    }
  }, [selectedEmployee, activeMainTab]);

  // Fetch Raw Feed when tab active, search, type filter, or page changes
  useEffect(() => {
    if (activeMainTab === "RAW_FEED") {
      fetchRawFeed();
    }
  }, [rawSearch, rawFilterType, rawPage, activeMainTab]);

  // Reset pagination when search or filters change on Raw Feed
  useEffect(() => {
    setRawPage(1);
    setExpandedRitm(null);
    setRitmDetails(null);
  }, [rawSearch, rawFilterType]);

  const fetchEmployees = async () => {
    try {
      setLoadingList(true);
      const url = ledgerSearch 
        ? `/api/servicenow/ledger?search=${encodeURIComponent(ledgerSearch)}&limit=100`
        : `/api/servicenow/ledger?limit=100`;
      
      const res = await fetch(url);
      if (!res.ok) throw new Error("Failed to fetch employee list");
      const data = await res.json();
      setEmployees(data.employees || []);
    } catch (err) {
      console.error(err);
      setError("Failed to load employees list.");
    } finally {
      setLoadingList(false);
    }
  };

  const fetchEmployeeDetails = async (email: string) => {
    try {
      setLoadingDetails(true);
      setError(null);
      const res = await fetch(`/api/servicenow/ledger/details?email=${encodeURIComponent(email)}`);
      if (!res.ok) throw new Error("Failed to fetch compliance details");
      const data = await res.json();
      setDetailData(data);
    } catch (err) {
      console.error(err);
      setError("Failed to load employee details.");
    } finally {
      setLoadingDetails(false);
    }
  };

  const fetchRawFeed = async () => {
    try {
      setLoadingRaw(true);
      const offset = (rawPage - 1) * limitPerPage;
      let url = `/api/servicenow/raw-feed?limit=${limitPerPage}&offset=${offset}&type=${rawFilterType}`;
      if (rawSearch) {
        url += `&search=${encodeURIComponent(rawSearch)}`;
      }
      
      const res = await fetch(url);
      if (!res.ok) throw new Error("Failed to fetch ServiceNow raw feed");
      const data = await res.json();
      setRawTickets(data.tickets || []);
      setRawTotalCount(data.count || 0);
    } catch (err) {
      console.error(err);
      setError("Failed to load raw ServiceNow feed.");
    } finally {
      setLoadingRaw(false);
    }
  };

  const handleRowClick = async (ritm: string) => {
    if (expandedRitm === ritm) {
      setExpandedRitm(null);
      setRitmDetails(null);
      return;
    }
    setExpandedRitm(ritm);
    setLoadingRitm(true);
    setRitmDetails(null);
    try {
      const res = await fetch(`/api/servicenow/ticket/details?ritm=${encodeURIComponent(ritm)}`);
      if (res.ok) {
        const data = await res.json();
        setRitmDetails(data);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingRitm(false);
    }
  };

  const getStatusStyle = (state: string | null) => {
    const s = (state || "").toLowerCase();
    if (s.includes("complete") || s.includes("approved")) {
      return { bg: "rgba(0,201,138,0.1)", color: C.green };
    }
    if (s.includes("progress") || s.includes("pending")) {
      return { bg: "rgba(247,148,29,0.1)", color: C.amber };
    }
    return { bg: "rgba(148,163,184,0.1)", color: C.sub };
  };

  return (
    <div style={{ fontFamily: "Adani", color: C.text, minHeight: "80vh" }}>
      
      {/* ── Page Header ── */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: 24, borderBottom: `1px solid ${C.border}`, paddingBottom: 16 }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div style={{ width: 36, height: 36, borderRadius: "50%", background: "rgba(0,102,179,0.1)", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <Contact size={20} color={C.orange} />
            </div>
            <h1 style={{ fontSize: 24, fontWeight: 800, letterSpacing: "-0.02em" }}>Employee Compliance Ledger</h1>
          </div>
          <p style={{ color: C.sub, fontSize: 13, marginTop: 4 }}>
            Detailed audit trails of all ServiceNow pre-clearance requests and periodic declarations grouped by employee.
          </p>
        </div>

        {/* ── Top-Level Navigation Tabs ── */}
        <div style={{ display: "flex", gap: 6, background: "rgba(0,0,0,0.03)", padding: 4, borderRadius: 10 }}>
          <button
            onClick={() => setActiveMainTab("AUDITED_LEDGER")}
            style={{
              padding: "8px 16px",
              borderRadius: 8,
              border: "none",
              cursor: "pointer",
              fontSize: 12,
              fontWeight: 700,
              background: activeMainTab === "AUDITED_LEDGER" ? "#FFFFFF" : "transparent",
              color: activeMainTab === "AUDITED_LEDGER" ? C.orange : C.sub,
              boxShadow: activeMainTab === "AUDITED_LEDGER" ? "0 1px 3px rgba(0,0,0,0.08)" : "none",
              transition: "all 0.15s"
            }}
          >
            Compliance Ledger (Audited)
          </button>
          <button
            onClick={() => setActiveMainTab("RAW_FEED")}
            style={{
              padding: "8px 16px",
              borderRadius: 8,
              border: "none",
              cursor: "pointer",
              fontSize: 12,
              fontWeight: 700,
              background: activeMainTab === "RAW_FEED" ? "#FFFFFF" : "transparent",
              color: activeMainTab === "RAW_FEED" ? C.orange : C.sub,
              boxShadow: activeMainTab === "RAW_FEED" ? "0 1px 3px rgba(0,0,0,0.08)" : "none",
              transition: "all 0.15s"
            }}
          >
            Raw ServiceNow Feed
          </button>
        </div>
      </div>

      {error && (
        <div style={{ padding: "12px 16px", background: "rgba(239,68,68,0.08)", color: "#EF4444", borderRadius: 8, fontSize: 12, marginBottom: 16 }}>
          {error}
        </div>
      )}

      {/* ── Tab 1: AUDITED LEDGER (Double layout) ── */}
      {activeMainTab === "AUDITED_LEDGER" && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Panel: Directory */}
          <div className="lg:col-span-4 flex flex-col" style={{
            background: C.card,
            border: `1px solid ${C.border}`,
            borderRadius: 14,
            boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
            height: "680px",
            overflow: "hidden"
          }}>
            <div style={{ padding: "16px 20px", borderBottom: `1px solid ${C.border}` }}>
              <div style={{ position: "relative", display: "flex", alignItems: "center" }}>
                <Search size={16} color={C.muted} style={{ position: "absolute", left: 12 }} />
                <input
                  type="text"
                  value={ledgerSearch}
                  onChange={(e) => setLedgerSearch(e.target.value)}
                  placeholder="Search name, code, or PAN..."
                  style={{
                    width: "100%",
                    padding: "9px 12px 9px 38px",
                    borderRadius: 10,
                    border: `1px solid ${C.border}`,
                    fontSize: 12,
                    outline: "none",
                    background: C.bg,
                    transition: "border 0.2s"
                  }}
                />
              </div>
            </div>

            <div style={{ flex: 1, overflowY: "auto", padding: "10px 14px" }}>
              {loadingList ? (
                <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "100%" }}>
                  <Loader2 size={24} color={C.orange} style={{ animation: "spin 1s linear infinite", marginBottom: 8 }} />
                  <span style={{ fontSize: 12, color: C.sub }}>Loading directory...</span>
                </div>
              ) : employees.length === 0 ? (
                <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "100%", color: C.muted }}>
                  <Inbox size={28} />
                  <span style={{ fontSize: 12, marginTop: 8 }}>No matching employees found</span>
                </div>
              ) : (
                employees.map((emp) => {
                  const isSelected = selectedEmployee?.email === emp.email;
                  return (
                    <div
                      key={emp.email}
                      onClick={() => setSelectedEmployee(emp)}
                      style={{
                        padding: "12px 14px",
                        borderRadius: 10,
                        cursor: "pointer",
                        marginBottom: 8,
                        background: isSelected ? "rgba(0,102,179,0.06)" : "transparent",
                        border: `1px solid ${isSelected ? "rgba(0,102,179,0.18)" : "transparent"}`,
                        transition: "all 0.15s ease",
                        position: "relative"
                      }}
                      className="hover:bg-slate-50"
                    >
                      {isSelected && (
                        <div style={{ position: "absolute", left: 0, top: "20%", bottom: "20%", width: 3, background: C.orange, borderRadius: "0 4px 4px 0" }} />
                      )}
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                        <div style={{ fontWeight: 700, fontSize: 13, color: C.text }}>{emp.name || "Unknown"}</div>
                        <ArrowRight size={12} color={isSelected ? C.orange : C.muted} />
                      </div>
                      
                      <div style={{ fontSize: 10, color: C.sub, marginTop: 2, textOverflow: "ellipsis", overflow: "hidden", whiteSpace: "nowrap" }}>
                        {emp.email}
                      </div>

                      <div style={{ display: "flex", flexWrap: "wrap", gap: 4, marginTop: 8 }}>
                        {emp.employee_code && (
                          <span style={{ fontSize: 9, background: "#F1F5F9", padding: "2px 6px", borderRadius: 4, color: C.sub }}>
                            Code: {emp.employee_code}
                          </span>
                        )}
                        {emp.declarations_count > 0 && (
                          <span style={{ fontSize: 9, background: "rgba(77,166,255,0.08)", padding: "2px 6px", borderRadius: 4, color: C.orange, fontWeight: 600 }}>
                            Decs: {emp.declarations_count}
                          </span>
                        )}
                        {emp.preclearances_count > 0 && (
                          <span style={{ fontSize: 9, background: "rgba(99,102,241,0.08)", padding: "2px 6px", borderRadius: 4, color: C.red, fontWeight: 600 }}>
                            Prcs: {emp.preclearances_count}
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>

          {/* Right Panel: Detail view */}
          <div className="lg:col-span-8 flex flex-col" style={{
            background: C.card,
            border: `1px solid ${C.border}`,
            borderRadius: 14,
            boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
            minHeight: "680px"
          }}>
            {!selectedEmployee ? (
              <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", flex: 1, padding: 60, textAlign: "center" }}>
                <div style={{ width: 64, height: 64, borderRadius: "50%", background: C.bg, display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 16 }}>
                  <Contact size={28} color={C.muted} />
                </div>
                <h3 style={{ fontSize: 15, fontWeight: 700, color: C.text }}>No Employee Selected</h3>
                <p style={{ fontSize: 12, color: C.sub, maxWidth: 300, marginTop: 6, lineHeight: 1.5 }}>
                  Please select an employee from the left panel to inspect their detailed ServiceNow disclosures and pre-clearance ledger.
                </p>
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
                <div style={{
                  padding: "20px 24px",
                  borderBottom: `1px solid ${C.border}`,
                  background: "linear-gradient(90deg, rgba(0,102,179,0.03) 0%, transparent 100%)",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  flexWrap: "wrap",
                  gap: 16
                }}>
                  <div>
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <span style={{ fontSize: 18, fontWeight: 800 }}>{selectedEmployee.name || "Unknown"}</span>
                      <span style={{ fontSize: 10, background: "rgba(0,102,179,0.1)", color: C.orange, padding: "2px 8px", borderRadius: 12, fontWeight: 700 }}>
                        Active compliance profile
                      </span>
                    </div>
                    
                    <div style={{ display: "flex", gap: 14, flexWrap: "wrap", marginTop: 8 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 11, color: C.sub }}>
                        <Briefcase size={12} color={C.muted} />
                        <span>{selectedEmployee.designation || "N/A"}</span>
                      </div>
                      <div style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 11, color: C.sub }}>
                        <Layers size={12} color={C.muted} />
                        <span>Code: {selectedEmployee.employee_code || "N/A"}</span>
                      </div>
                      <div style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 11, color: C.sub }}>
                        <User size={12} color={C.muted} />
                        <span>{selectedEmployee.email}</span>
                      </div>
                    </div>
                  </div>

                  <div style={{ display: "flex", gap: 8 }}>
                    <div style={{ border: `1px solid ${C.border}`, borderRadius: 8, padding: "8px 14px", background: "#fff", minWidth: 90, textAlign: "center" }}>
                      <div style={{ fontSize: 9, color: C.muted, textTransform: "uppercase", fontWeight: 700 }}>Preclearance</div>
                      <div style={{ fontSize: 18, fontWeight: 800, color: C.orange }}>{selectedEmployee.preclearances_count}</div>
                    </div>
                    <div style={{ border: `1px solid ${C.border}`, borderRadius: 8, padding: "8px 14px", background: "#fff", minWidth: 90, textAlign: "center" }}>
                      <div style={{ fontSize: 9, color: C.muted, textTransform: "uppercase", fontWeight: 700 }}>Declarations</div>
                      <div style={{ fontSize: 18, fontWeight: 800, color: C.green }}>{selectedEmployee.declarations_count}</div>
                    </div>
                  </div>
                </div>

                <div style={{ display: "flex", borderBottom: `1px solid ${C.border}`, padding: "0 24px" }}>
                  <button
                    onClick={() => setDetailTab("PRECLEARANCE")}
                    style={{
                      padding: "14px 20px 10px",
                      fontWeight: 700,
                      fontSize: 12,
                      border: "none",
                      borderBottom: `2px solid ${detailTab === "PRECLEARANCE" ? C.orange : "transparent"}`,
                      background: "transparent",
                      color: detailTab === "PRECLEARANCE" ? C.orange : C.sub,
                      cursor: "pointer"
                    }}
                  >
                    Pre-clearance Requests ({selectedEmployee.preclearances_count})
                  </button>
                  <button
                    onClick={() => setDetailTab("DECLARATION")}
                    style={{
                      padding: "14px 20px 10px",
                      fontWeight: 700,
                      fontSize: 12,
                      border: "none",
                      borderBottom: `2px solid ${detailTab === "DECLARATION" ? C.orange : "transparent"}`,
                      background: "transparent",
                      color: detailTab === "DECLARATION" ? C.orange : C.sub,
                      cursor: "pointer"
                    }}
                  >
                    Self-Declarations ({selectedEmployee.declarations_count})
                  </button>
                </div>

                <div style={{ flex: 1, padding: "20px 24px", overflowY: "auto", maxHeight: "520px" }}>
                  {loadingDetails ? (
                    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "200px" }}>
                      <Loader2 size={24} color={C.orange} style={{ animation: "spin 1s linear infinite", marginBottom: 8 }} />
                      <span style={{ fontSize: 12, color: C.sub }}>Fetching records...</span>
                    </div>
                  ) : detailTab === "PRECLEARANCE" ? (
                    <div>
                      {!detailData || detailData.preclearances.length === 0 ? (
                        <div style={{ padding: 40, textAlign: "center", color: C.muted }}>
                          <Inbox size={24} style={{ margin: "0 auto 8px" }} />
                          <div style={{ fontSize: 12 }}>No pre-clearance records found for this employee.</div>
                        </div>
                      ) : (
                        detailData.preclearances.map((pc, idx) => (
                          <div key={pc.ritm_number} style={{ border: `1px solid ${C.border}`, borderRadius: 10, marginBottom: 16, overflow: "hidden" }}>
                            <div style={{ padding: "10px 16px", background: "rgba(0,102,179,0.02)", borderBottom: `1px solid ${C.border}`, display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 8 }}>
                              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                                <span style={{ fontSize: 11, color: C.muted, fontWeight: 700 }}>#{idx + 1}</span>
                                <span style={{ fontWeight: 700, fontSize: 12, color: C.orange }}>{pc.ritm_number}</span>
                                <span style={{ fontSize: 10, color: C.sub }}>
                                  {pc.fiscal_year ? `${pc.fiscal_year}` : ""}
                                </span>
                              </div>
                              <span style={{ fontSize: 9, fontWeight: 700, textTransform: "uppercase", padding: "2px 8px", borderRadius: 12, background: getStatusStyle(pc.state).bg, color: getStatusStyle(pc.state).color }}>
                                {pc.state || "Pending"}
                              </span>
                            </div>

                            <div style={{ overflowX: "auto" }}>
                              <table style={{ width: "100%", borderCollapse: "collapse", minWidth: "500px" }}>
                                <thead>
                                  <tr style={{ background: "rgba(0,0,0,0.02)", borderBottom: `1px solid ${C.border}` }}>
                                    <th style={{ padding: "6px 12px", fontSize: 9, color: C.sub, fontWeight: 700, textAlign: "left", width: 50 }}>SR</th>
                                    <th style={{ padding: "6px 12px", fontSize: 9, color: C.sub, fontWeight: 700, textAlign: "left" }}>Beneficiary</th>
                                    <th style={{ padding: "6px 12px", fontSize: 9, color: C.sub, fontWeight: 700, textAlign: "left" }}>Relation</th>
                                    <th style={{ padding: "6px 12px", fontSize: 9, color: C.sub, fontWeight: 700, textAlign: "left" }}>PAN Number</th>
                                    <th style={{ padding: "6px 12px", fontSize: 9, color: C.sub, fontWeight: 700, textAlign: "right" }}>Approved Volume</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {pc.details && pc.details.length > 0 ? (
                                    pc.details.map((d, sIdx) => (
                                      <tr key={sIdx} style={{ borderBottom: sIdx === pc.details.length - 1 ? "none" : `1px solid ${C.border}` }}>
                                        <td style={{ padding: "8px 12px", fontSize: 10, color: C.muted }}>{sIdx + 1}</td>
                                        <td style={{ padding: "8px 12px", fontSize: 11, fontWeight: 600 }}>{d.name}</td>
                                        <td style={{ padding: "8px 12px", fontSize: 10, color: C.sub, textTransform: "capitalize" }}>{d.relationship}</td>
                                        <td style={{ padding: "8px 12px", fontSize: 11, color: C.orange, fontFamily: "monospace", fontWeight: 700 }}>{d.pan_card || "N/A"}</td>
                                        <td style={{ padding: "8px 12px", fontSize: 11, fontWeight: 700, textAlign: "right", color: C.text }}>
                                          {d.approved_quantity ? parseInt(String(d.approved_quantity)).toLocaleString() : "0"}
                                        </td>
                                      </tr>
                                    ))
                                  ) : (
                                    <tr>
                                      <td colSpan={5} style={{ padding: "12px", textAlign: "center", fontSize: 10, color: C.muted }}>
                                        No trade target details stored.
                                      </td>
                                    </tr>
                                  )}
                                </tbody>
                              </table>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  ) : (
                    <div>
                      {!detailData || detailData.declarations.length === 0 ? (
                        <div style={{ padding: 40, textAlign: "center", color: C.muted }}>
                          <Inbox size={24} style={{ margin: "0 auto 8px" }} />
                          <div style={{ fontSize: 12 }}>No self-declarations found for this employee.</div>
                        </div>
                      ) : (
                        detailData.declarations.map((dec, idx) => (
                          <div key={dec.ritm_number} style={{ border: `1px solid ${C.border}`, borderRadius: 10, marginBottom: 16, overflow: "hidden" }}>
                            <div style={{ padding: "10px 16px", background: "rgba(0,199,138,0.02)", borderBottom: `1px solid ${C.border}`, display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 8 }}>
                              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                                <span style={{ fontSize: 11, color: C.muted, fontWeight: 700 }}>#{idx + 1}</span>
                                <span style={{ fontWeight: 700, fontSize: 12, color: C.green }}>{dec.ritm_number}</span>
                                <span style={{ fontSize: 10, color: C.sub }}>
                                  {dec.fiscal_year ? `${dec.fiscal_year}` : ""}
                                </span>
                              </div>
                              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                                {dec.declaration_date && (
                                  <span style={{ fontSize: 10, color: C.sub, display: "flex", alignItems: "center", gap: 4 }}>
                                    <Calendar size={10} />
                                    {dec.declaration_date.split(" ")[0]}
                                  </span>
                                )}
                                <span style={{ fontSize: 9, fontWeight: 700, textTransform: "uppercase", padding: "2px 8px", borderRadius: 12, background: getStatusStyle(dec.state).bg, color: getStatusStyle(dec.state).color }}>
                                  {dec.state || "Submitted"}
                                </span>
                              </div>
                            </div>

                            <div style={{ overflowX: "auto" }}>
                              <table style={{ width: "100%", borderCollapse: "collapse", minWidth: "500px" }}>
                                <thead>
                                  <tr style={{ background: "rgba(0,0,0,0.02)", borderBottom: `1px solid ${C.border}` }}>
                                    <th style={{ padding: "6px 12px", fontSize: 9, color: C.sub, fontWeight: 700, textAlign: "left", width: 50 }}>SR</th>
                                    <th style={{ padding: "6px 12px", fontSize: 9, color: C.sub, fontWeight: 700, textAlign: "left" }}>Beneficiary</th>
                                    <th style={{ padding: "6px 12px", fontSize: 9, color: C.sub, fontWeight: 700, textAlign: "left" }}>Relation</th>
                                    <th style={{ padding: "6px 12px", fontSize: 9, color: C.sub, fontWeight: 700, textAlign: "left" }}>PAN Number</th>
                                    <th style={{ padding: "6px 12px", fontSize: 9, color: C.sub, fontWeight: 700, textAlign: "left" }}>Target Company</th>
                                    <th style={{ padding: "6px 12px", fontSize: 9, color: C.sub, fontWeight: 700, textAlign: "right" }}>Declared Qty</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {dec.holdings && dec.holdings.length > 0 ? (
                                    dec.holdings.map((h, sIdx) => (
                                      <tr key={sIdx} style={{ borderBottom: sIdx === dec.holdings.length - 1 ? "none" : `1px solid ${C.border}` }}>
                                        <td style={{ padding: "8px 12px", fontSize: 10, color: C.muted }}>{sIdx + 1}</td>
                                        <td style={{ padding: "8px 12px", fontSize: 11, fontWeight: 600 }}>{h.name}</td>
                                        <td style={{ padding: "8px 12px", fontSize: 10, color: C.sub, textTransform: "capitalize" }}>{h.relationship}</td>
                                        <td style={{ padding: "8px 12px", fontSize: 11, color: C.orange, fontFamily: "monospace", fontWeight: 700 }}>{h.pan_card || "N/A"}</td>
                                        <td style={{ padding: "8px 12px" }}>
                                          <span style={{ fontSize: 9, background: "rgba(0,102,179,0.06)", color: C.orange, padding: "2px 6px", borderRadius: 4, fontWeight: 700 }}>
                                            {h.company_name}
                                          </span>
                                        </td>
                                        <td style={{ padding: "8px 12px", fontSize: 11, fontWeight: 700, textAlign: "right", color: C.text }}>
                                          {h.declared_quantity ? parseInt(String(h.declared_quantity)).toLocaleString() : "0"}
                                        </td>
                                      </tr>
                                    ))
                                  ) : (
                                    <tr>
                                      <td colSpan={6} style={{ padding: "16px", textAlign: "center", fontSize: 11, color: C.muted }}>
                                        No detailed holdings rows parsed for this declaration.
                                      </td>
                                    </tr>
                                  )}
                                </tbody>
                              </table>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── Tab 2: RAW SERVICENOW FEED (Flat ledger list) ── */}
      {activeMainTab === "RAW_FEED" && (
        <div style={{
          background: C.card,
          border: `1px solid ${C.border}`,
          borderRadius: 14,
          boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
          padding: "20px 24px",
          minHeight: "600px",
          display: "flex",
          flexDirection: "column"
        }}>
          
          {/* Filters & Actions bar */}
          <div style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: 16,
            marginBottom: 20
          }}>
            <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "center" }}>
              
              {/* Search Bar */}
              <div style={{ position: "relative", display: "flex", alignItems: "center" }}>
                <Search size={14} color={C.muted} style={{ position: "absolute", left: 12 }} />
                <input
                  type="text"
                  value={rawSearch}
                  onChange={(e) => setRawSearch(e.target.value)}
                  placeholder="Search raw tickets..."
                  style={{
                    width: 250,
                    padding: "7px 12px 7px 34px",
                    borderRadius: 8,
                    border: `1px solid ${C.border}`,
                    fontSize: 12,
                    outline: "none",
                    background: C.bg
                  }}
                />
              </div>

              {/* Type Filter Select */}
              <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "5px 12px", borderRadius: 8, border: `1px solid ${C.border}`, background: C.bg }}>
                <Filter size={12} color={C.muted} />
                <select
                  value={rawFilterType}
                  onChange={(e) => setRawFilterType(e.target.value as any)}
                  style={{
                    background: "transparent",
                    border: "none",
                    outline: "none",
                    fontSize: 11,
                    fontWeight: 700,
                    color: C.text,
                    cursor: "pointer"
                  }}
                >
                  <option value="ALL">All Ticket Types</option>
                  <option value="DECLARATION">Self-Declarations Only</option>
                  <option value="PRECLEARANCE">Pre-clearance Requests Only</option>
                </select>
              </div>

            </div>

            {/* Total matches count */}
            <div style={{ fontSize: 12, color: C.sub }}>
              Found <strong style={{ color: C.orange }}>{rawTotalCount.toLocaleString()}</strong> raw records in system database
            </div>
          </div>

          {/* Raw Records Table */}
          <div style={{ flex: 1, overflowX: "auto", border: `1px solid ${C.border}`, borderRadius: 10, background: "#FFF" }}>
            {loadingRaw ? (
              <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "100px 0" }}>
                <Loader2 size={32} color={C.orange} style={{ animation: "spin 1s linear infinite", marginBottom: 8 }} />
                <span style={{ fontSize: 13, color: C.sub }}>Fetching raw ServiceNow feed...</span>
              </div>
            ) : rawTickets.length === 0 ? (
              <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "100px 0", color: C.muted }}>
                <Inbox size={36} />
                <span style={{ fontSize: 13, marginTop: 8 }}>No raw tickets found in database.</span>
              </div>
            ) : (
              <table style={{ width: "100%", borderCollapse: "collapse", minWidth: "1000px" }}>
                <thead>
                  <tr style={{ background: "rgba(0,102,179,0.03)", borderBottom: `1px solid ${C.border}` }}>
                    <th style={{ padding: "10px 14px", fontSize: 9, color: C.text, fontWeight: 800, textTransform: "uppercase", letterSpacing: "0.05em", textAlign: "left", width: 50 }}>SR</th>
                    <th style={{ padding: "10px 14px", fontSize: 9, color: C.text, fontWeight: 800, textTransform: "uppercase", letterSpacing: "0.05em", textAlign: "left", width: 150 }}>RITM Number</th>
                    <th style={{ padding: "10px 14px", fontSize: 9, color: C.text, fontWeight: 800, textTransform: "uppercase", letterSpacing: "0.05em", textAlign: "left", width: 140 }}>Ticket Type</th>
                    <th style={{ padding: "10px 14px", fontSize: 9, color: C.text, fontWeight: 800, textTransform: "uppercase", letterSpacing: "0.05em", textAlign: "left" }}>Employee Details</th>
                    <th style={{ padding: "10px 14px", fontSize: 9, color: C.text, fontWeight: 800, textTransform: "uppercase", letterSpacing: "0.05em", textAlign: "left", width: 120 }}>Fiscal Year</th>
                    <th style={{ padding: "10px 14px", fontSize: 9, color: C.text, fontWeight: 800, textTransform: "uppercase", letterSpacing: "0.05em", textAlign: "left", width: 140 }}>State</th>
                    <th style={{ padding: "10px 14px", fontSize: 9, color: C.text, fontWeight: 800, textTransform: "uppercase", letterSpacing: "0.05em", textAlign: "left", width: 130 }}>Date Ingested</th>
                  </tr>
                </thead>
                <tbody>
                  {rawTickets.map((ticket, index) => {
                    const srNo = (rawPage - 1) * limitPerPage + index + 1;
                    const isExpanded = expandedRitm === ticket.ritm_number;
                    
                    return (
                      <React.Fragment key={ticket.ritm_number}>
                        {/* Parent Row */}
                        <tr 
                          onClick={() => handleRowClick(ticket.ritm_number)}
                          style={{ 
                            borderBottom: isExpanded ? "none" : `1px solid ${C.border}`, 
                            background: isExpanded ? "rgba(0,102,179,0.03)" : (index % 2 === 0 ? "#FFFFFF" : C.bg),
                            cursor: "pointer"
                          }} 
                          className="hover:bg-slate-100 transition-colors"
                        >
                          {/* Serial No */}
                          <td style={{ padding: "12px 14px", fontSize: 11, color: C.sub }}>{srNo}</td>
                          
                          {/* RITM Number */}
                          <td style={{ padding: "12px 14px", fontSize: 12, fontWeight: 700, color: C.orange }}>
                            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                              {isExpanded ? <ChevronUp size={14} color={C.orange} /> : <ChevronDown size={14} color={C.orange} />}
                              {ticket.ritm_number}
                            </div>
                          </td>
                          
                          {/* Ticket Type */}
                          <td style={{ padding: "12px 14px" }}>
                            <span style={{
                              fontSize: 9,
                              fontWeight: 700,
                              padding: "3px 8px",
                              borderRadius: 6,
                              background: ticket.ticket_type === "Declaration" ? "rgba(0,199,138,0.08)" : "rgba(99,102,241,0.08)",
                              color: ticket.ticket_type === "Declaration" ? C.green : C.red
                            }}>
                              {ticket.ticket_type}
                            </span>
                          </td>
                          
                          {/* Employee details */}
                          <td style={{ padding: "12px 14px" }}>
                            <div style={{ fontWeight: 700, fontSize: 12, color: C.text }}>{ticket.name || "N/A"}</div>
                            <div style={{ fontSize: 10, color: C.sub }}>{ticket.email}</div>
                            {ticket.designation && (
                              <div style={{ fontSize: 9, color: C.muted, marginTop: 1 }}>
                                {ticket.designation} {ticket.employee_code ? `(Code: ${ticket.employee_code})` : ""}
                              </div>
                            )}
                          </td>
                          
                          {/* Fiscal Year */}
                          <td style={{ padding: "12px 14px", fontSize: 11, color: C.text }}>
                            {ticket.fiscal_year ? ticket.fiscal_year : "N/A"}
                          </td>
                          
                          {/* State */}
                          <td style={{ padding: "12px 14px" }}>
                            <span style={{
                              fontSize: 9,
                              fontWeight: 700,
                              textTransform: "uppercase",
                              padding: "2px 8px",
                              borderRadius: 12,
                              background: getStatusStyle(ticket.state).bg,
                              color: getStatusStyle(ticket.state).color
                            }}>
                              {ticket.state || "Ingested"}
                            </span>
                          </td>
                          
                          {/* Date Ingested */}
                          <td style={{ padding: "12px 14px", fontSize: 11, color: C.sub, whiteSpace: "nowrap" }}>
                            <div style={{ display: "flex", alignItems: "center", gap: 5 }}>
                              <Calendar size={11} color={C.muted} />
                              <span>{ticket.date ? ticket.date.split(" ")[0] : "N/A"}</span>
                            </div>
                          </td>
                        </tr>

                        {/* Expandable Child Row */}
                        {isExpanded && (
                          <tr style={{ background: "rgba(0,102,179,0.015)", borderBottom: `1px solid ${C.border}` }}>
                            <td colSpan={7} style={{ padding: "12px 24px 20px" }}>
                              <div style={{
                                padding: "16px",
                                border: `1px solid ${C.border}`,
                                borderRadius: 10,
                                background: "#FFFFFF",
                                boxShadow: "inset 0 1px 3px rgba(0,0,0,0.02)"
                              }}>
                                <div style={{ fontSize: 12, fontWeight: 700, color: C.text, marginBottom: 12, display: "flex", alignItems: "center", gap: 6 }}>
                                  <Database size={13} color={C.orange} />
                                  <span>ServiceNow Raw Holdings / Details payload for {ticket.ritm_number}</span>
                                </div>

                                {loadingRitm ? (
                                  <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "12px 0" }}>
                                    <Loader2 size={16} color={C.orange} style={{ animation: "spin 1s linear infinite" }} />
                                    <span style={{ fontSize: 11, color: C.sub }}>Loading ticket items...</span>
                                  </div>
                                ) : !ritmDetails || !ritmDetails.details || ritmDetails.details.length === 0 ? (
                                  <div style={{ fontSize: 11, color: C.muted, padding: "6px 0" }}>
                                    No details or holdings found for this transaction.
                                  </div>
                                ) : (
                                  <div style={{ overflowX: "auto" }}>
                                    <table style={{ width: "100%", borderCollapse: "collapse" }}>
                                      <thead>
                                        <tr style={{ background: "rgba(0,0,0,0.02)", borderBottom: `1px solid ${C.border}` }}>
                                          <th style={{ padding: "6px 12px", fontSize: 9, color: C.sub, fontWeight: 700, textAlign: "left", width: 50 }}>SR</th>
                                          <th style={{ padding: "6px 12px", fontSize: 9, color: C.sub, fontWeight: 700, textAlign: "left" }}>Beneficiary</th>
                                          <th style={{ padding: "6px 12px", fontSize: 9, color: C.sub, fontWeight: 700, textAlign: "left" }}>Relationship</th>
                                          <th style={{ padding: "6px 12px", fontSize: 9, color: C.sub, fontWeight: 700, textAlign: "left" }}>PAN Card</th>
                                          {ticket.ticket_type === "Declaration" && (
                                            <th style={{ padding: "6px 12px", fontSize: 9, color: C.sub, fontWeight: 700, textAlign: "left" }}>Company</th>
                                          )}
                                          <th style={{ padding: "6px 12px", fontSize: 9, color: C.sub, fontWeight: 700, textAlign: "right" }}>
                                            {ticket.ticket_type === "Declaration" ? "Declared Quantity" : "Approved Quantity"}
                                          </th>
                                        </tr>
                                      </thead>
                                      <tbody>
                                        {ritmDetails.details.map((row: any, rIdx: number) => (
                                          <tr key={rIdx} style={{ borderBottom: rIdx === ritmDetails.details.length - 1 ? "none" : `1px solid ${C.border}` }}>
                                            <td style={{ padding: "8px 12px", fontSize: 10, color: C.muted }}>{rIdx + 1}</td>
                                            <td style={{ padding: "8px 12px", fontSize: 11, fontWeight: 600 }}>{row.name}</td>
                                            <td style={{ padding: "8px 12px", fontSize: 10, color: C.sub, textTransform: "capitalize" }}>{row.relationship}</td>
                                            <td style={{ padding: "8px 12px", fontSize: 11, color: C.orange, fontFamily: "monospace", fontWeight: 700 }}>{row.pan_card || "N/A"}</td>
                                            {ticket.ticket_type === "Declaration" && (
                                              <td style={{ padding: "8px 12px" }}>
                                                <span style={{ fontSize: 9, background: "rgba(0,102,179,0.06)", color: C.orange, padding: "2px 6px", borderRadius: 4, fontWeight: 700 }}>
                                                  {row.company_name}
                                                </span>
                                              </td>
                                            )}
                                            <td style={{ padding: "8px 12px", fontSize: 11, fontWeight: 700, textAlign: "right", color: C.text }}>
                                              {ticket.ticket_type === "Declaration" 
                                                ? (row.declared_quantity ? parseInt(String(row.declared_quantity)).toLocaleString() : "0")
                                                : (row.approved_quantity ? parseInt(String(row.approved_quantity)).toLocaleString() : "0")
                                              }
                                            </td>
                                          </tr>
                                        ))}
                                      </tbody>
                                    </table>
                                  </div>
                                )}
                              </div>
                            </td>
                          </tr>
                        )}
                      </React.Fragment>
                    );
                  })}
                </tbody>
              </table>
            )}
          </div>

          {/* Pagination Controls */}
          {rawTotalCount > limitPerPage && (
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 20 }}>
              <div style={{ fontSize: 11, color: C.sub }}>
                Showing <strong>{((rawPage - 1) * limitPerPage) + 1}</strong> to <strong>{Math.min(rawPage * limitPerPage, rawTotalCount)}</strong> of <strong>{rawTotalCount.toLocaleString()}</strong> tickets
              </div>
              
              <div style={{ display: "flex", gap: 8 }}>
                <button
                  disabled={rawPage === 1 || loadingRaw}
                  onClick={() => setRawPage(prev => Math.max(1, prev - 1))}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 4,
                    padding: "6px 12px",
                    borderRadius: 6,
                    border: `1px solid ${C.border}`,
                    background: rawPage === 1 ? "transparent" : "#FFF",
                    color: rawPage === 1 ? C.muted : C.text,
                    cursor: rawPage === 1 ? "not-allowed" : "pointer",
                    fontSize: 11,
                    fontWeight: 700
                  }}
                >
                  <ChevronLeft size={12} />
                  Prev
                </button>
                <button
                  disabled={rawPage * limitPerPage >= rawTotalCount || loadingRaw}
                  onClick={() => setRawPage(prev => prev + 1)}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 4,
                    padding: "6px 12px",
                    borderRadius: 6,
                    border: `1px solid ${C.border}`,
                    background: rawPage * limitPerPage >= rawTotalCount ? "transparent" : "#FFF",
                    color: rawPage * limitPerPage >= rawTotalCount ? C.muted : C.text,
                    cursor: rawPage * limitPerPage >= rawTotalCount ? "not-allowed" : "pointer",
                    fontSize: 11,
                    fontWeight: 700
                  }}
                >
                  Next
                  <ChevronRight size={12} />
                </button>
              </div>
            </div>
          )}

        </div>
      )}

    </div>
  );
};

export default EmployeeComplianceLedger;
