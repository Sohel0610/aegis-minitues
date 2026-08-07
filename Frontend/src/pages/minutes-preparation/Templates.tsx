/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  FileText,
  Upload,
  Download,
  Search,
  Building2,
  Calendar,
  Layers,
  RefreshCw,
} from 'lucide-react';
import ProductDashboardLayout from '@/components/layout/ProductDashboardLayout';
import { getMinutesNavItems } from '@/constants/minutesNavigation';
import { useToast } from '@/components/ui/use-toast';
import { getCleanBusinessTemplateName } from './components/form-steps/Step0TemplateCompany';

interface StoredTemplate {
  id?: number;
  name: string;
  category?: string;
  companyName?: string;
  quarter?: string;
  size?: number;
  lastModified?: string;
  path?: string;
}

const formatBytes = (bytes?: number) => {
  if (!bytes || bytes <= 0) return '—';
  if (bytes < 1024) return `${bytes} B`;
  return `${(bytes / 1024).toFixed(1)} KB`;
};

const formatDate = (value?: string) => {
  if (!value) return '—';
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
};

const categoryBadgeClass = (category: string) => {
  const c = category.toLowerCase();
  if (c.includes('audit')) return 'bg-amber-50 text-amber-800 border-amber-200';
  if (c.includes('board')) return 'bg-blue-50 text-blue-800 border-blue-200';
  if (c.includes('agm') || c.includes('egm')) return 'bg-violet-50 text-violet-800 border-violet-200';
  if (c.includes('committee')) return 'bg-emerald-50 text-emerald-800 border-emerald-200';
  return 'bg-slate-50 text-slate-700 border-slate-200';
};

const Templates = () => {
  const navigationItems = getMinutesNavItems('templates');
  const { toast } = useToast();
  const uploadInputRef = useRef<HTMLInputElement>(null);

  const [templates, setTemplates] = useState<StoredTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [companyFilter, setCompanyFilter] = useState('all');

  const fetchTemplates = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/templates');
      if (res.ok) {
        const data = await res.json();
        setTemplates(data.data || []);
      } else {
        toast({
          title: 'Could not load templates',
          description: 'Please try again.',
          variant: 'destructive',
        });
      }
    } catch (err) {
      console.error('Failed to fetch templates', err);
      toast({
        title: 'Could not load templates',
        description: 'Check that the API server is running.',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void fetchTemplates();
  }, []);

  const enrichedTemplates = useMemo(() => {
    return templates.map((t) => {
      const formatted = getCleanBusinessTemplateName(t.name);
      return {
        ...t,
        displayTitle: formatted.title,
        displayCategory: t.category || formatted.category,
        displayCompany: t.companyName || '—',
        displayQuarter: t.quarter || formatted.quarterTag,
      };
    });
  }, [templates]);

  const categoryOptions = useMemo(() => {
    const set = new Set<string>();
    enrichedTemplates.forEach((t) => {
      if (t.displayCategory) set.add(t.displayCategory);
    });
    return Array.from(set).sort();
  }, [enrichedTemplates]);

  const companyOptions = useMemo(() => {
    const set = new Set<string>();
    enrichedTemplates.forEach((t) => {
      if (t.displayCompany && t.displayCompany !== '—') set.add(t.displayCompany);
    });
    return Array.from(set).sort();
  }, [enrichedTemplates]);

  const filteredTemplates = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    return enrichedTemplates.filter((t) => {
      if (categoryFilter !== 'all' && t.displayCategory !== categoryFilter) return false;
      if (companyFilter !== 'all' && t.displayCompany !== companyFilter) return false;
      if (!q) return true;
      return (
        t.name.toLowerCase().includes(q) ||
        t.displayTitle.toLowerCase().includes(q) ||
        (t.displayCompany || '').toLowerCase().includes(q) ||
        (t.displayCategory || '').toLowerCase().includes(q)
      );
    });
  }, [enrichedTemplates, searchQuery, categoryFilter, companyFilter]);

  const stats = useMemo(() => {
    const companies = new Set(
      enrichedTemplates.map((t) => t.displayCompany).filter((c) => c && c !== '—')
    );
    const board = enrichedTemplates.filter((t) =>
      (t.displayCategory || '').toLowerCase().includes('board')
    ).length;
    const committee = enrichedTemplates.filter((t) => {
      const c = (t.displayCategory || '').toLowerCase();
      return c.includes('committee') || c.includes('audit');
    }).length;
    return {
      total: enrichedTemplates.length,
      companies: companies.size,
      board,
      committee,
    };
  }, [enrichedTemplates]);

  const handleDownload = (filename: string) => {
    const link = document.createElement('a');
    link.href = `/api/templates/download/${encodeURIComponent(filename)}`;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleUpload = async (file: File | null | undefined) => {
    if (!file) return;
    if (!file.name.toLowerCase().endsWith('.docx')) {
      toast({
        title: 'Invalid file',
        description: 'Only .docx meeting templates are supported.',
        variant: 'destructive',
      });
      return;
    }

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('/api/upload-template', {
        method: 'POST',
        body: formData,
      });
      if (res.ok) {
        toast({ title: 'Template uploaded', description: `${file.name} was added to the library.` });
        await fetchTemplates();
      } else {
        const err = await res.json().catch(() => ({}));
        toast({
          title: 'Upload failed',
          description: err.detail || 'Could not upload template.',
          variant: 'destructive',
        });
      }
    } catch (err) {
      console.error('Upload error', err);
      toast({
        title: 'Upload failed',
        description: 'Could not connect to the server.',
        variant: 'destructive',
      });
    } finally {
      setUploading(false);
      if (uploadInputRef.current) uploadInputRef.current.value = '';
    }
  };

  return (
    <ProductDashboardLayout
      productName="Generate Minutes"
      productRoute="/minutes-preparation"
      navigationItems={navigationItems}
    >
      <div className="container mx-auto py-6 space-y-6">
        <div className="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Meeting Template Library</h1>
            <p className="text-sm text-slate-500 mt-1">
              Browse, search, and download official DOCX minutes templates stored in the system.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" size="sm" onClick={() => void fetchTemplates()} disabled={loading}>
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button
              size="sm"
              className="bg-blue-600 hover:bg-blue-700"
              onClick={() => uploadInputRef.current?.click()}
              disabled={uploading}
            >
              <Upload className="h-4 w-4 mr-2" />
              {uploading ? 'Uploading…' : 'Upload template'}
            </Button>
            <input
              ref={uploadInputRef}
              type="file"
              accept=".docx"
              className="hidden"
              onChange={(e) => void handleUpload(e.target.files?.[0])}
            />
          </div>
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <Card className="border-slate-200 shadow-xs">
            <CardContent className="p-4 flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
                <FileText className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xs text-slate-500">Total templates</p>
                <p className="text-xl font-bold text-slate-900">{stats.total}</p>
              </div>
            </CardContent>
          </Card>
          <Card className="border-slate-200 shadow-xs">
            <CardContent className="p-4 flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
                <Building2 className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xs text-slate-500">Companies</p>
                <p className="text-xl font-bold text-slate-900">{stats.companies}</p>
              </div>
            </CardContent>
          </Card>
          <Card className="border-slate-200 shadow-xs">
            <CardContent className="p-4 flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
                <Layers className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xs text-slate-500">Board meetings</p>
                <p className="text-xl font-bold text-slate-900">{stats.board}</p>
              </div>
            </CardContent>
          </Card>
          <Card className="border-slate-200 shadow-xs">
            <CardContent className="p-4 flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center">
                <Calendar className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xs text-slate-500">Committee templates</p>
                <p className="text-xl font-bold text-slate-900">{stats.committee}</p>
              </div>
            </CardContent>
          </Card>
        </div>

        <Card className="border-slate-200 shadow-xs rounded-xl overflow-hidden">
          <CardHeader className="border-b border-slate-100 bg-slate-50/50">
            <CardTitle className="text-base font-bold text-slate-900">Stored templates</CardTitle>
            <CardDescription className="text-xs">
              {filteredTemplates.length} of {templates.length} template{templates.length === 1 ? '' : 's'} shown
            </CardDescription>
          </CardHeader>
          <CardContent className="p-4 space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div className="relative md:col-span-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                <Input
                  placeholder="Search by name, company, or type…"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9 h-10"
                />
              </div>
              <Select value={categoryFilter} onValueChange={setCategoryFilter}>
                <SelectTrigger className="h-10">
                  <SelectValue placeholder="All categories" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All categories</SelectItem>
                  {categoryOptions.map((c) => (
                    <SelectItem key={c} value={c}>
                      {c}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={companyFilter} onValueChange={setCompanyFilter}>
                <SelectTrigger className="h-10">
                  <SelectValue placeholder="All companies" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All companies</SelectItem>
                  {companyOptions.map((c) => (
                    <SelectItem key={c} value={c}>
                      {c}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="rounded-lg border border-slate-200 overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow className="bg-slate-50/80 hover:bg-slate-50/80">
                    <TableHead className="text-xs font-bold uppercase tracking-wide">Template</TableHead>
                    <TableHead className="text-xs font-bold uppercase tracking-wide">Company</TableHead>
                    <TableHead className="text-xs font-bold uppercase tracking-wide">Type</TableHead>
                    <TableHead className="text-xs font-bold uppercase tracking-wide">Size</TableHead>
                    <TableHead className="text-xs font-bold uppercase tracking-wide">Added</TableHead>
                    <TableHead className="text-xs font-bold uppercase tracking-wide text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {loading ? (
                    <TableRow>
                      <TableCell colSpan={6} className="py-12 text-center text-sm text-slate-500">
                        Loading template library…
                      </TableCell>
                    </TableRow>
                  ) : filteredTemplates.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={6} className="py-12 text-center">
                        <FileText className="h-8 w-8 text-slate-300 mx-auto mb-2" />
                        <p className="text-sm text-slate-500">No templates match your filters.</p>
                      </TableCell>
                    </TableRow>
                  ) : (
                    filteredTemplates.map((template) => (
                      <TableRow key={template.id || template.name} className="hover:bg-slate-50/60">
                        <TableCell className="align-top py-3">
                          <div className="font-semibold text-sm text-slate-900">{template.displayTitle}</div>
                          <div className="text-[11px] text-slate-400 font-mono mt-0.5 truncate max-w-[280px]" title={template.name}>
                            {template.name}
                          </div>
                        </TableCell>
                        <TableCell className="align-top py-3 text-xs text-slate-700 max-w-[200px]">
                          <span className="line-clamp-2">{template.displayCompany}</span>
                        </TableCell>
                        <TableCell className="align-top py-3">
                          <Badge variant="outline" className={`text-[10px] font-semibold ${categoryBadgeClass(template.displayCategory || '')}`}>
                            {template.displayCategory}
                          </Badge>
                        </TableCell>
                        <TableCell className="align-top py-3 text-xs text-slate-600 font-mono">
                          {formatBytes(template.size)}
                        </TableCell>
                        <TableCell className="align-top py-3 text-xs text-slate-600">
                          {formatDate(template.lastModified)}
                        </TableCell>
                        <TableCell className="align-top py-3 text-right">
                          <Button
                            variant="outline"
                            size="sm"
                            className="h-8 text-xs"
                            onClick={() => handleDownload(template.name)}
                          >
                            <Download className="h-3.5 w-3.5 mr-1.5" />
                            Download
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>

            <div
              className="relative border border-dashed border-slate-200 rounded-xl p-8 text-center bg-slate-50/50 hover:bg-slate-50 transition-colors"
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => {
                e.preventDefault();
                void handleUpload(e.dataTransfer.files?.[0]);
              }}
            >
              <input
                type="file"
                accept=".docx"
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                onChange={(e) => void handleUpload(e.target.files?.[0])}
                disabled={uploading}
              />
              <div className="flex flex-col items-center gap-2 pointer-events-none">
                <div className="w-10 h-10 rounded-lg bg-white border border-slate-200 flex items-center justify-center">
                  <Upload className="h-5 w-5 text-slate-500" />
                </div>
                <h3 className="font-semibold text-slate-800 text-sm">Upload a meeting template</h3>
                <p className="text-xs text-slate-500">Drag and drop a .docx file here, or click to browse</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </ProductDashboardLayout>
  );
};

export default Templates;
