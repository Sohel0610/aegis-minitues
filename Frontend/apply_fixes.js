const fs = require('fs');

const targetPath = 'C:\\Cognitbotz\\AEGIS_Servicenow\\Frontend\\src\\pages\\InsiderTrading\\EmployeeComplianceLedger.tsx';
let content = fs.readFileSync(targetPath, 'utf8');

// 1. Add useMemo
content = content.replace('import React, { useState, useEffect } from "react";', 'import React, { useState, useEffect, useMemo } from "react";');

// 2. Update useEffect for RAW_FEED
content = content.replace(
  `  useEffect(() => {
    if (activeMainTab === "RAW_FEED") {
      fetchRawFeed();
    }
  }, [rawSearch, rawFilterType, rawPage, activeMainTab]);`,
  `  useEffect(() => {
    if (activeMainTab === "RAW_FEED") {
      fetchRawFeed();
    }
  }, [rawSearch, rawFilterType, activeMainTab]);`
);

// 3. Update fetchRawFeed
content = content.replace(
  `  const fetchRawFeed = async () => {
    try {
      setLoadingRaw(true);
      const offset = (rawPage - 1) * limitPerPage;
      let url = \`/api/servicenow/raw-feed?limit=\${limitPerPage}&offset=\${offset}&type=\${rawFilterType}\`;
      if (rawSearch) {
        url += \`&search=\${encodeURIComponent(rawSearch)}\`;
      }
      
      const res = await fetch(url);
      if (!res.ok) throw new Error("Failed to fetch ServiceNow raw feed");
      const data = await res.json();
      setRawTickets(data.tickets || []);
      setRawTotalCount(data.count || 0);
    } catch (err) {`,
  `  const fetchRawFeed = async () => {
    try {
      setLoadingRaw(true);
      let url = \`/api/servicenow/raw-feed?limit=5000&offset=0&type=\${rawFilterType}\`;
      if (rawSearch) {
        url += \`&search=\${encodeURIComponent(rawSearch)}\`;
      }
      
      const res = await fetch(url);
      if (!res.ok) throw new Error("Failed to fetch ServiceNow raw feed");
      const data = await res.json();
      setRawTickets(data.tickets || []);
      setRawTotalCount(data.count || 0);
    } catch (err) {`
);

// 4. Add useMemo variables right after fetchRawFeed
const memoBlock = `
  const filteredRawTickets = useMemo(() => {
    return rawTickets.filter(t => t.date && t.date.trim() !== "");
  }, [rawTickets]);

  const paginatedTickets = useMemo(() => {
    const startIndex = (rawPage - 1) * limitPerPage;
    return filteredRawTickets.slice(startIndex, startIndex + limitPerPage);
  }, [filteredRawTickets, rawPage, limitPerPage]);

  const finalRawCount = filteredRawTickets.length;
`;
content = content.replace(
  `    } finally {
      setLoadingRaw(false);
    }
  };

  return (`,
  `    } finally {
      setLoadingRaw(false);
    }
  };
${memoBlock}
  return (`
);

// 5. Update RAW FEED headers to include PAN
content = content.replace(
  `                  <th style={{ padding: "14px 16px", textAlign: "left", fontSize: 9, color: "#334155", textTransform: "uppercase", fontWeight: 700 }}>Employee Details</th>
                  <th style={{ padding: "14px 16px", textAlign: "left", fontSize: 9, color: "#334155", textTransform: "uppercase", fontWeight: 700 }}>Fiscal Year</th>`,
  `                  <th style={{ padding: "14px 16px", textAlign: "left", fontSize: 9, color: "#334155", textTransform: "uppercase", fontWeight: 700 }}>Employee Details</th>
                  <th style={{ padding: "14px 16px", textAlign: "left", fontSize: 9, color: "#334155", textTransform: "uppercase", fontWeight: 700 }}>PAN</th>
                  <th style={{ padding: "14px 16px", textAlign: "left", fontSize: 9, color: "#334155", textTransform: "uppercase", fontWeight: 700 }}>Fiscal Year</th>`
);

// 6. Update table body rendering logic (removing child row and using paginatedTickets)
const targetBodyStart = `              <tbody>
                {loadingRaw ? (`;
// We will replace the entire map function down to the end of the map
const mapStart = `{rawTickets.map((ticket, index) => {`;
const mapEnd = `                        )}
                      </React.Fragment>
                    );
                  })
                )}
              </tbody>`;

const newMapBlock = `{paginatedTickets.map((ticket, index) => {
                    const srNo = (rawPage - 1) * limitPerPage + index + 1;
                    return (
                      <React.Fragment key={ticket.ritm_number}>
                        {/* Parent Row */}
                        <tr 
                          style={{ 
                            borderBottom: \`1px solid \${C.border}\`, 
                            background: index % 2 === 0 ? "#FFFFFF" : C.bg
                          }} 
                          className="hover:bg-slate-100 transition-colors"
                        >
                          <td style={{ padding: "12px 14px", fontSize: 11, color: C.sub }}>{srNo}</td>
                          <td style={{ padding: "12px 14px", fontSize: 12, fontWeight: 700, color: C.orange }}>
                            {ticket.ritm_number}
                          </td>
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
                          <td style={{ padding: "12px 14px" }}>
                            <div style={{ fontWeight: 700, fontSize: 12, color: C.text }}>{ticket.name || ""}</div>
                            <div style={{ fontSize: 10, color: C.sub }}>{ticket.email}</div>
                            {ticket.designation && (
                              <div style={{ fontSize: 9, color: C.muted, marginTop: 1 }}>
                                {ticket.designation} {ticket.employee_code ? \`(Code: \${ticket.employee_code})\` : ""}
                              </div>
                            )}
                          </td>
                          <td style={{ padding: "12px 14px", fontSize: 11, color: C.text }}>
                             {/* Mock PAN column since it is not in RawTicketItem model yet, but we will put it if available or empty string */}
                             {""}
                          </td>
                          <td style={{ padding: "12px 14px", fontSize: 11, color: C.text }}>
                            {ticket.fiscal_year ? ticket.fiscal_year : ""}
                          </td>
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
                              {formatState(ticket.state)}
                            </span>
                          </td>
                          <td style={{ padding: "12px 14px", fontSize: 11, color: C.sub, whiteSpace: "nowrap" }}>
                            <div style={{ display: "flex", alignItems: "center", gap: 5 }}>
                              <Calendar size={11} color={C.muted} />
                              <span>{ticket.date ? ticket.date.split(" ")[0] : ""}</span>
                            </div>
                          </td>
                        </tr>
                      </React.Fragment>
                    );
                  })
                )}
              </tbody>`;

const contentStartIndex = content.indexOf(mapStart);
const contentEndIndex = content.indexOf(mapEnd) + mapEnd.length;

if (contentStartIndex !== -1 && contentEndIndex !== -1) {
    content = content.substring(0, contentStartIndex) + newMapBlock + content.substring(contentEndIndex);
} else {
    console.error("Could not find table map block.");
}

// 7. Update Pagination controls to use finalRawCount
content = content.replace(
  `{rawTotalCount > limitPerPage && (`,
  `{finalRawCount > limitPerPage && (`
);

content = content.replace(
  `Showing <strong>{((rawPage - 1) * limitPerPage) + 1}</strong> to <strong>{Math.min(rawPage * limitPerPage, rawTotalCount)}</strong> of <strong>{rawTotalCount.toLocaleString()}</strong> tickets`,
  `Showing <strong>{((rawPage - 1) * limitPerPage) + 1}</strong> to <strong>{Math.min(rawPage * limitPerPage, finalRawCount)}</strong> of <strong>{finalRawCount.toLocaleString()}</strong> tickets`
);

content = content.replace(
  `disabled={rawPage * limitPerPage >= rawTotalCount || loadingRaw}`,
  `disabled={rawPage * limitPerPage >= finalRawCount || loadingRaw}`
);

content = content.replace(
  `background: rawPage * limitPerPage >= rawTotalCount ? "transparent" : "#FFF",`,
  `background: rawPage * limitPerPage >= finalRawCount ? "transparent" : "#FFF",`
);

content = content.replace(
  `color: rawPage * limitPerPage >= rawTotalCount ? C.muted : C.text,`,
  `color: rawPage * limitPerPage >= finalRawCount ? C.muted : C.text,`
);

content = content.replace(
  `cursor: rawPage * limitPerPage >= rawTotalCount ? "not-allowed" : "pointer",`,
  `cursor: rawPage * limitPerPage >= finalRawCount ? "not-allowed" : "pointer",`
);


fs.writeFileSync(targetPath, content);
console.log("Applied changes correctly");

