import React, { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  FileText,
  Clock,
  Calendar,
  Download,
  Trash,
  Search,
  Folder,
  FolderOpen,
  ChevronRight,
  ChevronDown,
  FileSpreadsheet,
  Mail,
  Table as TableIcon,
  X,
  Send
} from 'lucide-react';
import ProductDashboardLayout from '@/components/layout/ProductDashboardLayout';
import { getMinutesNavItems } from '@/constants/minutesNavigation';

// Dynamically classify companies into Adani Business Units (BU)
const getBusinessUnit = (companyName: string): string => {
  const name = companyName.toLowerCase();
  if (name.includes('green') || name.includes('solar') || name.includes('wind') || name.includes('power') || name.includes('energy')) {
    return 'Energy';
  }
  if (name.includes('ports') || name.includes('logistics') || name.includes('sez') || name.includes('port')) {
    return 'Ports & Logistics';
  }
  if (name.includes('gas') || name.includes('utilities')) {
    return 'Gas & Utilities';
  }
  if (name.includes('transmission') || name.includes('electricity') || name.includes('road') || name.includes('infrastructure')) {
    return 'Infrastructure';
  }
  if (name.includes('digital') || name.includes('media') || name.includes('ndtv') || name.includes('data')) {
    return 'Digital & Media';
  }
  return 'Other / General';
};

const MeetingMinutes = () => {
  const navigationItems = getMinutesNavItems('minutes');

  const [meetingMinutes, setMeetingMinutes] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  // Email Delivery Modal state
  const [emailModalFile, setEmailModalFile] = useState<any>(null);
  const [recipientEmail, setRecipientEmail] = useState('');
  const [emailSubject, setEmailSubject] = useState('');
  const [emailBody, setEmailBody] = useState('');
  const [isSendingEmail, setIsSendingEmail] = useState(false);

  // Extracted Content & Structured Tables Modal state
  const [contentModalDoc, setContentModalDoc] = useState<any>(null);
  const [loadingDocContent, setLoadingDocContent] = useState(false);

  // Selection filter state for folder tree navigation
  const [selectedPath, setSelectedPath] = useState<{
    year?: string;
    bu?: string;
    company?: string;
    meetingType?: string;
  }>({});

  // Tree nodes expanded state
  const [expandedNodes, setExpandedNodes] = useState<Record<string, boolean>>({
    'root': true
  });

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/generated-minutes');
      if (res.ok) {
        const data = await res.json();
        setMeetingMinutes(data.data || []);
      }
    } catch (err) {
      console.error("Failed to fetch history", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleSendEmail = async () => {
    if (!recipientEmail || !emailModalFile) return;
    setIsSendingEmail(true);
    try {
      const res = await fetch('/api/email/send-mom', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          to_emails: [recipientEmail],
          subject: emailSubject || `Meeting Minutes - ${emailModalFile.company_name}`,
          body: emailBody || `Please find attached the meeting minutes for ${emailModalFile.company_name}.`,
          filename: emailModalFile.file_path
        })
      });
      if (res.ok) {
        alert(`Email sent successfully to ${recipientEmail}!`);
        setEmailModalFile(null);
        setRecipientEmail('');
      } else {
        const errData = await res.json();
        alert(`Failed to send email: ${errData.detail || 'SMTP error'}`);
      }
    } catch (err) {
      console.error("Failed to send email", err);
      alert("Error delivering email. Check SMTP server configuration.");
    } finally {
      setIsSendingEmail(false);
    }
  };

  const openDocumentContent = async (docId: number) => {
    setLoadingDocContent(true);
    try {
      const res = await fetch(`/api/repository/document-content/${docId}`);
      if (res.ok) {
        const data = await res.json();
        setContentModalDoc(data);
      }
    } catch (err) {
      console.error("Failed to fetch parsed content", err);
    } finally {
      setLoadingDocContent(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this meeting minute?')) return;
    try {
      const res = await fetch(`/api/generated-minutes/${id}`, { method: 'DELETE' });
      if (res.ok) {
        setMeetingMinutes(prev => prev.filter(m => m.id !== id));
      }
    } catch (err) {
      console.error("Failed to delete", err);
    }
  };

  const toggleNode = (nodeId: string) => {
    setExpandedNodes(prev => ({
      ...prev,
      [nodeId]: !prev[nodeId]
    }));
  };

  // Build the hierarchical folder tree data structure
  const folderTree = useMemo(() => {
    const tree: any = {};
    meetingMinutes.forEach(minute => {
      const date = new Date(minute.meeting_date);
      const year = isNaN(date.getTime()) ? 'Unknown' : date.getFullYear().toString();
      const bu = getBusinessUnit(minute.company_name);
      const company = minute.company_name;
      const mType = minute.meeting_type;

      if (!tree[year]) tree[year] = {};
      if (!tree[year][bu]) tree[year][bu] = {};
      if (!tree[year][bu][company]) tree[year][bu][company] = {};
      if (!tree[year][bu][company][mType]) tree[year][bu][company][mType] = [];

      tree[year][bu][company][mType].push(minute);
    });
    return tree;
  }, [meetingMinutes]);

  // Filter minutes list based on selected folder node and search query
  const filteredMinutes = useMemo(() => {
    return meetingMinutes.filter(minute => {
      // 1. Folder path filters
      const date = new Date(minute.meeting_date);
      const year = isNaN(date.getTime()) ? 'Unknown' : date.getFullYear().toString();
      const bu = getBusinessUnit(minute.company_name);

      if (selectedPath.year && year !== selectedPath.year) return false;
      if (selectedPath.bu && bu !== selectedPath.bu) return false;
      if (selectedPath.company && minute.company_name !== selectedPath.company) return false;
      if (selectedPath.meetingType && minute.meeting_type !== selectedPath.meetingType) return false;

      // 2. Search keyword filter
      if (searchQuery.trim() !== '') {
        const query = searchQuery.toLowerCase();
        return (
          minute.company_name.toLowerCase().includes(query) ||
          minute.meeting_type.toLowerCase().includes(query) ||
          minute.meeting_date.toLowerCase().includes(query) ||
          (minute.file_path && minute.file_path.toLowerCase().includes(query))
        );
      }

      return true;
    });
  }, [meetingMinutes, selectedPath, searchQuery]);

  return (
    <ProductDashboardLayout
      productName="Generate Minutes"
      productRoute="/minutes-preparation"
      navigationItems={navigationItems}
    >
      <div className="p-4 h-[calc(100vh-100px)] flex flex-col overflow-hidden">
        <div className="border border-slate-200 rounded-xl bg-white shadow-xs p-5 flex flex-col h-full overflow-hidden space-y-4">
          <div className="pb-3 border-b border-slate-100 flex items-center justify-between shrink-0">
            <div>
              <h1 className="text-xl font-bold text-slate-900">Meeting Minutes Repository</h1>
              <p className="text-xs text-slate-500 mt-0.5">Browse, upload and download documents hierarchically by Business Unit, Company and Year.</p>
            </div>
            <div className="flex items-center gap-2">
              <label htmlFor="repoFileUpload" className="cursor-pointer flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-xs transition-colors">
                <FileText className="h-4 w-4" />
                <span>Upload Word/PDF</span>
              </label>
              <input
                id="repoFileUpload"
                type="file"
                accept=".docx,.pdf"
                className="hidden"
                onChange={async (e) => {
                  const file = e.target.files?.[0];
                  if (!file) return;
                  const formData = new FormData();
                  formData.append('file', file);
                  formData.append('vertical_name', selectedPath.bu || 'Energy');
                  formData.append('company_name', selectedPath.company || 'General_Company');
                  formData.append('meeting_type', selectedPath.meetingType || 'Board_Meeting');
                  formData.append('meeting_year', selectedPath.year || '2026');

                  try {
                    const res = await fetch('/api/repository/upload', {
                      method: 'POST',
                      body: formData,
                    });
                    if (res.ok) {
                      alert('File uploaded to repository successfully!');
                      fetchHistory();
                    } else {
                      alert('Failed to upload document.');
                    }
                  } catch (err) {
                    console.error('Upload error', err);
                  }
                }}
              />
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-4 gap-5 items-stretch flex-1 min-h-0 overflow-hidden">
            {/* Left Side: Structured Folder Tree Browser */}
            <Card className="lg:col-span-1 border border-slate-200 shadow-none bg-white rounded-xl overflow-hidden flex flex-col h-full">
              <CardHeader className="bg-slate-50/50 pb-3 border-b border-slate-100 shrink-0">
                <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-2">
                  <Folder className="h-4 w-4 text-slate-400" />
                  Folder Navigator
                </CardTitle>
              </CardHeader>
              <CardContent className="p-3.5 overflow-y-auto flex-1 text-xs bg-white scrollbar-thin">
                <div className="space-y-1">
                  {/* Root Node: All Files */}
                  <div
                    onClick={() => setSelectedPath({})}
                    className={`flex items-center gap-2 py-2 px-3 rounded-lg cursor-pointer transition-colors ${Object.keys(selectedPath).length === 0 ? 'bg-slate-100 text-slate-900 font-semibold' : 'hover:bg-slate-50 text-slate-700'
                      }`}
                  >
                    <FolderOpen className="h-4 w-4 shrink-0 text-slate-500" />
                    <span>All Generated Minutes</span>
                  </div>

                  {/* Years Nodes */}
                  <div className="pl-3 border-l border-slate-200/60 space-y-1 mt-1">
                    {Object.keys(folderTree).sort().reverse().map(year => {
                      const yearNodeId = `year-${year}`;
                      const isYearExpanded = expandedNodes[yearNodeId];
                      const isYearSelected = selectedPath.year === year && !selectedPath.bu;

                      return (
                        <div key={year} className="space-y-1">
                          <div className="flex items-center justify-between group">
                            <div
                              onClick={() => setSelectedPath({ year })}
                              className={`flex items-center gap-2 py-1.5 px-2 rounded-md cursor-pointer transition-colors flex-1 ${isYearSelected ? 'bg-slate-100 text-slate-900 font-semibold' : 'hover:bg-slate-50 text-slate-600'
                                }`}
                            >
                              <Folder className="h-3.5 w-3.5 shrink-0 text-slate-400" />
                              <span>{year}</span>
                            </div>
                            <button
                              onClick={() => toggleNode(yearNodeId)}
                              className="p-1 hover:bg-slate-100 rounded text-slate-400"
                            >
                              {isYearExpanded ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
                            </button>
                          </div>

                          {/* Business Unit (BU) Nodes */}
                          {isYearExpanded && (
                            <div className="pl-4 border-l border-slate-200/60 space-y-1">
                              {Object.keys(folderTree[year]).sort().map(bu => {
                                const buNodeId = `bu-${year}-${bu}`;
                                const isBuExpanded = expandedNodes[buNodeId];
                                const isBuSelected = selectedPath.year === year && selectedPath.bu === bu && !selectedPath.company;

                                return (
                                  <div key={bu} className="space-y-1">
                                    <div className="flex items-center justify-between group">
                                      <div
                                        onClick={() => setSelectedPath({ year, bu })}
                                        className={`flex items-center gap-2 py-1.5 px-2 rounded-md cursor-pointer transition-colors flex-1 ${isBuSelected ? 'bg-slate-100 text-slate-900 font-semibold' : 'hover:bg-slate-50 text-slate-600'
                                          }`}
                                      >
                                        <Folder className="h-3.5 w-3.5 shrink-0 text-slate-400" />
                                        <span className="truncate">{bu}</span>
                                      </div>
                                      <button
                                        onClick={() => toggleNode(buNodeId)}
                                        className="p-1 hover:bg-slate-100 rounded text-slate-400"
                                      >
                                        {isBuExpanded ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
                                      </button>
                                    </div>

                                    {/* Company Nodes */}
                                    {isBuExpanded && (
                                      <div className="pl-4 border-l border-slate-200/60 space-y-1">
                                        {Object.keys(folderTree[year][bu]).sort().map(company => {
                                          const companyNodeId = `company-${year}-${bu}-${company}`;
                                          const isCompanyExpanded = expandedNodes[companyNodeId];
                                          const isCompanySelected = selectedPath.year === year && selectedPath.bu === bu && selectedPath.company === company && !selectedPath.meetingType;

                                          return (
                                            <div key={company} className="space-y-1">
                                              <div className="flex items-center justify-between group">
                                                <div
                                                  onClick={() => setSelectedPath({ year, bu, company })}
                                                  className={`flex items-center gap-2 py-1.5 px-2 rounded-md cursor-pointer transition-colors flex-1 min-w-0 ${isCompanySelected ? 'bg-slate-100 text-slate-900 font-semibold' : 'hover:bg-slate-50 text-slate-600'
                                                    }`}
                                                >
                                                  <Folder className="h-3.5 w-3.5 shrink-0 text-slate-400" />
                                                  <span className="truncate">{company}</span>
                                                </div>
                                                <button
                                                  onClick={() => toggleNode(companyNodeId)}
                                                  className="p-1 hover:bg-slate-100 rounded text-slate-400"
                                                >
                                                  {isCompanyExpanded ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
                                                </button>
                                              </div>

                                              {/* Meeting Type Nodes */}
                                              {isCompanyExpanded && (
                                                <div className="pl-4 border-l border-slate-200/60 space-y-1">
                                                  {Object.keys(folderTree[year][bu][company]).sort().map(meetingType => {
                                                    const isTypeSelected = selectedPath.year === year && selectedPath.bu === bu && selectedPath.company === company && selectedPath.meetingType === meetingType;

                                                    return (
                                                      <div
                                                        key={meetingType}
                                                        onClick={() => setSelectedPath({ year, bu, company, meetingType })}
                                                        className={`flex items-center gap-2 py-1 px-2 rounded-md cursor-pointer transition-colors truncate ${isTypeSelected ? 'bg-slate-100 text-slate-900 font-semibold' : 'hover:bg-slate-50 text-slate-500'
                                                          }`}
                                                      >
                                                        <FileSpreadsheet className="h-3 w-3 shrink-0 text-slate-400" />
                                                        <span className="text-[11px] truncate">{meetingType}</span>
                                                      </div>
                                                    );
                                                  })}
                                                </div>
                                              )}
                                            </div>
                                          );
                                        })}
                                      </div>
                                    )}
                                  </div>
                                );
                              })}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Right Side: Searchable Files Grid */}
            <div className="lg:col-span-3 flex flex-col h-full space-y-3 min-h-0 overflow-hidden">
              {/* Search and Filters Header */}
              <div className="flex flex-col sm:flex-row gap-3 bg-white p-3 border border-slate-200 rounded-xl shadow-none shrink-0">
                <div className="flex-1 relative">
                  <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                  <Input
                    placeholder="Search minutes by title, date, BU or company name..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-9 bg-white h-9 text-xs rounded-lg border-slate-200"
                  />
                </div>
                {Object.keys(selectedPath).length > 0 && (
                  <Button
                    variant="outline"
                    onClick={() => setSelectedPath({})}
                    className="text-slate-600 text-xs shrink-0 h-9 rounded-lg border-slate-200 font-semibold bg-white"
                  >
                    Clear Folder Filter
                  </Button>
                )}
              </div>

              {/* Folder breadcrumbs */}
              {Object.keys(selectedPath).length > 0 && (
                <div className="flex items-center gap-2 text-[10px] font-bold text-slate-500 uppercase px-1 tracking-wider shrink-0">
                  <span>Folders: </span>
                  {selectedPath.year && <span className="bg-slate-100 px-2 py-0.5 rounded text-slate-700">{selectedPath.year}</span>}
                  {selectedPath.bu && <span className="text-slate-400">➔</span>}
                  {selectedPath.bu && <span className="bg-slate-100 px-2 py-0.5 rounded text-slate-700">{selectedPath.bu}</span>}
                  {selectedPath.company && <span className="text-slate-400">➔</span>}
                  {selectedPath.company && <span className="bg-slate-100 px-2 py-0.5 rounded text-slate-700 truncate max-w-[150px]">{selectedPath.company}</span>}
                  {selectedPath.meetingType && <span className="text-slate-400">➔</span>}
                  {selectedPath.meetingType && <span className="bg-slate-100 px-2 py-0.5 rounded text-slate-700">{selectedPath.meetingType}</span>}
                </div>
              )}

              {/* Files List */}
              <Card className="border border-slate-200 shadow-none bg-white rounded-xl overflow-hidden flex-1 flex flex-col min-h-0">
                <CardContent className="p-4 sm:p-5 overflow-y-auto flex-1 pr-2">
                  <div className="space-y-3">
                    {filteredMinutes.map((minute) => (
                      <div
                        key={minute.id}
                        className="group flex flex-col sm:flex-row items-start sm:items-center justify-between p-3.5 border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors gap-4"
                      >
                        <div className="flex items-center gap-3.5 flex-1 min-w-0">
                          <div className="bg-slate-100 p-2.5 rounded-lg text-slate-600 shrink-0">
                            <FileText className="h-5 w-5" />
                          </div>
                          <div className="space-y-1 min-w-0">
                            <h3 className="font-bold text-sm text-slate-900 truncate">
                              {minute.company_name}
                            </h3>
                            <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-500">
                              <span className="bg-slate-100 text-slate-700 px-2 py-0.5 rounded-md font-medium text-[10px]">
                                {getBusinessUnit(minute.company_name)}
                              </span>
                              <span className="flex items-center gap-1 font-mono text-[10px]">
                                <Calendar className="h-3 w-3 text-slate-400" />
                                {minute.meeting_date}
                              </span>
                              <span className="flex items-center gap-1 text-[11px]">
                                <Clock className="h-3 w-3 text-slate-400" />
                                {minute.meeting_type}
                              </span>
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center gap-2 w-full sm:w-auto shrink-0 border-t sm:border-t-0 pt-2 sm:pt-0 border-slate-100">
                          <Button
                            variant="outline"
                            size="sm"
                            className="flex-1 sm:flex-none h-8 px-2.5 rounded-lg border-slate-200 text-blue-700 hover:bg-blue-50 font-semibold text-xs bg-white"
                            onClick={() => openDocumentContent(minute.id)}
                            title="View Extracted Text & Structured Tables"
                          >
                            <TableIcon className="h-3.5 w-3.5 mr-1 text-blue-600" /> Content
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            className="flex-1 sm:flex-none h-8 px-2.5 rounded-lg border-slate-200 text-slate-700 hover:bg-slate-50 font-semibold text-xs bg-white"
                            onClick={() => {
                              setEmailModalFile(minute);
                              setEmailSubject(`Meeting Minutes - ${minute.company_name} (${minute.meeting_date})`);
                              setEmailBody(`Dear Team,\n\nPlease find attached the Meeting Minutes document for ${minute.company_name} (${minute.meeting_type}).\n\nRegards,\nCompany Secretarial Team`);
                            }}
                            title="Send MOM via Email"
                          >
                            <Mail className="h-3.5 w-3.5 mr-1 text-slate-500" /> Email
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            className="flex-1 sm:flex-none h-8 px-2.5 rounded-lg border-slate-200 text-slate-700 font-semibold text-xs bg-white"
                            onClick={() => {
                              const link = document.createElement('a');
                              link.href = minute.download_url;
                              link.download = minute.file_path;
                              document.body.appendChild(link);
                              link.click();
                              document.body.removeChild(link);
                            }}
                          >
                            <Download className="h-3.5 w-3.5 mr-1 text-slate-500" /> Download
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-8 px-2.5 rounded-lg text-slate-400 hover:text-red-700 hover:bg-red-50 text-xs font-semibold"
                            onClick={() => handleDelete(minute.id)}
                          >
                            <Trash className="h-3.5 w-3.5" />
                          </Button>
                        </div>
                      </div>
                    ))}

                    {!loading && filteredMinutes.length === 0 && (
                      <div className="text-center py-10">
                        <FileText className="h-8 w-8 text-slate-300 mx-auto mb-2" />
                        <p className="text-slate-400 text-xs font-medium">No generated minutes found.</p>
                      </div>
                    )}

                    {loading && (
                      <div className="text-center py-10">
                        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-slate-600 mx-auto"></div>
                        <p className="mt-2 text-slate-500 text-xs font-medium">Loading history...</p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </div>

      {/* --- EMAIL MOM DELIVERY MODAL --- */}
      {emailModalFile && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-xl border border-slate-200 w-full max-w-md p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-bold text-slate-900 flex items-center gap-2 text-base">
                <Mail className="h-5 w-5 text-blue-600" /> Send Meeting Minutes Email
              </h3>
              <button onClick={() => setEmailModalFile(null)} className="text-slate-400 hover:text-slate-600 p-1 rounded-md">
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="font-semibold text-slate-700 block mb-1">Attachment</label>
                <div className="p-2 bg-slate-50 border border-slate-200 rounded-md font-mono text-slate-600 truncate">
                  {emailModalFile.file_path}
                </div>
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">Recipient Email Address *</label>
                <Input
                  type="email"
                  placeholder="e.g. secretarial@adani.com"
                  value={recipientEmail}
                  onChange={(e) => setRecipientEmail(e.target.value)}
                  className="h-9 text-xs"
                />
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">Subject</label>
                <Input
                  value={emailSubject}
                  onChange={(e) => setEmailSubject(e.target.value)}
                  className="h-9 text-xs"
                />
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">Message Body</label>
                <textarea
                  rows={4}
                  value={emailBody}
                  onChange={(e) => setEmailBody(e.target.value)}
                  className="w-full p-2 border border-slate-200 rounded-md text-xs font-sans focus:outline-none focus:border-blue-500"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
              <Button variant="outline" size="sm" onClick={() => setEmailModalFile(null)} className="h-9 text-xs font-medium">
                Cancel
              </Button>
              <Button
                size="sm"
                disabled={!recipientEmail || isSendingEmail}
                onClick={handleSendEmail}
                className="h-9 text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white"
              >
                <Send className="h-3.5 w-3.5 mr-1.5" />
                {isSendingEmail ? "Sending..." : "Send Email"}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* --- EXTRACTED TEXT & STRUCTURED TABLES MODAL --- */}
      {contentModalDoc && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-xl border border-slate-200 w-full max-w-3xl max-h-[85vh] flex flex-col p-6 space-y-4 overflow-hidden">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3 shrink-0">
              <div>
                <h3 className="font-bold text-slate-900 flex items-center gap-2 text-base">
                  <TableIcon className="h-5 w-5 text-blue-600" /> Extracted Document Content & Parsed Tables
                </h3>
                <p className="text-xs text-slate-500">{contentModalDoc.filename} ({contentModalDoc.file_type?.toUpperCase()})</p>
              </div>
              <button onClick={() => setContentModalDoc(null)} className="text-slate-400 hover:text-slate-600 p-1 rounded-md">
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="overflow-y-auto space-y-6 pr-2 flex-1 text-xs">
              {/* Parsed Tables Section */}
              {contentModalDoc.tables && contentModalDoc.tables.length > 0 && (
                <div className="space-y-3">
                  <h4 className="font-bold text-slate-800 text-xs uppercase tracking-wider flex items-center gap-1.5">
                    <TableIcon className="h-4 w-4 text-blue-600" /> Parsed Tables ({contentModalDoc.tables.length})
                  </h4>
                  {contentModalDoc.tables.map((tbl: any, idx: number) => (
                    <div key={idx} className="border border-slate-200 rounded-lg overflow-hidden bg-white shadow-2xs">
                      <div className="bg-slate-50 px-3 py-1.5 border-b border-slate-200 text-[11px] font-semibold text-slate-600">
                        Table #{idx + 1} {tbl.page ? `(Page ${tbl.page})` : ''}
                      </div>
                      <div className="overflow-x-auto">
                        <table className="w-full text-left text-xs border-collapse">
                          {tbl.headers && tbl.headers.length > 0 && (
                            <thead>
                              <tr className="bg-slate-100/70 border-b border-slate-200">
                                {tbl.headers.map((h: string, hIdx: number) => (
                                  <th key={hIdx} className="p-2 font-bold text-slate-700 border-r border-slate-200 last:border-r-0">
                                    {h}
                                  </th>
                                ))}
                              </tr>
                            </thead>
                          )}
                          <tbody>
                            {tbl.rows && tbl.rows.map((r: string[], rIdx: number) => (
                              <tr key={rIdx} className="border-b border-slate-100 last:border-b-0 hover:bg-slate-50">
                                {r.map((cell: string, cIdx: number) => (
                                  <td key={cIdx} className="p-2 text-slate-600 border-r border-slate-100 last:border-r-0 font-serif">
                                    {cell}
                                  </td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Extracted Paragraph Text Section */}
              <div className="space-y-2">
                <h4 className="font-bold text-slate-800 text-xs uppercase tracking-wider flex items-center gap-1.5">
                  <FileText className="h-4 w-4 text-slate-600" /> Extracted Text Content ({contentModalDoc.paragraph_count} paragraphs)
                </h4>
                <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg font-serif leading-relaxed text-slate-800 whitespace-pre-wrap max-h-60 overflow-y-auto">
                  {contentModalDoc.extracted_text || "No plain text extracted."}
                </div>
              </div>
            </div>

            <div className="flex justify-end pt-2 border-t border-slate-100 shrink-0">
              <Button size="sm" onClick={() => setContentModalDoc(null)} className="h-8 text-xs font-semibold">
                Close Viewer
              </Button>
            </div>
          </div>
        </div>
      )}
    </ProductDashboardLayout>
  );
};

export default MeetingMinutes;