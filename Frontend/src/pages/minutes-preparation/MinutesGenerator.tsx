/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useState, useEffect, useMemo } from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Calendar, Clock, Download, FileText, Home, History, FileSpreadsheet, Plus, Upload, BookOpen, ChevronRight, ArrowLeft, Search, Building2, Layers, AlertCircle, CheckCircle2, User, Users, Trash2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import ProductDashboardLayout from '@/components/layout/ProductDashboardLayout';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { getMinutesNavItems } from '@/constants/minutesNavigation';
import { companyPresets } from '@/constants/companyPresets';
import { useVertical } from '@/contexts/VerticalContext';

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

const MinutesGenerator = () => {
  const navigate = useNavigate();
  
  // Local state to track which BU is currently selected in Step 1
  const [activeVertical, setActiveVertical] = useState<any | null>(null);

  // Clear selected company & vertical on mount so the user starts fresh at Step 1 Grid
  useEffect(() => {
    setSelectedCompany(null);
    setSelectedVertical(null);
    setActiveVertical(null);
  }, []);

  // Dynamic Tab state for selected company details
  const [activeTab, setActiveTab] = useState<'schedule' | 'compliances' | 'history' | 'directors'>('schedule');

  // History & Compliance state
  const [history, setHistory] = useState<any[]>([]);
  const [compliances, setCompliances] = useState<any[]>([]);
  const [loadingCompliances, setLoadingCompliances] = useState(false);

  // Pagination for history
  const [historyPage, setHistoryPage] = useState<number>(1);
  const historyPageSize = 5;

  const {
    verticals,
    setSelectedVertical,
    selectedCompany,
    setSelectedCompany,
    loadingVerticals
  } = useVertical();

  // Local state for listing companies under the activeVertical
  const [localCompanies, setLocalCompanies] = useState<any[]>([]);
  const [loadingLocalCompanies, setLoadingLocalCompanies] = useState(false);
  const [localTotalCompanies, setLocalTotalCompanies] = useState<number>(0);
  const [localSearchQuery, setLocalSearchQuery] = useState<string>("");
  const [localPage, setLocalPage] = useState<number>(1);
  const localPageSize = 15;

  const [directorsList, setDirectorsList] = useState<any[]>([]);

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

  // Fetch companies for selected activeVertical, localPage, or localSearchQuery
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
        const res = await fetch(`/api/verticals/${activeVertical.id}/companies?q=${encodeURIComponent(localSearchQuery)}&limit=${localPageSize}&offset=${offset}`);
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
  }, [activeVertical, localSearchQuery, localPage]);

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

  // Filter History for selected company
  const companyHistory = useMemo(() => {
    if (!selectedCompany) return [];
    const compClean = cleanNameForCompare(selectedCompany.name);
    return history.filter(h => {
      if (!h.company_name) return false;
      return cleanNameForCompare(h.company_name).includes(compClean) || compClean.includes(cleanNameForCompare(h.company_name));
    });
  }, [history, selectedCompany]);

  const handleDeleteHistory = async (id: number) => {
    if (!window.confirm("Are you sure you want to delete this document? This will permanently delete it from the database and disk.")) return;
    try {
      const res = await fetch(`/api/generated-minutes/${id}`, {
        method: 'DELETE'
      });
      if (res.ok) {
        setHistory(prev => prev.filter(item => item.id !== id));
      } else {
        alert("Failed to delete document.");
      }
    } catch (err) {
      console.error("Error deleting document:", err);
      alert("Failed to delete document.");
    }
  };

  const handleGenerateClick = () => {
    if (!selectedCompany) return;
    sessionStorage.removeItem('minutes_form_draft');
    const selectedPreset = companyPresets.find(c => c.name === selectedCompany.name);
    const stateToPass = {
      companyName: selectedCompany.name,
      meetingDate: calendarData.meetingDate,
      meetingDay: calendarData.meetingDate ? new Date(calendarData.meetingDate).toLocaleDateString('en-US', { weekday: 'long' }) : '',
      meetingType: calendarData.meetingType,
      committeeName: calendarData.committeeName,
      timeCommenced: calendarData.meetingTime,
      meetingPlace: selectedPreset ? selectedPreset.address : "Adani Corporate House, Ahmedabad",
      presentDirectors: directorsList.length > 0 ? directorsList : (selectedPreset ? selectedPreset.directors : []),
      chairmanName: directorsList[0]?.name || (selectedPreset ? selectedPreset.directors[0]?.name : ''),
      resetDraft: true
    };
    navigate('/minutes-preparation/form-generator', { state: stateToPass });
  };

  const meetingTypes = [
    { value: "Board Meeting", label: "Board Meeting" },
    { value: "Committee Meeting", label: "Committee Meeting" },
    { value: "Annual General Meeting", label: "Annual General Meeting" },
    { value: "Extraordinary General Meeting", label: "Extraordinary General Meeting" }
  ];

  const navigationItems = getMinutesNavItems('dashboard');

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

                  {/* Search input inline */}
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

                {loadingLocalCompanies ? (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {[1, 2, 3, 4, 5, 6].map((i) => (
                      <div key={i} className="animate-pulse bg-white border border-slate-100 rounded-2xl h-24 p-6"></div>
                    ))}
                  </div>
                ) : localCompanies.length === 0 ? (
                  <div className="text-center py-12 bg-white rounded-2xl border border-dashed border-slate-200 text-slate-400 text-sm">
                    No entities found matching "{localSearchQuery}" under {activeVertical.name}.
                  </div>
                ) : (
                  <>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                      {localCompanies.map((c) => {
                        const abbr = getCompanyAbbreviation(c.name);
                        return (
                          <div
                            key={c.id}
                            onClick={() => {
                              setSelectedVertical(activeVertical);
                              setSelectedCompany(c);
                              setActiveTab('schedule');
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
      </ProductDashboardLayout>
    );
  }

  // --- RENDER 2: SCROUPED DETAIL TABS FOR SELECTED COMPANY ---
  const indexOfLastHistory = historyPage * historyPageSize;
  const indexOfFirstHistory = indexOfLastHistory - historyPageSize;
  const currentHistory = companyHistory.slice(indexOfFirstHistory, indexOfLastHistory);
  const totalHistoryPages = Math.ceil(companyHistory.length / historyPageSize) || 1;

  const handleBackToGrid = () => {
    setSelectedCompany(null);
    setSelectedVertical(null);
    setActiveVertical(null);
  };

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
            <Card className="border border-slate-200 shadow-xs rounded-xl bg-white overflow-hidden">
              <CardHeader className="border-b border-slate-100 bg-slate-50/50 pb-4">
                <CardTitle className="text-base font-bold text-slate-900">Schedule Board / Committee Meeting</CardTitle>
                <CardDescription className="text-xs text-slate-500">Configure meeting parameters to launch the minutes generator.</CardDescription>
              </CardHeader>
              <CardContent className="p-6 space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                  <div className="space-y-1.5">
                    <Label className="text-xs font-semibold text-slate-700">Meeting Type *</Label>
                    <Select value={calendarData.meetingType} onValueChange={(v) => setCalendarData({ ...calendarData, meetingType: v })}>
                      <SelectTrigger className="bg-white border-slate-200 h-9 rounded-lg text-xs font-medium"><SelectValue /></SelectTrigger>
                      <SelectContent className="bg-white">
                        {meetingTypes.map(t => <SelectItem key={t.value} value={t.value} className="text-xs">{t.label}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  </div>
                  
                  {calendarData.meetingType === 'Committee Meeting' && (
                    <div className="space-y-1.5">
                      <Label className="text-xs font-semibold text-slate-700">Committee Name *</Label>
                      <Input
                        placeholder="e.g. Audit Committee"
                        value={calendarData.committeeName}
                        onChange={(e) => setCalendarData({ ...calendarData, committeeName: e.target.value })}
                        className="bg-white border-slate-200 h-9 rounded-lg text-xs"
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
                        sessionStorage.removeItem('minutes_form_draft');
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
                <CardTitle>Past Minutes & Document Repository</CardTitle>
                <CardDescription>Download and view historical board documents.</CardDescription>
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
