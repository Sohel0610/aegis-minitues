import React, { useState, useEffect, useMemo, useRef } from 'react';
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
  Send,
  Lock,
  CheckCircle2,
  Pencil,
  Upload,
  Eye,
  Save
} from 'lucide-react';
import ProductDashboardLayout from '@/components/layout/ProductDashboardLayout';
import { getMinutesNavItems } from '@/constants/minutesNavigation';
import { useVertical } from '@/contexts/VerticalContext';

const cleanCompanyName = (name: string) => {
  let s = (name || '').toLowerCase();
  // Normalize common legal-form variants so "Ltd." matches "Limited"
  s = s
    .replace(/\bprivate\s+limited\b/g, 'pvt ltd')
    .replace(/\bpvt\.?\s*ltd\.?\b/g, 'pvt ltd')
    .replace(/\blimited\b/g, 'ltd')
    .replace(/\bltd\.?\b/g, 'ltd');
  return s.replace(/[^a-z0-9]/g, '');
};

const sameCompany = (a?: string, b?: string) => {
  if (!a || !b) return false;
  if (a.trim() === b.trim()) return true;
  const ca = cleanCompanyName(a);
  const cb = cleanCompanyName(b);
  if (!ca || !cb) return false;
  if (ca === cb) return true;
  // Allow short alias match only when one is a clear prefix of the other
  // e.g. avoid matching "Twenty Five B" with plain "Green Energy"
  return false;
};
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
  const { selectedCompany } = useVertical();
  const reviseInputRef = useRef<HTMLInputElement>(null);
  const signedInputRef = useRef<HTMLInputElement>(null);

  const [meetingMinutes, setMeetingMinutes] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  // Email Delivery Modal state
  const [emailModalFile, setEmailModalFile] = useState<any>(null);
  const [recipientEmail, setRecipientEmail] = useState('');
  const [emailSubject, setEmailSubject] = useState('');
  const [emailBody, setEmailBody] = useState('');
  const [isSendingEmail, setIsSendingEmail] = useState(false);

  // In-app document viewer / editor
  const [contentModalDoc, setContentModalDoc] = useState<any>(null);
  const [viewerMode, setViewerMode] = useState<'view' | 'edit'>('view');
  const [editText, setEditText] = useState('');
  const [savingContent, setSavingContent] = useState(false);
  const [loadingDocContent, setLoadingDocContent] = useState(false);
  const [activeMinute, setActiveMinute] = useState<any>(null);

  // Signed upload confirmation modal
  const [signedUploadTarget, setSignedUploadTarget] = useState<any>(null);
  const [signedConfirmFinal, setSignedConfirmFinal] = useState(false);
  const [signedConfirmOverride, setSignedConfirmOverride] = useState(false);
  const [pendingSignedFile, setPendingSignedFile] = useState<File | null>(null);
  const [uploadingSigned, setUploadingSigned] = useState(false);

  // Revise draft file target
  const [reviseTarget, setReviseTarget] = useState<any>(null);
  const [uploadingRevise, setUploadingRevise] = useState(false);

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

  const openDocumentContent = async (minute: any, mode: 'view' | 'edit' = 'view') => {
    setLoadingDocContent(true);
    setViewerMode(mode);
    setActiveMinute(minute);
    setContentModalDoc(null);
    try {
      const res = await fetch(`/api/repository/document-content/${minute.id}`);
      if (res.ok) {
        const data = await res.json();
        setContentModalDoc(data);
        setEditText(data.extracted_text || '');
      } else {
        const err = await res.json().catch(() => ({}));
        alert(err.detail || `Could not open document (HTTP ${res.status}).`);
        closeDocumentViewer();
      }
    } catch (err) {
      console.error("Failed to fetch parsed content", err);
      alert('Could not open document content in the app.');
      closeDocumentViewer();
    } finally {
      setLoadingDocContent(false);
    }
  };

  const closeDocumentViewer = () => {
    setContentModalDoc(null);
    setActiveMinute(null);
    setEditText('');
    setViewerMode('view');
  };

  const saveEditedContent = async () => {
    if (!activeMinute?.id) return;
    if (activeMinute.is_signed) {
      alert('Signed final documents cannot be edited.');
      return;
    }
    setSavingContent(true);
    try {
      const res = await fetch(`/api/generated-minutes/${activeMinute.id}/content`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ extracted_text: editText, edited_by: 'user' }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        alert(err.detail || 'Failed to save document');
        return;
      }
      const data = await res.json();
      setMeetingMinutes(prev =>
        prev.map(m =>
          m.id === activeMinute.id
            ? {
                ...m,
                file_path: data.file_path || m.file_path,
                download_url: data.download_url || m.download_url,
                status: 'draft',
                is_signed: false,
              }
            : m
        )
      );
      setActiveMinute((prev: any) =>
        prev
          ? {
              ...prev,
              file_path: data.file_path || prev.file_path,
              download_url: data.download_url || prev.download_url,
              status: 'draft',
              is_signed: false,
            }
          : prev
      );
      setContentModalDoc((prev: any) =>
        prev
          ? {
              ...prev,
              extracted_text: editText,
              filename: data.file_path || prev.filename,
              file_path: data.file_path || prev.file_path,
              paragraph_count: editText.split('\n').filter((l: string) => l.trim()).length,
            }
          : prev
      );
      setViewerMode('view');
      alert('Document saved in the application (draft).');
    } catch (err) {
      console.error(err);
      alert('Failed to save document');
    } finally {
      setSavingContent(false);
    }
  };

  const [statusFilter, setStatusFilter] = useState<'all' | 'draft' | 'finalized'>('all');

  const handleDelete = async (minute: any) => {
    const isSigned = Boolean(minute?.is_signed);
    if (isSigned) {
      alert('Signed final documents are locked and cannot be deleted.');
      return;
    }
    const isFinal = (minute?.status || 'draft').toLowerCase() === 'finalized';
    const label = `${minute?.company_name || 'minutes'} (${minute?.meeting_type || ''} · ${minute?.meeting_date || ''})`;
    const msg = isFinal
      ? `Delete this Final record?\n\n${label}\n\nThis removes it from the repository. Shared template files on disk are kept.`
      : `Delete this draft?\n\n${label}`;
    if (!confirm(msg)) return;
    try {
      const res = await fetch(`/api/generated-minutes/${minute.id}`, { method: 'DELETE' });
      if (res.ok) {
        setMeetingMinutes(prev => prev.filter(m => m.id !== minute.id));
      } else {
        const err = await res.json().catch(() => ({}));
        alert(err.detail || 'Failed to delete.');
      }
    } catch (err) {
      console.error("Failed to delete", err);
      alert('Failed to delete.');
    }
  };

  const handleFinalize = async (id: number) => {
    if (!confirm('Finalize and lock this minutes record? After this you can still upload a signed PDF that will replace the unsigned file.')) return;
    try {
      const res = await fetch(`/api/generated-minutes/${id}/finalize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ finalized_by: 'user' }),
      });
      if (res.ok) {
        const data = await res.json();
        setMeetingMinutes(prev =>
          prev.map(m =>
            m.id === id
              ? { ...m, status: 'finalized', finalized_at: data.finalized_at, finalized_by: data.finalized_by }
              : m
          )
        );
      } else {
        const err = await res.json().catch(() => ({}));
        alert(err.detail || 'Failed to finalize');
      }
    } catch (err) {
      console.error("Failed to finalize", err);
    }
  };

  const handleDownload = (minute: any) => {
    if (!minute?.download_url) return;
    const link = document.createElement('a');
    link.href = minute.download_url;
    link.download = minute.file_path || 'minutes.docx';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleView = (minute: any) => {
    openDocumentContent(minute, 'view');
  };

  const handleEdit = (minute: any) => {
    const isSigned = Boolean(minute.is_signed);
    if (isSigned) {
      alert('This document is signed and locked. Ask Master Admin to unlock before editing.');
      return;
    }
    openDocumentContent(minute, 'edit');
  };

  const openRevisePicker = (minute: any) => {
    if (minute.is_signed) {
      alert('Signed final document cannot be replaced here. Use Master Admin unlock if needed.');
      return;
    }
    setReviseTarget(minute);
    setTimeout(() => reviseInputRef.current?.click(), 0);
  };

  const handleReviseFileSelected = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file || !reviseTarget) return;
    if (!confirm(`Replace the current file for "${reviseTarget.company_name}" with "${file.name}"?\n\nThis keeps the record as Draft so you can review again.`)) {
      setReviseTarget(null);
      return;
    }
    setUploadingRevise(true);
    try {
      const fd = new FormData();
      fd.append('file', file);
      const res = await fetch(`/api/generated-minutes/${reviseTarget.id}/replace-file`, {
        method: 'POST',
        body: fd,
      });
      if (res.ok) {
        const data = await res.json();
        setMeetingMinutes(prev =>
          prev.map(m =>
            m.id === reviseTarget.id
              ? {
                  ...m,
                  file_path: data.file_path,
                  download_url: data.download_url,
                  status: 'draft',
                  is_signed: false,
                }
              : m
          )
        );
        alert(data.message || 'Document replaced.');
      } else {
        const err = await res.json().catch(() => ({}));
        alert(err.detail || 'Failed to replace document');
      }
    } catch (err) {
      console.error(err);
      alert('Failed to replace document');
    } finally {
      setUploadingRevise(false);
      setReviseTarget(null);
    }
  };

  const openSignedUpload = (minute: any) => {
    setSignedUploadTarget(minute);
    setSignedConfirmFinal(false);
    setSignedConfirmOverride(false);
    setPendingSignedFile(null);
  };

  const handleSignedFilePicked = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;
    setPendingSignedFile(file);
  };

  const submitSignedUpload = async () => {
    if (!signedUploadTarget || !pendingSignedFile) return;
    if (!signedConfirmFinal || !signedConfirmOverride) {
      alert('Please confirm both checkboxes before uploading.');
      return;
    }
    setUploadingSigned(true);
    try {
      const fd = new FormData();
      fd.append('file', pendingSignedFile);
      fd.append('confirm_final', 'true');
      fd.append('uploaded_by', 'user');
      const res = await fetch(`/api/generated-minutes/${signedUploadTarget.id}/upload-signed`, {
        method: 'POST',
        body: fd,
      });
      if (res.ok) {
        const data = await res.json();
        setMeetingMinutes(prev =>
          prev.map(m =>
            m.id === signedUploadTarget.id
              ? {
                  ...m,
                  file_path: data.file_path,
                  download_url: data.download_url,
                  status: 'finalized',
                  is_signed: true,
                  unsigned_file_path: data.unsigned_file_path,
                }
              : m
          )
        );
        alert(data.message || 'Signed document uploaded and locked.');
        setSignedUploadTarget(null);
        setPendingSignedFile(null);
      } else {
        const err = await res.json().catch(() => ({}));
        alert(err.detail || 'Failed to upload signed document');
      }
    } catch (err) {
      console.error(err);
      alert('Failed to upload signed document');
    } finally {
      setUploadingSigned(false);
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
      if (selectedCompany?.name && !sameCompany(minute.company_name, selectedCompany.name)) {
        return;
      }
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
  }, [meetingMinutes, selectedCompany]);

  // Filter minutes list based on selected entity, folder node and search query
  const filteredMinutes = useMemo(() => {
    return meetingMinutes.filter(minute => {
      // 0. Selected entity from top bar — only this company's minutes
      if (selectedCompany?.name && !sameCompany(minute.company_name, selectedCompany.name)) {
        return false;
      }

      // 1. Folder path filters
      const date = new Date(minute.meeting_date);
      const year = isNaN(date.getTime()) ? 'Unknown' : date.getFullYear().toString();
      const bu = getBusinessUnit(minute.company_name);

      if (selectedPath.year && year !== selectedPath.year) return false;
      if (selectedPath.bu && bu !== selectedPath.bu) return false;
      if (selectedPath.company && !sameCompany(minute.company_name, selectedPath.company)) return false;
      if (selectedPath.meetingType && minute.meeting_type !== selectedPath.meetingType) return false;

      // 2. Draft / Finalized status
      const status = (minute.status || 'draft').toLowerCase();
      if (statusFilter !== 'all' && status !== statusFilter) return false;

      // 3. Search keyword filter
      if (searchQuery.trim() !== '') {
        const query = searchQuery.toLowerCase();
        return (
          minute.company_name.toLowerCase().includes(query) ||
          (minute.meeting_type || '').toLowerCase().includes(query) ||
          (minute.meeting_date || '').toLowerCase().includes(query) ||
          (minute.file_path && minute.file_path.toLowerCase().includes(query))
        );
      }

      return true;
    });
  }, [meetingMinutes, selectedPath, searchQuery, statusFilter, selectedCompany]);

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
              <p className="text-xs text-slate-500 mt-0.5">
                {selectedCompany?.name
                  ? `Showing minutes for ${selectedCompany.name} only.`
                  : 'Browse, upload and download documents hierarchically by Business Unit, Company and Year.'}
              </p>
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
                  formData.append('company_name', selectedPath.company || selectedCompany?.name || 'General_Company');
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
                  e.target.value = '';
                }}
              />
              <input
                ref={reviseInputRef}
                type="file"
                accept=".docx,.pdf"
                className="hidden"
                onChange={handleReviseFileSelected}
              />
              <input
                ref={signedInputRef}
                type="file"
                accept=".docx,.pdf"
                className="hidden"
                onChange={handleSignedFilePicked}
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
                <div className="flex items-center gap-1 bg-slate-50 border border-slate-200 rounded-lg p-0.5">
                  {([
                    ['all', 'All'],
                    ['draft', 'Draft'],
                    ['finalized', 'Final'],
                  ] as const).map(([value, label]) => (
                    <button
                      key={value}
                      type="button"
                      onClick={() => setStatusFilter(value)}
                      className={`px-2.5 h-8 text-[11px] font-semibold rounded-md transition-colors ${
                        statusFilter === value
                          ? 'bg-white text-slate-900 shadow-sm border border-slate-200'
                          : 'text-slate-500 hover:text-slate-800'
                      }`}
                    >
                      {label}
                    </button>
                  ))}
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
                    {filteredMinutes.map((minute) => {
                      const isFinal = (minute.status || 'draft').toLowerCase() === 'finalized';
                      const isSigned = Boolean(minute.is_signed);
                      return (
                      <div
                        key={minute.id}
                        className="group flex flex-col sm:flex-row items-start sm:items-center justify-between p-3.5 border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors gap-4"
                      >
                        <div className="flex items-center gap-3.5 flex-1 min-w-0">
                          <div className={`p-2.5 rounded-lg shrink-0 ${isSigned ? 'bg-emerald-50 text-emerald-700' : isFinal ? 'bg-blue-50 text-blue-700' : 'bg-amber-50 text-amber-700'}`}>
                            {isSigned || isFinal ? <Lock className="h-5 w-5" /> : <FileText className="h-5 w-5" />}
                          </div>
                          <div className="space-y-1 min-w-0">
                            <div className="flex items-center gap-2 min-w-0 flex-wrap">
                              <h3 className="font-bold text-sm text-slate-900 truncate">
                                {minute.company_name}
                              </h3>
                              <span
                                className={`shrink-0 text-[10px] font-bold uppercase tracking-wide px-1.5 py-0.5 rounded ${
                                  isSigned
                                    ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                                    : isFinal
                                    ? 'bg-blue-50 text-blue-700 border border-blue-200'
                                    : 'bg-amber-50 text-amber-700 border border-amber-200'
                                }`}
                              >
                                {isSigned ? 'Signed Final' : isFinal ? 'Final' : 'Draft'}
                              </span>
                            </div>
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
                              {minute.meeting_number && (
                                <span className="text-[11px] font-semibold text-blue-700">{minute.meeting_number}</span>
                              )}
                            </div>
                          </div>
                        </div>

                        <div className="flex flex-wrap items-center gap-1.5 w-full sm:w-auto shrink-0 border-t sm:border-t-0 pt-2 sm:pt-0 border-slate-100">
                          <Button
                            variant="outline"
                            size="sm"
                            className="h-8 px-2 rounded-lg border-slate-200 text-slate-700 font-semibold text-xs bg-white"
                            onClick={() => handleView(minute)}
                            title="View document"
                          >
                            <Eye className="h-3.5 w-3.5 mr-1 text-slate-500" /> View
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            className="h-8 px-2 rounded-lg border-slate-200 text-slate-700 font-semibold text-xs bg-white"
                            onClick={() => handleDownload(minute)}
                            title="Download"
                          >
                            <Download className="h-3.5 w-3.5 mr-1 text-slate-500" /> Download
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            className="h-8 px-2 rounded-lg border-slate-200 text-slate-700 font-semibold text-xs bg-white"
                            onClick={() => {
                              setEmailModalFile(minute);
                              setEmailSubject(`Meeting Minutes - ${minute.company_name} (${minute.meeting_date})`);
                              setEmailBody(`Dear Team,\n\nPlease find attached the Meeting Minutes document for ${minute.company_name} (${minute.meeting_type}).\n\nRegards,\nCompany Secretarial Team`);
                            }}
                            title="Send email"
                          >
                            <Mail className="h-3.5 w-3.5 mr-1 text-slate-500" /> Email
                          </Button>
                          {!isSigned && (
                            <Button
                              variant="outline"
                              size="sm"
                              className="h-8 px-2 rounded-lg border-slate-200 text-indigo-700 hover:bg-indigo-50 font-semibold text-xs bg-white"
                              onClick={() => handleEdit(minute)}
                              title="Edit in generator (fix mistakes)"
                            >
                              <Pencil className="h-3.5 w-3.5 mr-1" /> Edit
                            </Button>
                          )}
                          {!isSigned && (
                            <Button
                              variant="outline"
                              size="sm"
                              className="h-8 px-2 rounded-lg border-slate-200 text-slate-700 font-semibold text-xs bg-white"
                              onClick={() => openRevisePicker(minute)}
                              disabled={uploadingRevise}
                              title="Upload a corrected Word/PDF to replace this file"
                            >
                              <Upload className="h-3.5 w-3.5 mr-1" /> Replace
                            </Button>
                          )}
                          {!isFinal && (
                            <Button
                              variant="outline"
                              size="sm"
                              className="h-8 px-2 rounded-lg border-emerald-200 text-emerald-700 hover:bg-emerald-50 font-semibold text-xs bg-white"
                              onClick={() => handleFinalize(minute.id)}
                              title="Finalize and lock"
                            >
                              <CheckCircle2 className="h-3.5 w-3.5 mr-1" /> Finalize
                            </Button>
                          )}
                          {!isSigned && (
                            <Button
                              variant="outline"
                              size="sm"
                              className="h-8 px-2 rounded-lg border-blue-200 text-blue-700 hover:bg-blue-50 font-semibold text-xs bg-white"
                              onClick={() => openSignedUpload(minute)}
                              title="Upload signed PDF — replaces unsigned file"
                            >
                              <Upload className="h-3.5 w-3.5 mr-1" /> Upload Signed
                            </Button>
                          )}
                          {!isSigned && (
                            <Button
                              variant="outline"
                              size="sm"
                              className="h-8 px-2 rounded-lg border-red-200 text-red-700 hover:bg-red-50 font-semibold text-xs bg-white"
                              onClick={() => handleDelete(minute)}
                              title="Delete from repository"
                            >
                              <Trash className="h-3.5 w-3.5 mr-1" /> Delete
                            </Button>
                          )}
                        </div>
                      </div>
                    );
                    })}

                    {!loading && filteredMinutes.length === 0 && (
                      <div className="text-center py-10">
                        <FileText className="h-8 w-8 text-slate-300 mx-auto mb-2" />
                        <p className="text-slate-400 text-xs font-medium">
                          {selectedCompany?.name
                            ? `No minutes for ${selectedCompany.name} yet.`
                            : 'No generated minutes found.'}
                        </p>
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

      {/* --- SIGNED UPLOAD CONFIRMATION MODAL --- */}
      {signedUploadTarget && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-xl border border-slate-200 w-full max-w-md p-6 space-y-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h3 className="text-base font-bold text-slate-900">Upload signed document</h3>
                <p className="text-xs text-slate-500 mt-1">
                  {signedUploadTarget.company_name} · {signedUploadTarget.meeting_type} · {signedUploadTarget.meeting_date}
                </p>
              </div>
              <button
                type="button"
                className="text-slate-400 hover:text-slate-700"
                onClick={() => {
                  setSignedUploadTarget(null);
                  setPendingSignedFile(null);
                }}
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900 space-y-1">
              <p className="font-semibold">This will replace the unsigned file.</p>
              <p>The current unsigned document is kept as a backup. The new file becomes the official Final (signed) version.</p>
            </div>

            <div className="space-y-2">
              <Button
                type="button"
                variant="outline"
                className="w-full text-xs h-9"
                onClick={() => signedInputRef.current?.click()}
              >
                <Upload className="h-3.5 w-3.5 mr-1.5" />
                {pendingSignedFile ? pendingSignedFile.name : 'Choose signed PDF / Word file'}
              </Button>
            </div>

            <label className="flex items-start gap-2 text-xs text-slate-700 cursor-pointer">
              <input
                type="checkbox"
                className="mt-0.5"
                checked={signedConfirmFinal}
                onChange={(e) => setSignedConfirmFinal(e.target.checked)}
              />
              <span>I confirm this is the <strong>final signed</strong> document.</span>
            </label>
            <label className="flex items-start gap-2 text-xs text-slate-700 cursor-pointer">
              <input
                type="checkbox"
                className="mt-0.5"
                checked={signedConfirmOverride}
                onChange={(e) => setSignedConfirmOverride(e.target.checked)}
              />
              <span>I understand it will <strong>override</strong> the unsigned version in the repository.</span>
            </label>

            <div className="flex justify-end gap-2 pt-2">
              <Button
                type="button"
                variant="outline"
                className="text-xs h-9"
                onClick={() => {
                  setSignedUploadTarget(null);
                  setPendingSignedFile(null);
                }}
              >
                Cancel
              </Button>
              <Button
                type="button"
                className="text-xs h-9 bg-blue-600 hover:bg-blue-700 text-white"
                disabled={!pendingSignedFile || !signedConfirmFinal || !signedConfirmOverride || uploadingSigned}
                onClick={submitSignedUpload}
              >
                {uploadingSigned ? 'Uploading…' : 'Confirm & Upload'}
              </Button>
            </div>
          </div>
        </div>
      )}

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

      {/* --- IN-APP DOCUMENT VIEWER / EDITOR --- */}
      {(contentModalDoc || loadingDocContent) && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-xl border border-slate-200 w-full max-w-4xl max-h-[90vh] flex flex-col p-6 space-y-4 overflow-hidden">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3 shrink-0 gap-3">
              <div className="min-w-0">
                <h3 className="font-bold text-slate-900 flex items-center gap-2 text-base">
                  {viewerMode === 'edit' ? (
                    <Pencil className="h-5 w-5 text-amber-600" />
                  ) : (
                    <Eye className="h-5 w-5 text-blue-600" />
                  )}
                  {viewerMode === 'edit' ? 'Edit Document' : 'View Document'}
                </h3>
                <p className="text-xs text-slate-500 truncate">
                  {activeMinute?.company_name || contentModalDoc?.company_name} ·{' '}
                  {contentModalDoc?.filename || activeMinute?.file_path || 'Loading…'}
                </p>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                {contentModalDoc && viewerMode === 'view' && !activeMinute?.is_signed && (
                  <Button
                    size="sm"
                    variant="outline"
                    className="h-8 text-xs"
                    onClick={() => setViewerMode('edit')}
                  >
                    <Pencil className="h-3.5 w-3.5 mr-1" /> Edit
                  </Button>
                )}
                {viewerMode === 'edit' && (
                  <Button
                    size="sm"
                    className="h-8 text-xs bg-blue-600 hover:bg-blue-700 text-white"
                    disabled={savingContent}
                    onClick={saveEditedContent}
                  >
                    <Save className="h-3.5 w-3.5 mr-1" />
                    {savingContent ? 'Saving…' : 'Save'}
                  </Button>
                )}
                <button onClick={closeDocumentViewer} className="text-slate-400 hover:text-slate-600 p-1 rounded-md">
                  <X className="h-4 w-4" />
                </button>
              </div>
            </div>

            {loadingDocContent && !contentModalDoc ? (
              <div className="flex-1 flex items-center justify-center text-sm text-slate-500 py-16">
                Opening document in application…
              </div>
            ) : contentModalDoc ? (
              <div className="overflow-y-auto space-y-6 pr-2 flex-1 text-xs min-h-0">
                {/* PDF inline preview when available */}
                {(contentModalDoc.file_type || '').toLowerCase() === 'pdf' && contentModalDoc.filename && viewerMode === 'view' && (
                  <iframe
                    title="PDF preview"
                    src={`/api/generated-minutes/view/${encodeURIComponent(contentModalDoc.filename)}`}
                    className="w-full h-[55vh] rounded-lg border border-slate-200 bg-slate-50"
                  />
                )}

                {viewerMode === 'edit' ? (
                  <div className="space-y-2">
                    <h4 className="font-bold text-slate-800 text-xs uppercase tracking-wider">
                      Edit document text
                    </h4>
                    <textarea
                      value={editText}
                      onChange={(e) => setEditText(e.target.value)}
                      className="w-full min-h-[50vh] p-4 bg-white border border-slate-200 rounded-lg font-serif leading-relaxed text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <p className="text-[11px] text-slate-500">
                      Changes are saved in the app as a new draft Word file for this record.
                    </p>
                  </div>
                ) : (
                  <>
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

                    <div className="space-y-2">
                      <h4 className="font-bold text-slate-800 text-xs uppercase tracking-wider flex items-center gap-1.5">
                        <FileText className="h-4 w-4 text-slate-600" /> Document content
                      </h4>
                      <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg font-serif leading-relaxed text-sm text-slate-800 whitespace-pre-wrap max-h-[55vh] overflow-y-auto">
                        {contentModalDoc.extracted_text || "No plain text extracted."}
                      </div>
                    </div>
                  </>
                )}
              </div>
            ) : null}

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-100 shrink-0">
              {viewerMode === 'edit' && (
                <Button size="sm" variant="outline" onClick={() => setViewerMode('view')} className="h-8 text-xs">
                  Cancel edit
                </Button>
              )}
              <Button size="sm" onClick={closeDocumentViewer} className="h-8 text-xs font-semibold">
                Close
              </Button>
            </div>
          </div>
        </div>
      )}
    </ProductDashboardLayout>
  );
};

export default MeetingMinutes;