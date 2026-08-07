import React, { useState, useEffect, useMemo } from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Plus, Trash2, Search } from 'lucide-react';
import ProductDashboardLayout from '@/components/layout/ProductDashboardLayout';
import { useToast } from "@/components/ui/use-toast";
import { getMinutesNavItems } from '@/constants/minutesNavigation';

interface ResolutionTemplate {
    id: number;
    template_name: string;
    resolution_text: string;
    created_at: string;
}

const TemplateResolution = () => {
    const [templates, setTemplates] = useState<ResolutionTemplate[]>([]);
    const [newName, setNewName] = useState('');
    const [newText, setNewText] = useState('');
    const [searchTerm, setSearchTerm] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const { toast } = useToast();

    const navigationItems = getMinutesNavItems('template-resolution');

    const fetchTemplates = async () => {
        try {
            const res = await fetch('/api/resolutions');
            if (res.ok) {
                const data = await res.json();
                setTemplates(data.data || []);
            }
        } catch (err) {
            console.error("Failed to fetch templates", err);
        }
    };

    useEffect(() => {
        fetchTemplates();
    }, []);

    const handleAddTemplate = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newName.trim() || !newText.trim()) return;

        setIsLoading(true);
        try {
            const res = await fetch('/api/resolutions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    template_name: newName,
                    resolution_text: newText
                })
            });

            if (res.ok) {
                toast({
                    title: "Template Saved",
                    description: "Resolution template has been added successfully."
                });
                setNewName('');
                setNewText('');
                fetchTemplates();
            }
        } catch (err) {
            toast({
                title: "Error",
                description: "Failed to save template.",
                variant: "destructive"
            });
        } finally {
            setIsLoading(false);
        }
    };

    const handleDeleteTemplate = async (id: number) => {
        if (!confirm('Are you sure you want to delete this template?')) return;

        try {
            const res = await fetch(`/api/resolutions/${id}`, { method: 'DELETE' });
            if (res.ok) {
                toast({
                    title: "Template Deleted",
                    description: "The template has been removed."
                });
                fetchTemplates();
            }
        } catch (err) {
            console.error("Failed to delete template", err);
        }
    };

    const filteredTemplates = useMemo(() => {
        if (!searchTerm.trim()) return templates;
        const query = searchTerm.toLowerCase();
        return templates.filter(t => 
            t.template_name.toLowerCase().includes(query) ||
            t.resolution_text.toLowerCase().includes(query)
        );
    }, [templates, searchTerm]);

    return (
        <ProductDashboardLayout productName="Generate Minutes" productRoute="/minutes-preparation" navigationItems={navigationItems}>
            <div className="p-6">
                <div className="border border-slate-200 rounded-xl bg-white shadow-xs p-6 space-y-6">
                    <div className="pb-4 border-b border-slate-100">
                        <h1 className="text-xl font-bold text-slate-900">Template Resolution</h1>
                        <p className="text-xs text-slate-500 mt-1">Manage reusable resolution templates for meeting minutes.</p>
                    </div>

                    <Card className="border border-slate-200 shadow-none bg-white rounded-xl overflow-hidden">
                        <CardHeader className="bg-slate-50/50 border-b border-slate-100 pb-3">
                            <CardTitle className="text-sm font-bold text-slate-900">Add New Resolution Template</CardTitle>
                            <CardDescription className="text-xs text-slate-500 mt-0.5">Enter a template name and statutory resolution text</CardDescription>
                        </CardHeader>
                        <CardContent className="p-4 space-y-4">
                            <form onSubmit={handleAddTemplate} className="space-y-4">
                                <div className="space-y-1.5">
                                    <Label htmlFor="templateName" className="text-xs font-semibold text-slate-700">Template Name *</Label>
                                    <Input
                                        id="templateName"
                                        placeholder="e.g., Appointment of Statutory Auditor"
                                        value={newName}
                                        onChange={(e) => setNewName(e.target.value)}
                                        required
                                        className="bg-white border-slate-200 h-9 rounded-lg text-xs"
                                    />
                                </div>
                                <div className="space-y-1.5">
                                    <Label htmlFor="resolutionText" className="text-xs font-semibold text-slate-700">Resolution Text *</Label>
                                    <textarea
                                        id="resolutionText"
                                        className="w-full min-h-[120px] p-3 border border-slate-200 rounded-lg text-xs focus:outline-none focus:border-slate-400 bg-white"
                                        placeholder="Enter the full text of the resolution..."
                                        value={newText}
                                        onChange={(e) => setNewText(e.target.value)}
                                        required
                                    />
                                </div>
                                <Button type="submit" disabled={isLoading} className="bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs rounded-lg h-9 px-4">
                                    {isLoading ? 'Saving...' : (
                                        <><Plus className="h-4 w-4 mr-1.5" /> Save Template</>
                                    )}
                                </Button>
                            </form>
                        </CardContent>
                    </Card>

                    <Card className="border border-slate-200 shadow-none bg-white rounded-xl overflow-hidden">
                        <CardHeader className="bg-slate-50/50 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 pb-3 border-b border-slate-100">
                            <div>
                                <CardTitle className="text-sm font-bold text-slate-900">Stored Resolution Templates</CardTitle>
                                <CardDescription className="text-xs text-slate-500 mt-0.5">Search and manage existing templates</CardDescription>
                            </div>
                            <div className="relative w-full md:w-64 shrink-0">
                                <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                                <Input
                                    placeholder="Search templates..."
                                    value={searchTerm}
                                    onChange={(e) => setSearchTerm(e.target.value)}
                                    className="pl-9 bg-white border-slate-200 h-9 text-xs rounded-lg"
                                />
                            </div>
                        </CardHeader>
                        <CardContent className="p-0">
                            <Table>
                                <TableHeader className="bg-slate-50/30">
                                    <TableRow>
                                        <TableHead className="text-xs font-bold text-slate-700">Template Name</TableHead>
                                        <TableHead className="text-xs font-bold text-slate-700">Preview</TableHead>
                                        <TableHead className="w-[80px] text-center text-xs font-bold text-slate-700">Action</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {filteredTemplates.length === 0 ? (
                                        <TableRow>
                                            <TableCell colSpan={3} className="text-center py-8 text-xs text-slate-400">
                                                No templates found matching your criteria.
                                            </TableCell>
                                        </TableRow>
                                    ) : (
                                        filteredTemplates.map((template) => (
                                            <TableRow key={template.id} className="border-b border-slate-100">
                                                <TableCell className="font-bold text-xs text-slate-900">{template.template_name}</TableCell>
                                                <TableCell className="max-w-[400px] truncate text-slate-600 text-xs">
                                                    {template.resolution_text}
                                                </TableCell>
                                                <TableCell className="text-center">
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        className="text-slate-400 hover:text-red-700 hover:bg-red-50 h-8 w-8 p-0 rounded-lg"
                                                        onClick={() => handleDeleteTemplate(template.id)}
                                                    >
                                                        <Trash2 className="h-4 w-4" />
                                                    </Button>
                                                </TableCell>
                                            </TableRow>
                                        ))
                                    )}
                                </TableBody>
                            </Table>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </ProductDashboardLayout>
    );
};

export default TemplateResolution;
