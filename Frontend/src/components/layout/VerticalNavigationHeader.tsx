import React, { useState, useRef, useEffect } from "react";
import { useVertical, Vertical, Company } from "@/contexts/VerticalContext";
import {
  Layers,
  Building2,
  Search,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Check,
  User,
  ShieldCheck,
  Building
} from "lucide-react";

const A = {
  blue: "#0057B8",
  navy: "#0F172A",
  muted: "#64748B",
  lightBg: "#F8FAFC",
  border: "#E2E8F0",
  orange: "#0066B3",
  brandGradient: "linear-gradient(135deg, #0057B8 0%, #0080D6 100%)",
};

export const VerticalNavigationHeader: React.FC = () => {
  const {
    verticals,
    selectedVertical,
    setSelectedVertical,
    companies,
    totalCompanies,
    selectedCompany,
    setSelectedCompany,
    searchQuery,
    setSearchQuery,
    page,
    setPage,
    pageSize,
    loadingVerticals,
    loadingCompanies,
  } = useVertical();

  const [isVertOpen, setIsVertOpen] = useState(false);
  const [isCompOpen, setIsCompOpen] = useState(false);

  const vertRef = useRef<HTMLDivElement>(null);
  const compRef = useRef<HTMLDivElement>(null);

  // Close dropdowns on click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (vertRef.current && !vertRef.current.contains(event.target as Node)) {
        setIsVertOpen(false);
      }
      if (compRef.current && !compRef.current.contains(event.target as Node)) {
        setIsCompOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const totalPages = Math.ceil(totalCompanies / pageSize) || 1;

  const handleVerticalSelect = (v: Vertical) => {
    setSelectedVertical(v);
    setIsVertOpen(false);
  };

  const handleCompanySelect = (c: Company) => {
    setSelectedCompany(c);
    setIsCompOpen(false);
  };

  return (
    <div
      style={{
        background: "#FFFFFF",
        borderBottom: `1px solid ${A.border}`,
        padding: "10px 24px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: 16,
        flexWrap: "wrap",
        boxShadow: "0 1px 3px rgba(0,0,0,0.03)",
        position: "sticky",
        top: 0,
        zIndex: 30,
      }}
    >
      {/* Left Group: Vertical & Company Selectors */}
      <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap", flex: 1, minWidth: 280 }}>
        
        {/* 1. VERTICAL DROPDOWN */}
        <div ref={vertRef} style={{ position: "relative" }}>
          <button
            onClick={() => {
              setIsVertOpen(!isVertOpen);
              setIsCompOpen(false);
            }}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              padding: "7px 14px",
              background: "rgba(0,102,179,0.06)",
              border: `1px solid rgba(0,102,179,0.2)`,
              borderRadius: 10,
              cursor: "pointer",
              transition: "all 0.15s ease",
            }}
          >
            <Layers size={16} color={A.orange} />
            <div style={{ textAlign: "left" }}>
              <div style={{ fontSize: 10, color: A.muted, fontWeight: 700, letterSpacing: "0.05em", textTransform: "uppercase" }}>
                Business Unit (Vertical)
              </div>
              <div style={{ fontSize: 13, color: A.navy, fontWeight: 600, display: "flex", alignItems: "center", gap: 6 }}>
                {loadingVerticals ? "Loading Verticals..." : selectedVertical ? selectedVertical.name : "Select Vertical"}
                {selectedVertical && (
                  <span style={{ fontSize: 10, background: A.orange, color: "#fff", padding: "1px 5px", borderRadius: 4, fontWeight: 700 }}>
                    {selectedVertical.code}
                  </span>
                )}
              </div>
            </div>
            <ChevronDown size={14} color={A.muted} style={{ marginLeft: 4, transform: isVertOpen ? "rotate(180deg)" : "none", transition: "transform 0.2s" }} />
          </button>

          {/* Vertical Dropdown Menu */}
          {isVertOpen && (
            <div
              style={{
                position: "absolute",
                top: "calc(100% + 6px)",
                left: 0,
                width: 280,
                maxHeight: 340,
                overflowY: "auto",
                background: "#FFFFFF",
                border: `1px solid ${A.border}`,
                borderRadius: 12,
                boxShadow: "0 10px 25px -5px rgba(0,0,0,0.1), 0 8px 10px -6px rgba(0,0,0,0.05)",
                zIndex: 100,
                padding: "6px",
              }}
            >
              <div style={{ fontSize: 11, fontWeight: 700, color: A.muted, padding: "8px 10px 4px", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                Select Business Unit ({verticals.length})
              </div>
              {verticals.map((v) => {
                const isSelected = selectedVertical?.id === v.id;
                return (
                  <button
                    key={v.id}
                    onClick={() => handleVerticalSelect(v)}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      width: "100%",
                      padding: "8px 10px",
                      borderRadius: 8,
                      border: "none",
                      background: isSelected ? "rgba(0,102,179,0.08)" : "transparent",
                      cursor: "pointer",
                      textAlign: "left",
                      marginBottom: 2,
                      transition: "background 0.15s",
                    }}
                  >
                    <span style={{ fontSize: 13, fontWeight: isSelected ? 600 : 400, color: isSelected ? A.orange : A.navy }}>
                      {v.name}
                    </span>
                    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                      <span style={{ fontSize: 10, background: isSelected ? A.orange : "#F1F5F9", color: isSelected ? "#fff" : A.muted, padding: "2px 6px", borderRadius: 4, fontWeight: 600 }}>
                        {v.code}
                      </span>
                      {isSelected && <Check size={14} color={A.orange} />}
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Separator icon */}
        <span style={{ color: A.border, fontSize: 16 }}>/</span>

        {/* 2. COMPANY DROPDOWN WITH SEARCH & PAGINATION */}
        <div ref={compRef} style={{ position: "relative" }}>
          <button
            onClick={() => {
              setIsCompOpen(!isCompOpen);
              setIsVertOpen(false);
            }}
            disabled={!selectedVertical}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              padding: "7px 14px",
              background: selectedCompany ? "rgba(15,23,42,0.04)" : "#FFFFFF",
              border: `1px solid ${selectedCompany ? "rgba(15,23,42,0.2)" : A.border}`,
              borderRadius: 10,
              cursor: selectedVertical ? "pointer" : "not-allowed",
              opacity: selectedVertical ? 1 : 0.6,
              transition: "all 0.15s ease",
            }}
          >
            <Building2 size={16} color={selectedCompany ? A.navy : A.muted} />
            <div style={{ textAlign: "left", maxWidth: 260 }}>
              <div style={{ fontSize: 10, color: A.muted, fontWeight: 700, letterSpacing: "0.05em", textTransform: "uppercase" }}>
                Company / Entity
              </div>
              <div style={{ fontSize: 13, color: A.navy, fontWeight: 600, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                {loadingCompanies ? "Loading Companies..." : selectedCompany ? selectedCompany.name : "Select Company"}
              </div>
            </div>
            <ChevronDown size={14} color={A.muted} style={{ marginLeft: 4, transform: isCompOpen ? "rotate(180deg)" : "none", transition: "transform 0.2s" }} />
          </button>

          {/* Company Search & Paginated Dropdown */}
          {isCompOpen && (
            <div
              style={{
                position: "absolute",
                top: "calc(100% + 6px)",
                left: 0,
                width: 380,
                maxHeight: 420,
                background: "#FFFFFF",
                border: `1px solid ${A.border}`,
                borderRadius: 12,
                boxShadow: "0 10px 25px -5px rgba(0,0,0,0.1), 0 8px 10px -6px rgba(0,0,0,0.05)",
                zIndex: 100,
                display: "flex",
                flexDirection: "column",
                overflow: "hidden",
              }}
            >
              {/* Search Header */}
              <div style={{ padding: "10px 12px", borderBottom: `1px solid ${A.border}`, background: "#FAFAFA" }}>
                <div style={{ position: "relative", display: "flex", alignItems: "center" }}>
                  <Search size={14} color={A.muted} style={{ position: "absolute", left: 10 }} />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => {
                      setSearchQuery(e.target.value);
                      setPage(1);
                    }}
                    placeholder={`Search ${totalCompanies} companies...`}
                    style={{
                      width: "100%",
                      padding: "6px 10px 6px 30px",
                      fontSize: 12,
                      border: `1px solid ${A.border}`,
                      borderRadius: 6,
                      outline: "none",
                      background: "#FFFFFF",
                    }}
                  />
                </div>
              </div>

              {/* Company List */}
              <div style={{ flex: 1, overflowY: "auto", padding: "4px 6px" }}>
                {loadingCompanies ? (
                  <div style={{ padding: 20, textAlign: "center", fontSize: 12, color: A.muted }}>
                    Loading companies...
                  </div>
                ) : companies.length === 0 ? (
                  <div style={{ padding: 20, textAlign: "center", fontSize: 12, color: A.muted }}>
                    No companies found matching "{searchQuery}"
                  </div>
                ) : (
                  companies.map((c) => {
                    const isSelected = selectedCompany?.id === c.id;
                    return (
                      <button
                        key={c.id}
                        onClick={() => handleCompanySelect(c)}
                        style={{
                          display: "flex",
                          flexDirection: "column",
                          alignItems: "flex-start",
                          width: "100%",
                          padding: "8px 10px",
                          borderRadius: 8,
                          border: "none",
                          background: isSelected ? "rgba(0,87,184,0.08)" : "transparent",
                          cursor: "pointer",
                          textAlign: "left",
                          marginBottom: 2,
                        }}
                      >
                        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", width: "100%" }}>
                          <span style={{ fontSize: 12.5, fontWeight: isSelected ? 600 : 500, color: isSelected ? A.blue : A.navy }}>
                            {c.name}
                          </span>
                          {isSelected && <Check size={14} color={A.blue} />}
                        </div>
                        {c.cin && (
                          <span style={{ fontSize: 10, color: A.muted, fontFamily: "monospace", marginTop: 2 }}>
                            CIN: {c.cin}
                          </span>
                        )}
                        {c.secretary_name && (
                          <div style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 10, color: A.muted, marginTop: 2 }}>
                            <User size={10} /> CS: {c.secretary_name}
                          </div>
                        )}
                      </button>
                    );
                  })
                )}
              </div>

              {/* Pagination Footer */}
              <div
                style={{
                  padding: "8px 12px",
                  borderTop: `1px solid ${A.border}`,
                  background: "#FAFAFA",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  fontSize: 11,
                  color: A.muted,
                }}
              >
                <span>
                  Page {page} of {totalPages} ({totalCompanies} total)
                </span>
                <div style={{ display: "flex", gap: 4 }}>
                  <button
                    disabled={page <= 1}
                    onClick={() => setPage(page - 1)}
                    style={{
                      padding: "3px 8px",
                      fontSize: 11,
                      border: `1px solid ${A.border}`,
                      borderRadius: 4,
                      background: page <= 1 ? "#F1F5F9" : "#FFFFFF",
                      cursor: page <= 1 ? "not-allowed" : "pointer",
                    }}
                  >
                    <ChevronLeft size={12} />
                  </button>
                  <button
                    disabled={page >= totalPages}
                    onClick={() => setPage(page + 1)}
                    style={{
                      padding: "3px 8px",
                      fontSize: 11,
                      border: `1px solid ${A.border}`,
                      borderRadius: 4,
                      background: page >= totalPages ? "#F1F5F9" : "#FFFFFF",
                      cursor: page >= totalPages ? "not-allowed" : "pointer",
                    }}
                  >
                    <ChevronRight size={12} />
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Right Badge: Active Scoping Context */}
      {selectedCompany && (
        <div style={{ display: "flex", alignItems: "center", gap: 8, background: "#F1F5F9", padding: "6px 12px", borderRadius: 8, fontSize: 12 }}>
          <ShieldCheck size={14} color={A.blue} />
          <span style={{ color: A.muted, fontWeight: 500 }}>Context:</span>
          <span style={{ fontWeight: 600, color: A.navy }}>{selectedCompany.name}</span>
          {selectedCompany.secretary_name && (
            <span style={{ fontSize: 11, background: "#E2E8F0", padding: "2px 6px", borderRadius: 4, color: A.navy }}>
              CS: {selectedCompany.secretary_name}
            </span>
          )}
        </div>
      )}
    </div>
  );
};
