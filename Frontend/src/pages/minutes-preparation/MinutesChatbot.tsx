import { useState, useEffect, useRef } from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import {
    SendIcon,
    PlusIcon,
    MessageSquareIcon,
    FileTextIcon,
    UploadIcon,
    Trash2Icon,
} from 'lucide-react';
import ProductDashboardLayout from '@/components/layout/ProductDashboardLayout';
import { cn } from '@/lib/utils';
import { toast } from '@/components/ui/use-toast';
import { getMinutesNavItems } from '@/constants/minutesNavigation';
import { useAuth } from '@/contexts/AuthContext';

interface Message {
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
    sources?: { document: string; chunk: string }[];
}

interface SessionInfo {
    id: string;
    title: string;
}

const MinutesChatbot = () => {
    const navigationItems = getMinutesNavItems('chatbot');
    const { user } = useAuth();

    const [sessions, setSessions] = useState<SessionInfo[]>([]);
    const [activeSessionId, setActiveSessionId] = useState<string>(`session_${Date.now()}`);
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const userEmail = user?.email || 'guest@aegis.local';

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

    const deleteSession = async (sessionId: string, e: React.MouseEvent) => {
        e.stopPropagation();
        try {
            const resp = await fetch(`/api/minutes-chatbot/session/${sessionId}`, {
                method: 'DELETE',
                headers: { 'X-User-Email': userEmail }
            });
            if (resp.ok) {
                setSessions(prev => prev.filter(s => s.id !== sessionId));
                if (activeSessionId === sessionId) {
                    const newId = `session_${Date.now()}`;
                    setActiveSessionId(newId);
                    setMessages([]);
                }
                toast({ title: "Session Deleted", description: "Chat history has been removed." });
            }
        } catch (err) {
            console.error("Failed to delete session", err);
            toast({ title: "Error", description: "Failed to delete session.", variant: "destructive" });
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

            if (!sessions.find(s => s.id === activeSessionId)) {
                setSessions(prev => [{
                    id: activeSessionId, 
                    title: input.substring(0, 30) + (input.length > 30 ? "..." : "")
                }, ...prev]);
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
            <div className="flex h-[calc(100vh-65px)] w-full overflow-hidden bg-slate-50/50">
                {/* Sidebar Session Drawer */}
                <div className="w-72 md:w-80 flex flex-col border-r border-slate-200 bg-white shrink-0">
                    <div className="p-4 border-b border-slate-100 bg-white">
                        <Button
                            onClick={startNewChat}
                            className="w-full flex items-center justify-center gap-2 bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs rounded-lg h-9 shadow-2xs transition-colors"
                        >
                            <PlusIcon className="h-4 w-4" />
                            New Session
                        </Button>
                    </div>
                    <div className="flex-1 overflow-hidden">
                        <ScrollArea className="h-full px-3 py-3">
                            <div className="space-y-1">
                                <h3 className="px-3 text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">
                                    Recent Sessions
                                </h3>
                                {sessions.length === 0 ? (
                                    <p className="text-xs text-center text-slate-400 py-10">No chat history yet</p>
                                ) : (
                                    sessions.map(s => (
                                        <div
                                            key={s.id}
                                            onClick={() => setActiveSessionId(s.id)}
                                            className={cn(
                                                "w-full flex items-center justify-between gap-2 px-3 py-2 rounded-lg text-xs transition-all text-left truncate group cursor-pointer",
                                                activeSessionId === s.id
                                                    ? "bg-slate-100 text-slate-900 font-bold border border-slate-200/80 shadow-2xs"
                                                    : "hover:bg-slate-50 text-slate-600 font-medium"
                                            )}
                                        >
                                            <div className="flex items-center gap-2.5 min-w-0 flex-1">
                                                <MessageSquareIcon className={cn("h-3.5 w-3.5 shrink-0", activeSessionId === s.id ? "text-slate-900" : "text-slate-400")} />
                                                <span className="truncate">{s.title || s.id.replace('session_', '')}</span>
                                            </div>
                                            <button
                                                onClick={(e) => deleteSession(s.id, e)}
                                                title="Delete session"
                                                className="opacity-0 group-hover:opacity-100 p-1 hover:bg-slate-200/80 text-slate-400 hover:text-red-600 rounded transition-all shrink-0"
                                            >
                                                <Trash2Icon className="h-3.5 w-3.5" />
                                            </button>
                                        </div>
                                    ))
                                )}
                            </div>
                        </ScrollArea>
                    </div>
                </div>

                {/* Main Workspace Chat Area */}
                <div className="flex-1 flex flex-col h-full bg-white overflow-hidden">
                    <div className="border-b border-slate-200 py-3 px-6 bg-white shrink-0 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-blue-50 text-blue-700 rounded-lg border border-blue-100">
                                <MessageSquareIcon className="h-4 w-4" />
                            </div>
                            <div>
                                <h2 className="text-sm font-bold text-slate-900">Meeting Assistant</h2>
                                <span className="text-[11px] text-slate-500 font-medium">Query minutes, resolutions, and schedules</span>
                            </div>
                        </div>
                        <div className="flex items-center gap-2">
                            <Button variant="outline" size="sm" onClick={() => fileInputRef.current?.click()} className="text-xs h-8 border-slate-200 font-semibold rounded-lg bg-white shadow-2xs hover:bg-slate-50">
                                <UploadIcon className="h-3.5 w-3.5 mr-1.5 text-slate-600" />
                                Upload Reference File
                            </Button>
                            <input type="file" ref={fileInputRef} onChange={handleFileUpload} hidden />
                        </div>
                    </div>

                    <div className="flex-1 overflow-hidden relative bg-slate-50/20">
                        <ScrollArea className="h-full p-4 md:p-6" ref={scrollRef}>
                            <div className="max-w-4xl mx-auto space-y-6">
                                {messages.length === 0 && !isLoading && (
                                    <div className="flex flex-col items-center justify-center h-[50vh] text-center space-y-4">
                                        <div className="p-3 bg-blue-50 text-blue-600 rounded-xl border border-blue-100 shadow-2xs">
                                            <MessageSquareIcon className="h-7 w-7" />
                                        </div>
                                        <div className="space-y-1">
                                            <h2 className="text-base font-bold text-slate-900">Meeting Query Hub</h2>
                                            <p className="text-xs text-slate-500 max-w-sm">
                                                Ask questions about meeting agendas, decisions, or action items.
                                            </p>
                                        </div>
                                        <div className="grid grid-cols-2 gap-2 mt-4 max-w-md">
                                            {[
                                                "Summarize last meeting",
                                                "List all action items",
                                                "Show me the agenda",
                                                "Find decisions on resolution"
                                            ].map(q => (
                                                <Button 
                                                    key={q} 
                                                    variant="outline" 
                                                    className="text-xs h-auto py-2.5 border-slate-200 bg-white hover:bg-slate-50 hover:border-slate-300 text-slate-700 font-medium rounded-lg shadow-2xs" 
                                                    onClick={() => setInput(q)}
                                                >
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
                                            <Avatar className="h-7 w-7 mt-0.5 border border-slate-200 shadow-2xs">
                                                <AvatarFallback className={cn("text-[10px] font-bold", m.role === 'user' ? "bg-slate-950 text-white" : "bg-slate-100 text-slate-700")}>
                                                    {m.role === 'user' ? 'U' : 'A'}
                                                </AvatarFallback>
                                            </Avatar>
                                            <div className="space-y-2">
                                                <div className={cn(
                                                    "p-3.5 rounded-xl shadow-2xs text-xs leading-relaxed",
                                                    m.role === 'user'
                                                        ? "bg-slate-900 text-white rounded-tr-none"
                                                        : "bg-white text-slate-800 border border-slate-200 rounded-tl-none"
                                                )}>
                                                    <div className="whitespace-pre-wrap">{m.content}</div>
                                                </div>

                                                {m.sources && m.sources.length > 0 && (
                                                    <div className="flex flex-wrap gap-2 mt-2">
                                                        <span className="text-[10px] font-bold text-slate-400 uppercase mr-1 mt-1">Sources:</span>
                                                        {m.sources.map((s, idx) => (
                                                            <div key={idx} className="bg-slate-100 text-[10px] px-2 py-0.5 rounded-md text-slate-600 border border-slate-200 flex items-center gap-1">
                                                                <FileTextIcon className="h-3 w-3 text-slate-400" />
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
                                    <div className="flex gap-3 items-start">
                                        <Avatar className="h-7 w-7 border border-slate-200 shadow-2xs">
                                            <AvatarFallback className="text-[10px] font-bold bg-slate-100 text-slate-700">A</AvatarFallback>
                                        </Avatar>
                                        <div className="bg-white border border-slate-200 p-3.5 rounded-xl rounded-tl-none shadow-2xs space-y-1.5 w-32">
                                            <div className="h-2 w-full bg-slate-100 rounded animate-pulse"></div>
                                            <div className="h-2 w-2/3 bg-slate-100 rounded animate-pulse"></div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </ScrollArea>
                    </div>

                    <div className="p-4 bg-white border-t border-slate-200 shrink-0">
                        <div className="max-w-4xl mx-auto w-full relative">
                            <Input
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                                placeholder="Message meeting assistant..."
                                className="pr-12 h-11 rounded-lg border-slate-200 focus:border-slate-400 focus:ring-0 text-xs bg-slate-50/50 focus:bg-white transition-colors"
                            />
                            <Button
                                size="icon"
                                onClick={handleSendMessage}
                                disabled={!input.trim() || isLoading}
                                className={cn(
                                    "absolute right-1 top-1 h-9 w-9 rounded-md transition-colors shadow-none",
                                    input.trim() ? "bg-slate-900 hover:bg-slate-800 text-white" : "bg-slate-100 text-slate-400 pointer-events-none"
                                )}
                            >
                                <SendIcon className="h-4 w-4" />
                            </Button>
                        </div>
                    </div>
                </div>
            </div>
        </ProductDashboardLayout>
    );
};

export default MinutesChatbot;
