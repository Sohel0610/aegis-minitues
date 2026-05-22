import { useState, useEffect } from "react";
import {
  Loader2,
  Search,
  Contact,
  FileText,
  ShieldCheck,
  User,
  ArrowRight,
  TrendingUp,
  Inbox,
  Briefcase,
  Layers,
  Calendar,
  CreditCard,
  Building,
  CheckCircle2,
  Clock
} from "lucide-react";

// ── Color palette (consistent with ServiceNowReconciliation.tsx) ──
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

const EmployeeComplianceLedger = () => {
  const [employees, setEmployees] = useState<EmployeeLedgerItem[]>([]);
  const [selectedEmployee, setSelectedEmployee] = useState<EmployeeLedgerItem | null>(null);
  const [detailData, setDetailData] = useState<EmployeeDetailResponse | null>(null);
  
  const [search, setSearch] = useState("");
  const [loadingList, setLoadingList] = useState(true);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [detailTab, setDetailTab] = useState<"PRECLEARANCE" | "DECLARATION">("PRECLEARANCE");
  const [error, setError] = useState<string | null>(null);

  // Fetch employees list on mount and when search changes
  useEffect(() => {
    fetchEmployees();
  }, [search]);

  // Fetch details when selected employee changes
  useEffect(() => {
    if (selectedEmployee) {
      fetchEmployeeDetails(selectedEmployee.email);
    } else {
      setDetailData(null);
    }
  }, [selectedEmployee]);

  const fetchEmployees = async () => {
    try {
      setLoadingList(true);
      const url = search 
        ? `/api/servicenow/ledger?search=${encodeURIComponent(search)}&limit=100`
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
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
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
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* ── Left Side: Employee Directory (4 columns) ── */}
        <div className="lg:col-span-4 flex flex-col" style={{
          background: C.card,
          border: `1px solid ${C.border}`,
          borderRadius: 14,
          boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
          height: "680px",
          overflow: "hidden"
        }}>
          {/* Search bar */}
          <div style={{ padding: "16px 20px", borderBottom: `1px solid ${C.border}` }}>
            <div style={{ position: "relative", display: "flex", alignItems: "center" }}>
              <Search size={16} color={C.muted} style={{ position: "absolute", left: 12 }} />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
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

          {/* Employee Directory List */}
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
                      <ArrowRight size={12} color={isSelected ? C.orange : C.muted} style={{ transform: isSelected ? "translateX(2px)" : "none", transition: "transform 0.15s" }} />
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

        {/* ── Right Side: Detailed Profile & History Ledger (8 columns) ── */}
        <div className="lg:col-span-8 flex flex-col" style={{
          background: C.card,
          border: `1px solid ${C.border}`,
          borderRadius: 14,
          boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
          minHeight: "680px",
          position: "relative"
        }}>
          {!selectedEmployee ? (
            /* Empty State */
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
            /* Selected Employee Profile Ledger */
            <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
              
              {/* Employee Summary Card */}
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

                {/* KPI metrics */}
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

              {/* Sub tabs navigation */}
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
                    cursor: "pointer",
                    transition: "all 0.15s"
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
                    cursor: "pointer",
                    transition: "all 0.15s"
                  }}
                >
                  Self-Declarations ({selectedEmployee.declarations_count})
                </button>
              </div>

              {/* Ledger Tab Contents */}
              <div style={{ flex: 1, padding: "20px 24px", overflowY: "auto", maxHeight: "520px" }}>
                {loadingDetails ? (
                  <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "200px" }}>
                    <Loader2 size={24} color={C.orange} style={{ animation: "spin 1s linear infinite", marginBottom: 8 }} />
                    <span style={{ fontSize: 12, color: C.sub }}>Fetching records...</span>
                  </div>
                ) : detailTab === "PRECLEARANCE" ? (
                  
                  /* Preclearance list */
                  <div>
                    {!detailData || detailData.preclearances.length === 0 ? (
                      <div style={{ padding: 40, textAlign: "center", color: C.muted }}>
                        <Inbox size={24} style={{ margin: "0 auto 8px" }} />
                        <div style={{ fontSize: 12 }}>No pre-clearance records found for this employee.</div>
                      </div>
                    ) : (
                      detailData.preclearances.map((pc, idx) => (
                        <div key={pc.ritm_number} style={{
                          border: `1px solid ${C.border}`,
                          borderRadius: 10,
                          marginBottom: 16,
                          overflow: "hidden"
                        }}>
                          {/* Header of Preclearance card */}
                          <div style={{
                            padding: "10px 16px",
                            background: "rgba(0,102,179,0.02)",
                            borderBottom: `1px solid ${C.border}`,
                            display: "flex",
                            justifyContent: "space-between",
                            alignItems: "center",
                            flexWrap: "wrap",
                            gap: 8
                          }}>
                            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                              <span style={{ fontSize: 11, color: C.muted, fontWeight: 700 }}>#{idx + 1}</span>
                              <span style={{ fontWeight: 700, fontSize: 12, color: C.orange }}>{pc.ritm_number}</span>
                              <span style={{ fontSize: 10, color: C.sub }}>
                                {pc.fiscal_year ? `${pc.fiscal_year}` : ""} {pc.phase ? `(${pc.phase})` : ""}
                              </span>
                            </div>
                            
                            {/* Status badge */}
                            <span style={{
                              fontSize: 9,
                              fontWeight: 700,
                              textTransform: "uppercase",
                              padding: "2px 8px",
                              borderRadius: 12,
                              background: getStatusStyle(pc.state).bg,
                              color: getStatusStyle(pc.state).color
                            }}>
                              {pc.state || "Pending"}
                            </span>
                          </div>

                          {/* Nested trade details table */}
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
                  
                  /* Declaration list */
                  <div>
                    {!detailData || detailData.declarations.length === 0 ? (
                      <div style={{ padding: 40, textAlign: "center", color: C.muted }}>
                        <Inbox size={24} style={{ margin: "0 auto 8px" }} />
                        <div style={{ fontSize: 12 }}>No self-declarations found for this employee.</div>
                      </div>
                    ) : (
                      detailData.declarations.map((dec, idx) => (
                        <div key={dec.ritm_number} style={{
                          border: `1px solid ${C.border}`,
                          borderRadius: 10,
                          marginBottom: 16,
                          overflow: "hidden"
                        }}>
                          {/* Header of Declaration card */}
                          <div style={{
                            padding: "10px 16px",
                            background: "rgba(0,199,138,0.02)",
                            borderBottom: `1px solid ${C.border}`,
                            display: "flex",
                            justifyContent: "space-between",
                            alignItems: "center",
                            flexWrap: "wrap",
                            gap: 8
                          }}>
                            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                              <span style={{ fontSize: 11, color: C.muted, fontWeight: 700 }}>#{idx + 1}</span>
                              <span style={{ fontWeight: 700, fontSize: 12, color: C.green }}>{dec.ritm_number}</span>
                              <span style={{ fontSize: 10, color: C.sub }}>
                                {dec.fiscal_year ? `${dec.fiscal_year}` : ""} {dec.phase ? `(${dec.phase})` : ""}
                              </span>
                            </div>
                            
                            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                              {dec.declaration_date && (
                                <span style={{ fontSize: 10, color: C.sub, display: "flex", alignItems: "center", gap: 4 }}>
                                  <Calendar size={10} />
                                  {dec.declaration_date.split(" ")[0]}
                                </span>
                              )}
                              <span style={{
                                fontSize: 9,
                                fontWeight: 700,
                                textTransform: "uppercase",
                                padding: "2px 8px",
                                borderRadius: 12,
                                background: getStatusStyle(dec.state).bg,
                                color: getStatusStyle(dec.state).color
                              }}>
                                {dec.state || "Submitted"}
                              </span>
                            </div>
                          </div>

                          {/* Nested holdings table */}
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
    </div>
  );
};

export default EmployeeComplianceLedger;
