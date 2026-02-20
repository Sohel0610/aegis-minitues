
import React, { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Upload, FileText, Download, Sparkles, Home, History, FileSpreadsheet, Plus, HelpCircle, BookOpen } from 'lucide-react';
import ProductDashboardLayout from '@/components/layout/ProductDashboardLayout';
import { useToast } from "@/components/ui/use-toast";
import { Progress } from "@/components/ui/progress";

const CreateAgenda = () => {
    const [files, setFiles] = useState<File[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [progress, setProgress] = useState(0);
    const [agendaName, setAgendaName] = useState('');
    const [meetingType, setMeetingType] = useState('Board Meeting');
    const [generatedAgenda, setGeneratedAgenda] = useState<string | null>(null);
    const { toast } = useToast();

    // Chatbot state
    const [chatMessages, setChatMessages] = useState<{ role: 'user' | 'assistant', text: string }[]>([]);
    const [chatInput, setChatInput] = useState('');
    const [isAsking, setIsAsking] = useState(false);

    const handleAsk = async () => {
        if (!chatInput.trim()) return;

        const userMsg = { role: 'user' as const, text: chatInput };
        setChatMessages(prev => [...prev, userMsg]);
        setChatInput('');
        setIsAsking(true);

        try {
            const res = await fetch('/api/minutes-chatbot/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query: userMsg.text,
                    session_id: 'session_agenda_page'
                })
            });

            if (!res.ok) throw new Error('API error');
            const data = await res.json();

            setChatMessages(prev => [...prev, { role: 'assistant', text: data.answer }]);
        } catch (error) {
            setChatMessages(prev => [...prev, { role: 'assistant', text: 'Sorry, I encountered an error. Please try again later.' }]);
        } finally {
            setIsAsking(false);
        }
    };


    const navigationItems = [
        { id: 'home', label: 'Home', icon: Home, href: '/' },
        { id: 'dashboard', label: 'Generate Minutes', icon: FileText, href: '/minutes-preparation' },
        { id: 'create-agenda', label: 'Create Agenda', icon: Plus, href: '/minutes-preparation/create-agenda', isActive: true },
        { id: 'compliances', label: 'Secretarial Compliances', icon: FileSpreadsheet, href: '/minutes-preparation/compliances' },
        { id: 'ai-mom', label: 'AI MOM', icon: Sparkles, href: '/minutes-preparation/ai-assistant' },
        { id: 'template-resolution', label: 'Template Resolution', icon: History, href: '/minutes-preparation/template-resolution' },
        { id: 'manual', label: 'User Manual', icon: BookOpen, href: '#' }
    ];

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files) {
            const newFiles = Array.from(e.target.files);
            setFiles(prev => [...prev, ...newFiles]);
        }
    };

    const removeFile = (index: number) => {
        setFiles(prev => prev.filter((_, i) => i !== index));
    };

    const generateAgenda = async () => {
        if (!agendaName || files.length === 0) {
            toast({
                title: "Missing Information",
                description: "Please provide an agenda name and upload at least one supporting document.",
                variant: "destructive"
            });
            return;
        }

        setIsLoading(true);
        setProgress(10);

        // Simulate AI Generation for now
        const interval = setInterval(() => {
            setProgress(prev => {
                if (prev >= 90) {
                    clearInterval(interval);
                    return 90;
                }
                return prev + 10;
            });
        }, 500);

        try {
            // Logic for AI generation would go here
            // 1. Upload files
            // 2. Call AI endpoint with file IDs
            await new Promise(resolve => setTimeout(resolve, 3000));

            setGeneratedAgenda(`
AGENDA FOR THE ${meetingType.toUpperCase()}
Subject: ${agendaName}

1. LEAVE OF ABSENCE
To grant leave of absence to directors who have expressed their inability to attend.

2. CONFIRMATION OF PREVIOUS MINUTES
To confirm the minutes of the previous meeting.

3. REVIEW OF SUPPORTING DOCUMENTS
${files.map(f => `- Analysis of ${f.name}`).join('\n')}

4. KEY PROPOSALS
- Proposal A based on uploaded data
- Budget allocation review

5. ANY OTHER BUSINESS
With the permission of the Chair.
      `);

            setProgress(100);
            toast({
                title: "Agenda Generated",
                description: "AI has successfully generated the meeting agenda."
            });
        } catch (err) {
            toast({
                title: "Error",
                description: "Failed to generate agenda.",
                variant: "destructive"
            });
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <ProductDashboardLayout productName="Generate Minutes" productRoute="/minutes-preparation" navigationItems={navigationItems}>
            <div className="container mx-auto py-6">
                <div className="space-y-8">
                    <div>
                        <h1 className="text-3xl font-bold">Create Agenda</h1>
                        <p className="text-muted-foreground">AI-powered agenda generation using supporting documents</p>
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                        <div className="space-y-6">
                            <Card>
                                <CardHeader>
                                    <CardTitle>Meeting Details</CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="agendaName">Meeting Subject / Title *</Label>
                                        <Input
                                            id="agendaName"
                                            placeholder="e.g., Quarterly Financial Review"
                                            value={agendaName}
                                            onChange={(e) => setAgendaName(e.target.value)}
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="meetingType">Meeting Type</Label>
                                        <Select value={meetingType} onValueChange={setMeetingType}>
                                            <SelectTrigger>
                                                <SelectValue />
                                            </SelectTrigger>
                                            <SelectContent>
                                                <SelectItem value="Board Meeting">Board Meeting</SelectItem>
                                                <SelectItem value="Committee Meeting">Committee Meeting</SelectItem>
                                                <SelectItem value="AGM">Annual General Meeting (AGM)</SelectItem>
                                            </SelectContent>
                                        </Select>
                                    </div>
                                </CardContent>
                            </Card>

                            <Card>
                                <CardHeader>
                                    <CardTitle>Supporting Documents</CardTitle>
                                    <CardDescription>Upload PDFs, PPTs, Excel, or Word files</CardDescription>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                    <div
                                        className="border-2 border-dashed rounded-lg p-8 text-center hover:bg-gray-50 cursor-pointer transition-colors"
                                        onClick={() => document.getElementById('file-upload')?.click()}
                                    >
                                        <Upload className="h-10 w-10 mx-auto text-muted-foreground mb-2" />
                                        <p className="text-sm font-medium">Click to upload or drag and drop</p>
                                        <p className="text-xs text-muted-foreground mt-1">Supports PDF, PPTX, XLSX, DOCX</p>
                                        <input
                                            id="file-upload"
                                            type="file"
                                            className="hidden"
                                            multiple
                                            onChange={handleFileChange}
                                        />
                                    </div>

                                    {files.length > 0 && (
                                        <div className="space-y-2">
                                            <Label>Uploaded Files ({files.length})</Label>
                                            <div className="max-h-[200px] overflow-y-auto border rounded-md p-2 space-y-2">
                                                {files.map((file, i) => (
                                                    <div key={i} className="flex items-center justify-between text-sm p-2 bg-gray-50 rounded">
                                                        <div className="flex items-center gap-2 truncate">
                                                            <FileText className="h-4 w-4 text-blue-500" />
                                                            <span className="truncate">{file.name}</span>
                                                        </div>
                                                        <Button variant="ghost" size="sm" onClick={() => removeFile(i)} className="text-red-500 h-6 w-6 p-0">×</Button>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </CardContent>
                                <CardFooter>
                                    <Button
                                        className="w-full bg-gradient-to-r from-blue-600 to-indigo-600"
                                        disabled={isLoading}
                                        onClick={generateAgenda}
                                    >
                                        {isLoading ? 'Processing Documents...' : <><Sparkles className="h-4 w-4 mr-2" /> Generate AI Agenda</>}
                                    </Button>
                                </CardFooter>
                            </Card>
                        </div>

                        <div className="space-y-6">
                            <Card className="h-full flex flex-col">
                                <CardHeader className="border-b">
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <CardTitle>AI Generated Agenda</CardTitle>
                                            <CardDescription>Preview and refine the generated agenda</CardDescription>
                                        </div>
                                        {generatedAgenda && (
                                            <Button variant="outline" size="sm">
                                                <Download className="h-4 w-4 mr-2" /> Export
                                            </Button>
                                        )}
                                    </div>
                                </CardHeader>
                                <CardContent className="flex-1 p-0 overflow-hidden">
                                    {isLoading ? (
                                        <div className="p-12 flex flex-col items-center justify-center h-full space-y-4">
                                            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                                            <p className="text-sm font-medium">AI is analyzing documents...</p>
                                            <Progress value={progress} className="w-64" />
                                        </div>
                                    ) : generatedAgenda ? (
                                        <div className="p-6 h-full overflow-y-auto bg-gray-50 font-serif whitespace-pre-wrap text-sm leading-relaxed">
                                            {generatedAgenda}
                                        </div>
                                    ) : (
                                        <div className="p-12 flex flex-col items-center justify-center h-full text-center space-y-4 opacity-50">
                                            < Sparkles className="h-16 w-16 text-gray-300" />
                                            <p>Generation preview will appear here after analysis.</p>
                                            <p className="text-xs">Providing more context in uploaded files yields better results.</p>
                                        </div>
                                    )}
                                </CardContent>
                            </Card>
                        </div>
                    </div>

                    {/* Integrated Chatbot */}
                    <Card className="border-blue-200 bg-blue-50/50">
                        <CardHeader className="py-4">
                            <CardTitle className="text-lg flex items-center gap-2">
                                <HelpCircle className="h-5 w-5 text-blue-600" />
                                Meeting Assistant Chatbot
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="bg-white border rounded-lg p-4 h-[200px] mb-4 overflow-y-auto flex flex-col gap-2">
                                {chatMessages.length === 0 ? (
                                    <div className="flex-1 flex items-center justify-center text-muted-foreground italic text-sm">
                                        Ask me anything about the meeting documents...
                                    </div>
                                ) : (
                                    chatMessages.map((msg, i) => (
                                        <div key={i} className={`p-2 rounded-lg text-sm ${msg.role === 'user' ? 'bg-blue-100 self-end max-w-[80%]' : 'bg-gray-100 self-start max-w-[80%]'}`}>
                                            <p className="font-semibold text-xs mb-1">{msg.role === 'user' ? 'You' : 'Assistant'}</p>
                                            <p>{msg.text}</p>
                                        </div>
                                    ))
                                )}
                                {isAsking && (
                                    <div className="bg-gray-100 self-start p-2 rounded-lg text-sm animate-pulse">
                                        Thinking...
                                    </div>
                                )}
                            </div>
                            <div className="flex gap-2">
                                <Input
                                    className="bg-white"
                                    placeholder="What happened in the previous audit meeting?"
                                    value={chatInput}
                                    onChange={(e) => setChatInput(e.target.value)}
                                    onKeyDown={(e) => e.key === 'Enter' && handleAsk()}
                                />
                                <Button className="bg-blue-600" onClick={handleAsk} disabled={isAsking || !chatInput.trim()}>
                                    Ask
                                </Button>
                            </div>
                        </CardContent>
                    </Card>

                </div>
            </div>
        </ProductDashboardLayout>
    );
};

export default CreateAgenda;
