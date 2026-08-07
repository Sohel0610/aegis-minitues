/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useState, useEffect, useMemo } from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Calendar, Clock, Download, FileText, Home, History, FileSpreadsheet, Plus, Upload, BookOpen, ChevronRight, ArrowLeft, Search, Building2, Layers, AlertCircle, CheckCircle2, User, Users, Trash2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import ProductDashboardLayout from '@/components/layout/ProductDashboardLayout';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { getMinutesNavItems } from '@/constants/minutesNavigation';
import { companyPresets } from '@/constants/companyPresets';
import { useVertical } from '@/contexts/VerticalContext';
import { useToast } from '@/components/ui/use-toast';

// Cleanup helpers
const cleanNameForCompare = (name: string) => {
  return name.toLowerCase().replace(/limited|private|ltd|pvt|&|and|\s+/gi, "").trim();
};

const getCompanyAbbreviation = (name: string) => {
  const clean = name.replace(/limited|private|ltd|pvt/gi, "").trim();
  if (clean.toLowerCase().includes("green energy")) return "AGEL";
  if (clean.toLowerCase().includes("enterprises")) return "AEL";
  if (clean.toLowerCase().includes("energy solutions")) return "AESL";
  if (clean.toLowerCase().includes("power")) return "APL";
  if (clean.toLowerCase().includes("ports")) return "APSEZ";
  if (clean.toLowerCase().includes("total gas")) return "ATGL";
  if (clean.toLowerCase().includes("ambuja cement")) return "ACL";
  if (clean.toLowerCase().includes("acc")) return "ACC";

  const words = clean.split(/\s+/).filter(w => w.length > 0);
  if (words.length >= 3) {
    return (words[0][0] + words[1][0] + words[2][0]).toUpperCase();
  } else if (words.length === 2) {
    return (words[0].substring(0, 2) + words[1][0]).toUpperCase();
  } else if (words.length === 1) {
    return words[0].substring(0, 4).toUpperCase();
  }
  return "COMP";
};

/** Map BU meeting-type filter → Schedule form meetingType / committeeName */
const mapFilterToCalendar = (filter: string): { meetingType: string; committeeName: string } => {
  if (!filter || filter === 'all') {
    return { meetingType: 'Board Meeting', committeeName: '' };
  }
  if (filter === 'Board Meeting') {
    return { meetingType: 'Board Meeting', committeeName: '' };
  }
  if (filter === 'AGM') {
    return { meetingType: 'Annual General Meeting', committeeName: '' };
  }
  if (filter === 'EGM') {
    return { meetingType: 'Extraordinary General Meeting', committeeName: '' };
  }
  // Committee filters (Audit Committee, NRC, SRC, CSR, Risk, etc.)
  return { meetingType: 'Committee Meeting', committeeName: filter };
};

/** Only auto-pick Chairman when designation says Chair/Chairperson — never fall back to first director (avoids Gautam-on-every-company). */
const pickDefaultChairman = (directors: any[]): string => {
  if (!directors?.length) return '';
  const byRole = directors.find((d) => {
    const desig = `${d.designation || d.role || ''}`.toLowerCase();
    return /\bchair(man|person|person)?\b/.test(desig) || desig.includes('chair');
  });
  return byRole?.name || '';
};

const formatMeetingDate = (dateStr?: string) => {
  if (!dateStr) return '—';
  const d = new Date(dateStr);
  if (Number.isNaN(d.getTime())) return dateStr;
  return d.toLocaleDateString('en-US', { day: 'numeric', month: 'short', year: 'numeric' });
};

const MinutesGenerator = () => {
  const navigate = useNavigate();
  
  const {
    verticals,
    setSelectedVertical,
    selectedCompany,
    setSelectedCompany,
    loadingVerticals
  } = useVertical();

  // Local state to track which BU is currently selected in Step 1
  const [activeVertical, setActiveVertical] = useState<any | null>(null);

  // Dynamic Tab state for selected company details
  const [activeTab, setActiveTab] = useState<'schedule' | 'compliances' | 'history' | 'directors'>('schedule');

  // History & Compliance state
  const [history, setHistory] = useState<any[]>([]);
  const [compliances, setCompliances] = useState<any[]>([]);
  const [loadingCompliances, setLoadingCompliances] = useState(false);

  // Pagination for history
  const [historyPage, setHistoryPage] = useState<number>(1);
  const historyPageSize = 5;

  // Clear selected company & vertical on mount so the user starts fresh at Step 1 Grid
  useEffect(() => {
    if (setSelectedCompany) setSelectedCompany(null);
    if (setSelectedVertical) setSelectedVertical(null);
    setActiveVertical(null);
  }, [setSelectedCompany, setSelectedVertical]);

  // Local state for listing companies under the activeVertical
  const [localCompanies, setLocalCompanies] = useState<any[]>([]);
  const [loadingLocalCompanies, setLoadingLocalCompanies] = useState(false);
  const [localTotalCompanies, setLocalTotalCompanies] = useState<number>(0);
  const [localSearchQuery, setLocalSearchQuery] = useState<string>("");
  const [localPage, setLocalPage] = useState<number>(1);
  const localPageSize = 15;
  const [meetingTypeFilter, setMeetingTypeFilter] = useState<string>("all");

  // Add/Delete Company UI state
  const [showAddCompanyModal, setShowAddCompanyModal] = useState(false);
  const [addCompanyForm, setAddCompanyForm] = useState({
    name: '',
    code: '',
    cin: '',
    type: 'Public Limited',
    secretary_name: '',
    status: 'Active'
  });
  const [addingCompany, setAddingCompany] = useState(false);
  const [showDeleteCompanyModal, setShowDeleteCompanyModal] = useState(false);
  const [companyToDelete, setCompanyToDelete] = useState<any | null>(null);
  const [deleteConfirmText, setDeleteConfirmText] = useState('');
  const [deletingCompany, setDeletingCompany] = useState(false);

  const { toast } = useToast();

  const [directorsList, setDirectorsList] = useState<any[]>([]);
  const [companyMeetings, setCompanyMeetings] = useState<any[]>([]);
  const [loadingMeetings, setLoadingMeetings] = useState(false);
  const [nextMeetingNumber, setNextMeetingNumber] = useState<string>('1ST');

  // Add Company Handler
  const handleAddCompany = async () => {
    if (!addCompanyForm.name.trim()) {
      alert("Company name is required!");
      return;
    }
    if (!activeVertical) {
      alert("Please select a business unit first!");
      return;
    }

    setAddingCompany(true);
    try {
      const res = await fetch(`/api/verticals/${activeVertical.id}/companies`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(addCompanyForm)
      });

      if (res.ok) {
        const newCompany = await res.json();
        alert(`Company "${newCompany.name}" added successfully!`);
        
        // Refresh company list
        setLocalPage(1);
        setShowAddCompanyModal(false);
        setAddCompanyForm({
          name: '',
          code: '',
          cin: '',
          type: 'Public Limited',
          secretary_name: '',
          status: 'Active'
        });

        // Trigger re-fetch by updating a dependency
        const offset = 0;
        const filterParam = meetingTypeFilter !== 'all' ? `&meeting_type_filter=${encodeURIComponent(meetingTypeFilter)}` : '';
        const refreshRes = await fetch(`/api/verticals/${activeVertical.id}/companies?q=${encodeURIComponent(localSearchQuery)}&limit=${localPageSize}&offset=${offset}${filterParam}`);
        if (refreshRes.ok) {
          const data = await refreshRes.json();
          setLocalCompanies(data.data || []);
          setLocalTotalCompanies(data.count || (data.data || []).length);
        }
      } else {
        const error = await res.json();
        alert(`Failed to add company: ${error.detail || 'Unknown error'}`);
      }
    } catch (err) {
      console.error("Error adding company:", err);
      alert("Failed to add company. Please try again.");
    } finally {
      setAddingCompany(false);
    }
  };

  const openDeleteCompanyModal = (company: any) => {
    setCompanyToDelete(company);
    setDeleteConfirmText('');
    setShowDeleteCompanyModal(true);
  };

  const closeDeleteCompanyModal = () => {
    if (deletingCompany) return;
    setShowDeleteCompanyModal(false);
    setCompanyToDelete(null);
    setDeleteConfirmText('');
  };

  const confirmDeleteCompany = async () => {
    if (!companyToDelete || deleteConfirmText !== 'DELETE') return;

    setDeletingCompany(true);
    try {
      const res = await fetch(`/api/companies/${companyToDelete.id}?confirm=true`, {
        method: 'DELETE',
      });

      if (res.ok) {
        const result = await res.json();
        toast({
          title: 'Company deleted',
          description: `"${companyToDelete.name}" and ${result.deleted_records?.total || 0} related record(s) were removed.`,
        });

        setLocalCompanies((prev) => prev.filter((c) => c.id !== companyToDelete.id));
        setLocalTotalCompanies((prev) => prev - 1);
        setShowDeleteCompanyModal(false);
        setCompanyToDelete(null);
        setDeleteConfirmText('');
      } else {
        const error = await res.json();
        toast({
          title: 'Delete failed',
          description: error.detail || 'Unknown error',
          variant: 'destructive',
        });
      }
    } catch (err) {
      console.error('Error deleting company:', err);
      toast({
        title: 'Delete failed',
        description: 'Could not delete company. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setDeletingCompany(false);
    }
  };

  // Calendarization state
  const [calendarData, setCalendarData] = useState({
    meetingDate: '',
    meetingTime: '',
    meetingType: 'Board Meeting',
    committeeName: ''
  });

  // Fetch History on mount
  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const res = await fetch('/api/generated-minutes');
        if (res.ok) {
          const data = await res.json();
          setHistory(data.data || []);
        }
      } catch (err) {
        console.error("Failed to fetch history", err);
      }
    };
    fetchHistory();
  }, []);

  // Fetch Compliances on mount
  useEffect(() => {
    const fetchCompliances = async () => {
      setLoadingCompliances(true);
      try {
        const res = await fetch('/api/compliances');
        if (res.ok) {
          const data = await res.json();
          setCompliances(data.data || []);
        }
      } catch (err) {
        console.error("Failed to fetch compliances", err);
      } finally {
        setLoadingCompliances(false);
      }
    };
    fetchCompliances();
  }, []);

  // Fetch companies for selected activeVertical, localPage, localSearchQuery, or meetingTypeFilter
  useEffect(() => {
    if (!activeVertical) {
      setLocalCompanies([]);
      setLocalTotalCompanies(0);
      return;
    }
    const fetchLocalCompanies = async () => {
      setLoadingLocalCompanies(true);
      try {
        const offset = (localPage - 1) * localPageSize;
        const filterParam = meetingTypeFilter !== 'all' ? `&meeting_type_filter=${encodeURIComponent(meetingTypeFilter)}` : '';
        const res = await fetch(`/api/verticals/${activeVertical.id}/companies?q=${encodeURIComponent(localSearchQuery)}&limit=${localPageSize}&offset=${offset}${filterParam}`);
        if (res.ok) {
          const data = await res.json();
          setLocalCompanies(data.data || []);
          setLocalTotalCompanies(data.count || (data.data || []).length);
        }
      } catch (err) {
        console.error("Failed to fetch local companies", err);
      } finally {
        setLoadingLocalCompanies(false);
      }
    };

    const delayDebounce = setTimeout(() => {
      fetchLocalCompanies();
    }, 300);

    return () => clearTimeout(delayDebounce);
  }, [activeVertical, localSearchQuery, localPage, meetingTypeFilter]);

  // Fetch directors list when selected company changes
  useEffect(() => {
    if (!selectedCompany) return;
    const fetchDirectors = async () => {
      try {
        const res = await fetch(`/api/companies/${encodeURIComponent(selectedCompany.name)}/directors`);
        if (res.ok) {
          const data = await res.json();
          setDirectorsList(data.data || []);
        }
      } catch (err) {
        console.error("Failed to fetch directors", err);
      }
    };
    fetchDirectors();
  }, [selectedCompany]);

  // Fetch meetings for selected company, filtered by BU meeting-type filter
  useEffect(() => {
    if (!selectedCompany?.id) {
      setCompanyMeetings([]);
      setNextMeetingNumber('1ST');
      return;
    }
    const fetchMeetings = async () => {
      setLoadingMeetings(true);
      try {
        const typeParam = meetingTypeFilter !== 'all'
          ? `?meeting_type=${encodeURIComponent(meetingTypeFilter)}`
          : '';
        const res = await fetch(`/api/companies/${selectedCompany.id}/meetings${typeParam}`);
        if (res.ok) {
          const data = await res.json();
          setCompanyMeetings(data.data || []);
          setNextMeetingNumber(data.next_meeting_number || '1ST');
        } else {
          setCompanyMeetings([]);
        }
      } catch (err) {
        console.error("Failed to fetch company meetings", err);
        setCompanyMeetings([]);
      } finally {
        setLoadingMeetings(false);
      }
    };
    fetchMeetings();
  }, [selectedCompany, meetingTypeFilter]);

  // Filter Compliances for selected company
  const companyCompliances = useMemo(() => {
    if (!selectedCompany) return [];
    const compClean = cleanNameForCompare(selectedCompany.name);
    return compliances.filter(c => {
      if (!c.company_name) return false;
      return cleanNameForCompare(c.company_name).includes(compClean) || compClean.includes(cleanNameForCompare(c.company_name));
    });
  }, [compliances, selectedCompany]);

  // Calculate compliance statistics
  const complianceStats = useMemo(() => {
    return {
      completed: companyCompliances.filter(c => c.status === 'Completed').length,
      upcoming: companyCompliances.filter(c => c.status !== 'Completed' && c.status !== 'Overdue').length,
      overdue: companyCompliances.filter(c => c.status === 'Overdue' || c.status === 'Urgent').length
    };
  }, [companyCompliances]);

  // Filter History for selected company (and BU meeting-type filter when set)
  const companyHistory = useMemo(() => {
    if (!selectedCompany) return [];
    const compClean = cleanNameForCompare(selectedCompany.name);
    return history.filter(h => {
      if (!h.company_name) return false;
      const nameMatch = cleanNameForCompare(h.company_name).includes(compClean) || compClean.includes(cleanNameForCompare(h.company_name));
      if (!nameMatch) return false;
      if (meetingTypeFilter !== 'all') {
        return (h.meeting_type || '').toLowerCase() === meetingTypeFilter.toLowerCase();
      }
      return true;
    });
  }, [history, selectedCompany, meetingTypeFilter]);

  const handleDeleteHistory = async (id: number) => {
    if (!window.confirm("Are you sure you want to delete this draft document?")) return;
    try {
      const res = await fetch(`/api/generated-minutes/${id}`, {
        method: 'DELETE'
      });
      if (res.ok) {
        setHistory(prev => prev.filter(item => item.id !== id));
      } else {
        const err = await res.json().catch(() => ({}));
        alert(err.detail || "Failed to delete. Finalized minutes are locked.");
      }
    } catch (err) {
      console.error("Error deleting document:", err);
      alert("Failed to delete document.");
    }
  };

  const handleGenerateClick = () => {
    if (!selectedCompany) return;
    // Do NOT wipe drafts here — resume if user already filled steps for this meeting
    const selectedPreset = companyPresets.find(c => c.name === selectedCompany.name);
    const directors = directorsList.length > 0 ? directorsList : (selectedPreset ? selectedPreset.directors : []);
    const stateToPass = {
      companyName: selectedCompany.name,
      meetingDate: calendarData.meetingDate,
      meetingDay: calendarData.meetingDate ? new Date(calendarData.meetingDate).toLocaleDateString('en-US', { weekday: 'long' }) : '',
      meetingNumber: nextMeetingNumber,
      // Prefer the BU filter label when set (e.g. Audit Committee) so template picker filters correctly
      meetingType: meetingTypeFilter !== 'all' && meetingTypeFilter !== 'Board Meeting' && meetingTypeFilter !== 'AGM' && meetingTypeFilter !== 'EGM'
        ? (calendarData.meetingType === 'Committee Meeting' ? 'Committee Meeting' : meetingTypeFilter)
        : calendarData.meetingType,
      committeeName: meetingTypeFilter !== 'all' && !['Board Meeting', 'AGM', 'EGM', 'all'].includes(meetingTypeFilter)
        ? (calendarData.committeeName || meetingTypeFilter)
        : calendarData.committeeName,
      timeCommenced: calendarData.meetingTime,
      meetingPlace: selectedPreset ? selectedPreset.address : "Adani Corporate House, Ahmedabad",
      presentDirectors: directors,
      chairmanName: pickDefaultChairman(directors),
      signingChairmanName: pickDefaultChairman(directors),
      companySecretary: selectedCompany.secretary_name || '',
      resetDraft: false,
    };
    // Resolve meeting chairman from previous minutes / template for this company + type
    const typeForChair =
      stateToPass.committeeName ||
      (stateToPass.meetingType === 'Committee Meeting' ? 'Audit Committee' : stateToPass.meetingType);
    fetch(
      `/api/companies/${encodeURIComponent(selectedCompany.name)}/default-chairman?meeting_type=${encodeURIComponent(typeForChair)}`
    )
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data?.chairman_name) {
          navigate('/minutes-preparation/form-generator', {
            state: {
              ...stateToPass,
              chairmanName: data.chairman_name,
              signingChairmanName: data.chairman_name,
            },
          });
        } else {
          navigate('/minutes-preparation/form-generator', { state: stateToPass });
        }
      })
      .catch(() => navigate('/minutes-preparation/form-generator', { state: stateToPass }));
  };

  const meetingTypes = [
    { value: "Board Meeting", label: "Board Meeting" },
    { value: "Committee Meeting", label: "Committee Meeting" },
    { value: "Annual General Meeting", label: "Annual General Meeting" },
    { value: "Extraordinary General Meeting", label: "Extraordinary General Meeting" }
  ];

  const navigationItems = getMinutesNavItems('dashboard');

  const handleBackToGrid = () => {
    // Stay on the same BU + meeting-type filter; only leave the company detail
    setSelectedCompany(null);
    setSelectedVertical(null);
    setCompanyMeetings([]);
    setCalendarData({
      meetingDate: '',
      meetingTime: '',
      meetingType: 'Board Meeting',
      committeeName: ''
    });
  };

  const openCompanyWithFilter = (company: any) => {
    const mapped = mapFilterToCalendar(meetingTypeFilter);
    setSelectedVertical(activeVertical);
    setSelectedCompany(company);
    setActiveTab('schedule');
    setCalendarData(prev => ({
      ...prev,
      meetingType: mapped.meetingType,
      committeeName: mapped.committeeName,
    }));
  };

  // --- RENDER 1: SELECTION GRID (LANDING PAGE) ---
  if (!selectedCompany) {
    return (
      <ProductDashboardLayout productName="Generate Minutes" productRoute="/minutes-preparation" navigationItems={navigationItems}>
        <div style={{ background: "#F8FAFC", minHeight: "100%", padding: "40px 24px" }}>
          
          {/* Header Title section mirroring "Shareholding Agent" screenshot */}
          <div className="text-left mb-6 pb-4 border-b border-slate-100">
            <h1 className="text-xl font-bold text-slate-900">
              Minutes Agent
            </h1>
            <p className="text-xs text-slate-500 mt-1">
              Corporate governance tracking, statutory compliance calendars, and meeting minutes generation for Adani Business Units.
            </p>
          </div>

          <div className="max-w-6xl mx-auto">
            {/* STEP 1: SELECT VERTICAL GRID */}
            {!activeVertical ? (
              <div className="space-y-6">
                <div style={{ borderBottom: "1px solid #E2E8F0", paddingBottom: "10px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <h2 className="text-lg font-bold text-slate-800">Select Business Unit (Vertical)</h2>
                  <span className="text-xs text-muted-foreground">{verticals.length} Business Units</span>
                </div>

                {loadingVerticals ? (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {[1, 2, 3, 4, 5, 6].map((i) => (
                      <div key={i} className="animate-pulse bg-white border border-slate-100 rounded-2xl h-24 p-6"></div>
                    ))}
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {verticals.map((v) => (
                      <div
                        key={v.id}
                        onClick={() => {
                          setActiveVertical(v);
                          setLocalPage(1);
                          setLocalSearchQuery("");
                        }}
                        style={{
                          background: "#FFFFFF",
                          border: "1px solid #E2E8F0",
                          borderRadius: "16px",
                          padding: "20px 24px",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "space-between",
                          cursor: "pointer",
                          transition: "all 0.2s ease",
                          boxShadow: "0 1px 3px rgba(0,0,0,0.02)"
                        }}
                        className="hover:shadow-md hover:border-blue-400 group"
                      >
                        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
                          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", background: "#F1F5F9", borderRadius: "12px", width: "48px", height: "48px", flexShrink: 0, padding: "8px" }}>
                            <img src="/adani.svg" alt="Adani" style={{ height: "100%", width: "auto" }} />
                          </div>
                          <div>
                            <div style={{ fontSize: "16px", fontWeight: 700, color: "#0F172A" }}>{v.code}</div>
                            <div style={{ fontSize: "12px", color: "#64748B", textTransform: "uppercase", fontWeight: 500 }}>{v.name}</div>
                          </div>
                        </div>
                        <div 
                          style={{
                            width: "32px",
                            height: "32px",
                            borderRadius: "50%",
                            border: "1px solid #E2E8F0",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            color: "#0057B8",
                            background: "#F8FAFC"
                          }}
                          className="group-hover:bg-blue-600 group-hover:text-white group-hover:border-blue-600 transition-all shrink-0"
                        >
                          <ChevronRight size={16} />
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              /* STEP 2: SELECT COMPANY GRID UNDER SELECTED VERTICAL */
              <div className="space-y-6">
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 pb-4 border-b border-slate-200">
                  <div className="flex items-center gap-3">
                    <Button
                      variant="ghost"
                      onClick={() => setActiveVertical(null)}
                      className="p-2 h-auto text-slate-500 hover:text-slate-900 rounded-full"
                    >
                      <ArrowLeft size={18} />
                    </Button>
                    <div>
                      <h2 className="text-xl font-bold text-slate-800">Select Entity under {activeVertical.name}</h2>
                      <p className="text-xs text-muted-foreground">Showing {localTotalCompanies} companies</p>
                    </div>
                  </div>

                  {/* Filter, Search, and Add Company Button */}
                  <div className="flex flex-col sm:flex-row gap-3 w-full sm:w-auto">
                    {/* Add Company Button */}
                    <Button
                      onClick={() => setShowAddCompanyModal(true)}
                      className="bg-blue-600 hover:bg-blue-700 text-white text-xs h-9 rounded-xl px-4 gap-2"
                    >
                      <Plus size={14} />
                      Add Company
                    </Button>

                    {/* Meeting Type Filter Dropdown */}
                    <Select value={meetingTypeFilter} onValueChange={(val) => {
                      setMeetingTypeFilter(val);
                      setLocalPage(1);
                    }}>
                      <SelectTrigger className="w-full sm:min-w-[240px] sm:w-[260px] bg-white text-xs h-9 rounded-xl border-slate-200 [&>span]:line-clamp-none">
                        <SelectValue placeholder="Filter by Meeting Type" />
                      </SelectTrigger>
                      <SelectContent className="bg-white min-w-[260px]">
                        <SelectItem value="all" className="text-xs">All Meetings</SelectItem>
                        <SelectItem value="Board Meeting" className="text-xs">Board Meeting</SelectItem>
                        <SelectItem value="Audit Committee" className="text-xs">Audit Committee</SelectItem>
                        <SelectItem value="Nomination and Remuneration Committee" className="text-xs">NRC</SelectItem>
                        <SelectItem value="Stakeholders Relationship Committee" className="text-xs">SRC</SelectItem>
                        <SelectItem value="CSR Committee" className="text-xs">CSR Committee</SelectItem>
                        <SelectItem value="Risk Management Committee" className="text-xs">Risk Committee</SelectItem>
                        <SelectItem value="AGM" className="text-xs">AGM</SelectItem>
                        <SelectItem value="EGM" className="text-xs">EGM</SelectItem>
                      </SelectContent>
                    </Select>

                    {/* Search input */}
                    <div style={{ position: "relative", width: "100%", maxWidth: "300px" }}>
                      <Search size={14} color="#64748B" style={{ position: "absolute", left: "10px", top: "50%", transform: "translateY(-50%)" }} />
                      <Input
                        placeholder="Search company or entity..."
                        value={localSearchQuery}
                        onChange={(e) => {
                          setLocalSearchQuery(e.target.value);
                          setLocalPage(1);
                        }}
                        className="pl-8 bg-white text-xs h-9 rounded-xl border-slate-200"
                      />
                    </div>
                  </div>
                </div>

                {loadingLocalCompanies ? (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {[1, 2, 3, 4, 5, 6].map((i) => (
                      <div key={i} className="animate-pulse bg-white border border-slate-100 rounded-2xl h-24 p-6"></div>
                    ))}
                  </div>
                ) : localCompanies.length === 0 ? (
                  <div className="text-center py-12 bg-white rounded-2xl border border-dashed border-slate-200 text-slate-400 text-sm">
                    No entities found{localSearchQuery ? ` matching "${localSearchQuery}"` : ''} under {activeVertical.name}.
                    {meetingTypeFilter !== 'all' && localSearchQuery === '' ? ' Try another Business Unit, or add a company.' : ''}
                  </div>
                ) : (
                  <>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                      {localCompanies.map((c) => {
                        const abbr = getCompanyAbbreviation(c.name);
                        
                        return (
                          <div
                            key={c.id}
                            onClick={() => openCompanyWithFilter(c)}
                            style={{
                              background: "#FFFFFF",
                              border: "1px solid #E2E8F0",
                              borderRadius: "16px",
                              padding: "20px 24px",
                              cursor: "pointer",
                              transition: "all 0.2s ease",
                              boxShadow: "0 1px 3px rgba(0,0,0,0.02)"
                            }}
                            className="hover:shadow-md hover:border-blue-400 group"
                          >
                            <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
                              <div style={{ display: "flex", alignItems: "center", gap: "16px", flex: 1 }}>
                                <div style={{ display: "flex", alignItems: "center", justifyContent: "center", background: "#F1F5F9", borderRadius: "12px", width: "48px", height: "48px", flexShrink: 0, padding: "8px" }}>
                                  <img src="/adani.svg" alt="Adani" style={{ height: "100%", width: "auto" }} />
                                </div>
                                <div style={{ maxWidth: "160px" }}>
                                  <div style={{ fontSize: "16px", fontWeight: 700, color: "#0F172A" }}>{abbr}</div>
                                  <div 
                                    style={{ 
                                      fontSize: "12px", 
                                      color: "#64748B", 
                                      textTransform: "uppercase", 
                                      fontWeight: 500,
                                      overflow: "hidden",
                                      textOverflow: "ellipsis",
                                      whiteSpace: "nowrap"
                                    }}
                                  >
                                    {c.name}
                                  </div>
                                  {c.secretary_name && (
                                    <div style={{ fontSize: "11px", color: "#0057B8", marginTop: "2px", fontWeight: 600 }}>CS: {c.secretary_name}</div>
                                  )}
                                </div>
                              </div>
                              <div className="flex gap-2 items-center">
                                {/* Delete Button - Shows on hover */}
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    openDeleteCompanyModal(c);
                                  }}
                                  className="w-8 h-8 rounded-full border border-red-200 flex items-center justify-center text-red-600 bg-red-50 opacity-0 group-hover:opacity-100 hover:bg-red-600 hover:text-white hover:border-red-600 transition-all duration-200"
                                  title="Delete Company"
                                >
                                  <Trash2 size={14} />
                                </button>
                                <div 
                                  className="w-8 h-8 rounded-full border border-slate-200 flex items-center justify-center text-blue-600 bg-slate-50 group-hover:bg-blue-600 group-hover:text-white group-hover:border-blue-600 transition-all"
                                >
                                  <ChevronRight size={16} />
                                </div>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>

                    {/* Pagination for Companies Grid */}
                    {localTotalCompanies > localPageSize && (
                      <div className="flex items-center justify-between pt-6 text-sm text-slate-500">
                        <span>Showing {((localPage - 1) * localPageSize) + 1}–{Math.min(localPage * localPageSize, localTotalCompanies)} of {localTotalCompanies} entities</span>
                        <div className="flex gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            disabled={localPage <= 1}
                            onClick={() => setLocalPage(localPage - 1)}
                          >
                            Previous
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            disabled={localPage >= Math.ceil(localTotalCompanies / localPageSize)}
                            onClick={() => setLocalPage(localPage + 1)}
                          >
                            Next
                          </Button>
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Add Company Dialog — must live in this branch (company list) */}
        <Dialog open={showAddCompanyModal} onOpenChange={setShowAddCompanyModal}>
          <DialogContent className="bg-white max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Add New Company</DialogTitle>
              <DialogDescription>
                Add a new company under <strong>{activeVertical?.name}</strong>
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="company-name" className="text-sm font-semibold">
                  Company Name <span className="text-red-600">*</span>
                </Label>
                <Input
                  id="company-name"
                  placeholder="e.g., ADANI GREEN ENERGY LIMITED"
                  value={addCompanyForm.name}
                  onChange={(e) => setAddCompanyForm(prev => ({ ...prev, name: e.target.value }))}
                  className="h-11"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="company-code" className="text-sm font-semibold">
                  Company Code
                </Label>
                <Input
                  id="company-code"
                  placeholder="e.g., AGEL (auto-generated if empty)"
                  value={addCompanyForm.code}
                  onChange={(e) => setAddCompanyForm(prev => ({ ...prev, code: e.target.value }))}
                  className="h-11"
                />
                <p className="text-xs text-slate-500">
                  Leave empty to auto-generate from company name
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="company-cin" className="text-sm font-semibold">
                  CIN (Corporate Identity Number)
                </Label>
                <Input
                  id="company-cin"
                  placeholder="e.g., L40101GJ2015PLC084374"
                  value={addCompanyForm.cin}
                  onChange={(e) => setAddCompanyForm(prev => ({ ...prev, cin: e.target.value }))}
                  className="h-11 font-mono"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="company-type" className="text-sm font-semibold">
                  Company Type
                </Label>
                <Select
                  value={addCompanyForm.type}
                  onValueChange={(val) => setAddCompanyForm(prev => ({ ...prev, type: val }))}
                >
                  <SelectTrigger className="h-11">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Public Limited">Public Limited</SelectItem>
                    <SelectItem value="Private Limited">Private Limited</SelectItem>
                    <SelectItem value="LLP">LLP</SelectItem>
                    <SelectItem value="OPC">One Person Company</SelectItem>
                    <SelectItem value="Partnership">Partnership</SelectItem>
                    <SelectItem value="Proprietorship">Proprietorship</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="secretary-name" className="text-sm font-semibold">
                  Company Secretary Name
                </Label>
                <Input
                  id="secretary-name"
                  placeholder="e.g., Kuntal Chandya"
                  value={addCompanyForm.secretary_name}
                  onChange={(e) => setAddCompanyForm(prev => ({ ...prev, secretary_name: e.target.value }))}
                  className="h-11"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="company-status" className="text-sm font-semibold">
                  Status
                </Label>
                <Select
                  value={addCompanyForm.status}
                  onValueChange={(val) => setAddCompanyForm(prev => ({ ...prev, status: val }))}
                >
                  <SelectTrigger className="h-11">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Active">Active</SelectItem>
                    <SelectItem value="Inactive">Inactive</SelectItem>
                    <SelectItem value="Dissolved">Dissolved</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setShowAddCompanyModal(false)}
                disabled={addingCompany}
              >
                Cancel
              </Button>
              <Button
                onClick={handleAddCompany}
                disabled={addingCompany || !addCompanyForm.name.trim()}
                className="bg-blue-600 hover:bg-blue-700"
              >
                {addingCompany ? "Adding..." : "Add Company"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Delete Company Dialog */}
        <Dialog open={showDeleteCompanyModal} onOpenChange={(open) => !open && closeDeleteCompanyModal()}>
          <DialogContent className="bg-white max-w-lg">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2 text-red-700">
                <AlertCircle className="h-5 w-5" />
                Delete company?
              </DialogTitle>
              <DialogDescription asChild>
                <div className="space-y-4 pt-1 text-sm text-slate-600">
                  <p>
                    Are you sure you want to delete{' '}
                    <strong className="text-slate-900">{companyToDelete?.name}</strong>?
                  </p>
                  <div className="rounded-lg border border-red-100 bg-red-50/60 p-3">
                    <p className="font-medium text-red-800 mb-2">This will permanently delete:</p>
                    <ul className="list-disc pl-5 space-y-1 text-red-900/80">
                      <li>Company record</li>
                      <li>All meetings and minutes</li>
                      <li>All attendance records</li>
                      <li>All directors</li>
                      <li>All related data</li>
                    </ul>
                  </div>
                  <p className="text-xs text-slate-500">This action cannot be undone.</p>
                  <div className="space-y-2">
                    <Label htmlFor="delete-confirm" className="text-sm font-semibold text-slate-700">
                      Type <span className="font-mono text-red-600">DELETE</span> to confirm
                    </Label>
                    <Input
                      id="delete-confirm"
                      value={deleteConfirmText}
                      onChange={(e) => setDeleteConfirmText(e.target.value)}
                      placeholder="DELETE"
                      className="h-10 font-mono"
                      autoComplete="off"
                      disabled={deletingCompany}
                    />
                  </div>
                </div>
              </DialogDescription>
            </DialogHeader>
            <DialogFooter className="gap-2 sm:gap-0">
              <Button
                variant="outline"
                onClick={closeDeleteCompanyModal}
                disabled={deletingCompany}
              >
                Cancel
              </Button>
              <Button
                variant="destructive"
                onClick={confirmDeleteCompany}
                disabled={deletingCompany || deleteConfirmText !== 'DELETE'}
              >
                {deletingCompany ? 'Deleting...' : 'Delete company'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </ProductDashboardLayout>
    );
  }

  // --- RENDER 2: SCROUPED DETAIL TABS FOR SELECTED COMPANY ---
  const indexOfLastHistory = historyPage * historyPageSize;
  const indexOfFirstHistory = indexOfLastHistory - historyPageSize;
  const currentHistory = companyHistory.slice(indexOfFirstHistory, indexOfLastHistory);
  const totalHistoryPages = Math.ceil(companyHistory.length / historyPageSize) || 1;

  return (
    <ProductDashboardLayout productName="Generate Minutes" productRoute="/minutes-preparation" navigationItems={navigationItems}>
      <div className="container mx-auto py-6 space-y-6">
        
        {/* Dynamic Context Header */}
        <div className="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div className="flex items-center gap-4">
            <Button
              variant="outline"
              size="sm"
              onClick={handleBackToGrid}
              className="rounded-full w-9 h-9 p-0 hover:bg-slate-50"
            >
              <ArrowLeft size={16} />
            </Button>
            <div>
              <h2 className="text-2xl font-bold text-slate-800">{selectedCompany.name}</h2>
              <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-1 text-xs text-muted-foreground">
                {selectedCompany.cin && <span>CIN: <strong className="font-mono">{selectedCompany.cin}</strong></span>}
                <span>Type: <strong>{selectedCompany.type || "Public"}</strong></span>
                {selectedCompany.secretary_name && <span>Secretary: <strong className="text-blue-600">{selectedCompany.secretary_name}</strong></span>}
                {meetingTypeFilter !== 'all' && (
                  <Badge className="bg-blue-50 text-blue-700 border border-blue-200 hover:bg-blue-50 font-semibold">
                    {meetingTypeFilter}
                  </Badge>
                )}
              </div>
            </div>
          </div>
          <Button
            variant="outline"
            onClick={handleBackToGrid}
            className="text-xs border-dashed shrink-0"
          >
            Switch Entity
          </Button>
        </div>

        {/* Tab Buttons bar */}
        <div className="flex gap-1 border-b border-slate-200">
          <button
            onClick={() => setActiveTab('schedule')}
            className={`px-4 py-2.5 text-xs font-semibold border-b-2 transition-all ${activeTab === 'schedule' ? 'border-blue-600 text-blue-600 font-bold' : 'border-transparent text-slate-500 hover:text-slate-900'}`}
          >
            Schedule Meeting
          </button>
          <button
            onClick={() => setActiveTab('compliances')}
            className={`px-4 py-2.5 text-xs font-semibold border-b-2 transition-all ${activeTab === 'compliances' ? 'border-blue-600 text-blue-600 font-bold' : 'border-transparent text-slate-500 hover:text-slate-900'}`}
          >
            Compliance Calendar ({companyCompliances.length})
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`px-4 py-2.5 text-xs font-semibold border-b-2 transition-all ${activeTab === 'history' ? 'border-blue-600 text-blue-600 font-bold' : 'border-transparent text-slate-500 hover:text-slate-900'}`}
          >
            Past Minutes ({companyHistory.length})
          </button>
          <button
            onClick={() => setActiveTab('directors')}
            className={`px-4 py-2.5 text-xs font-semibold border-b-2 transition-all ${activeTab === 'directors' ? 'border-blue-600 text-blue-600 font-bold' : 'border-transparent text-slate-500 hover:text-slate-900'}`}
          >
            Directors ({directorsList.length})
          </button>
        </div>

        {/* TAB CONTENTS */}
        <div className="space-y-6">
          
          {/* TAB 1: SCHEDULE MEETING */}
          {activeTab === 'schedule' && (
            <div className="space-y-6">
              {/* Meetings for selected type — ordered by number + date */}
              <Card className="border border-slate-200 shadow-xs rounded-xl bg-white overflow-hidden">
                <CardHeader className="border-b border-slate-100 bg-slate-50/50 pb-4">
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                    <div>
                      <CardTitle className="text-base font-bold text-slate-900">
                        {meetingTypeFilter !== 'all' ? `${meetingTypeFilter} Meetings` : 'All Meetings'}
                      </CardTitle>
                      <CardDescription className="text-xs text-slate-500">
                        Previous meetings for this company (by meeting number). Used to auto-set the next meeting number — e.g. after 90TH, next is 91ST.
                      </CardDescription>
                    </div>
                    <div className="flex items-center gap-2 text-xs">
                      <Badge variant="outline" className="font-semibold border-slate-200">
                        {companyMeetings.length} meeting{companyMeetings.length === 1 ? '' : 's'}
                      </Badge>
                      <Badge className="bg-emerald-50 text-emerald-700 border border-emerald-200 hover:bg-emerald-50 font-semibold">
                        Next: {nextMeetingNumber}
                      </Badge>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="p-0">
                  {loadingMeetings ? (
                    <div className="p-8 text-center text-xs text-slate-400">Loading meetings…</div>
                  ) : companyMeetings.length === 0 ? (
                    <div className="p-8 text-center text-xs text-slate-400">
                      {meetingTypeFilter !== 'all'
                        ? `No ${meetingTypeFilter} records found for this company.`
                        : 'No meeting records found for this company.'}
                    </div>
                  ) : (
                    <Table>
                      <TableHeader>
                        <TableRow className="bg-slate-50/80">
                          <TableHead className="text-xs font-semibold w-16">#</TableHead>
                          <TableHead className="text-xs font-semibold">Meeting No.</TableHead>
                          <TableHead className="text-xs font-semibold">Date</TableHead>
                          <TableHead className="text-xs font-semibold">Type</TableHead>
                          <TableHead className="text-xs font-semibold">Document</TableHead>
                          <TableHead className="text-xs font-semibold text-right">Action</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {companyMeetings.map((m, idx) => (
                          <TableRow key={m.id} className="hover:bg-slate-50/50">
                            <TableCell className="text-xs text-slate-400">{idx + 1}</TableCell>
                            <TableCell className="text-xs font-bold text-blue-700">
                              {m.meeting_number || '—'}
                            </TableCell>
                            <TableCell className="text-xs font-medium text-slate-800">
                              {formatMeetingDate(m.meeting_date)}
                            </TableCell>
                            <TableCell className="text-xs text-slate-600">{m.meeting_type || '—'}</TableCell>
                            <TableCell className="text-xs text-slate-500 truncate max-w-[200px]">
                              {m.file_path || '—'}
                            </TableCell>
                            <TableCell className="text-right">
                              {m.download_url && (
                                <a
                                  href={m.download_url}
                                  className="inline-flex items-center gap-1 text-xs font-semibold text-blue-600 hover:text-blue-800"
                                >
                                  <Download className="h-3.5 w-3.5" />
                                  Download
                                </a>
                              )}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  )}
                </CardContent>
              </Card>

              <Card className="border border-slate-200 shadow-xs rounded-xl bg-white overflow-hidden">
              <CardHeader className="border-b border-slate-100 bg-slate-50/50 pb-4">
                <CardTitle className="text-base font-bold text-slate-900">Schedule Board / Committee Meeting</CardTitle>
                <CardDescription className="text-xs text-slate-500">
                  {meetingTypeFilter !== 'all'
                    ? `Meeting type is set from the BU filter (${meetingTypeFilter}). Pick a date to continue.`
                    : 'Configure meeting parameters to launch the minutes generator.'}
                </CardDescription>
              </CardHeader>
              <CardContent className="p-6 space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                  <div className="space-y-1.5">
                    <Label className="text-xs font-semibold text-slate-700">Meeting Type *</Label>
                    <Select
                      value={calendarData.meetingType}
                      onValueChange={(v) => setCalendarData({ ...calendarData, meetingType: v, committeeName: v === 'Committee Meeting' ? calendarData.committeeName : '' })}
                      disabled={meetingTypeFilter !== 'all'}
                    >
                      <SelectTrigger className="bg-white border-slate-200 h-9 rounded-lg text-xs font-medium disabled:opacity-80 disabled:bg-slate-50">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-white">
                        {meetingTypes.map(t => <SelectItem key={t.value} value={t.value} className="text-xs">{t.label}</SelectItem>)}
                      </SelectContent>
                    </Select>
                    {meetingTypeFilter !== 'all' && (
                      <span className="text-[11px] text-slate-500">Locked from BU filter</span>
                    )}
                  </div>
                  
                  {(calendarData.meetingType === 'Committee Meeting' || (meetingTypeFilter !== 'all' && calendarData.committeeName)) && (
                    <div className="space-y-1.5">
                      <Label className="text-xs font-semibold text-slate-700">Committee Name *</Label>
                      <Input
                        placeholder="e.g. Audit Committee"
                        value={calendarData.committeeName}
                        onChange={(e) => setCalendarData({ ...calendarData, committeeName: e.target.value })}
                        disabled={meetingTypeFilter !== 'all'}
                        className="bg-white border-slate-200 h-9 rounded-lg text-xs disabled:opacity-80 disabled:bg-slate-50"
                      />
                    </div>
                  )}
                  
                  <div className="space-y-1.5">
                    <Label className="text-xs font-semibold text-slate-700">Meeting Date *</Label>
                    <Input 
                      type="date" 
                      value={calendarData.meetingDate} 
                      onChange={(e) => setCalendarData({ ...calendarData, meetingDate: e.target.value })} 
                      className="bg-white border-slate-200 h-9 rounded-lg text-xs" 
                    />
                    {calendarData.meetingDate && (
                      <span className="text-[11px] font-medium text-slate-500 block">
                        Day: {new Date(calendarData.meetingDate).toLocaleDateString('en-US', { weekday: 'long' })}
                      </span>
                    )}
                  </div>
                  
                  <div className="space-y-1.5">
                    <Label className="text-xs font-semibold text-slate-700">Start Time</Label>
                    <Input 
                      type="time" 
                      value={calendarData.meetingTime} 
                      onChange={(e) => setCalendarData({ ...calendarData, meetingTime: e.target.value })} 
                      className="bg-white border-slate-200 h-9 rounded-lg text-xs" 
                    />
                  </div>

                  <div className="space-y-1.5">
                    <Label className="text-xs font-semibold text-slate-700">Meeting No. (auto)</Label>
                    <div className="h-9 px-3 rounded-lg border border-emerald-200 bg-emerald-50 flex items-center text-xs font-bold text-emerald-700">
                      {nextMeetingNumber}
                    </div>
                    <span className="text-[11px] text-slate-500">
                      From previous meetings of this company{meetingTypeFilter !== 'all' ? ` / ${meetingTypeFilter}` : ''}.
                    </span>
                  </div>
                </div>

                <div className="pt-4 border-t border-slate-100 flex flex-col sm:flex-row items-center justify-between gap-4">
                  <span className="text-xs text-slate-500">
                    Custom DOCX templates can also be uploaded in Step 1 of the generator.
                  </span>
                  <div className="flex items-center gap-3 w-full sm:w-auto">
                    <Button
                      variant="outline"
                      className="text-xs font-semibold rounded-lg border-slate-200 h-9"
                      onClick={() => {
                        // Custom template path starts fresh
                        navigate('/minutes-preparation/form-generator', {
                          state: {
                            ...calendarData,
                            template: 'custom',
                            companyName: selectedCompany.name,
                            resetDraft: true
                          }
                        });
                      }}
                    >
                      <Upload className="h-3.5 w-3.5 mr-1.5 text-slate-500" />
                      Use Custom Template
                    </Button>
                    <Button
                      className="bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs rounded-lg h-9 px-5 shadow-xs"
                      disabled={!calendarData.meetingDate}
                      onClick={handleGenerateClick}
                    >
                      Continue to Generate Minutes
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
            </div>
          )}

          {/* TAB 2: SECRETARIAL COMPLIANCES */}
          {activeTab === 'compliances' && (
            <div className="space-y-6">
              {/* Compliance Stat Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <Card className="bg-green-50/50 border-green-200">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-lg flex items-center gap-2 text-green-800">
                      <CheckCircle2 className="h-5 w-5 text-green-600" />
                      Completed
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-3xl font-bold text-green-700">{complianceStats.completed}</p>
                    <p className="text-xs text-muted-foreground">Statutory filings finalized</p>
                  </CardContent>
                </Card>
                <Card className="bg-amber-50/50 border-amber-200">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-lg flex items-center gap-2 text-amber-800">
                      <Clock className="h-5 w-5 text-amber-600" />
                      Upcoming
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-3xl font-bold text-amber-700">{complianceStats.upcoming}</p>
                    <p className="text-xs text-muted-foreground">Due within the next 30 days</p>
                  </CardContent>
                </Card>
                <Card className="bg-red-50/50 border-red-200">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-lg flex items-center gap-2 text-red-800">
                      <AlertCircle className="h-5 w-5 text-red-600" />
                      Overdue
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-3xl font-bold text-red-700">{complianceStats.overdue}</p>
                    <p className="text-xs text-muted-foreground">Requires immediate action</p>
                  </CardContent>
                </Card>
              </div>

              {/* Compliance Table */}
              <Card>
                <CardHeader>
                  <CardTitle>Compliance Checklist</CardTitle>
                  <CardDescription>Required statutory form submissions for this company.</CardDescription>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Form/Requirement</TableHead>
                        <TableHead>Description</TableHead>
                        <TableHead>Due Date</TableHead>
                        <TableHead>Priority</TableHead>
                        <TableHead>Status</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {loadingCompliances ? (
                        <TableRow>
                          <TableCell colSpan={5} className="text-center py-6 text-slate-500">Loading checklists...</TableCell>
                        </TableRow>
                      ) : companyCompliances.length === 0 ? (
                        <TableRow>
                          <TableCell colSpan={5} className="text-center py-6 text-slate-500">No statutory compliances found for this company.</TableCell>
                        </TableRow>
                      ) : (
                        companyCompliances.map((c) => (
                          <TableRow key={c.id}>
                            <TableCell className="font-bold text-slate-800">{c.form}</TableCell>
                            <TableCell className="text-slate-600 text-sm">{c.description}</TableCell>
                            <TableCell className="text-slate-600 text-sm">{c.due_date}</TableCell>
                            <TableCell>
                              <Badge variant={c.priority === 'Critical' ? 'destructive' : c.priority === 'High' ? 'default' : 'secondary'}>
                                {c.priority}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              <Badge
                                className={
                                  c.status === 'Completed' ? 'bg-green-100 text-green-800 hover:bg-green-100' :
                                  c.status === 'Urgent' || c.status === 'Overdue' ? 'bg-red-100 text-red-800 hover:bg-red-100' :
                                  'bg-blue-100 text-blue-800 hover:bg-blue-100'
                                }
                              >
                                {c.status}
                              </Badge>
                            </TableCell>
                          </TableRow>
                        ))
                      )}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </div>
          )}

          {/* TAB 3: MEETING HISTORY */}
          {activeTab === 'history' && (
            <Card>
              <CardHeader>
                <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
                  <div>
                    <CardTitle>Past Minutes</CardTitle>
                    <CardDescription>
                      Minutes generated for this company. Full View / Edit / Finalize / Upload Signed is on the Meeting Minutes repository page.
                    </CardDescription>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    className="text-xs h-8 font-semibold border-slate-200"
                    onClick={() => navigate('/minutes-preparation/minutes')}
                  >
                    <FileText className="h-3.5 w-3.5 mr-1.5" />
                    Open Meeting Minutes Repository
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Meeting Type</TableHead>
                      <TableHead>Date</TableHead>
                      <TableHead>Created At</TableHead>
                      <TableHead>Action</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {currentHistory.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={4} className="text-center py-6 text-slate-500">No past minutes found.</TableCell>
                      </TableRow>
                    ) : (
                      currentHistory.map((item) => (
                        <TableRow key={item.id}>
                          <TableCell className="font-medium text-slate-800">{item.meeting_type}</TableCell>
                          <TableCell className="text-slate-600 text-sm">{item.meeting_date}</TableCell>
                          <TableCell className="text-slate-600 text-sm">{new Date(item.created_at).toLocaleString()}</TableCell>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              <Button variant="outline" size="sm" onClick={() => {
                                const link = document.createElement('a');
                                link.href = item.download_url;
                                link.download = item.file_path;
                                document.body.appendChild(link);
                                link.click();
                                document.body.removeChild(link);
                              }}>
                                <Download className="h-4 w-4 mr-1" /> Download
                              </Button>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleDeleteHistory(item.id)}
                                className="text-red-600 border-red-200 hover:bg-red-50 hover:text-red-700 h-8 text-xs font-semibold"
                              >
                                <Trash2 className="h-3.5 w-3.5 mr-1" /> Delete
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>

                {companyHistory.length > historyPageSize && (
                  <div className="flex items-center justify-between pt-4 text-xs text-gray-500">
                    <span>Page {historyPage} of {totalHistoryPages}</span>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={historyPage <= 1}
                        onClick={() => setHistoryPage(p => Math.max(1, p - 1))}
                        className="h-7 px-2"
                      >
                        Previous
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={historyPage >= totalHistoryPages}
                        onClick={() => setHistoryPage(p => p + 1)}
                        className="h-7 px-2"
                      >
                        Next
                      </Button>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* TAB 4: DIRECTORS LIST */}
          {activeTab === 'directors' && (
            <Card>
              <CardHeader>
                <CardTitle>Board of Directors</CardTitle>
                <CardDescription>Active board members registered for this corporate entity.</CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Director Name</TableHead>
                      <TableHead>DIN (Director Identification Number)</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {directorsList.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={2} className="text-center py-6 text-slate-500">No board members linked to this company.</TableCell>
                      </TableRow>
                    ) : (
                      directorsList.map((d) => (
                        <TableRow key={d.din}>
                          <TableCell className="font-bold text-slate-800">{d.name}</TableCell>
                          <TableCell className="font-mono text-slate-600">{d.din}</TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </ProductDashboardLayout>
  );
};

export default MinutesGenerator;
