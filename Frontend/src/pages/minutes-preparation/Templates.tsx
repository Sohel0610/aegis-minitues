/* eslint-disable @typescript-eslint/no-explicit-any */
import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { FileText, Upload, Download, Plus, Trash, Eye, FileSpreadsheet, History } from 'lucide-react';
import ProductDashboardLayout from '@/components/layout/ProductDashboardLayout';
import { Link } from 'react-router-dom';
import { getMinutesNavItems } from '@/constants/minutesNavigation';
import { useToast } from "@/components/ui/use-toast";

const Templates = () => {
  const navigationItems = getMinutesNavItems('templates');
  const { toast } = useToast();

  const [templates, setTemplates] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(true);

  const fetchTemplates = async () => {
    try {
      const res = await fetch('/api/templates');
      if (res.ok) {
        const data = await res.json();
        setTemplates(data.data || []);
      }
    } catch (err) {
      console.error("Failed to fetch templates", err);
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    fetchTemplates();
  }, []);

  const handleDownload = (filename: string) => {
    const link = document.createElement('a');
    link.href = `/api/templates/download/${filename}`;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleDelete = async (filename: string) => {
    if (!confirm(`Are you sure you want to delete ${filename}?`)) return;

    try {
      const res = await fetch(`/api/templates/${filename}`, {
        method: 'DELETE'
      });
      if (res.ok) {
        fetchTemplates();
      }
    } catch (err) {
      console.error("Failed to delete template", err);
    }
  };

  return (
    <ProductDashboardLayout
      productName="Generate Minutes"
      productRoute="/minutes-preparation"
      navigationItems={navigationItems}
    >
      <div className="p-6">
        <div className="border border-slate-200 rounded-xl bg-white shadow-xs p-6 space-y-6">
          <div className="pb-4 border-b border-slate-100 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div>
              <h1 className="text-xl font-bold text-slate-900">Template Management</h1>
              <p className="text-xs text-slate-500 mt-1">Manage and configure meeting minutes templates.</p>
            </div>
            <div className="flex gap-2">
              <Link to="/minutes-preparation/renderer">
                <Button variant="outline" className="flex items-center gap-2 text-xs font-semibold rounded-lg border-slate-200 h-9 bg-white">
                  <Eye className="h-4 w-4 text-slate-500" />
                  Template Renderer
                </Button>
              </Link>
              <Button 
                className="flex items-center gap-2 bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs rounded-lg h-9"
                onClick={() => document.getElementById('add-template-input')?.click()}
              >
                <Plus className="h-4 w-4" />
                Add New Template
              </Button>
              <input
                id="add-template-input"
                type="file"
                accept=".docx"
                className="hidden"
                onChange={async (e) => {
                  const file = e.target.files?.[0];
                  if (!file) return;

                  const formData = new FormData();
                  formData.append('file', file);

                  try {
                    const res = await fetch('/api/upload-template', {
                      method: 'POST',
                      body: formData
                    });
                    if (res.ok) {
                      fetchTemplates();
                      toast({ title: "Success", description: "Template added successfully." });
                    } else {
                      toast({ title: "Error", description: "Upload failed", variant: "destructive" });
                    }
                  } catch (err) {
                    console.error('Upload error', err);
                  }
                }}
              />
            </div>
          </div>

          <Card className="w-full border border-slate-200 shadow-none bg-white rounded-xl overflow-hidden">
            <CardHeader className="bg-slate-50/50 border-b border-slate-100 pb-4">
              <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-2">
                <FileSpreadsheet className="h-4 w-4 text-slate-400" />
                Available Templates
              </CardTitle>
              <CardDescription className="text-xs text-slate-500 mt-1">
                Manage and customize your meeting minutes DOCX templates
              </CardDescription>
            </CardHeader>
            <CardContent className="p-6">
              <div 
                className="space-y-3 max-h-[500px] overflow-y-auto pr-1 scroll-smooth"
              >
                {templates.length === 0 && !loading && (
                  <div className="text-center py-10">
                    <FileText className="h-8 w-8 text-slate-300 mx-auto mb-2" />
                    <p className="text-slate-400 text-xs font-medium">No templates found in the system.</p>
                  </div>
                )}
                {loading && (
                  <div className="text-center py-10">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-slate-600 mx-auto"></div>
                    <p className="mt-2 text-slate-500 text-xs font-medium">Loading templates repository...</p>
                  </div>
                )}
                {templates.map((template, idx) => (
                  <div
                    key={idx}
                    className="group flex flex-col md:flex-row items-start md:items-center justify-between p-3.5 border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors gap-4"
                  >
                    <div className="flex items-center gap-3.5 flex-1 min-w-0 w-full">
                      <div className="bg-blue-50 border border-blue-200/60 p-2.5 rounded-lg text-blue-600 shrink-0">
                        <FileText className="h-5 w-5" />
                      </div>
                      <div className="space-y-1 min-w-0 flex-1">
                        {(() => {
                          const rawName = template.name || '';
                          let companyPrefix = 'Adani Group';
                          if (rawName.startsWith('AGEL')) companyPrefix = 'AGEL';
                          else if (rawName.startsWith('AGE(UP)L')) companyPrefix = 'AGE(UP)L';
                          else if (rawName.includes('AGE25BL')) companyPrefix = 'AGE25BL';

                          let category = 'Board Meeting';
                          if (rawName.includes('- AC -') || rawName.toLowerCase().includes('audit')) category = 'Audit Committee';
                          else if (rawName.toLowerCase().includes('agm')) category = 'AGM';

                          let quarterTag = '';
                          if (rawName.includes('28.04') || rawName.includes('Q1')) quarterTag = ' (Q1 Focus)';
                          else if (rawName.includes('28.07') || rawName.includes('Q2')) quarterTag = ' (Q2 Focus)';
                          else if (rawName.includes('28.10') || rawName.includes('Q3')) quarterTag = ' (Q3 Focus)';
                          else if (rawName.includes('23.01') || rawName.includes('Q4')) quarterTag = ' (Q4 Annual Focus)';

                          const cleanTitle = `${companyPrefix} — ${category}${quarterTag}`;

                          return (
                            <>
                              <div className="flex items-center gap-2">
                                <h3 className="font-bold text-sm text-slate-900 truncate" title={rawName}>
                                  {cleanTitle}
                                </h3>
                                <span className="bg-blue-50 text-blue-700 border border-blue-200/60 px-2 py-0.5 rounded text-[10px] font-semibold">
                                  {category}
                                </span>
                              </div>
                              <div className="text-[11px] text-slate-400 font-mono truncate">{rawName}</div>
                            </>
                          );
                        })()}
                        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-500 pt-1">
                          <div className="flex items-center gap-1.5 font-mono text-[10px]">
                            <History className="h-3.5 w-3.5 text-slate-400" />
                            {template.lastModified}
                          </div>
                          <div className="flex items-center gap-1.5 font-mono text-[10px]">
                            <FileSpreadsheet className="h-3.5 w-3.5 text-slate-400" />
                            {(template.size / 1024).toFixed(1)} KB
                          </div>
                          <span className="bg-slate-100 text-slate-700 px-2 py-0.5 rounded-md font-medium text-[9px] uppercase tracking-wider">
                            DOCX
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 w-full md:w-auto pt-3 md:pt-0 border-t md:border-t-0 border-slate-100 justify-end">
                      <Button
                        variant="outline"
                        size="sm"
                        className="flex-1 sm:flex-none h-8 px-3 rounded-lg border-slate-200 text-slate-700 font-semibold text-xs bg-white hover:bg-slate-50"
                        onClick={() => handleDownload(template.name)}
                      >
                        <Download className="h-3.5 w-3.5 mr-1.5 text-slate-500" />
                        Download
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-8 px-3 rounded-lg text-slate-400 hover:text-red-700 hover:bg-red-50 text-xs font-semibold"
                        onClick={() => handleDelete(template.name)}
                      >
                        <Trash className="h-3.5 w-3.5 mr-1.5" />
                        Delete
                      </Button>
                    </div>
                  </div>
                ))}
              </div>

              <div
                className="mt-6 relative border border-dashed border-slate-200 rounded-xl p-8 text-center bg-slate-50/50 hover:bg-slate-50 transition-colors"
              >
                <input
                  type="file"
                  accept=".docx"
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                  onChange={async (e) => {
                    const file = e.target.files?.[0];
                    if (!file) return;

                    const formData = new FormData();
                    formData.append('file', file);

                    try {
                      const res = await fetch('/api/upload-template', {
                        method: 'POST',
                        body: formData
                      });
                      if (res.ok) {
                        fetchTemplates();
                        toast({ title: "Success", description: "Template uploaded successfully." });
                      } else {
                        toast({ title: "Error", description: "Upload failed", variant: "destructive" });
                      }
                    } catch (err) {
                      console.error('Upload error', err);
                    }
                  }}
                />
                <div className="flex flex-col items-center gap-2">
                  <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center mb-2">
                    <Upload className="h-5 w-5 text-slate-500" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-slate-800 text-sm mb-0.5">Upload New Template</h3>
                    <p className="text-xs text-slate-500">
                      Drag and drop a .docx file here or click to browse
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </ProductDashboardLayout>
  );
};

export default Templates;