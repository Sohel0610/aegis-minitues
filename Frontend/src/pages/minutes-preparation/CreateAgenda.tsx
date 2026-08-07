/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Upload, FileText, Download, Plus, X, Copy, Check, Calendar, Layers, FileCheck } from 'lucide-react';
import ProductDashboardLayout from '@/components/layout/ProductDashboardLayout';
import { useToast } from "@/components/ui/use-toast";
import { Progress } from "@/components/ui/progress";
import { getMinutesNavItems } from '@/constants/minutesNavigation';
import { useAuth } from '@/contexts/AuthContext';
import { useVertical } from '@/contexts/VerticalContext';

const CreateAgenda = () => {
    const [files, setFiles] = useState<File[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [progress, setProgress] = useState(0);
    const [agendaName, setAgendaName] = useState('');
    const [meetingType, setMeetingType] = useState('Board Meeting');
    const [generatedAgenda, setGeneratedAgenda] = useState<string | null>(null);
    const [copied, setCopied] = useState(false);
    
    const { toast } = useToast();
    const { user } = useAuth();
    const { selectedCompany } = useVertical();

    const userEmail = user?.email || 'guest@aegis.local';
    const activeCompany = selectedCompany?.name || 'Adani Group';

    const navigationItems = getMinutesNavItems('create-agenda');

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files) {
            const newFiles = Array.from(e.target.files);
            setFiles(prev => [...prev, ...newFiles]);
        }
    };

    const removeFile = (index: number) => {
        setFiles(prev => prev.filter((_, i) => i !== index));
    };

    const handleCopyAgenda = () => {
        if (!generatedAgenda) return;
        navigator.clipboard.writeText(generatedAgenda);
        setCopied(true);
        toast({ title: "Copied to Clipboard", description: "Agenda text has been copied." });
        setTimeout(() => setCopied(false), 2000);
    };

    const generateAgenda = async () => {
        if (!agendaName || files.length === 0) {
            toast({
                title: "Missing Information",
                description: "Please provide a meeting subject and upload at least one supporting document.",
                variant: "destructive"
            });
            return;
        }

        setIsLoading(true);
        setProgress(10);

        const interval = setInterval(() => {
            setProgress(prev => {
                if (prev >= 90) {
                    clearInterval(interval);
                    return 90;
                }
                return prev + 10;
            });
        }, 400);

        const sessionId = `agenda_${Date.now()}`;

        try {
            for (const file of files) {
                const formData = new FormData();
                formData.append('file', file);
                formData.append('session_id', sessionId);
                
                await fetch('/api/minutes-chatbot/upload', {
                    method: 'POST',
                    headers: { 'X-User-Email': userEmail },
                    body: formData
                });
            }

            const prompt = `Generate a formal meeting agenda for ${activeCompany} - ${meetingType} regarding "${agendaName}". 
Base the agenda on the uploaded documents. Ensure the agenda includes standard corporate items (e.g., Leave of Absence, Confirmation of Previous Minutes, Any Other Business) as well as specific discussion points extracted from the documents. Format the output cleanly with clear item numbers.`;

            const queryRes = await fetch('/api/minutes-chatbot/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-User-Email': userEmail
                },
                body: JSON.stringify({
                    query: prompt,
                    session_id: sessionId
                })
            });

            if (!queryRes.ok) {
                throw new Error("Failed to generate agenda");
            }

            const queryData = await queryRes.json();
            setGeneratedAgenda(queryData.answer);

            setProgress(100);
            toast({
                title: "Agenda Generated",
                description: "The meeting agenda has been compiled successfully."
            });
        } catch (err) {
            toast({
                title: "Error",
                description: "Failed to generate agenda. Please verify server connection.",
                variant: "destructive"
            });
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <ProductDashboardLayout productName="Generate Minutes" productRoute="/minutes-preparation" navigationItems={navigationItems}>
            <div className="p-4 h-[calc(100vh-65px)] overflow-hidden">
                <div className="border border-slate-200 rounded-xl bg-white shadow-xs p-4 flex flex-col h-full overflow-hidden space-y-4">
                    
                    {/* Header */}
                    <div className="pb-3 border-b border-slate-100 flex justify-between items-center shrink-0">
                        <div>
                            <div className="flex items-center gap-2">
                                <h1 className="text-xl font-bold text-slate-900">Agenda Builder</h1>
                                <Badge variant="secondary" className="bg-slate-100 text-slate-800 border-slate-200 text-[10px] font-semibold tracking-wider">
                                    {activeCompany}
                                </Badge>
                            </div>
                            <p className="text-xs text-slate-500 mt-0.5">
                                Compile formal agendas from reference materials.
                            </p>
                        </div>
                    </div>

                    {/* Main 2-Column Non-scrolling Grid */}
                    <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 flex-1 overflow-hidden">
                        
                        {/* LEFT COLUMN: Inputs & Uploads (5 Cols) */}
                        <div className="lg:col-span-5 flex flex-col gap-4 overflow-hidden h-full">
                            <Card className="border border-slate-200 shadow-none bg-white rounded-xl overflow-hidden shrink-0">
                                <CardHeader className="bg-slate-50/50 border-b border-slate-100 py-2.5 px-4">
                                    <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-2">
                                        <Calendar className="h-3.5 w-3.5 text-slate-400" />
                                        Meeting Details
                                    </CardTitle>
                                </CardHeader>
                                <CardContent className="p-3.5 space-y-3">
                                    <div className="space-y-1">
                                        <Label htmlFor="agendaName" className="text-xs font-semibold text-slate-700">Meeting Subject / Title *</Label>
                                        <Input
                                            id="agendaName"
                                            placeholder="e.g., Q3 Financial Review & Audit Approvals"
                                            value={agendaName}
                                            onChange={(e) => setAgendaName(e.target.value)}
                                            className="bg-white border-slate-200 h-8 rounded-lg text-xs"
                                        />
                                    </div>
                                    <div className="space-y-1">
                                        <Label htmlFor="meetingType" className="text-xs font-semibold text-slate-700">Meeting Type</Label>
                                        <Select value={meetingType} onValueChange={setMeetingType}>
                                            <SelectTrigger className="bg-white border-slate-200 h-8 rounded-lg text-xs">
                                                <SelectValue />
                                            </SelectTrigger>
                                            <SelectContent className="bg-white">
                                                <SelectItem value="Board Meeting">Board Meeting</SelectItem>
                                                <SelectItem value="Committee Meeting">Committee Meeting</SelectItem>
                                                <SelectItem value="Annual General Meeting (AGM)">Annual General Meeting (AGM)</SelectItem>
                                                <SelectItem value="Extraordinary General Meeting (EGM)">Extraordinary General Meeting (EGM)</SelectItem>
                                            </SelectContent>
                                        </Select>
                                    </div>
                                </CardContent>
                            </Card>

                            {/* Supporting Documents Upload Card */}
                            <Card className="border border-slate-200 shadow-none bg-white rounded-xl overflow-hidden flex-1 flex flex-col justify-between min-h-0">
                                <CardHeader className="bg-slate-50/50 border-b border-slate-100 py-2.5 px-4 shrink-0">
                                    <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-2">
                                        <Upload className="h-3.5 w-3.5 text-slate-400" />
                                        Supporting Documents
                                    </CardTitle>
                                </CardHeader>
                                
                                <CardContent className="p-3.5 space-y-3 flex-1 overflow-hidden flex flex-col">
                                    <div
                                        className="border border-dashed border-slate-200 rounded-xl p-4 text-center hover:border-slate-300 bg-slate-50/50 hover:bg-slate-50 cursor-pointer transition-colors flex flex-col items-center justify-center shrink-0"
                                        onClick={() => document.getElementById('file-upload')?.click()}
                                    >
                                        <div className="w-8 h-8 rounded-lg bg-slate-100 flex items-center justify-center mb-1.5">
                                            <Upload className="h-4 w-4 text-slate-500" />
                                        </div>
                                        <p className="text-xs font-bold text-slate-800">Click to upload or drag & drop</p>
                                        <p className="text-[10px] text-slate-400 mt-0.5">PDF, PPTX, XLSX, DOCX (Max 25MB)</p>
                                        <input
                                            id="file-upload"
                                            type="file"
                                            className="hidden"
                                            multiple
                                            onChange={handleFileChange}
                                        />
                                    </div>

                                    {files.length > 0 && (
                                        <div className="space-y-1.5 flex-1 overflow-hidden flex flex-col pt-1">
                                            <Label className="text-xs font-semibold text-slate-700">Uploaded Files ({files.length})</Label>
                                            <div className="flex-1 overflow-y-auto space-y-1.5 pr-1">
                                                {files.map((file, i) => (
                                                    <div key={i} className="flex items-center justify-between text-xs p-2 bg-slate-50 border border-slate-200 rounded-lg">
                                                        <div className="flex items-center gap-2 truncate">
                                                            <FileText className="h-3.5 w-3.5 text-slate-500 shrink-0" />
                                                            <span className="truncate font-semibold text-slate-800">{file.name}</span>
                                                            <span className="text-[10px] text-slate-400 font-mono">({(file.size / 1024).toFixed(0)} KB)</span>
                                                        </div>
                                                        <button 
                                                            type="button" 
                                                            onClick={() => removeFile(i)} 
                                                            className="text-slate-400 hover:text-red-700 p-0.5 rounded transition-colors"
                                                        >
                                                            <X className="h-3.5 w-3.5" />
                                                        </button>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </CardContent>

                                <CardFooter className="bg-slate-50/50 border-t border-slate-100 p-3 shrink-0">
                                    <Button
                                        className="w-full h-9 bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs rounded-lg shadow-xs transition-colors"
                                        disabled={isLoading}
                                        onClick={generateAgenda}
                                    >
                                        {isLoading ? (
                                            <span className="flex items-center gap-2">
                                                <div className="animate-spin rounded-full h-3.5 w-3.5 border-2 border-white border-t-transparent"></div>
                                                Compiling Agenda...
                                            </span>
                                        ) : (
                                            "Compile Agenda Draft"
                                        )}
                                    </Button>
                                </CardFooter>
                            </Card>
                        </div>

                        {/* RIGHT COLUMN: Agenda Output Studio (7 Cols) */}
                        <div className="lg:col-span-7 flex flex-col overflow-hidden h-full">
                            <Card className="border border-slate-200 shadow-none bg-white rounded-xl overflow-hidden flex-1 flex flex-col h-full">
                                <CardHeader className="bg-slate-50/50 border-b border-slate-100 py-2.5 px-4 flex flex-row items-center justify-between shrink-0">
                                    <div>
                                        <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-2">
                                            <FileCheck className="h-3.5 w-3.5 text-slate-400" />
                                            Agenda Draft Preview
                                        </CardTitle>
                                    </div>

                                    {generatedAgenda && (
                                        <Button 
                                            variant="outline" 
                                            size="sm" 
                                            onClick={handleCopyAgenda}
                                            className="h-7 text-xs font-semibold rounded-lg border-slate-200 bg-white"
                                        >
                                            {copied ? <Check className="h-3 w-3 text-emerald-600 mr-1" /> : <Copy className="h-3 w-3 mr-1" />}
                                            {copied ? 'Copied' : 'Copy'}
                                        </Button>
                                    )}
                                </CardHeader>

                                <CardContent className="p-3.5 flex-1 flex flex-col justify-center overflow-hidden bg-slate-50/10">
                                    {isLoading ? (
                                        <div className="p-6 flex flex-col items-center justify-center space-y-3 text-center">
                                            <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center">
                                                <div className="animate-spin rounded-full h-4 w-4 border-2 border-slate-600 border-t-transparent"></div>
                                            </div>
                                            <div>
                                                <h3 className="font-bold text-slate-800 text-xs">Reading Reference Documents</h3>
                                                <p className="text-[11px] text-slate-500 mt-0.5">Extracting resolutions and financial reviews...</p>
                                            </div>
                                            <Progress value={progress} className="w-48 h-1 bg-slate-200" />
                                        </div>
                                    ) : generatedAgenda ? (
                                        <div className="h-full overflow-y-auto bg-white p-4 rounded-lg border border-slate-200 text-xs leading-relaxed text-slate-800 whitespace-pre-wrap font-sans">
                                            {generatedAgenda}
                                        </div>
                                    ) : (
                                        <div className="p-6 flex flex-col items-center justify-center text-center space-y-2 text-slate-400">
                                            <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center">
                                                <Layers className="h-5 w-5 text-slate-400" />
                                            </div>
                                            <h4 className="font-bold text-slate-600 text-xs">No Agenda Generated Yet</h4>
                                            <p className="text-[11px] max-w-xs text-slate-400">
                                                Fill in the meeting subject, upload your board documents on the left, and click <strong>Compile Agenda Draft</strong>.
                                            </p>
                                        </div>
                                    )}
                                </CardContent>
                            </Card>
                        </div>
                    </div>
                </div>
            </div>
        </ProductDashboardLayout>
    );
};

export default CreateAgenda;
