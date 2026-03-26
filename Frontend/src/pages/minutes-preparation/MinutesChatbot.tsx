import { useState, useEffect, useRef } from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import {
    SendIcon,
    PlusIcon,
    MessageSquareIcon,
    HistoryIcon,
    HomeIcon,
    FileTextIcon,
    LayoutDashboardIcon,
    BotIcon,
    UserIcon,
    UploadIcon,
    SearchIcon,
    Trash2Icon,
    FileSpreadsheetIcon,
    Users,
    BookOpen
} from 'lucide-react';
import ProductDashboardLayout from '@/components/layout/ProductDashboardLayout';
import { cn } from '@/lib/utils';
import { toast } from '@/components/ui/use-toast';

interface Message {
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
    sources?: { document: string; chunk: string }[];
}

const MinutesChatbot = () => {
    const navigationItems = [
        { id: 'home', label: 'Home', icon: HomeIcon, href: '/' },
        { id: 'dashboard', label: 'Generate Minutes', icon: FileTextIcon, href: '/minutes-preparation' },
        { id: 'create-agenda', label: 'Create Agenda', icon: PlusIcon, href: '/minutes-preparation/create-agenda' },
        { id: 'compliances', label: 'Secretarial Compliances', icon: FileSpreadsheetIcon, href: '/minutes-preparation/compliances' },
        { id: 'ai-mom', label: 'AI MOM', icon: FileTextIcon, href: '/minutes-preparation/ai-assistant' },
        { id: 'chatbot', label: 'Meeting Assistant', icon: MessageSquareIcon, href: '/minutes-preparation/chatbot', isActive: true },
        { id: 'template-resolution', label: 'Template Resolution', icon: HistoryIcon, href: '/minutes-preparation/template-resolution' },
        { id: 'minutes', label: 'Meeting Minutes', icon: FileTextIcon, href: '/minutes-preparation/minutes' },
        { id: 'templates', label: 'Templates', icon: FileSpreadsheetIcon, href: '/minutes-preparation/templates' },
        { id: 'directors', label: 'Directors', icon: Users, href: '/minutes-preparation/directors' },
        { id: 'manual', label: 'User Manual', icon: BookOpen, href: '#' }
    ];

    const [sessions, setSessions] = useState<string[]>([]);
    const [activeSessionId, setActiveSessionId] = useState<string>(`session_${Date.now()}`);
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Get user email from storage or mock
    const userEmail = "admin@adani.com";

    useEffect(() => {
        fetchSessions();
    }, []);

    useEffect(() => {
        if (activeSessionId) {
            fetchHistory(activeSessionId);
        }
    }, [activeSessionId]);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages, isLoading]);

    const fetchSessions = async () => {
        try {
            const resp = await fetch('/api/minutes-chatbot/sessions', {
                headers: { 'X-User-Email': userEmail }
            });
            const data = await resp.json();
            if (data.sessions) {
                setSessions(data.sessions);
            }
        } catch (err) {
            console.error("Failed to fetch sessions", err);
        }
    };

    const fetchHistory = async (sid: string) => {
        try {
            const resp = await fetch(`/api/minutes-chatbot/history/${sid}`, {
                headers: { 'X-User-Email': userEmail }
            });
            const data = await resp.json();
            if (Array.isArray(data)) {
                setMessages(data.map(m => ({
                    role: m.role,
                    content: m.message,
                    timestamp: m.timestamp
                })));
            }
        } catch (err) {
            console.error("Failed to fetch history", err);
        }
    };

    const handleSendMessage = async () => {
        if (!input.trim() || isLoading) return;

        const userMsg: Message = {
            role: 'user',
            content: input,
            timestamp: new Date().toISOString()
        };

        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setIsLoading(true);

        try {
            const resp = await fetch('/api/minutes-chatbot/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-User-Email': userEmail
                },
                body: JSON.stringify({
                    query: input,
                    session_id: activeSessionId
                })
            });

            if (!resp.ok) throw new Error("Backend error");

            const data = await resp.json();

            const assistMsg: Message = {
                role: 'assistant',
                content: data.answer,
                timestamp: new Date().toISOString(),
                sources: data.sources
            };

            setMessages(prev => [...prev, assistMsg]);

            // Refresh sessions list if new
            if (!sessions.includes(activeSessionId)) {
                setSessions(prev => [activeSessionId, ...prev]);
            }

        } catch (err) {
            toast({
                title: "Error",
                description: "Failed to get response from assistant.",
                variant: "destructive"
            });
        } finally {
            setIsLoading(false);
        }
    };

    const startNewChat = () => {
        const newId = `session_${Date.now()}`;
        setActiveSessionId(newId);
        setMessages([]);
    };

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        if (!e.target.files?.length) return;
        const file = e.target.files[0];

        const formData = new FormData();
        formData.append('file', file);

        toast({ title: "Uploading...", description: `Uploading ${file.name} to knowledge base.` });

        try {
            const resp = await fetch('/api/minutes-chatbot/upload', {
                method: 'POST',
                headers: { 'X-User-Email': userEmail },
                body: formData
            });

            if (resp.ok) {
                toast({ title: "Success", description: "Document indexed successfully." });
            } else {
                throw new Error("Upload failed");
            }
        } catch (err) {
            toast({ title: "Upload Failed", description: "Could not process document.", variant: "destructive" });
        }
    };

    return (
        <ProductDashboardLayout
            productName="Meeting Assistant"
            productRoute="/minutes-preparation"
            navigationItems={navigationItems}
        >
            <div className="flex h-[calc(100vh-120px)] overflow-hidden gap-4 p-2">
                {/* Sidebar */}
                <Card className="w-80 flex flex-col shadow-md border-gray-200">
                    <CardHeader className="pb-4 border-b">
                        <Button
                            onClick={startNewChat}
                            className="w-full flex items-center gap-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700"
                        >
                            <PlusIcon className="h-4 w-4" />
                            New Chat
                        </Button>
                    </CardHeader>
                    <CardContent className="flex-1 p-0 overflow-hidden">
                        <ScrollArea className="h-full px-2 py-4">
                            <div className="space-y-2">
                                <h3 className="px-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                                    Recent Sessions
                                </h3>
                                {sessions.length === 0 ? (
                                    <p className="text-xs text-center text-muted-foreground py-10">No chat history yet</p>
                                ) : (
                                    sessions.map(sid => (
                                        <button
                                            key={sid}
                                            onClick={() => setActiveSessionId(sid)}
                                            className={cn(
                                                "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all text-left truncate group",
                                                activeSessionId === sid
                                                    ? "bg-blue-50 text-blue-700 font-medium border border-blue-100 shadow-sm"
                                                    : "hover:bg-gray-50 text-gray-600"
                                            )}
                                        >
                                            <MessageSquareIcon className={cn("h-4 w-4 shrink-0", activeSessionId === sid ? "text-blue-500" : "text-gray-400")} />
                                            <span className="truncate">{sid.replace('session_', '')}</span>
                                        </button>
                                    ))
                                )}
                            </div>
                        </ScrollArea>
                    </CardContent>
                </Card>

                {/* Main Chat Area */}
                <Card className="flex-1 flex flex-col shadow-xl border-gray-200 bg-gray-50/30">
                    <CardHeader className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-10 py-3">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-blue-100 rounded-lg">
                                    <BotIcon className="h-5 w-5 text-blue-600" />
                                </div>
                                <div>
                                    <CardTitle className="text-lg">Aegis AI Assistant</CardTitle>
                                    <span className="text-[10px] bg-green-100 text-green-700 px-1.5 py-0.5 rounded-full font-bold uppercase">Online</span>
                                </div>
                            </div>
                            <div className="flex items-center gap-2">
                                <Button variant="outline" size="sm" onClick={() => fileInputRef.current?.click()} className="text-xs h-8">
                                    <UploadIcon className="h-3.5 w-3.5 mr-1" />
                                    Train AI
                                </Button>
                                <input type="file" ref={fileInputRef} onChange={handleFileUpload} hidden />
                            </div>
                        </div>
                    </CardHeader>

                    <CardContent className="flex-1 overflow-hidden p-0 relative">
                        <ScrollArea className="h-full p-4 md:p-6" ref={scrollRef}>
                            <div className="max-w-4xl mx-auto space-y-6">
                                {messages.length === 0 && !isLoading && (
                                    <div className="flex flex-col items-center justify-center h-[50vh] text-center space-y-4">
                                        <div className="p-4 bg-white rounded-full shadow-lg">
                                            <BotIcon className="h-12 w-12 text-blue-500" />
                                        </div>
                                        <div className="space-y-2">
                                            <h2 className="text-2xl font-bold text-gray-800">Hello! I'm your Meeting Assistant</h2>
                                            <p className="text-gray-500 max-w-sm">
                                                Ask me anything about your meeting agendas, decisions, or action items. I can analyze uploaded PDF and Word documents.
                                            </p>
                                        </div>
                                        <div className="grid grid-cols-2 gap-3 mt-8">
                                            {["Summarize last meeting", "List all action items", "Show me the agenda", "Find decisions on X"].map(q => (
                                                <Button key={q} variant="outline" className="text-xs h-auto py-2 border-dashed bg-white" onClick={() => setInput(q)}>
                                                    {q}
                                                </Button>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {messages.map((m, i) => (
                                    <div key={i} className={cn("flex flex-col", m.role === 'user' ? "items-end" : "items-start")}>
                                        <div className={cn(
                                            "flex gap-3 max-w-[85%]",
                                            m.role === 'user' ? "flex-row-reverse" : "flex-row"
                                        )}>
                                            <Avatar className={cn("h-8 w-8 mt-1 border-2 shadow-sm", m.role === 'user' ? "border-indigo-100" : "border-blue-100")}>
                                                <AvatarFallback className={m.role === 'user' ? "bg-indigo-50 text-indigo-700" : "bg-blue-50 text-blue-700"}>
                                                    {m.role === 'user' ? <UserIcon className="h-4 w-4" /> : <BotIcon className="h-4 w-4" />}
                                                </AvatarFallback>
                                            </Avatar>
                                            <div className="space-y-2">
                                                <div className={cn(
                                                    "p-4 rounded-2xl shadow-sm text-sm leading-relaxed",
                                                    m.role === 'user'
                                                        ? "bg-indigo-600 text-white rounded-tr-none"
                                                        : "bg-white text-gray-800 border border-gray-100 rounded-tl-none"
                                                )}>
                                                    <div className="whitespace-pre-wrap">{m.content}</div>
                                                </div>

                                                {m.sources && m.sources.length > 0 && (
                                                    <div className="flex flex-wrap gap-2 mt-2">
                                                        <span className="text-[10px] font-bold text-gray-400 uppercase mr-1 mt-1">Sources:</span>
                                                        {m.sources.map((s, idx) => (
                                                            <div key={idx} className="bg-gray-100 text-[10px] px-2 py-0.5 rounded-full text-gray-600 border flex items-center gap-1">
                                                                <FileTextIcon className="h-3 w-3" />
                                                                {s.document}
                                                            </div>
                                                        ))}
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                ))}

                                {isLoading && (
                                    <div className="flex gap-3 items-start animate-pulse">
                                        <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center">
                                            <BotIcon className="h-4 w-4 text-blue-500" />
                                        </div>
                                        <div className="bg-white border p-4 rounded-2xl rounded-tl-none shadow-sm space-y-2 w-32">
                                            <div className="h-2 w-full bg-gray-100 rounded"></div>
                                            <div className="h-2 w-2/3 bg-gray-100 rounded"></div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </ScrollArea>
                    </CardContent>

                    <CardFooter className="p-4 bg-white border-t">
                        <div className="max-w-4xl mx-auto w-full relative group">
                            <Input
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                                placeholder="Message meeting assistant..."
                                className="pr-14 h-14 rounded-xl border-gray-200 focus:border-blue-500 focus:ring-blue-500 transition-all shadow-sm"
                            />
                            <Button
                                size="icon"
                                onClick={handleSendMessage}
                                disabled={!input.trim() || isLoading}
                                className={cn(
                                    "absolute right-2 top-2 h-10 w-10 rounded-lg transition-all shadow-md",
                                    input.trim() ? "bg-blue-600 hover:bg-blue-700" : "bg-gray-300 pointer-events-none"
                                )}
                            >
                                <SendIcon className="h-5 w-5" />
                            </Button>
                        </div>
                    </CardFooter>
                </Card>
            </div>
        </ProductDashboardLayout>
    );
};

export default MinutesChatbot;
