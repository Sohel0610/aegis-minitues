import React, { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { CheckCircle2, AlertCircle, Clock, Filter, Download } from 'lucide-react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import ProductDashboardLayout from '@/components/layout/ProductDashboardLayout';
import { getMinutesNavItems } from '@/constants/minutesNavigation';
import { useVertical } from '@/contexts/VerticalContext';

const SecretarialCompliances = () => {
    const navigationItems = getMinutesNavItems('compliances');
    const { selectedVertical: ctxVertical } = useVertical();

    const [compliances, setCompliances] = useState<any[]>([]);
    const [verticals, setVerticals] = useState<any[]>([]);
    const [selectedVertical, setSelectedVertical] = useState<string>('all');
    const [loading, setLoading] = useState(true);
    const [apiKpis, setApiKpis] = useState<any>(null);

    const fetchCompliances = async () => {
        try {
            const res = await fetch('/api/compliances');
            if (res.ok) {
                const data = await res.json();
                setCompliances(data.data || []);
            }
        } catch (err) {
            console.error("Failed to fetch compliances", err);
        } finally {
            setLoading(false);
        }
    };

    const fetchKPIs = async () => {
        try {
            const res = await fetch('/api/compliances/kpis');
            if (res.ok) {
                const data = await res.json();
                setApiKpis(data);
            }
        } catch (err) {
            console.error("Failed to fetch KPIs from API", err);
        }
    };

    const fetchVerticals = async () => {
        try {
            const res = await fetch('/api/verticals');
            if (res.ok) {
                const data = await res.json();
                setVerticals(data.data || []);
            }
        } catch (err) {
            console.error("Failed to fetch verticals", err);
        }
    };

    useEffect(() => {
        fetchCompliances();
        fetchKPIs();
        fetchVerticals();
    }, []);

    // Set initial selected vertical from context if available
    useEffect(() => {
        if (ctxVertical && ctxVertical.name) {
            setSelectedVertical(ctxVertical.name);
        }
    }, [ctxVertical]);

    // Filter compliances dynamically based on the selected Business Unit
    const filteredCompliances = useMemo(() => {
        if (selectedVertical === 'all') return compliances;
        return compliances.filter(c => c.vertical_name === selectedVertical);
    }, [compliances, selectedVertical]);

    // Recalculate metrics reactively
    const stats = useMemo(() => {
        if (selectedVertical === 'all' && apiKpis) {
            return {
                completed: apiKpis.completed || 0,
                upcoming: apiKpis.pending || 0,
                overdue: apiKpis.critical || 0
            };
        }
        return {
            completed: filteredCompliances.filter(c => c.status === 'Completed').length,
            upcoming: filteredCompliances.filter(c => c.status !== 'Completed' && c.status !== 'Overdue').length,
            overdue: filteredCompliances.filter(c => c.status === 'Overdue' || c.status === 'Urgent').length
        };
    }, [filteredCompliances, selectedVertical, apiKpis]);

    const handleExportAttendance = () => {
        window.open('/api/reports/attendance/export', '_blank');
    };

    return (
        <ProductDashboardLayout productName="Generate Minutes" productRoute="/minutes-preparation" navigationItems={navigationItems}>
            <div className="container mx-auto py-6">
                <div className="space-y-8">
                    {/* Header with Business Unit Scoping Filter and Attendance Export */}
                    <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                        <div>
                            <h1 className="text-3xl font-bold text-slate-900">Secretarial Compliances</h1>
                            <p className="text-muted-foreground">Monitor statutory filings and compliance calendars for Adani Business Units</p>
                        </div>
                        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
                            <Button 
                                variant="outline"
                                onClick={handleExportAttendance}
                                className="bg-white border-slate-200 text-slate-700 font-semibold text-xs h-10 shadow-xs hover:bg-slate-50"
                            >
                                <Download className="h-4 w-4 mr-2 text-blue-600" />
                                Export Attendance Report
                            </Button>
                            <div className="flex items-center gap-2 bg-white p-1.5 border border-slate-200 rounded-xl shadow-xs w-full md:w-auto">
                                <Filter className="h-4 w-4 text-slate-400 shrink-0 ml-1" />
                                <Select value={selectedVertical} onValueChange={setSelectedVertical}>
                                    <SelectTrigger className="w-full md:w-52 bg-white border-none shadow-none focus:ring-0 text-xs font-medium">
                                        <SelectValue placeholder="All Business Units" />
                                    </SelectTrigger>
                                    <SelectContent className="bg-white">
                                        <SelectItem value="all">All Business Units (BUs)</SelectItem>
                                        {verticals.map(v => (
                                            <SelectItem key={v.id} value={v.name}>{v.name}</SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>
                        </div>
                    </div>

                    {/* KPI Metric Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <Card className="bg-green-50/50 border-green-200">
                            <CardHeader className="pb-2">
                                <CardTitle className="text-lg flex items-center gap-2 text-green-800">
                                    <CheckCircle2 className="h-5 w-5 text-green-600" />
                                    Completed
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <p className="text-3xl font-bold text-green-700">{stats.completed}</p>
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
                                <p className="text-3xl font-bold text-amber-700">{stats.upcoming}</p>
                                <p className="text-xs text-muted-foreground">Due within the next 30 days</p>
                            </CardContent>
                        </Card>
                        <Card className="bg-red-50/50 border-red-200">
                            <CardHeader className="pb-2">
                                <CardTitle className="text-lg flex items-center gap-2 text-red-800">
                                    <AlertCircle className="h-5 w-5 text-red-600" />
                                    Overdue / Urgent
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <p className="text-3xl font-bold text-red-700">{stats.overdue}</p>
                                <p className="text-xs text-muted-foreground">Requires immediate attention</p>
                            </CardContent>
                        </Card>
                    </div>

                    {/* Table View */}
                    <Card className="border border-slate-100 shadow-sm bg-white">
                        <CardHeader>
                            <CardTitle>Compliance Calendar</CardTitle>
                            <CardDescription>
                                {selectedVertical === 'all' 
                                    ? 'Showing statutory requirements across all Business Units'
                                    : `Showing statutory requirements for Business Unit: ${selectedVertical}`}
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>Form/Requirement</TableHead>
                                        <TableHead>Company</TableHead>
                                        <TableHead>Description</TableHead>
                                        <TableHead>Due Date</TableHead>
                                        <TableHead>Priority</TableHead>
                                        <TableHead>Status</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {loading && (
                                        <TableRow>
                                            <TableCell colSpan={6} className="text-center py-8">
                                                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
                                                <p className="mt-2 text-sm text-muted-foreground">Loading compliances...</p>
                                            </TableCell>
                                        </TableRow>
                                    )}
                                    {!loading && filteredCompliances.length === 0 && (
                                        <TableRow>
                                            <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                                                No compliance records found for this selection.
                                            </TableCell>
                                        </TableRow>
                                    )}
                                    {filteredCompliances.map((c) => (
                                        <TableRow key={c.id}>
                                            <TableCell className="font-bold text-slate-800">{c.form}</TableCell>
                                            <TableCell className="text-slate-600 text-sm font-medium">{c.company_name || 'N/A'}</TableCell>
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
                                    ))}
                                </TableBody>
                            </Table>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </ProductDashboardLayout>
    );
};

export default SecretarialCompliances;
