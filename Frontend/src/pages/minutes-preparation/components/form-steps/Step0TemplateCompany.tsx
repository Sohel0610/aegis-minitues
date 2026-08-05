/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useState, useEffect, useMemo } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Popover, PopoverTrigger, PopoverContent } from "@/components/ui/popover";
import { CheckCircle, Upload, Search, FileText, Building, ChevronDown, Check } from 'lucide-react';

import { StepProps } from './types';
import { useVertical } from '@/contexts/VerticalContext';

const namesLooselyMatch = (a?: string, b?: string) => {
  const norm = (s: string) =>
    s
      .toLowerCase()
      .replace(/\b(mr|mrs|ms|dr)\b\.?/g, '')
      .replace(/[^a-z]/g, '');
  if (!a || !b) return false;
  const x = norm(a);
  const y = norm(b);
  return x === y || x.includes(y) || y.includes(x);
};

// Enterprise Clean Template Name Formatter (Strips raw dates & technical filenames)
export const getCleanBusinessTemplateName = (rawFilename: string): { title: string; category: string; quarterTag: string } => {
  if (!rawFilename) return { title: 'Standard Meeting Template', category: 'Board Meeting', quarterTag: 'Standard' };

  const raw = rawFilename.replace(/^\d+\.\s*/, '').replace(/\.docx$/i, '');

  let companyPrefix = 'Adani Group';
  if (raw.startsWith('AGEL')) companyPrefix = 'AGEL';
  else if (raw.startsWith('AGE(UP)L')) companyPrefix = 'AGE(UP)L';
  else if (raw.includes('AGE25BL')) companyPrefix = 'AGE25BL';
  else {
    const firstWord = raw.split(/[-_\s]/)[0];
    if (firstWord && firstWord.length > 2) companyPrefix = firstWord;
  }

  let category = 'Board Meeting';
  if (raw.includes('- AC -') || /\bAC\b/.test(raw) || raw.toLowerCase().includes('audit')) {
    category = 'Audit Committee';
  } else if (raw.includes('- BM -') || /\bBM\b/.test(raw) || raw.toLowerCase().includes('board')) {
    category = 'Board Meeting';
  } else if (raw.toLowerCase().includes('nrc') || raw.toLowerCase().includes('nomination')) {
    category = 'Nomination and Remuneration Committee';
  } else if (raw.toLowerCase().includes('src') || raw.toLowerCase().includes('stakeholder')) {
    category = 'Stakeholders Relationship Committee';
  } else if (raw.toLowerCase().includes('csr')) {
    category = 'CSR Committee';
  } else if (raw.toLowerCase().includes('risk') || raw.includes('- RMC -')) {
    category = 'Risk Management Committee';
  } else if (raw.toLowerCase().includes('agm') || raw.toLowerCase().includes('annual')) {
    category = 'AGM';
  } else if (raw.toLowerCase().includes('egm') || raw.toLowerCase().includes('extraordinary')) {
    category = 'EGM';
  }

  let quarterTag = 'Standard';
  if (raw.includes('28.04') || raw.includes('28.05') || raw.includes('Q1')) {
    quarterTag = 'Q1 Focus';
  } else if (raw.includes('28.07') || raw.includes('28.08') || raw.includes('Q2')) {
    quarterTag = 'Q2 Focus';
  } else if (raw.includes('28.10') || raw.includes('28.11') || raw.includes('Q3')) {
    quarterTag = 'Q3 Focus';
  } else if (raw.includes('23.01') || raw.includes('28.01') || raw.includes('Q4')) {
    quarterTag = 'Q4 Annual Focus';
  }

  // Extract the meeting date from the filename (DD.MM.YYYY pattern)
  const dateMatch = rawFilename.match(/(\d{2})\.(\d{2})\.(\d{4})/);
  let dateSuffix = '';
  if (dateMatch) {
    const [, dd, mm, yyyy] = dateMatch;
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const monthName = months[parseInt(mm, 10) - 1] || mm;
    dateSuffix = ` — ${dd} ${monthName} ${yyyy}`;
  }

  let finalTitle = `${companyPrefix} — ${category}`;
  if (quarterTag !== 'Standard') {
    finalTitle += ` (${quarterTag})`;
  }
  // Always append the date so each template is uniquely identifiable
  finalTitle += dateSuffix;

  return {
    title: finalTitle,
    category,
    quarterTag
  };
};

/** Map selected company name → template filename code (AGEL, AGE25BL, …) */
const COMPANY_TEMPLATE_CODES: Record<string, string[]> = {
  'Adani Green Energy Limited': ['AGEL'],
  'Adani Green Energy Ltd.': ['AGEL'],
  'Adani Green Energy (UP) Limited': ['AGE(UP)L', 'AGEUPL'],
  'Adani Green Energy Twenty Five B Limited': ['AGE25BL'],
};

/** Resolve which template category should be shown for the current form meeting type */
const resolveTargetTemplateCategory = (meetingType?: string, committeeName?: string): string | null => {
  if (!meetingType) return null;
  if (meetingType === 'Board Meeting') return 'Board Meeting';
  if (meetingType === 'Annual General Meeting') return 'AGM';
  if (meetingType === 'Extraordinary General Meeting') return 'EGM';
  if (meetingType === 'Committee Meeting') {
    return (committeeName || '').trim() || null; // e.g. Audit Committee
  }
  // Direct committee / type labels (Audit Committee, NRC, …)
  return meetingType;
};

const templateMatchesMeetingType = (
  category: string,
  meetingType?: string,
  committeeName?: string,
): boolean => {
  const target = resolveTargetTemplateCategory(meetingType, committeeName);
  if (!target) return true;
  return category.toLowerCase() === target.toLowerCase();
};

// Helper function to parse raw meeting minutes text and extract structured fields
export const parseMinutesText = (text: string): Record<string, any> => {
  const extracted: Record<string, any> = {};
  if (!text || !text.trim()) return extracted;

  // 1. Company Name
  const compMatch = text.match(/([A-Z0-9\s\(\)\-\.]{4,}(?:LIMITED|LTD|PRIVATE LIMITED|PVT LTD))/i);
  if (compMatch) {
    extracted.companyName = compMatch[1].trim();
  }

  // 2. Financial Year
  const fyMatch = text.match(/F\.?Y\.?\s*(\d{4}[-\/]\d{2,4})/i);
  if (fyMatch) {
    const fyStr = fyMatch[1];
    if (fyStr.includes('-')) {
      const parts = fyStr.split('-');
      const startYr = parseInt(parts[0]);
      if (!isNaN(startYr)) {
        extracted.fsYear = startYr + 1;
        extracted.directorsReportYear = startYr + 1;
        extracted.rptFinYearRangeFrom = startYr;
        extracted.rptFinYearRangeTo = startYr + 1;
      }
    }
  }

  // 3. Meeting Type
  if (/AUDIT COMMITTEE/i.test(text)) {
    extracted.meetingType = 'Committee Meeting';
    extracted.committeeName = 'Audit Committee';
  } else if (/ANNUAL GENERAL MEETING/i.test(text) || /AGM/i.test(text)) {
    extracted.meetingType = 'Annual General Meeting';
  } else if (/BOARD MEETING/i.test(text)) {
    extracted.meetingType = 'Board Meeting';
  }

  // 4. Meeting Date & Day
  const monthsMap: Record<string, string> = {
    JANUARY: '01', FEBRUARY: '02', MARCH: '03', APRIL: '04', MAY: '05', JUNE: '06',
    JULY: '07', AUGUST: '08', SEPTEMBER: '09', OCTOBER: '10', NOVEMBER: '11', DECEMBER: '12'
  };

  const dateMatch = text.match(/(MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY|SUNDAY)?,?\s*(\d{1,2})(?:ST|ND|RD|TH)?\s+(JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER)\s+(\d{4})/i);
  if (dateMatch) {
    const dayStr = dateMatch[1];
    const dd = dateMatch[2].padStart(2, '0');
    const mm = monthsMap[dateMatch[3].toUpperCase()] || '01';
    let yyyy = dateMatch[4];

    if (yyyy === '2000' && extracted.fsYear) {
      yyyy = extracted.fsYear.toString();
    }

    extracted.meetingDate = `${yyyy}-${mm}-${dd}`;
    if (dayStr) {
      extracted.meetingDay = dayStr.charAt(0).toUpperCase() + dayStr.slice(1).toLowerCase();
    } else {
      const d = new Date(extracted.meetingDate);
      if (!isNaN(d.getTime())) {
        extracted.meetingDay = d.toLocaleDateString('en-US', { weekday: 'long' });
      }
    }
  }

  // 5. Start & End Time
  const convertTime = (timeStr: string) => {
    const m = timeStr.match(/(\d{1,2})[\:\.](\d{2})\s*(A\.?M\.?|P\.?M\.?)/i);
    if (!m) return '';
    let hrs = parseInt(m[1]);
    const mins = m[2];
    const ampm = m[3].replace(/\./g, '').toUpperCase();
    if (ampm === 'PM' && hrs < 12) hrs += 12;
    if (ampm === 'AM' && hrs === 12) hrs = 0;
    return `${hrs.toString().padStart(2, '0')}:${mins}`;
  };

  const startTimeMatch = text.match(/commenced\s+its\s+business\s+at\s+(\d{1,2}[\:\.]\d{2}\s*(?:A\.?M\.?|P\.?M\.?))/i) ||
                         text.match(/AT\s+(\d{1,2}[\:\.]\d{2}\s*(?:A\.?M\.?|P\.?M\.?))/i);
  if (startTimeMatch) {
    extracted.timeCommenced = convertTime(startTimeMatch[1]);
  }

  const endTimeMatch = text.match(/concluded\s+(?:with\s+a\s+vote\s+of\s+thanks\s+to\s+the\s+chair\s+)?at\s+(\d{1,2}[\:\.]\d{2}\s*(?:A\.?M\.?|P\.?M\.?))/i);
  if (endTimeMatch) {
    extracted.timeConcluded = convertTime(endTimeMatch[1]);
  }

  // 6. Meeting Place
  const placeMatch = text.match(/AT\s+([A-Z0-9\s,\.\-–]{8,}(?:AHMEDABAD|MUMBAI|DELHI|GURGAON|BENGALURU|HYDERABAD|KOLKATA|\d{6}))/i);
  if (placeMatch) {
    extracted.meetingPlace = placeMatch[1].trim().replace(/\s+/g, ' ');
  }

  // 7. Present Directors & Attendees
  const dirs: { name: string; din: string }[] = [];
  const dirLines = text.match(/(\d+\.\s*(?:Mr\.|Mrs\.|Ms\.|Dr\.)?\s*[A-Za-z\s]+(?:\s*-\s*[A-Za-z\s]+)?)/gi);
  if (dirLines) {
    for (const dl of dirLines) {
      const clean = dl.replace(/^\d+\.\s*/, '').replace(/\s*-\s*.*$/, '').trim();
      const rawName = clean.replace(/^(Mr\.|Mrs\.|Ms\.|Dr\.)\s+/i, '');
      if (rawName && rawName.length > 2 && !dirs.some(d => d.name === rawName)) {
        dirs.push({ name: rawName, din: '' });
      }
    }
  }
  if (dirs.length > 0) {
    extracted.presentDirectors = dirs;
    extracted.signatory1Name = dirs[0]?.name || '';
    extracted.signatory1Role = 'Director';
    if (dirs.length > 1) {
      extracted.signatory2Name = dirs[1]?.name || '';
      extracted.signatory2Role = 'Director';
    }
  }

  // 8. Invitee / In Attendance
  const inviteeMatch = text.match(/Invitee[^\n]*\n\s*(?:Mr\.|Mrs\.|Ms\.)?\s*([A-Za-z\s]+?)\s*-\s*([A-Za-z\s,]+)/i);
  if (inviteeMatch) {
    extracted.inAttendance = [{ name: inviteeMatch[1].trim(), role: inviteeMatch[2].trim() }];
  }

  // 9. Chairman Name
  const chairMatch = text.match(/CHAIRMAN\s*\n\s*([A-Za-z\s]+?)\s+occupied\s+the\s+Chair/i) || text.match(/Chairman:?\s*([A-Za-z\s]+)/i);
  if (chairMatch) {
    const name = chairMatch[1].trim();
    extracted.chairmanName = name;
    extracted.signingChairmanName = name;
  } else if (dirs.length > 0) {
    extracted.chairmanName = dirs[0].name;
    extracted.signingChairmanName = dirs[0].name;
  }

  // 10. Previous Minutes Date
  const prevDateMatch = text.match(/previous\s+meeting[^\n]*?held\s+on\s+(\d{1,2})(?:ST|ND|RD|TH)?\s+(JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER)\s+(\d{4})/i);
  if (prevDateMatch) {
    const dd = prevDateMatch[1].padStart(2, '0');
    const mm = monthsMap[prevDateMatch[2].toUpperCase()] || '01';
    const yyyy = prevDateMatch[3];
    extracted.previousMinutesDate = `${yyyy}-${mm}-${dd}`;
  }

  // 11. Date of Entry & Signing & Place
  const signingDateMatch = text.match(/Date\s+of\s+signing:?\s*(\d{1,2})(?:ST|ND|RD|TH)?\s+(JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER)\s+(\d{4})/i);
  if (signingDateMatch) {
    const dd = signingDateMatch[1].padStart(2, '0');
    const mm = monthsMap[signingDateMatch[2].toUpperCase()] || '01';
    const yyyy = signingDateMatch[3];
    extracted.signingDate = `${yyyy}-${mm}-${dd}`;
    extracted.recordingDate = `${yyyy}-${mm}-${dd}`;
  }

  const placeSigningMatch = text.match(/Place:?\s*([A-Za-z]+)/i);
  if (placeSigningMatch) {
    extracted.signingPlace = placeSigningMatch[1].trim();
  }

  return extracted;
};

export const Step0TemplateCompany: React.FC<StepProps> = (props) => {
  const { 
    formData, 
    setFormData, 
    isUploadingTemplate, 
    handleCustomTemplateUpload, 
    numberToOrdinal,
    toast
  } = props;

  const { selectedVertical: ctxVertical, selectedCompany: ctxCompany } = useVertical();

  const [dbTemplates, setDbTemplates] = useState<any[]>([]);
  const [templateSearch, setTemplateSearch] = useState('');

  useEffect(() => {
    const fetchDbTemplates = async () => {
      try {
        const res = await fetch('/api/templates');
        if (res.ok) {
          const data = await res.json();
          setDbTemplates(data.data || []);
        }
      } catch (err) {
        console.error("Failed to fetch templates", err);
      }
    };
    fetchDbTemplates();
  }, []);

  // Sync with global VerticalContext when header selection changes
  useEffect(() => {
    if (!ctxCompany) return;
    let cancelled = false;
    const syncCompany = async () => {
      let fetchedDirectors: any[] = [];
      try {
        const res = await fetch(`/api/companies/${encodeURIComponent(ctxCompany.name)}/directors`);
        if (res.ok) {
          const dirData = await res.json();
          fetchedDirectors = dirData.data || [];
        }
      } catch (e) {
        console.error(e);
      }
      if (cancelled) return;

      setFormData((prev) => {
        const companyChanged = (prev.companyName || '').trim() !== (ctxCompany.name || '').trim();
        const dirs = fetchedDirectors.length > 0 ? fetchedDirectors : prev.presentDirectors;
        const chairFromRole =
          (dirs || []).find((d: any) =>
            `${d.designation || d.role || ''}`.toLowerCase().includes('chair')
          )?.name || '';
        // Never blank an existing/draft chairman — late sync after draft restore was clearing it
        const nextChair = chairFromRole || (!companyChanged ? prev.chairmanName : '') || '';
        return {
          ...prev,
          companyName: ctxCompany.name,
          companySecretary: ctxCompany.secretary_name || prev.companySecretary,
          presentDirectors: dirs && dirs.length > 0 ? dirs : prev.presentDirectors,
          chairmanName: nextChair,
          signingChairmanName: nextChair || prev.signingChairmanName,
        };
      });
    };
    void syncCompany();
    return () => {
      cancelled = true;
    };
  }, [ctxCompany, setFormData]);

  // Process template list with clean enterprise titles
  const processedTemplates = useMemo(() => {
    const defaultTemplates = [
      { name: "87. AGEL - BM - 28.04.2025.docx" },
      { name: "88. AGEL - BM - 28.07.2025.docx" },
      { name: "89. AGEL - BM - 28.10.2025.docx" },
      { name: "90. AGEL - BM - 23.01.2026.docx" },
    ];

    const sourceList = dbTemplates.length > 0 ? dbTemplates : defaultTemplates;

    return sourceList.map((t: any) => {
      const raw = typeof t === 'string' ? t : t.name;
      const formatted = getCleanBusinessTemplateName(raw);

      return {
        rawName: raw,
        displayName: formatted.title,
        category: formatted.category,
        quarterTag: formatted.quarterTag
      };
    });
  }, [dbTemplates]);

  // Filter templates by meeting type (from BU filter), search, and prefer company match
  const filteredTemplates = useMemo(() => {
    let list = processedTemplates;

    // Hard filter: only templates matching selected Board / Audit / etc.
    list = list.filter(t =>
      templateMatchesMeetingType(t.category, formData.meetingType, formData.committeeName)
    );

    if (templateSearch.trim()) {
      const q = templateSearch.toLowerCase();
      list = list.filter(t => t.displayName.toLowerCase().includes(q) || t.rawName.toLowerCase().includes(q));
    }

    // Prefer templates for the active company (by known code), then others of same type
    const codes = (COMPANY_TEMPLATE_CODES[formData.companyName || ''] || []).map(c => c.toLowerCase());
    if (codes.length > 0) {
      list = [...list].sort((a, b) => {
        const aMatch = codes.some(c => a.rawName.toLowerCase().includes(c) || a.displayName.toLowerCase().includes(c));
        const bMatch = codes.some(c => b.rawName.toLowerCase().includes(c) || b.displayName.toLowerCase().includes(c));
        if (aMatch && !bMatch) return -1;
        if (!aMatch && bMatch) return 1;
        return a.displayName.localeCompare(b.displayName);
      });
    } else if (formData.companyName) {
      const compWord = formData.companyName.split(' ')[0].toLowerCase();
      list = [...list].sort((a, b) => {
        const aMatch = a.displayName.toLowerCase().includes(compWord);
        const bMatch = b.displayName.toLowerCase().includes(compWord);
        if (aMatch && !bMatch) return -1;
        if (!aMatch && bMatch) return 1;
        return 0;
      });
    }
    return list;
  }, [processedTemplates, templateSearch, formData.companyName, formData.meetingType, formData.committeeName]);

  // Drop a previously selected template if it doesn't match the active meeting type
  useEffect(() => {
    if (!formData.template || formData.template === 'custom') return;
    const selected = processedTemplates.find(t => t.rawName === formData.template);
    if (!selected) return;
    if (!templateMatchesMeetingType(selected.category, formData.meetingType, formData.committeeName)) {
      setFormData(prev => ({ ...prev, template: '' }));
    }
  }, [formData.template, formData.meetingType, formData.committeeName, processedTemplates, setFormData]);

  // Get active selected template object
  const activeTemplateObj = useMemo(() => {
    return processedTemplates.find(t => t.rawName === formData.template);
  }, [processedTemplates, formData.template]);

  const targetCategory = resolveTargetTemplateCategory(formData.meetingType, formData.committeeName);

  const [openTemplateDropdown, setOpenTemplateDropdown] = useState(false);

  return (
    <Card className="mb-4 border border-slate-200 shadow-xs rounded-xl bg-white">
      <CardHeader className="border-b border-slate-100 py-3 px-4">
        <CardTitle className="text-sm font-bold text-slate-900">Template & Company Information</CardTitle>
        <CardDescription className="text-xs text-slate-500">
          Select an official template structure and enter meeting details for <strong className="text-slate-800">{formData.companyName || 'the company'}</strong>.
        </CardDescription>
      </CardHeader>
      <CardContent className="p-4 space-y-4">

        {/* SEARCHABLE TEMPLATE SELECTOR */}
        <div className="space-y-3">
          <div className="flex items-center justify-between gap-2">
            <Label htmlFor="template" className="text-xs font-semibold text-slate-700">Official Template Selection *</Label>
            <span className="text-[11px] text-slate-500 font-medium shrink-0">
              {filteredTemplates.length} template{filteredTemplates.length === 1 ? '' : 's'}
              {targetCategory ? ` · ${targetCategory}` : ''}
            </span>
          </div>
          {targetCategory && (
            <p className="text-[11px] text-slate-500 -mt-1">
              Showing only <strong className="text-slate-700">{targetCategory}</strong> templates (from your meeting type selection).
            </p>
          )}

          {/* Clean Active Selected Banner */}
          {activeTemplateObj && (
            <div className="p-3 bg-blue-50/70 border border-blue-200/80 rounded-lg flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <FileText className="h-4 w-4 text-blue-600 shrink-0" />
                <div>
                  <div className="text-xs font-bold text-slate-900">{activeTemplateObj.displayName}</div>
                  <div className="text-[10px] text-slate-500 font-medium">Selected Blueprint • {activeTemplateObj.category}</div>
                </div>
              </div>
              <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-blue-100 text-blue-700">Active</span>
            </div>
          )}

          {/* Integrated Searchable Template Dropdown */}
          <Popover open={openTemplateDropdown} onOpenChange={setOpenTemplateDropdown}>
            <PopoverTrigger asChild>
              <button
                type="button"
                className="w-full flex items-center justify-between bg-white border border-slate-200 hover:border-slate-300 text-xs h-9 px-3 rounded-lg text-slate-700 transition-colors shadow-2xs focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
              >
                <span className={`truncate font-medium ${formData.template ? 'text-slate-900' : 'text-slate-400'}`}>
                  {formData.template === 'custom'
                    ? 'Custom Uploaded DOCX Template'
                    : activeTemplateObj
                    ? activeTemplateObj.displayName
                    : 'Select official template structure...'}
                </span>
                <ChevronDown className="h-4 w-4 text-slate-400 shrink-0 ml-2" />
              </button>
            </PopoverTrigger>
            <PopoverContent className="w-[--radix-popover-trigger-width] min-w-[320px] p-0 bg-white shadow-xl rounded-xl border border-slate-200" align="start">
              <div className="p-2 border-b border-slate-100 relative">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400 pointer-events-none" />
                <Input
                  placeholder="Search templates by company or category..."
                  value={templateSearch}
                  onChange={(e) => setTemplateSearch(e.target.value)}
                  className="pl-8 h-8 bg-slate-50/70 border-slate-200 text-xs rounded-md focus:bg-white"
                  autoFocus
                />
              </div>
              <div className="max-h-[260px] overflow-y-auto p-1 space-y-0.5">
                {filteredTemplates.length > 0 ? (
                  filteredTemplates.map((t) => {
                    const isSelected = formData.template === t.rawName;
                    return (
                      <button
                        key={t.rawName}
                        type="button"
                        onClick={() => {
                          setFormData(prev => ({ ...prev, template: t.rawName }));
                          setOpenTemplateDropdown(false);
                          // Auto-fill chairman from template only if that person is on this company's board
                          fetch(`/api/templates/${encodeURIComponent(t.rawName)}/chairman`)
                            .then((r) => (r.ok ? r.json() : null))
                            .then((data) => {
                              const name = (data?.chairman_name || '').trim();
                              if (!name) return;
                              setFormData((prev) => {
                                const onBoard = (prev.presentDirectors || []).some((d: any) =>
                                  namesLooselyMatch(d.name, name)
                                );
                                if (!onBoard) return prev;
                                return {
                                  ...prev,
                                  chairmanName: name,
                                  signingChairmanName: name,
                                };
                              });
                            })
                            .catch(() => {});
                        }}
                        className={`w-full flex items-center justify-between text-left px-2.5 py-2 rounded-md text-xs transition-colors ${
                          isSelected ? 'bg-blue-50/80 text-blue-900 font-semibold' : 'hover:bg-slate-50 text-slate-700'
                        }`}
                      >
                        <div className="flex items-center gap-2 truncate pr-2">
                          {isSelected && <Check className="h-3.5 w-3.5 text-blue-600 shrink-0" />}
                          <span className="truncate">{t.displayName}</span>
                        </div>
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 font-medium shrink-0">
                          {t.category}
                        </span>
                      </button>
                    );
                  })
                ) : (
                  <div className="p-4 text-center text-xs text-slate-400">
                    {targetCategory
                      ? `No ${targetCategory} templates found.`
                      : 'No matching templates found.'}
                  </div>
                )}
                <div className="border-t border-slate-100 my-1 pt-1">
                  <button
                    type="button"
                    onClick={() => {
                      setFormData(prev => ({ ...prev, template: 'custom' }));
                      setOpenTemplateDropdown(false);
                    }}
                    className={`w-full flex items-center gap-2 text-left px-2.5 py-2 rounded-md text-xs font-medium transition-colors ${
                      formData.template === 'custom'
                        ? 'bg-blue-50 text-blue-700 font-semibold'
                        : 'text-blue-600 hover:bg-blue-50/50'
                    }`}
                  >
                    <Upload className="h-3.5 w-3.5 text-blue-600 shrink-0" />
                    <span>+ Upload Custom DOCX Template...</span>
                  </button>
                </div>
              </div>
            </PopoverContent>
          </Popover>
        </div>

        {/* CUSTOM UPLOAD AREA */}
        {formData.template === 'custom' && (
          <div className="space-y-3">
            <Label className="text-xs font-semibold text-slate-700">Upload Custom DOCX Template *</Label>
            <div
              className={`relative border-2 border-dashed rounded-xl p-6 transition-all text-center ${
                formData.customTemplateFilename ? 'border-green-300 bg-green-50/60' : 'border-blue-200 bg-blue-50/30'
              }`}
            >
              <input
                id="customTemplate"
                type="file"
                accept=".docx"
                onChange={handleCustomTemplateUpload}
                disabled={isUploadingTemplate}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />
              <div className="flex flex-col items-center gap-2">
                {isUploadingTemplate ? (
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
                ) : formData.customTemplateFilename ? (
                  <div className="bg-green-100 p-2.5 rounded-full">
                    <CheckCircle className="h-5 w-5 text-green-600" />
                  </div>
                ) : (
                  <div className="bg-blue-100 p-2.5 rounded-full">
                    <Upload className="h-5 w-5 text-blue-600" />
                  </div>
                )}

                <div>
                  <p className="font-semibold text-xs text-slate-900">
                    {formData.customTemplateFilename ? 'Template Loaded Successfully' : 'Drop your template file here or click to browse'}
                  </p>
                  <p className="text-[11px] text-slate-500 mt-0.5">
                    {formData.customTemplateFilename || 'Only .docx files with [Placeholders] supported'}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* COMPANY NAME DISPLAY / INPUT */}
        <div className="space-y-2">
          <Label htmlFor="companyName" className="text-xs font-semibold text-slate-700">Company Name *</Label>
          {formData.companyName ? (
            <div className="p-3.5 bg-slate-50 border border-slate-200/80 rounded-xl flex items-center justify-between shadow-2xs">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-slate-100/80 border border-slate-200/80 flex items-center justify-center p-1.5 shrink-0">
                  <img src="/adani.svg" alt="Adani" className="h-full w-auto" />
                </div>
                <div>
                  <div className="text-xs font-bold text-slate-900">{formData.companyName}</div>
                  <div className="text-[11px] text-slate-500 font-medium">
                    {ctxVertical ? `Business Unit: ${ctxVertical.name}` : 'Adani Group Entity'}
                  </div>
                </div>
              </div>
              <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-semibold bg-blue-50 text-blue-700 border border-blue-200/60">
                Active Context
              </span>
            </div>
          ) : (
            <Input
              id="companyName"
              value={formData.companyName || ''}
              onChange={(e) => setFormData(prev => ({ ...prev, companyName: e.target.value }))}
              placeholder="Enter company name..."
              className="bg-white border-slate-200 h-9 rounded-lg text-xs"
            />
          )}
        </div>

        {/* MEETING NUMBER & TYPE */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="meetingNumber" className="text-xs font-semibold text-slate-700">Meeting Number</Label>
            <Input
              id="meetingNumber"
              type="number"
              min="1"
              value={formData.meetingNumber ? parseInt(formData.meetingNumber.replace(/(st|nd|rd|th)$/, '')) || '' : ''}
              onChange={(e) => {
                const num = parseInt(e.target.value);
                if (!isNaN(num) && numberToOrdinal) {
                  const ordinal = numberToOrdinal(num);
                  setFormData(prev => ({ ...prev, meetingNumber: ordinal }));
                } else {
                  setFormData(prev => ({ ...prev, meetingNumber: '' }));
                }
              }}
              placeholder="e.g., 5 (converts to 5th)"
              className="bg-white border-slate-200 h-9 rounded-lg text-xs"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="meetingType" className="text-xs font-semibold text-slate-700">Meeting Type</Label>
            <Select
              value={formData.meetingType}
              onValueChange={(value) => setFormData(prev => ({ ...prev, meetingType: value }))}
            >
              <SelectTrigger className="bg-white border-slate-200 h-9 rounded-lg text-xs font-medium">
                <SelectValue placeholder="Select meeting type" />
              </SelectTrigger>
              <SelectContent className="bg-white">
                <SelectItem value="Board Meeting" className="text-xs">Board Meeting</SelectItem>
                <SelectItem value="Annual General Meeting" className="text-xs">Annual General Meeting</SelectItem>
                <SelectItem value="Extraordinary General Meeting" className="text-xs">Extraordinary General Meeting</SelectItem>
                <SelectItem value="Committee Meeting" className="text-xs">Committee Meeting</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* MEETING DATE & START TIME */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="space-y-2">
            <Label htmlFor="meetingDate" className="text-xs font-semibold text-slate-700">Meeting Date *</Label>
            <Input
              id="meetingDate"
              type="date"
              value={formData.meetingDate}
              onChange={(e) => {
                setFormData(prev => ({ ...prev, meetingDate: e.target.value }));
                if (e.target.value) {
                  const dayName = new Date(e.target.value).toLocaleDateString('en-US', { weekday: 'long' });
                  setFormData(prev => ({ ...prev, meetingDay: dayName }));
                }
              }}
              className="bg-white border-slate-200 h-9 rounded-lg text-xs"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="meetingDay" className="text-xs font-semibold text-slate-700">Meeting Day</Label>
            <Input
              id="meetingDay"
              value={formData.meetingDay}
              readOnly
              placeholder="Auto-calculated from date"
              className="bg-slate-50 border-slate-200 h-9 rounded-lg text-xs text-slate-600"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="timeCommenced" className="text-xs font-semibold text-slate-700">Meeting Start Time</Label>
            <Input
              id="timeCommenced"
              type="time"
              value={formData.timeCommenced}
              onChange={(e) => setFormData(prev => ({ ...prev, timeCommenced: e.target.value }))}
              className="bg-white border-slate-200 h-9 rounded-lg text-xs"
            />
          </div>
        </div>

      </CardContent>
    </Card>
  );
};
