
import React, { useState, useEffect } from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Plus, Trash2 } from 'lucide-react';
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

    return (
        <ProductDashboardLayout productName="Generate Minutes" productRoute="/minutes-preparation" navigationItems={navigationItems}>
            <div className="container mx-auto py-6">
                <div className="space-y-8">
                    <div>
                        <h1 className="text-3xl font-bold">Template Resolution</h1>
                        <p className="text-muted-foreground">Manage reusable resolution templates for your meeting minutes</p>
                    </div>

                    <Card>
                        <CardHeader>
                            <CardTitle>Add New Resolution Template</CardTitle>
                            <CardDescription>Enter a name and the resolution text to save for future use</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <form onSubmit={handleAddTemplate} className="space-y-4">
                                <div className="space-y-2">
                                    <Label htmlFor="templateName">Template Name *</Label>
                                    <Input
                                        id="templateName"
                                        placeholder="e.g., Appointment of Statutory Auditor"
                                        value={newName}
                                        onChange={(e) => setNewName(e.target.value)}
                                        required
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="resolutionText">Resolution Text *</Label>
                                    <textarea
                                        id="resolutionText"
                                        className="w-full min-h-[150px] p-3 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        placeholder="Enter the full text of the resolution..."
                                        value={newText}
                                        onChange={(e) => setNewText(e.target.value)}
                                        required
                                    />
                                </div>
                                <Button type="submit" disabled={isLoading}>
                                    {isLoading ? 'Saving...' : (
                                        <><Plus className="h-4 w-4 mr-2" /> Save Template</>
                                    )}
                                </Button>
                            </form>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader>
                            <CardTitle>Stored Resolution Templates</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>Template Name</TableHead>
                                        <TableHead>Preview</TableHead>
                                        <TableHead className="w-[100px]">Action</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {templates.length === 0 ? (
                                        <TableRow>
                                            <TableCell colSpan={3} className="text-center py-8 text-muted-foreground">
                                                No templates found. Add your first resolution template above.
                                            </TableCell>
                                        </TableRow>
                                    ) : (
                                        templates.map((template) => (
                                            <TableRow key={template.id}>
                                                <TableCell className="font-medium">{template.template_name}</TableCell>
                                                <TableCell className="max-w-[400px] truncate text-muted-foreground italic">
                                                    {template.resolution_text}
                                                </TableCell>
                                                <TableCell>
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        className="text-red-500 hover:text-red-700 hover:bg-red-50"
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
