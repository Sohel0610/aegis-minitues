/**
 * InsiderTradingFilterContext
 * Provides global filter state (company, batch, depository) shared across all Insider Trading tabs.
 */
import React, { createContext, useContext, useState, useEffect, useCallback } from "react";

// ── Types ─────────────────────────────────────────────────────────
export interface BatchInfo {
  id: number;
  batch_name: string;
  older_date?: string;
  latest_date?: string;
  created_at?: string;
}

export interface FilterOptions {
  companies: string[];
  depositories: string[];
  batches: BatchInfo[];
}

export interface InsiderTradingFilters {
  company: string;
  batch: string;
  depository: string;
}

interface FilterContextType {
  filters: InsiderTradingFilters;
  filterOptions: FilterOptions | null;
  setCompany: (v: string) => void;
  setBatch: (v: string) => void;
  setDepository: (v: string) => void;
  clearFilters: () => void;
  loading: boolean;
  /** Build query string from current filters (for API calls) */
  buildQuery: (extra?: Record<string, string | number>) => string;
}

const defaultFilters: InsiderTradingFilters = { company: "", batch: "", depository: "" };

const FilterContext = createContext<FilterContextType | undefined>(undefined);

// ── Provider ──────────────────────────────────────────────────────
export const InsiderTradingFilterProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [filters, setFilters] = useState<InsiderTradingFilters>(defaultFilters);
  const [filterOptions, setFilterOptions] = useState<FilterOptions | null>(null);
  const [loading, setLoading] = useState(true);

  // Fetch filter options once on mount
  useEffect(() => {
    const fetchOptions = async () => {
      try {
        const res = await fetch("/api/insider-trading/filter-options");
        if (res.ok) {
          const data = await res.json();
          const options = {
            companies: data.companies || [],
            depositories: data.depositories || [],
            batches: data.batches || [],
          };
          setFilterOptions(options);
        }
      } catch (err) {
        console.error("Failed to fetch filter options:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchOptions();
  }, []);

  const setCompany = useCallback((v: string) => setFilters((p) => ({ ...p, company: v })), []);
  const setBatch = useCallback((v: string) => setFilters((p) => ({ ...p, batch: v })), []);
  const setDepository = useCallback((v: string) => setFilters((p) => ({ ...p, depository: v })), []);
  const clearFilters = useCallback(() => {
    setFilters(defaultFilters);
  }, []);

  const buildQuery = useCallback(
    (extra?: Record<string, string | number>) => {
      const params = new URLSearchParams();
      if (filters.company) params.append("company", filters.company);
      if (filters.batch) params.append("batch", filters.batch);
      if (filters.depository) params.append("depository", filters.depository);
      if (extra) {
        Object.entries(extra).forEach(([k, v]) => {
          if (v !== undefined && v !== null && v !== "") params.append(k, String(v));
        });
      }
      const qs = params.toString();
      return qs ? `?${qs}` : "";
    },
    [filters]
  );

  return (
    <FilterContext.Provider
      value={{
        filters,
        filterOptions,
        setCompany,
        setBatch,
        setDepository,
        clearFilters,
        loading,
        buildQuery,
      }}
    >
      {children}
    </FilterContext.Provider>
  );
};

// ── Hook ──────────────────────────────────────────────────────────
export const useInsiderTradingFilters = () => {
  const ctx = useContext(FilterContext);
  if (!ctx) throw new Error("useInsiderTradingFilters must be used within InsiderTradingFilterProvider");
  return ctx;
};
