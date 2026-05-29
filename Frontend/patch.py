import sys

file_path = 'C:\\Cognitbotz\\AEGIS_Servicenow\\Frontend\\src\\pages\\InsiderTrading\\EmployeeComplianceLedger.tsx'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. useMemo
content = content.replace(
    'import React, { useState, useEffect } from "react";',
    'import React, { useState, useEffect, useMemo } from "react";'
)

# 2. useEffect for RAW_FEED
old_use_effect = """  useEffect(() => {
    if (activeMainTab === "RAW_FEED") {
      fetchRawFeed();
    }
  }, [rawSearch, rawFilterType, rawPage, activeMainTab]);"""
new_use_effect = """  useEffect(() => {
    if (activeMainTab === "RAW_FEED") {
      fetchRawFeed();
    }
  }, [rawSearch, rawFilterType, activeMainTab]);"""
content = content.replace(old_use_effect, new_use_effect)

# 3. fetchRawFeed and memos
old_fetch = """  const fetchRawFeed = async () => {
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
  };"""

new_fetch = """  const fetchRawFeed = async () => {
    try {
      setLoadingRaw(true);
      let url = `/api/servicenow/raw-feed?limit=5000&offset=0&type=${rawFilterType}`;
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

  const filteredRawTickets = useMemo(() => {
    return rawTickets.filter(t => t.date && t.date.trim() !== "");
  }, [rawTickets]);

  const paginatedTickets = useMemo(() => {
    const startIndex = (rawPage - 1) * limitPerPage;
    return filteredRawTickets.slice(startIndex, startIndex + limitPerPage);
  }, [filteredRawTickets, rawPage, limitPerPage]);

  const finalRawCount = filteredRawTickets.length;"""
content = content.replace(old_fetch, new_fetch)

# 4. Header PAN
old_th = """                    <th style={{ padding: "10px 14px", fontSize: 9, color: C.text, fontWeight: 800, textTransform: "uppercase", letterSpacing: "0.05em", textAlign: "left" }}>Employee Details</th>
                    <th style={{ padding: "10px 14px", fontSize: 9, color: C.text, fontWeight: 800, textTransform: "uppercase", letterSpacing: "0.05em", textAlign: "left", width: 120 }}>Fiscal Year</th>"""
new_th = """                    <th style={{ padding: "10px 14px", fontSize: 9, color: C.text, fontWeight: 800, textTransform: "uppercase", letterSpacing: "0.05em", textAlign: "left" }}>Employee Details</th>
                    <th style={{ padding: "10px 14px", fontSize: 9, color: C.text, fontWeight: 800, textTransform: "uppercase", letterSpacing: "0.05em", textAlign: "left", width: 100 }}>PAN</th>
                    <th style={{ padding: "10px 14px", fontSize: 9, color: C.text, fontWeight: 800, textTransform: "uppercase", letterSpacing: "0.05em", textAlign: "left", width: 120 }}>Fiscal Year</th>"""
content = content.replace(old_th, new_th)

# 5. Exact Table Body replacement using string replace
old_body_start = """                <tbody>
                  {rawTickets.map((ticket, index) => {"""
old_body_end = """                        )}
                      </React.Fragment>
                    );
                  })}
                </tbody>"""

start_idx = content.find(old_body_start)
end_idx = content.find(old_body_end, start_idx) + len(old_body_end)

if start_idx != -1 and end_idx != -1:
    body_replacement = """                <tbody>
                  {paginatedTickets.map((ticket, index) => {
                    const srNo = (rawPage - 1) * limitPerPage + index + 1;
                    return (
                      <tr 
                        key={ticket.ritm_number}
                        style={{ 
                          borderBottom: `1px solid ${C.border}`, 
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
                              {ticket.designation} {ticket.employee_code ? `(Code: ${ticket.employee_code})` : ""}
                            </div>
                          )}
                        </td>
                        <td style={{ padding: "12px 14px", fontSize: 11, color: C.text }}>
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
                    );
                  })}
                </tbody>"""
    content = content[:start_idx] + body_replacement + content[end_idx:]
else:
    print("Could not find table body markers")
    sys.exit(1)

# 6. Pagination controls count replacement
content = content.replace('{rawTotalCount > limitPerPage && (', '{finalRawCount > limitPerPage && (')
content = content.replace(
    'Showing <strong>{((rawPage - 1) * limitPerPage) + 1}</strong> to <strong>{Math.min(rawPage * limitPerPage, rawTotalCount)}</strong> of <strong>{rawTotalCount.toLocaleString()}</strong> tickets',
    'Showing <strong>{((rawPage - 1) * limitPerPage) + 1}</strong> to <strong>{Math.min(rawPage * limitPerPage, finalRawCount)}</strong> of <strong>{finalRawCount.toLocaleString()}</strong> tickets'
)
content = content.replace(
    'disabled={rawPage * limitPerPage >= rawTotalCount || loadingRaw}',
    'disabled={rawPage * limitPerPage >= finalRawCount || loadingRaw}'
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Patch applied")
