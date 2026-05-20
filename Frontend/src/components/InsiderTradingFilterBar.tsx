/**
 * InsiderTradingFilterBar
 * Shared filter UI (Company, Batch, Depository) — redesigned to match outside project style.
 */
import { useState } from "react";
import { Filter, X, ChevronDown } from "lucide-react";
import { useInsiderTradingFilters } from "@/contexts/InsiderTradingFilterContext";

const C = {
  bg: "#F8FAFB",
  card: "#FFFFFF",
  border: "rgba(0,0,0,0.08)",
  orange: "#0066B3",
  text: "#1E293B",
  sub: "#64748B",
  muted: "#94A3B8",
};

function FilterDropdown({
  options,
  selected,
  placeholder,
  onSelect,
}: {
  options: { label: string; value: string }[];
  selected: string;
  placeholder: string;
  onSelect: (v: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const valueText = selected
    ? options.find((o) => o.value === selected)?.label || selected
    : "All";

  return (
    <div style={{ position: "relative" }}>
      <button
        onClick={() => setOpen(!open)}
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "flex-start",
          gap: 2,
          padding: "6px 14px",
          borderRadius: 8,
          background: C.card,
          border: `1px solid ${C.border}`,
          cursor: "pointer",
          fontFamily: "Adani",
          width: placeholder === "Select Business Units" ? 220 : 160,
          textAlign: "left",
        }}
      >
        <span style={{ fontSize: 9, color: C.muted, textTransform: "uppercase", fontWeight: 700, letterSpacing: "0.05em" }}>
          {placeholder}
        </span>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", width: "100%", gap: 6 }}>
          <span style={{ fontSize: 12, color: selected ? C.orange : C.text, fontWeight: 600, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", maxWidth: placeholder === "Select Business Units" ? 170 : 110 }}>
            {valueText}
          </span>
          <ChevronDown
            size={12}
            color={selected ? C.orange : C.muted}
            style={{ flexShrink: 0, marginLeft: "auto" }}
          />
        </div>
      </button>
      {open && (
        <div
          style={{
            position: "absolute",
            top: "100%",
            left: 0,
            marginTop: 4,
            background: C.card,
            border: `1px solid ${C.border}`,
            borderRadius: 8,
            boxShadow: "0 4px 12px rgba(0,0,0,0.08)",
            zIndex: 50,
            minWidth: 200,
            maxHeight: 240,
            overflowY: "auto",
          }}
        >
          {options.map((opt) => (
            <div
              key={opt.value}
              onClick={() => {
                onSelect(opt.value);
                setOpen(false);
              }}
              style={{
                padding: "8px 12px",
                fontSize: 12,
                cursor: "pointer",
                background: selected === opt.value ? "#F0F7FF" : "transparent",
                color: selected === opt.value ? C.orange : C.text,
                fontFamily: "Adani",
              }}
              onMouseEnter={(e) => {
                if (selected !== opt.value)
                  e.currentTarget.style.background = C.bg;
              }}
              onMouseLeave={(e) => {
                if (selected !== opt.value)
                  e.currentTarget.style.background = "transparent";
              }}
            >
              {opt.label}
            </div>
          ))}
        </div>
      )}
      {open && (
        <div
          style={{ position: "fixed", inset: 0, zIndex: 40 }}
          onClick={() => setOpen(false)}
        />
      )}
    </div>
  );
}

const InsiderTradingFilterBar = () => {
  const {
    filters,
    filterOptions,
    setCompany,
    setBatch,
    setDepository,
    clearFilters,
  } = useInsiderTradingFilters();

  if (!filterOptions) return null;

  const batchOptions = filterOptions.batches.map((b) => ({
    value: b.batch_name,
    label: `${b.batch_name}${b.older_date && b.latest_date ? ` (${b.older_date} → ${b.latest_date})` : ""}`,
  }));

  const companyOptions = filterOptions.companies.map((c) => ({
    value: c,
    label: c,
  }));

  const depositoryOptions = filterOptions.depositories.map((d) => ({
    value: d,
    label: d,
  }));

  return (
    <div
      style={{
        background: C.card,
        border: `1px solid ${C.border}`,
        borderRadius: 12,
        padding: "13px 20px",
        marginBottom: 20,
        display: "flex",
        alignItems: "center",
        gap: 14,
        flexWrap: "wrap",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <div
          style={{
            width: 32,
            height: 32,
            borderRadius: 8,
            background: "rgba(0,102,179,0.12)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <Filter size={14} color={C.orange} />
        </div>
        <div>
          <div style={{ fontSize: 13, color: C.text, fontWeight: 600 }}>
            Filters
          </div>
          <div style={{ fontSize: 10, color: C.muted }}>
            Applied across all tabs
          </div>
        </div>
      </div>

      <FilterDropdown
        options={batchOptions}
        selected={filters.batch}
        placeholder="Select Date Range"
        onSelect={setBatch}
      />
      <FilterDropdown
        options={companyOptions}
        selected={filters.company}
        placeholder="Select Business Units"
        onSelect={setCompany}
      />
      <FilterDropdown
        options={depositoryOptions}
        selected={filters.depository}
        placeholder="All"
        onSelect={setDepository}
      />

      <button
        onClick={clearFilters}
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "flex-start",
          gap: 2,
          padding: "6px 14px",
          borderRadius: 8,
          background: "transparent",
          border: `1px solid ${C.border}`,
          cursor: "pointer",
          fontFamily: "Adani",
          minWidth: 80,
          textAlign: "left",
        }}
      >
        <span style={{ fontSize: 9, color: C.muted, textTransform: "uppercase", fontWeight: 700, letterSpacing: "0.05em" }}>
          Clear
        </span>
        <div style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 12, color: C.sub, fontWeight: 600 }}>
          <X size={12} /> Reset
        </div>
      </button>
    </div>
  );
};

export default InsiderTradingFilterBar;
