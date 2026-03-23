import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { FileText, Upload, Download, Plus, Edit, Trash, Eye, Home, FileSpreadsheet, History, BookOpen, Users } from 'lucide-react';
import ProductDashboardLayout from '@/components/layout/ProductDashboardLayout';
import { Link } from 'react-router-dom';

const Templates = () => {
  // Define navigation items for this product
  const navigationItems = [
    { id: 'home', label: 'Home', icon: Home, href: '/' },
    { id: 'dashboard', label: 'Generate Minutes', icon: FileText, href: '/minutes-preparation' },
    { id: 'create-agenda', label: 'Create Agenda', icon: Plus, href: '/minutes-preparation/create-agenda' },
    { id: 'compliances', label: 'Secretarial Compliances', icon: FileText, href: '/minutes-preparation/compliances' },
    { id: 'ai-mom', label: 'AI MOM', icon: FileText, href: '/minutes-preparation/ai-assistant' },
    { id: 'template-resolution', label: 'Template Resolution', icon: History, href: '/minutes-preparation/template-resolution' },
    { id: 'minutes', label: 'Meeting Minutes', icon: FileText, href: '/minutes-preparation/minutes' },
    { id: 'templates', label: 'Templates', icon: FileSpreadsheet, href: '/minutes-preparation/templates', isActive: true },
    { id: 'directors', label: 'Directors', icon: Users, href: '/minutes-preparation/directors' },
    { id: 'manual', label: 'User Manual', icon: BookOpen, href: '#' }
  ];

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
      <div className="container mx-auto py-6">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4">
          <div>
            <h1 className="text-3xl font-bold">Template Management</h1>
            <p className="text-muted-foreground">Manage meeting minutes templates</p>
          </div>
          <div className="flex gap-2">
            <Link to="/minutes-preparation/renderer">
              <Button variant="outline" className="flex items-center gap-2">
                <Eye className="h-4 w-4" />
                Template Renderer
              </Button>
            </Link>
            <Button className="flex items-center gap-2">
              <Plus className="h-4 w-4" />
              Add New Template
            </Button>
          </div>
        </div>

        <Card className="max-w-5xl mx-auto border-none shadow-xl bg-white/80 backdrop-blur-sm">
          <CardHeader className="pb-4">
            <CardTitle className="text-2xl flex items-center gap-3">
              <div className="bg-primary/10 p-2 rounded-lg text-primary">
                <FileSpreadsheet className="h-6 w-6" />
              </div>
              Available Templates
            </CardTitle>
            <CardDescription className="text-base">
              Manage and customize your meeting minutes DOCX templates
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {templates.length === 0 && !loading && (
                <div className="text-center py-12 bg-slate-50 rounded-2xl border border-dashed border-slate-200">
                  <FileText className="h-12 w-12 text-slate-300 mx-auto mb-3" />
                  <p className="text-slate-500 font-medium">No templates found in the system.</p>
                </div>
              )}
              {loading && (
                <div className="text-center py-12">
                  <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary mx-auto"></div>
                  <p className="mt-4 text-slate-500 font-medium">Loading templates repository...</p>
                </div>
              )}
              {templates.map((template, idx) => (
                <div
                  key={idx}
                  className="group flex flex-col md:flex-row items-start md:items-center justify-between p-6 border rounded-2xl hover:bg-slate-50 transition-all duration-300 gap-6 shadow-sm hover:shadow-md border-slate-100"
                >
                  <div className="flex items-center gap-6 flex-1">
                    <div className="hidden sm:flex bg-blue-600/10 p-4 rounded-xl group-hover:bg-blue-600 group-hover:text-white transition-all duration-500 shadow-inner">
                      <FileText className="h-8 w-8 text-blue-600 group-hover:text-white transition-colors" />
                    </div>
                    <div className="space-y-2">
                      <h3 className="font-bold text-xl text-slate-900 group-hover:text-primary transition-colors">{template.name}</h3>
                      <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-slate-500">
                        <div className="flex items-center gap-2 bg-slate-100 px-3 py-1 rounded-full font-medium">
                          <History className="h-4 w-4 text-slate-400" />
                          {template.lastModified}
                        </div>
                        <div className="flex items-center gap-2 bg-slate-100 px-3 py-1 rounded-full font-medium">
                          <FileSpreadsheet className="h-4 w-4 text-slate-400" />
                          {(template.size / 1024).toFixed(1)} KB
                        </div>
                        <div className="flex items-center gap-2 bg-blue-50 text-blue-600 px-3 py-1 rounded-full font-semibold text-xs border border-blue-100 uppercase tracking-wider">
                          DOCX
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 w-full md:w-auto pt-4 md:pt-0 border-t md:border-t-0 border-slate-100">
                    <Button
                      variant="outline"
                      size="sm"
                      className="flex-1 sm:flex-none h-10 px-6 rounded-xl border-slate-200 bg-white hover:bg-slate-50 hover:text-primary transition-all font-semibold"
                      onClick={() => handleDownload(template.name)}
                    >
                      <Download className="h-4 w-4 mr-2" />
                      Download
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-10 px-4 rounded-xl text-red-500 hover:text-white hover:bg-red-500 transition-all"
                      onClick={() => handleDelete(template.name)}
                    >
                      <Trash className="h-4 w-4 mr-2" />
                      Delete
                    </Button>
                  </div>
                </div>
              ))}
            </div>

            <div
              className="mt-8 relative border-2 border-dashed rounded-xl p-8 transition-all duration-200 text-center border-blue-200 bg-blue-50/30 hover:bg-blue-50/50"
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
                    } else {
                      alert('Upload failed');
                    }
                  } catch (err) {
                    console.error('Upload error', err);
                  }
                }}
              />
              <div className="flex flex-col items-center gap-2">
                <div className="bg-blue-100 p-3 rounded-full">
                  <Upload className="h-6 w-6 text-blue-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">Upload New Template</h3>
                  <p className="text-sm text-gray-500">
                    Drag and drop a .docx file here or click to browse
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </ProductDashboardLayout>
  );
};

export default Templates;