/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { FileText, Download, Building, UserCheck, Eye, Plus, X, Search } from 'lucide-react';
import ProductDashboardLayout from '@/components/layout/ProductDashboardLayout';
import templateStructures from '@/template_structures.json';
import { getMinutesNavItems } from '@/constants/minutesNavigation';
import { useToast } from "@/components/ui/use-toast";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useVertical } from '@/contexts/VerticalContext';

// Floating Auto-Suggest Director Input Component
const DirectorInputRow: React.FC<{
  index: number;
  director: { name: string; din: string };
  masterDirectors: any[];
  onNameChange: (index: number, name: string, din?: string) => void;
  onDinChange: (index: number, din: string) => void;
  onRemove: (index: number) => void;
  canRemove: boolean;
}> = ({ index, director, masterDirectors, onNameChange, onDinChange, onRemove, canRemove }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState(director.name);

  useEffect(() => {
    setQuery(director.name);
  }, [director.name]);

  const filtered = useMemo(() => {
    if (!query || query.trim().length === 0) return masterDirectors.slice(0, 8);
    const q = query.toLowerCase().trim();
    return masterDirectors.filter(d =>
      d.name?.toLowerCase().includes(q) || d.din?.includes(q)
    ).slice(0, 8);
  }, [query, masterDirectors]);

  const handleSelect = (d: any) => {
    setQuery(d.name);
    onNameChange(index, d.name, d.din);
    setIsOpen(false);
  };

  return (
    <div className="relative flex items-center gap-2 p-2 bg-slate-50 border border-slate-200 rounded-lg">
      <div className="flex-1 relative">
        <Input
          value={query}
          onChange={(e) => {
            const val = e.target.value;
            setQuery(val);
            onNameChange(index, val);
            setIsOpen(true);
          }}
          onFocus={() => setIsOpen(true)}
          onBlur={() => setTimeout(() => setIsOpen(false), 200)}
          placeholder={`Director ${index + 1} Name (type to search...)`}
          className="bg-white border-slate-200 h-8 text-xs font-semibold text-slate-800"
        />
        {isOpen && filtered.length > 0 && (
          <div className="absolute left-0 right-0 top-9 bg-white border border-slate-200 rounded-lg shadow-xl z-50 max-h-48 overflow-y-auto py-1">
            {filtered.map((d: any, idx: number) => (
              <div
                key={idx}
                onMouseDown={() => handleSelect(d)}
                className="px-3 py-1.5 hover:bg-blue-50 cursor-pointer flex justify-between items-center text-xs transition-colors border-b border-slate-100 last:border-0"
              >
                <div className="flex items-center gap-1.5">
                  <UserCheck className="h-3.5 w-3.5 text-blue-600 shrink-0" />
                  <span className="font-bold text-slate-900">{d.name}</span>
                </div>
                <span className="font-mono text-[10px] text-blue-700 bg-blue-100/70 px-2 py-0.5 rounded font-semibold">
                  DIN: {d.din}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
      <div className="w-36">
        <Input
          value={director.din}
          onChange={(e) => onDinChange(index, e.target.value)}
          placeholder="DIN (8 Digits)"
          className="bg-white border-slate-200 h-8 text-xs font-mono text-slate-700 font-semibold"
        />
      </div>
      {canRemove && (
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={() => onRemove(index)}
          className="h-8 w-8 p-0 text-slate-400 hover:text-red-700"
        >
          <X className="h-4 w-4" />
        </Button>
      )}
    </div>
  );
};

const TemplateRenderer = () => {
  const navigationItems = getMinutesNavItems('renderer');
  const { toast } = useToast();
  const { selectedCompany: ctxCompany } = useVertical();

  const [dbTemplates, setDbTemplates] = useState<any[]>([]);
  const [masterDirectors, setMasterDirectors] = useState<any[]>([]);
  const [templateContent, setTemplateContent] = useState<any[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Dynamic Form State
  const [formData, setFormData] = useState({
    template: '87. AGEL - BM - 28.04.2025.docx',
    companyName: '',
    meetingNumber: '1st',
    meetingType: 'Board of Directors',
    meetingDay: 'Monday',
    meetingDate: new Date().toISOString().split('T')[0],
    meetingStartTime: '10:00',
    meetingEndTime: '11:30',
    meetingPlace: 'Adani Corporate House, Ahmedabad',
    chairmanName: '',
    directors: [
      { name: '', din: '' },
      { name: '', din: '' }
    ],
    authorisedOfficer: '',
    previousMeetingDate: '',
    auditorPaymentAmount: '',
    auditorPaymentWords: '',
    financialYear: new Date().getFullYear().toString(),
    agmNumber: '',
    agmDay: '',
    agmDate: '',
    agmTime: '',
    agmPlace: '',
    recordingDate: new Date().toISOString().split('T')[0],
    signingDate: new Date().toISOString().split('T')[0],
    quorum: 'Valid Quorum Present',
    previousMinutes: 'Confirmed and Signed',
    concerns: 'None',
    declarations: 'Received and Noted',
    auditorPayment: 'Approved',
    financialStatements: 'Approved',
    directorsReport: 'Approved',
  });

  // Fetch Database Templates & Master Directors
  useEffect(() => {
    const fetchDbTemplates = async () => {
      try {
        const res = await fetch('/api/templates');
        if (res.ok) {
          const data = await res.json();
          const list = data.data || [];
          setDbTemplates(list);
          if (list.length > 0) {
            const firstT = list[0]?.name || list[0];
            if (firstT && typeof firstT === 'string') {
              setFormData(prev => ({ ...prev, template: prev.template || firstT }));
            }
          }
        }
      } catch (err) {
        console.error("Failed to fetch templates from DB", err);
      }
    };

    const fetchMasterDirectors = async () => {
      try {
        const res = await fetch('/api/directors');
        if (res.ok) {
          const data = await res.json();
          const list = Array.isArray(data) ? data : (data.data || []);
          setMasterDirectors(list);
        }
      } catch (err) {
        console.error("Failed to fetch master directors", err);
      }
    };

    fetchDbTemplates();
    fetchMasterDirectors();
  }, []);

  // Sync with active company from global VerticalContext
  useEffect(() => {
    if (ctxCompany && ctxCompany.name) {
      handleCompanyChange(ctxCompany.name);
    }
  }, [ctxCompany]);

  // When Company Name changes, auto-fetch registered directors dynamically
  const handleCompanyChange = async (cName: string) => {
    setFormData(prev => ({ ...prev, companyName: cName }));
    if (!cName.trim()) return;

    try {
      const res = await fetch(`/api/companies/${encodeURIComponent(cName)}/directors`);
      if (res.ok) {
        const data = await res.json();
        const dirs = data.data || (Array.isArray(data) ? data : []);
        if (dirs.length > 0) {
          const fetchedDirs = dirs.map((d: any) => ({
            name: d.name || '',
            din: d.din || ''
          }));
          setFormData(prev => ({
            ...prev,
            directors: fetchedDirs,
            chairmanName: fetchedDirs[0]?.name || prev.chairmanName
          }));
          toast({
            title: "Directors Loaded",
            description: `Auto-loaded ${fetchedDirs.length} directors for ${cName}.`
          });
        }
      }
    } catch (err) {
      console.error("Failed to fetch company directors", err);
    }
  };

  const handleDirectorNameChange = (index: number, nameValue: string, explicitDin?: string) => {
    let matchedDin = explicitDin;
    if (!matchedDin && nameValue.trim().length > 0) {
      const q = nameValue.toLowerCase().trim();
      const matched = masterDirectors.find(d =>
        d.name?.toLowerCase().trim() === q ||
        d.name?.toLowerCase().includes(q)
      );
      if (matched) matchedDin = matched.din;
    }

    setFormData(prev => {
      const newDirs = [...prev.directors];
      newDirs[index] = {
        name: nameValue,
        din: matchedDin || newDirs[index].din
      };
      return { ...prev, directors: newDirs };
    });

    if (matchedDin) {
      toast({
        title: "DIN Auto-Populated",
        description: `Linked DIN ${matchedDin} for ${nameValue}.`
      });

      // Fetch real Director Disclosure details (MBP-1 & DIR-8)
      fetch(`/api/directors/${encodeURIComponent(matchedDin)}/disclosure-details`)
        .then(res => res.ok ? res.json() : null)
        .then(details => {
          if (details && details.mbp1_disclosure_text) {
            toast({
              title: "Director Disclosure Loaded",
              description: `Fetched MBP-1 interest & DIR-8 status for ${nameValue}.`
            });
          }
        })
        .catch(err => console.error("Error fetching director disclosure details:", err));
    }
  };

  const handleDirectorDinChange = (index: number, dinValue: string) => {
    setFormData(prev => {
      const newDirs = [...prev.directors];
      newDirs[index] = { ...newDirs[index], din: dinValue };
      return { ...prev, directors: newDirs };
    });
  };

  const addDirector = () => {
    setFormData(prev => ({
      ...prev,
      directors: [...prev.directors, { name: '', din: '' }]
    }));
  };

  const removeDirector = (index: number) => {
    setFormData(prev => {
      const newDirs = [...prev.directors];
      newDirs.splice(index, 1);
      return { ...prev, directors: newDirs };
    });
  };

  const numberToIndianRupeesWords = (numStr: string): string => {
    const clean = numStr.replace(/[^0-9]/g, '');
    if (!clean || clean === '0') return '';
    const num = parseInt(clean, 10);
    if (isNaN(num) || num <= 0) return '';

    const single = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine'];
    const double = ['Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen'];
    const tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety'];

    const formatLessThanThousand = (n: number): string => {
      let str = '';
      if (n >= 100) {
        str += single[Math.floor(n / 100)] + ' Hundred ';
        n %= 100;
      }
      if (n >= 10 && n < 20) {
        str += double[n - 10] + ' ';
      } else {
        if (n >= 20) {
          str += tens[Math.floor(n / 10)] + ' ';
          n %= 10;
        }
        if (n > 0) {
          str += single[n] + ' ';
        }
      }
      return str.trim();
    };

    let word = '';
    let n = num;

    if (Math.floor(n / 10000000) > 0) {
      word += formatLessThanThousand(Math.floor(n / 10000000)) + ' Crore ';
      n %= 10000000;
    }
    if (Math.floor(n / 100000) > 0) {
      word += formatLessThanThousand(Math.floor(n / 100000)) + ' Lakhs ';
      n %= 100000;
    }
    if (Math.floor(n / 1000) > 0) {
      word += formatLessThanThousand(Math.floor(n / 1000)) + ' Thousand ';
      n %= 1000;
    }
    if (n > 0) {
      word += formatLessThanThousand(n);
    }

    return `Rupees ${word.trim()} Only`;
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    if (name === 'auditorPaymentAmount') {
      const words = numberToIndianRupeesWords(value);
      setFormData(prev => ({
        ...prev,
        auditorPaymentAmount: value,
        auditorPaymentWords: words || prev.auditorPaymentWords
      }));
    } else {
      setFormData(prev => ({ ...prev, [name]: value }));
    }
    if (errors[name]) {
      setErrors(prev => {
        const next = { ...prev };
        delete next[name];
        return next;
      });
    }
  };

  const handleSelectChange = (name: string, value: string) => {
    setFormData(prev => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors(prev => {
        const next = { ...prev };
        delete next[name];
        return next;
      });
    }
  };

  // Smart Template Content Resolver
  useEffect(() => {
    const loadTemplateContent = () => {
      try {
        const selected = formData.template;
        if (!selected) return;

        let structure = templateStructures[selected as keyof typeof templateStructures];

        if (!structure || structure.length === 0) {
          if (selected.includes('28.07.2025') || selected.includes('Q2')) {
            structure = templateStructures['Q2'];
          } else if (selected.includes('28.10.2025') || selected.includes('Q3')) {
            structure = templateStructures['Q3'];
          } else if (selected.includes('23.01.2026') || selected.includes('Q4')) {
            structure = templateStructures['Q4'];
          } else {
            structure = templateStructures['Q1'];
          }
        }
        setTemplateContent(structure || []);
      } catch (error) {
        console.error('Error loading template structure:', error);
        setTemplateContent([]);
      }
    };
    loadTemplateContent();
  }, [formData.template]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      const response = await fetch('/api/generate-minutes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        const result = await response.json();
        const downloadUrl = `/api/templates/download/${result.filename}`;
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = result.filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        toast({ title: "Document Generated", description: "Your official minutes DOCX file has been downloaded." });
      } else {
        const error = await response.json();
        toast({ title: "Generation Error", description: error.detail || "Failed to generate document.", variant: "destructive" });
      }
    } catch (error) {
      console.error('Error:', error);
      toast({ title: "Error", description: "Failed to connect to server.", variant: "destructive" });
    } finally {
      setIsSubmitting(false);
    }
  };

  const placeholderToFieldMap: Record<string, string> = {
    '[No. of Meeting]': 'meetingNumber',
    '[Type of Meeting]': 'meetingType',
    '[Name of Company]': 'companyName',
    '[Day of Meeting]': 'meetingDay',
    '[Date of Meeting]': 'meetingDate',
    '[Time: COMMENCED AT]': 'meetingStartTime',
    '[Time: CONCLUDED AT]': 'meetingEndTime',
    '[Place of Meeting]': 'meetingPlace',
    '[Manual]': 'chairmanName',
    '[Auto]': 'previousMeetingDate',
    '[from MCA]': 'directors',
    '[From website: MCA]': 'agmPlace',
    '20____': 'financialYear',
    '[Recording Date]': 'recordingDate',
    '[Signing Date]': 'signingDate'
  };

  const getFormValue = (fieldName: string): string => {
    const val = formData[fieldName as keyof typeof formData];
    if (Array.isArray(val)) return '';
    return (val as string) || '';
  };

  const renderTemplatePreview = () => {
    if (templateContent.length === 0) {
      return (
        <div className="flex flex-col items-center justify-center h-64 text-slate-400 text-xs space-y-2">
          <FileText className="h-10 w-10 text-slate-300" />
          <p>Select an official template to preview</p>
        </div>
      );
    }

    return (
      <div className="space-y-4 text-xs leading-relaxed text-slate-800 font-sans">
        {templateContent.map((element, index) => {
          if (element.type === 'paragraph') {
            return (
              <p key={index} className="mb-2">
                {element.segments.map((segment: any, segIndex: number) => {
                  if (segment.is_placeholder) {
                    if (segment.text === '[from MCA]') {
                      return (
                        <span key={segIndex} className="inline-block mx-1">
                          <Input
                            type="text"
                            value={formData.directors[0]?.name || ''}
                            onChange={(e) => handleDirectorNameChange(0, e.target.value)}
                            placeholder="Director Name"
                            className="w-36 h-7 inline-block text-xs bg-blue-50/60 border-blue-300 text-blue-900 font-semibold focus:bg-white"
                          />
                        </span>
                      );
                    } else if (segment.text === '[Manual]') {
                      return (
                        <span key={segIndex} className="inline-block mx-1">
                          <Input
                            type="text"
                            value={formData.chairmanName}
                            onChange={(e) => handleInputChange({ target: { name: 'chairmanName', value: e.target.value } } as any)}
                            placeholder="Chairman Name"
                            className="w-36 h-7 inline-block text-xs bg-blue-50/60 border-blue-300 text-blue-900 font-semibold focus:bg-white"
                          />
                        </span>
                      );
                    } else {
                      const fieldName = placeholderToFieldMap[segment.text] || segment.text.replace(/[[\]]/g, '');
                      return (
                        <span key={segIndex} className="inline-block mx-1">
                          <Input
                            type={fieldName.includes('Date') ? 'date' : 'text'}
                            value={getFormValue(fieldName)}
                            onChange={(e) => {
                              const val = e.target.value;
                              if (fieldName === 'companyName') {
                                handleCompanyChange(val);
                              } else {
                                setFormData(prev => ({ ...prev, [fieldName]: val }));
                              }
                            }}
                            placeholder={segment.text}
                            className="w-36 h-7 inline-block text-xs bg-blue-50/60 border-blue-300 text-blue-900 font-semibold focus:bg-white"
                          />
                        </span>
                      );
                    }
                  } else {
                    return <span key={segIndex}>{segment.text}</span>;
                  }
                })}
              </p>
            );
          } else if (element.type === 'table') {
            return (
              <div key={index} className="my-3 p-3 bg-slate-50 border border-slate-200 rounded-lg">
                <h4 className="font-bold text-slate-800 text-xs mb-2">Board Directors Attendance Table:</h4>
                <div className="space-y-1.5">
                  {formData.directors.map((d, dIdx) => (
                    <div key={dIdx} className="flex gap-2 items-center text-xs">
                      <span className="w-5 font-bold text-slate-400">{dIdx + 1}.</span>
                      <span className="font-semibold text-slate-800 flex-1">{d.name || "Director Name"}</span>
                      <span className="font-mono text-blue-700 bg-blue-50 px-2 py-0.5 border border-blue-200 rounded font-semibold">
                        DIN: {d.din || "--------"}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            );
          }
          return null;
        })}
      </div>
    );
  };

  return (
    <ProductDashboardLayout productName="Generate Minutes" productRoute="/minutes-preparation" navigationItems={navigationItems}>
      <div className="p-4 h-[calc(100vh-65px)] overflow-hidden">
        <div className="border border-slate-200 rounded-xl bg-white shadow-xs p-4 flex flex-col h-full overflow-hidden space-y-3">

          {/* Header Bar */}
          <div className="pb-3 border-b border-slate-100 flex flex-col md:flex-row justify-between items-start md:items-center gap-3 shrink-0">
            <div>
              <h1 className="text-xl font-bold text-slate-900">Template Renderer</h1>
              <p className="text-xs text-slate-500 mt-0.5">Live document preview and statutory metadata entry.</p>
            </div>

            {/* Template Selection Dropdown */}
            <div className="w-full md:w-80 shrink-0">
              <Select
                value={formData.template}
                onValueChange={(val) => handleSelectChange('template', val)}
              >
                <SelectTrigger className="bg-white border-slate-200 text-xs h-9 rounded-lg font-semibold text-slate-800">
                  <SelectValue placeholder="Select Official Template" />
                </SelectTrigger>
                <SelectContent className="bg-white max-h-[300px]">
                  {dbTemplates.map((t) => {
                    const rawName = t.name || t;
                    let companyPrefix = 'Adani Group';
                    if (rawName.startsWith('AGEL')) companyPrefix = 'AGEL';
                    else if (rawName.startsWith('AGE(UP)L')) companyPrefix = 'AGE(UP)L';
                    else if (rawName.includes('AGE25BL')) companyPrefix = 'AGE25BL';

                    let category = 'Board Meeting';
                    if (rawName.includes('- AC -') || rawName.toLowerCase().includes('audit')) category = 'Audit Committee';
                    else if (rawName.toLowerCase().includes('agm')) category = 'AGM';

                    let quarterTag = '';
                    if (rawName.includes('28.04') || rawName.includes('Q1')) quarterTag = ' (Q1)';
                    else if (rawName.includes('28.07') || rawName.includes('Q2')) quarterTag = ' (Q2)';
                    else if (rawName.includes('28.10') || rawName.includes('Q3')) quarterTag = ' (Q3)';
                    else if (rawName.includes('23.01') || rawName.includes('Q4')) quarterTag = ' (Q4)';

                    const cleanTitle = `${companyPrefix} — ${category}${quarterTag}`;

                    return (
                      <SelectItem key={t.id || rawName} value={rawName} className="bg-white text-xs py-1.5">
                        <div className="flex items-center justify-between w-full gap-2">
                          <span className="font-semibold text-slate-800">{cleanTitle}</span>
                          <span className="text-[9px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-500 font-medium">
                            {category}
                          </span>
                        </div>
                      </SelectItem>
                    );
                  })}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Main 50/50 Non-scrolling Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 flex-1 overflow-hidden">

            {/* LEFT COLUMN: Live Document Paper Preview (6 Cols) */}
            <div className="lg:col-span-6 flex flex-col overflow-hidden h-full">
              <Card className="border border-slate-200 shadow-none bg-white rounded-xl overflow-hidden flex-1 flex flex-col h-full">
                <CardHeader className="bg-slate-50/50 border-b border-slate-100 py-2.5 px-4 shrink-0 flex flex-row items-center justify-between">
                  <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-2">
                    <Eye className="h-3.5 w-3.5 text-slate-400" />
                    Template Live Preview Sheet
                  </CardTitle>
                  <span className="text-[11px] font-mono text-slate-400 truncate max-w-[200px]">{formData.template}</span>
                </CardHeader>

                <CardContent className="p-4 flex-1 overflow-y-auto bg-slate-100/40">
                  <div className="bg-white border border-slate-200 rounded-lg p-6 shadow-xs min-h-full">
                    {renderTemplatePreview()}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* RIGHT COLUMN: Metadata & Auto-Recommending Directors (6 Cols) */}
            <div className="lg:col-span-6 flex flex-col overflow-hidden h-full">
              <Card className="border border-slate-200 shadow-none bg-white rounded-xl overflow-hidden flex-1 flex flex-col h-full">
                <CardHeader className="bg-slate-50/50 border-b border-slate-100 py-2.5 px-4 shrink-0">
                  <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-2">
                    <FileText className="h-3.5 w-3.5 text-slate-400" />
                    Meeting Metadata & Attendees
                  </CardTitle>
                </CardHeader>

                <CardContent className="p-3.5 flex-1 overflow-hidden flex flex-col">
                  <form onSubmit={handleSubmit} className="flex-1 flex flex-col overflow-hidden justify-between space-y-3">
                    <Tabs defaultValue="attendees" className="flex-1 flex flex-col overflow-hidden">
                      <TabsList className="grid w-full grid-cols-3 bg-slate-100 p-1 mb-3 rounded-lg shrink-0">
                        <TabsTrigger value="company" className="rounded-md py-1 text-xs font-semibold">Meeting Info</TabsTrigger>
                        <TabsTrigger value="attendees" className="rounded-md py-1 text-xs font-semibold">Directors & DIN</TabsTrigger>
                        <TabsTrigger value="details" className="rounded-md py-1 text-xs font-semibold">Financials</TabsTrigger>
                      </TabsList>

                      {/* TAB 1: MEETING INFO */}
                      <TabsContent value="company" className="flex-1 overflow-y-auto pr-1 space-y-3">
                        <div className="space-y-1">
                          <Label htmlFor="companyName" className="text-xs font-semibold text-slate-700">Company Name *</Label>
                          <div className="relative">
                            <Building className="absolute left-3 top-2.5 h-3.5 w-3.5 text-slate-400" />
                            <Input
                              id="companyName"
                              name="companyName"
                              value={formData.companyName}
                              onChange={(e) => handleCompanyChange(e.target.value)}
                              placeholder="Enter or search company..."
                              className="pl-8 bg-white border-slate-200 h-8 text-xs rounded-lg font-semibold"
                            />
                          </div>
                        </div>

                        <div className="grid grid-cols-2 gap-2">
                          <div className="space-y-1">
                            <Label htmlFor="meetingNumber" className="text-xs font-semibold text-slate-700">Meeting Number *</Label>
                            <Input
                              id="meetingNumber"
                              name="meetingNumber"
                              value={formData.meetingNumber}
                              onChange={handleInputChange}
                              placeholder="e.g., 1st, 2nd, 87th"
                              className="bg-white border-slate-200 h-8 text-xs rounded-lg"
                            />
                          </div>
                          <div className="space-y-1">
                            <Label htmlFor="meetingType" className="text-xs font-semibold text-slate-700">Meeting Type</Label>
                            <Select value={formData.meetingType} onValueChange={(val) => handleSelectChange('meetingType', val)}>
                              <SelectTrigger className="bg-white border-slate-200 h-8 text-xs rounded-lg">
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent className="bg-white">
                                <SelectItem value="Board of Directors">Board of Directors</SelectItem>
                                <SelectItem value="Audit Committee">Audit Committee</SelectItem>
                                <SelectItem value="Annual General Meeting">Annual General Meeting</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                        </div>

                        <div className="grid grid-cols-2 gap-2">
                          <div className="space-y-1">
                            <Label htmlFor="meetingDay" className="text-xs font-semibold text-slate-700">Day of Meeting</Label>
                            <Input
                              id="meetingDay"
                              name="meetingDay"
                              value={formData.meetingDay}
                              onChange={handleInputChange}
                              placeholder="e.g., Monday"
                              className="bg-white border-slate-200 h-8 text-xs rounded-lg"
                            />
                          </div>
                          <div className="space-y-1">
                            <Label htmlFor="meetingDate" className="text-xs font-semibold text-slate-700">Date of Meeting *</Label>
                            <Input
                              id="meetingDate"
                              name="meetingDate"
                              type="date"
                              value={formData.meetingDate}
                              onChange={handleInputChange}
                              className="bg-white border-slate-200 h-8 text-xs rounded-lg"
                            />
                          </div>
                        </div>

                        <div className="grid grid-cols-2 gap-2">
                          <div className="space-y-1">
                            <Label htmlFor="meetingStartTime" className="text-xs font-semibold text-slate-700">Start Time</Label>
                            <Input
                              id="meetingStartTime"
                              name="meetingStartTime"
                              type="time"
                              value={formData.meetingStartTime}
                              onChange={handleInputChange}
                              className="bg-white border-slate-200 h-8 text-xs rounded-lg"
                            />
                          </div>
                          <div className="space-y-1">
                            <Label htmlFor="meetingEndTime" className="text-xs font-semibold text-slate-700">End Time</Label>
                            <Input
                              id="meetingEndTime"
                              name="meetingEndTime"
                              type="time"
                              value={formData.meetingEndTime}
                              onChange={handleInputChange}
                              className="bg-white border-slate-200 h-8 text-xs rounded-lg"
                            />
                          </div>
                        </div>

                        <div className="space-y-1">
                          <Label htmlFor="meetingPlace" className="text-xs font-semibold text-slate-700">Place of Meeting *</Label>
                          <Input
                            id="meetingPlace"
                            name="meetingPlace"
                            value={formData.meetingPlace}
                            onChange={handleInputChange}
                            placeholder="Enter meeting venue..."
                            className="bg-white border-slate-200 h-8 text-xs rounded-lg"
                          />
                        </div>
                      </TabsContent>

                      {/* TAB 2: DIRECTORS & FLOATING AUTO DIN LOOKUP */}
                      <TabsContent value="attendees" className="flex-1 overflow-y-auto pr-1 space-y-3">
                        <div className="space-y-1">
                          <Label htmlFor="chairmanName" className="text-xs font-semibold text-slate-700">Chairman Name *</Label>
                          <Select
                            value={formData.chairmanName}
                            onValueChange={(val) => setFormData(prev => ({ ...prev, chairmanName: val }))}
                          >
                            <SelectTrigger className="bg-white border-slate-200 h-8 text-xs rounded-lg font-bold text-slate-900">
                              <SelectValue placeholder="Select Chairman from company directors..." />
                            </SelectTrigger>
                            <SelectContent className="bg-white">
                              {formData.directors && formData.directors.length > 0 ? (
                                formData.directors.map((d: any, idx: number) => (
                                  <SelectItem key={idx} value={d.name || `Director ${idx + 1}`} className="text-xs font-medium">
                                    {d.name || `Director ${idx + 1}`} {d.din ? `(DIN: ${d.din})` : ''}
                                  </SelectItem>
                                ))
                              ) : (
                                <SelectItem value="Gautam Adani" className="text-xs font-medium">
                                  Gautam Adani (DIN: 00222019)
                                </SelectItem>
                              )}
                            </SelectContent>
                          </Select>
                        </div>

                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <Label className="text-xs font-semibold text-slate-700 flex items-center gap-1.5">
                              <UserCheck className="h-3.5 w-3.5 text-blue-600" />
                              Board Directors & Auto DIN Lookup *
                            </Label>
                            <span className="text-[10px] text-blue-600 font-semibold bg-blue-50 px-2 py-0.5 rounded">
                              Type to see floating suggestions
                            </span>
                          </div>

                          <div className="space-y-2">
                            {formData.directors.map((director, index) => (
                              <DirectorInputRow
                                key={index}
                                index={index}
                                director={director}
                                masterDirectors={masterDirectors}
                                onNameChange={handleDirectorNameChange}
                                onDinChange={handleDirectorDinChange}
                                onRemove={removeDirector}
                                canRemove={formData.directors.length > 1}
                              />
                            ))}
                          </div>

                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            onClick={addDirector}
                            className="w-full h-8 text-xs font-semibold border-dashed border-slate-300 text-slate-700 hover:bg-slate-50"
                          >
                            <Plus className="h-3.5 w-3.5 mr-1.5" />
                            Add Director
                          </Button>
                        </div>
                      </TabsContent>

                      {/* TAB 3: DETAILS & FINANCIALS */}
                      <TabsContent value="details" className="flex-1 overflow-y-auto pr-1 space-y-3">
                        <div className="grid grid-cols-2 gap-2">
                          <div className="space-y-1">
                            <Label htmlFor="financialYear" className="text-xs font-semibold text-slate-700">Financial Year</Label>
                            <Input
                              id="financialYear"
                              name="financialYear"
                              value={formData.financialYear}
                              onChange={handleInputChange}
                              placeholder="e.g., 2026"
                              className="bg-white border-slate-200 h-8 text-xs rounded-lg"
                            />
                          </div>
                          <div className="space-y-1">
                            <Label htmlFor="auditorPaymentAmount" className="text-xs font-semibold text-slate-700">Auditor Payment (₹)</Label>
                            <Input
                              id="auditorPaymentAmount"
                              name="auditorPaymentAmount"
                              value={formData.auditorPaymentAmount}
                              onChange={handleInputChange}
                              placeholder="e.g., 500000"
                              className="bg-white border-slate-200 h-8 text-xs rounded-lg"
                            />
                          </div>
                        </div>

                        <div className="space-y-1">
                          <Label htmlFor="auditorPaymentWords" className="text-xs font-semibold text-slate-700">Payment Amount (In Words)</Label>
                          <Input
                            id="auditorPaymentWords"
                            name="auditorPaymentWords"
                            value={formData.auditorPaymentWords}
                            onChange={handleInputChange}
                            placeholder="Rupees Five Lakhs Only"
                            className="bg-white border-slate-200 h-8 text-xs rounded-lg"
                          />
                        </div>
                      </TabsContent>
                    </Tabs>

                    {/* Bottom Action Button */}
                    <div className="pt-2 border-t border-slate-100 shrink-0">
                      <Button
                        type="submit"
                        disabled={isSubmitting}
                        className="w-full h-9 bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs rounded-lg shadow-xs transition-colors"
                      >
                        {isSubmitting ? (
                          <span className="flex items-center justify-center gap-2">
                            <div className="animate-spin rounded-full h-3.5 w-3.5 border-2 border-white border-t-transparent"></div>
                            Generating Document...
                          </span>
                        ) : (
                          <span className="flex items-center justify-center gap-2">
                            <Download className="h-4 w-4" />
                            Generate Minutes Document
                          </span>
                        )}
                      </Button>
                    </div>
                  </form>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </div>
    </ProductDashboardLayout>
  );
};

export default TemplateRenderer;
