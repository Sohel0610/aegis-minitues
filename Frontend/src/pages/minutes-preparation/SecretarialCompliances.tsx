
import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Home, FileText, FileSpreadsheet, History, Sparkles, CheckCircle2, AlertCircle, Clock, BookOpen, Users, Plus, MessageSquare } from 'lucide-react';
import ProductDashboardLayout from '@/components/layout/ProductDashboardLayout';

const SecretarialCompliances = () => {
    const navigationItems = [
        { id: 'home', label: 'Home', icon: Home, href: '/' },
        { id: 'dashboard', label: 'Generate Minutes', icon: FileText, href: '/minutes-preparation' },
        { id: 'create-agenda', label: 'Create Agenda', icon: Plus, href: '/minutes-preparation/create-agenda' },
        { id: 'compliances', label: 'Secretarial Compliances', icon: FileSpreadsheet, href: '/minutes-preparation/compliances', isActive: true },
        { id: 'ai-mom', label: 'AI MOM', icon: FileText, href: '/minutes-preparation/ai-assistant' },
        { id: 'chatbot', label: 'Meeting Assistant', icon: MessageSquare, href: '/minutes-preparation/chatbot' },
        { id: 'template-resolution', label: 'Template Resolution', icon: History, href: '/minutes-preparation/template-resolution' },
        { id: 'minutes', label: 'Meeting Minutes', icon: FileText, href: '/minutes-preparation/minutes' },
        { id: 'templates', label: 'Templates', icon: FileSpreadsheet, href: '/minutes-preparation/templates' },
        { id: 'directors', label: 'Directors', icon: Users, href: '/minutes-preparation/directors' },
        { id: 'manual', label: 'User Manual', icon: BookOpen, href: '#' }
    ];

    const [compliances, setCompliances] = React.useState<any[]>([]);
    const [loading, setLoading] = React.useState(true);

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

    React.useEffect(() => {
        fetchCompliances();
    }, []);

    const stats = {
        completed: compliances.filter(c => c.status === 'Completed').length,
        upcoming: compliances.filter(c => c.status !== 'Completed' && c.status !== 'Overdue').length,
        overdue: compliances.filter(c => c.status === 'Overdue' || c.status === 'Urgent').length
    };


    return (
        <ProductDashboardLayout productName="Generate Minutes" productRoute="/minutes-preparation" navigationItems={navigationItems}>
            <div className="container mx-auto py-6">
                <div className="space-y-8">
                    <div>
                        <h1 className="text-3xl font-bold">Secretarial Compliances</h1>
                        <p className="text-muted-foreground">Monitor and manage statutory filings and compliance calendar</p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <Card className="bg-green-50/50 border-green-200">
                            <CardHeader className="pb-2">
                                <CardTitle className="text-lg flex items-center gap-2">
                                    <CheckCircle2 className="h-5 w-5 text-green-600" />
                                    Completed
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <p className="text-3xl font-bold">{stats.completed}</p>
                                <p className="text-xs text-muted-foreground">Filings this year</p>
                            </CardContent>
                        </Card>
                        <Card className="bg-amber-50/50 border-amber-200">
                            <CardHeader className="pb-2">
                                <CardTitle className="text-lg flex items-center gap-2">
                                    <Clock className="h-5 w-5 text-amber-600" />
                                    Upcoming
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <p className="text-3xl font-bold">{stats.upcoming}</p>
                                <p className="text-xs text-muted-foreground">Due in next 30 days</p>
                            </CardContent>
                        </Card>
                        <Card className="bg-red-50/50 border-red-200">
                            <CardHeader className="pb-2">
                                <CardTitle className="text-lg flex items-center gap-2">
                                    <AlertCircle className="h-5 w-5 text-red-600" />
                                    Overdue / Urgent
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <p className="text-3xl font-bold text-red-600">{stats.overdue}</p>
                                <p className="text-xs text-muted-foreground">Requires immediate action</p>
                            </CardContent>
                        </Card>
                    </div>

                    <Card>
                        <CardHeader>
                            <CardTitle>Compliance Calendar</CardTitle>
                            <CardDescription>Upcoming statutory requirements and filings</CardDescription>
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
                                    {loading && (
                                        <TableRow>
                                            <TableCell colSpan={5} className="text-center py-8">
                                                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
                                                <p className="mt-2 text-sm text-muted-foreground">Loading compliances...</p>
                                            </TableCell>
                                        </TableRow>
                                    )}
                                    {!loading && compliances.length === 0 && (
                                        <TableRow>
                                            <TableCell colSpan={5} className="text-center py-8 text-muted-foreground">
                                                No compliance records found.
                                            </TableCell>
                                        </TableRow>
                                    )}
                                    {compliances.map((c) => (
                                        <TableRow key={c.id}>
                                            <TableCell className="font-bold">{c.form}</TableCell>
                                            <TableCell>{c.description}</TableCell>
                                            <TableCell>{c.due_date}</TableCell>
                                            <TableCell>
                                                <Badge variant={c.priority === 'Critical' ? 'destructive' : c.priority === 'High' ? 'default' : 'secondary'}>
                                                    {c.priority}
                                                </Badge>
                                            </TableCell>
                                            <TableCell>
                                                <Badge
                                                    className={
                                                        c.status === 'Completed' ? 'bg-green-100 text-green-800' :
                                                            c.status === 'Urgent' ? 'bg-red-100 text-red-800' :
                                                                'bg-blue-100 text-blue-800'
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
