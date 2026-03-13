import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Home, FileText, Plus, FileSpreadsheet, History, BookOpen, Clock, Calendar, Download, Trash, Eye, Search, Users, Filter } from 'lucide-react';
import ProductDashboardLayout from '@/components/layout/ProductDashboardLayout';

const MeetingMinutes = () => {
  // Define navigation items for this product
  const navigationItems = [
    { id: 'home', label: 'Home', icon: Home, href: '/' },
    { id: 'dashboard', label: 'Generate Minutes', icon: FileText, href: '/minutes-preparation' },
    { id: 'create-agenda', label: 'Create Agenda', icon: FileText, href: '/minutes-preparation/create-agenda' },
    { id: 'compliances', label: 'Secretarial Compliances', icon: FileText, href: '/minutes-preparation/compliances' },
    { id: 'ai-mom', label: 'AI MOM', icon: FileText, href: '/minutes-preparation/ai-assistant' },
    { id: 'template-resolution', label: 'Template Resolution', icon: History, href: '/minutes-preparation/template-resolution' },
    { id: 'minutes', label: 'Meeting Minutes', icon: FileText, href: '/minutes-preparation/minutes', isActive: true },
    { id: 'templates', label: 'Templates', icon: FileSpreadsheet, href: '/minutes-preparation/templates' },
    { id: 'directors', label: 'Directors', icon: Users, href: '/minutes-preparation/directors' },
    { id: 'manual', label: 'User Manual', icon: BookOpen, href: '#' }
  ];

  const [meetingMinutes, setMeetingMinutes] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
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
    fetchHistory();
  }, []);

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


  return (
    <ProductDashboardLayout
      productName="Generate Minutes"
      productRoute="/minutes-preparation"
      navigationItems={navigationItems}
    >
      <div className="container mx-auto py-6">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4">
          <div>
            <h1 className="text-3xl font-bold">Meeting Minutes</h1>
            <p className="text-muted-foreground">View and manage meeting minutes</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" className="flex items-center gap-2">
              <Filter className="h-4 w-4" />
              Filter
            </Button>
            <Button variant="outline" className="flex items-center gap-2">
              <Search className="h-4 w-4" />
              Search
            </Button>
          </div>
        </div>

        <Card className="max-w-5xl mx-auto border-none shadow-xl bg-white/80 backdrop-blur-sm">
          <CardHeader className="pb-4">
            <CardTitle className="text-2xl flex items-center gap-3">
              <div className="bg-primary/10 p-2 rounded-lg text-primary">
                <FileText className="h-6 w-6" />
              </div>
              Generated Minutes
            </CardTitle>
            <CardDescription className="text-base">
              Manage and access all meeting minutes generated using the Project AEGIS system
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {meetingMinutes.map((minute) => (
                <div
                  key={minute.id}
                  className="group flex flex-col md:flex-row items-start md:items-center justify-between p-6 border rounded-2xl hover:bg-slate-50 transition-all duration-300 gap-6 shadow-sm hover:shadow-md border-slate-100"
                >
                  <div className="flex items-center gap-6 flex-1">
                    <div className="hidden sm:flex bg-blue-600/10 p-4 rounded-xl group-hover:bg-blue-600 group-hover:text-white transition-all duration-500 shadow-inner">
                      <FileText className="h-8 w-8 text-blue-600 group-hover:text-white transition-colors" />
                    </div>
                    <div className="space-y-2">
                      <h3 className="font-bold text-xl text-slate-900 group-hover:text-primary transition-colors">{minute.company_name}</h3>
                      <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-slate-500">
                        <div className="flex items-center gap-2 bg-slate-100 px-3 py-1 rounded-full font-medium">
                          <Calendar className="h-3.5 w-3.5 text-slate-400" />
                          {minute.meeting_date}
                        </div>
                        <div className="flex items-center gap-2 bg-slate-100 px-3 py-1 rounded-full font-medium">
                          <FileSpreadsheet className="h-3.5 w-3.5 text-slate-400" />
                          {minute.meeting_type}
                        </div>
                        <div className="flex items-center gap-2 bg-blue-50 text-blue-600 px-3 py-1 rounded-full font-medium text-xs">
                          <Clock className="h-3.5 w-3.5 mr-1" />
                          {new Date(minute.created_at).toLocaleDateString()}
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="flex flex-col sm:flex-row items-center gap-4 w-full md:w-auto pt-4 md:pt-0 border-t md:border-t-0 border-slate-100">
                    <span className="px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider bg-green-100 text-green-700 border border-green-200">
                      Generated
                    </span>
                    <div className="flex items-center gap-2 w-full sm:w-auto">
                      <Button
                        variant="outline"
                        size="sm"
                        className="flex-1 sm:flex-none h-10 px-4 rounded-xl border-slate-200 bg-white hover:bg-slate-50 hover:text-primary transition-all"
                        onClick={() => {
                          const link = document.createElement('a');
                          link.href = minute.download_url;
                          link.download = minute.file_path;
                          document.body.appendChild(link);
                          link.click();
                          document.body.removeChild(link);
                        }}
                      >
                        <Download className="h-4 w-4 mr-2" /> Download
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-10 px-4 rounded-xl text-red-500 hover:text-white hover:bg-red-500 transition-all"
                        onClick={() => handleDelete(minute.id)}
                      >
                        <Trash className="h-4 w-4 mr-2" /> Delete
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
              {!loading && meetingMinutes.length === 0 && (
                <div className="text-center py-12 bg-slate-50 rounded-2xl border border-dashed border-slate-200">
                  <FileText className="h-12 w-12 text-slate-300 mx-auto mb-3" />
                  <p className="text-slate-500 font-medium">No meeting minutes found in your history.</p>
                </div>
              )}
              {loading && (
                <div className="text-center py-12">
                  <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary mx-auto"></div>
                  <p className="mt-4 text-slate-500 font-medium">Loading history...</p>
                </div>
              )}
            </div>

            <div className="mt-10 flex flex-col sm:flex-row justify-between items-center bg-slate-50 p-4 rounded-2xl gap-4">
              <p className="text-sm font-medium text-slate-500">
                Showing <span className="text-slate-900 font-bold">{meetingMinutes.length}</span> of <span className="text-slate-900 font-bold">{meetingMinutes.length}</span> meeting minutes
              </p>
              <div className="flex gap-3">
                <Button variant="outline" size="sm" disabled className="h-10 px-6 rounded-xl border-slate-200 bg-white shadow-sm">
                  Previous
                </Button>
                <Button variant="outline" size="sm" className="h-10 px-6 rounded-xl border-slate-200 bg-white shadow-sm hover:bg-primary hover:text-white transition-all">
                  Next
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </ProductDashboardLayout>
  );
};

export default MeetingMinutes;