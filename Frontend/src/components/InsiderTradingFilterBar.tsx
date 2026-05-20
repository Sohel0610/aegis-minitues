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
  text: "#323232",
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
  const isPlaceholder = !selected;
  const displayText = selected
    ? options.find((o) => o.value === selected)?.label || selected
    : placeholder;

  return (
    <div style={{ position: "relative" }}>
      <button
        onClick={() => setOpen(!open)}
        style={{
          display: "flex",
          alignItems: "center",
          gap: 6,
          padding: "7px 13px",
          borderRadius: 8,
          background: C.card,
          border: `1px solid ${C.border}`,
          cursor: "pointer",
          color: isPlaceholder ? C.muted : C.orange,
          fontSize: 12,
          fontWeight: 600,
          fontFamily: "Poppins",
          whiteSpace: "nowrap",
          maxWidth: 240,
        }}
      >
        <span style={{ overflow: "hidden", textOverflow: "ellipsis" }}>
          {displayText}
        </span>
        <ChevronDown
          size={13}
          color={isPlaceholder ? C.muted : C.orange}
          style={{ flexShrink: 0 }}
        />
      </button>
      {open && (
        <div
          style={{
            position: "absolute",
            top: "100%",
            left: 0,
            marginTop: 4,
            background: "#FFFFFF",
            border: `1px solid ${C.border}`,
            borderRadius: 8,
            boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
            zIndex: 100,
            minWidth: 280,
            maxHeight: 300,
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
                padding: "10px 14px",
                cursor: "pointer",
                fontSize: 12,
                color: C.text,
                fontWeight: opt.value === selected ? 600 : 400,
                background: opt.value === selected ? "rgba(0,102,179,0.06)" : "transparent",
                borderBottom: `1px solid ${C.border}`,
                display: "flex",
                alignItems: "center",
                gap: 8,
                fontFamily: "Poppins",
              }}
            >
              <span style={{ overflow: "hidden", textOverflow: "ellipsis" }}>
                {opt.label}
              </span>
            </div>
          ))}
        </div>
      )}
      {/* Close dropdown when clicking outside */}
      {open && (
        <div
          style={{ position: "fixed", inset: 0, zIndex: 99 }}
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
        placeholder="Select Period"
        onSelect={setBatch}
      />
      <FilterDropdown
        options={companyOptions}
        selected={filters.company}
        placeholder="Select Company"
        onSelect={setCompany}
      />
      <FilterDropdown
        options={depositoryOptions}
        selected={filters.depository}
        placeholder="Depository Type"
        onSelect={setDepository}
      />

      <button
        onClick={clearFilters}
        style={{
          display: "flex",
          alignItems: "center",
          gap: 5,
          padding: "7px 13px",
          borderRadius: 8,
          background: "transparent",
          border: `1px solid ${C.border}`,
          cursor: "pointer",
          color: C.sub,
          fontSize: 12,
          fontFamily: "Poppins",
        }}
      >
        <X size={13} /> Clear
      </button>
    </div>
  );
};

export default InsiderTradingFilterBar;
