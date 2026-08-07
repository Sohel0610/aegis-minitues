import React, { createContext, useContext, useState, useEffect, useCallback } from "react";

export interface Vertical {
  id: number;
  name: string;
  code: string;
  company_count?: number;
}

export interface Company {
  id: number;
  name: string;
  cin?: string;
  type?: string;
  vertical_id?: number;
  status?: string;
  secretary_name?: string;
}

interface VerticalContextType {
  verticals: Vertical[];
  selectedVertical: Vertical | null;
  setSelectedVertical: (v: Vertical | null) => void;
  companies: Company[];
  totalCompanies: number;
  selectedCompany: Company | null;
  setSelectedCompany: (c: Company | null) => void;
  searchQuery: string;
  setSearchQuery: (q: string) => void;
  page: number;
  setPage: (p: number) => void;
  pageSize: number;
  loadingVerticals: boolean;
  loadingCompanies: boolean;
  refreshCompanies: () => void;
}

const VerticalContext = createContext<VerticalContextType | undefined>(undefined);

export const VerticalProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [verticals, setVerticals] = useState<Vertical[]>([]);
  const [selectedVertical, setSelectedVerticalState] = useState<Vertical | null>(null);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [totalCompanies, setTotalCompanies] = useState<number>(0);
  const [selectedCompany, setSelectedCompanyState] = useState<Company | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [page, setPage] = useState<number>(1);
  const pageSize = 15;

  const [loadingVerticals, setLoadingVerticals] = useState<boolean>(true);
  const [loadingCompanies, setLoadingCompanies] = useState<boolean>(false);

  // Fetch all Verticals on mount
  useEffect(() => {
    const fetchVerticals = async () => {
      setLoadingVerticals(true);
      const fallbackList: Vertical[] = [
        { id: 1, name: "Adani Green Energy (Renewables)", code: "AGEL", company_count: 12 },
        { id: 2, name: "Adani Energy Solutions (Transmission)", code: "AESL", company_count: 8 },
        { id: 3, name: "Adani Ports & SEZ (Ports)", code: "APSEZ", company_count: 15 },
        { id: 4, name: "Adani Enterprises (Incubator)", code: "AEL", company_count: 20 },
        { id: 5, name: "Adani Power (Thermal)", code: "APL", company_count: 6 },
      ];
      try {
        const res = await fetch("/api/verticals");
        if (res.ok) {
          const json = await res.json();
          const list: Vertical[] = json.data?.length ? json.data : fallbackList;
          setVerticals(list);
          const storedVId = localStorage.getItem("aegis_selected_vertical_id");
          let initialVert = list.find((v) => String(v.id) === storedVId) || list[0];
          if (initialVert) setSelectedVerticalState(initialVert);
        } else {
          setVerticals(fallbackList);
          setSelectedVerticalState(fallbackList[0]);
        }
      } catch (err) {
        console.error("Failed to fetch verticals, using fallback:", err);
        setVerticals(fallbackList);
        setSelectedVerticalState(fallbackList[0]);
      } finally {
        setLoadingVerticals(false);
      }
    };
    fetchVerticals();
  }, []);

  // Fetch Companies when selectedVertical, searchQuery, or page changes
  const fetchCompanies = useCallback(async () => {
    if (!selectedVertical) {
      setCompanies([]);
      setTotalCompanies(0);
      return;
    }

    setLoadingCompanies(true);
    const fallbackCompList: Company[] = [
      { id: 101, name: "Adani Green Energy Ltd", cin: "L40106GJ2015PLC082007", type: "Listed Public" },
      { id: 102, name: "Adani Renewable Energy Holding Four Ltd", cin: "U40106GJ2020PLC115201", type: "Unlisted Public" },
      { id: 103, name: "Adani Solar Energy Kutchh One Ltd", cin: "U40300GJ2021PTC120400", type: "Private Limited" },
    ];
    try {
      const offset = (page - 1) * pageSize;
      const params = new URLSearchParams({
        limit: String(pageSize),
        offset: String(offset),
      });
      if (searchQuery.trim()) {
        params.append("q", searchQuery.trim());
      }
      const res = await fetch(`/api/verticals/${selectedVertical.id}/companies?${params.toString()}`);
      if (res.ok) {
        const json = await res.json();
        const compList: Company[] = json.data?.length ? json.data : fallbackCompList;
        setCompanies(compList);
        setTotalCompanies(json.count || compList.length);
      } else {
        setCompanies(fallbackCompList);
        setTotalCompanies(fallbackCompList.length);
      }
    } catch (err) {
      console.error("Failed to fetch companies for vertical, using fallback:", err);
      setCompanies(fallbackCompList);
      setTotalCompanies(fallbackCompList.length);
    } finally {
      setLoadingCompanies(false);
    }
  }, [selectedVertical, searchQuery, page, pageSize, selectedCompany]);

  useEffect(() => {
    fetchCompanies();
  }, [fetchCompanies]);

  const setSelectedVertical = (v: Vertical | null) => {
    if (v && selectedVertical && v.id === selectedVertical.id) {
      return; // Already active vertical, do not wipe selected company
    }
    setSelectedVerticalState(v);
    if (v) {
      localStorage.setItem("aegis_selected_vertical_id", String(v.id));
    } else {
      localStorage.removeItem("aegis_selected_vertical_id");
    }
    // Reset search, page & company when vertical changes
    setSearchQuery("");
    setPage(1);
    setSelectedCompanyState(null);
    localStorage.removeItem("aegis_selected_company_id");
  };

  const setSelectedCompany = (c: Company | null) => {
    setSelectedCompanyState(c);
    if (c) {
      localStorage.setItem("aegis_selected_company_id", String(c.id));
    } else {
      localStorage.removeItem("aegis_selected_company_id");
    }
  };

  return (
    <VerticalContext.Provider
      value={{
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
        refreshCompanies: fetchCompanies,
      }}
    >
      {children}
    </VerticalContext.Provider>
  );
};

export const useVertical = () => {
  const ctx = useContext(VerticalContext);
  if (!ctx) {
    throw new Error("useVertical must be used within a VerticalProvider");
  }
  return ctx;
};
