import { useEffect, useMemo, useRef, useState } from 'react';
import DOMPurify from 'dompurify';
import { marked } from 'marked';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Textarea } from '@/components/ui/textarea';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import {
  AlertTriangle,
  BotIcon,
  Building2,
  CalendarDays,
  CheckCircle2,
  ChevronRight,
  Database,
  Edit3,
  FileTextIcon,
  FileUp,
  History,
  LoaderCircle,
  Maximize2,
  MessageSquareIcon,
  Minimize2,
  PanelLeft,
  PanelLeftClose,
  PanelRight,
  PanelRightClose,
  PlusIcon,
  Save,
  SendIcon,
  ShieldCheck,
  Sparkles,
  Tag,
  UserIcon,
  Users,
  X,
} from 'lucide-react';
import ProductDashboardLayout from '@/components/layout/ProductDashboardLayout';
import { cn } from '@/lib/utils';
import { toast } from '@/components/ui/use-toast';
import { getMinutesNavItems } from '@/constants/minutesNavigation';

interface Source {
  document_id: number;
  document: string;
  chunk_index: number;
  location: string;
  excerpt: string;
  similarity: number;
}

interface Confidence {
  confidence: 'high' | 'medium' | 'low';
  reason: string;
  evidence_found: boolean;
  numerical_claims_verified: boolean;
  potential_conflicts: string[];
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  sources?: Source[];
  retrievalMode?: string;
  confidence?: Confidence;
  activity?: string[];
}

interface SessionInfo { id: string; title: string; }
interface ChatDocument {
  id: number;
  filename: string;
  file_type: string;
  file_size: number;
  upload_date: string;
  status: string;
  pages: number;
  extractor?: string;
  warnings?: string[];
  error?: string;
  meeting_title?: string | null;
  meeting_date?: string | null;
  meeting_type?: string | null;
  company_name?: string | null;
  key_topics?: string[];
  participants_count?: number;
  extraction_confidence?: string | null;
}

interface MeetingMetadataDetail {
  document_id: number;
  has_metadata: boolean;
  meeting_title?: string | null;
  meeting_date?: string | null;
  meeting_type?: string | null;
  company_name?: string | null;
  project_name?: string | null;
  participants?: { name: string; role: string }[];
  chairperson?: string | null;
  agenda_summary?: string | null;
  key_topics?: string[];
  key_decisions?: string[];
  action_items_summary?: { task: string; owner: string; deadline: string }[];
  meeting_summary?: string | null;
  extraction_confidence?: string | null;
  extracted_at?: string | null;
  user_edited?: string | null;
}

interface ChatbotStatus {
  status: string;
  environment: string;
  llm_provider: string;
  embedding_provider: string;
  document_processor: string;
}

const modeLabel: Record<string, string> = {
  hybrid_rag: 'Document search',
  agentic_rag: 'Multi-step analysis',
  structured_plus_rag: 'Structured records + documents',
};

const meetingTypeLabel: Record<string, string> = {
  board_meeting: 'Board Meeting',
  audit_committee: 'Audit Committee',
  nomination_remuneration_committee: 'NRC',
  stakeholder_relationship_committee: 'SRC',
  risk_management_committee: 'Risk Committee',
  csr_committee: 'CSR Committee',
  AGM: 'AGM',
  EGM: 'EGM',
  vendor_review: 'Vendor Review',
  project_review: 'Project Review',
  internal_review: 'Internal Review',
  committee_meeting: 'Committee Meeting',
  team_meeting: 'Team Meeting',
  standup: 'Standup',
  retrospective: 'Retrospective',
  townhall: 'Townhall',
  other: 'Other',
};

const formatBytes = (bytes: number) => bytes < 1024 * 1024
  ? `${Math.max(1, Math.round(bytes / 1024))} KB`
  : `${(bytes / (1024 * 1024)).toFixed(1)} MB`;

const renderMarkdown = (content: string) => DOMPurify.sanitize(marked.parse(content, { async: false }) as string);

const MinutesChatbot = () => {
  const navigationItems = getMinutesNavItems('chatbot');
  const [sessions, setSessions] = useState<SessionInfo[]>([]);
  const [documents, setDocuments] = useState<ChatDocument[]>([]);
  const [selectedDocumentIds, setSelectedDocumentIds] = useState<number[]>([]);
  const [activeSessionId, setActiveSessionId] = useState(`session_${Date.now()}`);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [chatStatus, setChatStatus] = useState<ChatbotStatus | null>(null);
  const [selectedSource, setSelectedSource] = useState<Source | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messageEndRef = useRef<HTMLDivElement>(null);

  const authHeaders = () => {
    const token = localStorage.getItem('aegis_auth_token');
    return token ? { Authorization: `Bearer ${token}` } : {};
  };

  const readyDocuments = useMemo(() => documents.filter((document) => document.status === 'ready'), [documents]);
  const selectedCount = selectedDocumentIds.length || readyDocuments.length;

  const fetchSessions = async () => {
    const response = await fetch('/api/minutes-chatbot/sessions', { headers: authHeaders() });
    if (!response.ok) throw new Error('Unable to load chat sessions');
    const data = await response.json();
    setSessions(data.sessions || []);
  };

  const fetchDocuments = async () => {
    const response = await fetch('/api/minutes-chatbot/documents', { headers: authHeaders() });
    if (!response.ok) throw new Error('Unable to load documents');
    const data: ChatDocument[] = await response.json();
    setDocuments(data);
    setSelectedDocumentIds((previous) => previous.filter((id) => data.some((document) => document.id === id && document.status === 'ready')));
  };

  const fetchStatus = async () => {
    const response = await fetch('/api/minutes-chatbot/status');
    if (response.ok) setChatStatus(await response.json());
  };

  const fetchHistory = async (sessionId: string) => {
    const response = await fetch(`/api/minutes-chatbot/history/${sessionId}`, { headers: authHeaders() });
    if (!response.ok) throw new Error('Unable to load chat history');
    const data = await response.json();
    if (Array.isArray(data)) {
      setMessages(data.map((item) => ({
        role: item.role,
        content: item.message,
        timestamp: item.timestamp,
        sources: item.metadata?.sources,
        retrievalMode: item.metadata?.retrieval_mode,
        confidence: item.metadata?.confidence,
      })));
    }
  };

  useEffect(() => {
    Promise.all([fetchSessions(), fetchDocuments(), fetchStatus()]).catch(() => {
      toast({ title: 'Connection issue', description: 'Some chatbot information could not be loaded.', variant: 'destructive' });
    });
  }, []);

  useEffect(() => {
    fetchHistory(activeSessionId).catch(() => setMessages([]));
  }, [activeSessionId]);

  useEffect(() => {
    messageEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages, isLoading]);

  const handleSendMessage = async () => {
    const query = input.trim();
    if (!query || isLoading) return;
    setMessages((previous) => [...previous, { role: 'user', content: query, timestamp: new Date().toISOString() }]);
    setInput('');
    setIsLoading(true);
    try {
      const response = await fetch('/api/minutes-chatbot/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify({ query, session_id: activeSessionId, document_ids: selectedDocumentIds }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Backend error');
      setMessages((previous) => [...previous, {
        role: 'assistant', content: data.answer, timestamp: new Date().toISOString(), sources: data.sources,
        retrievalMode: data.retrieval_mode, confidence: data.confidence, activity: data.activity,
      }]);
      if (!sessions.some((session) => session.id === activeSessionId)) {
        setSessions((previous) => [{ id: activeSessionId, title: query.slice(0, 48) + (query.length > 48 ? '…' : '') }, ...previous]);
      }
    } catch (error) {
      toast({ title: 'Chatbot request failed', description: error instanceof Error ? error.message : 'Please retry.', variant: 'destructive' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    try {
      const response = await fetch('/api/minutes-chatbot/upload', { method: 'POST', headers: authHeaders(), body: formData });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Upload failed');
      const meta = data.meeting_metadata;
      const metaDesc = meta?.meeting_title
        ? `${data.filename} indexed with ${data.chunks_indexed} sections. Meeting: ${meta.meeting_title}${meta.meeting_date ? ` (${meta.meeting_date})` : ''}${meta.meeting_type ? ` — ${meetingTypeLabel[meta.meeting_type] || meta.meeting_type}` : ''}`
        : `${data.filename} indexed with ${data.chunks_indexed} evidence sections.`;
      toast({ title: 'Document ready', description: metaDesc });
      if (data.warnings?.length) toast({ title: 'Extraction note', description: data.warnings.join(' '), variant: 'default' });
      await fetchDocuments();
      setSelectedDocumentIds((previous) => [...new Set([...previous, data.id])]);
    } catch (error) {
      toast({ title: 'Document could not be processed', description: error instanceof Error ? error.message : 'Upload failed.', variant: 'destructive' });
    } finally {
      setIsUploading(false);
      event.target.value = '';
    }
  };

  const [showScope, setShowScope] = useState(true);
  const [showHistory, setShowHistory] = useState(true);
  const [isMaximized, setIsMaximized] = useState(false);
  const [editingDoc, setEditingDoc] = useState<ChatDocument | null>(null);
  const [editMeta, setEditMeta] = useState<MeetingMetadataDetail | null>(null);
  const [isSavingMeta, setIsSavingMeta] = useState(false);

  const fetchMetadata = async (docId: number) => {
    try {
      const response = await fetch(`/api/minutes-chatbot/documents/${docId}/metadata`, { headers: authHeaders() });
      if (response.ok) {
        const data: MeetingMetadataDetail = await response.json();
        setEditMeta(data);
      }
    } catch {
      toast({ title: 'Could not load metadata', variant: 'destructive' });
    }
  };

  const handleEditDocument = (doc: ChatDocument) => {
    setEditingDoc(doc);
    fetchMetadata(doc.id);
  };

  const handleSaveMetadata = async () => {
    if (!editMeta || !editingDoc) return;
    setIsSavingMeta(true);
    try {
      const response = await fetch(`/api/minutes-chatbot/documents/${editingDoc.id}/metadata`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify({
          meeting_title: editMeta.meeting_title,
          meeting_date: editMeta.meeting_date,
          meeting_type: editMeta.meeting_type,
          company_name: editMeta.company_name,
          project_name: editMeta.project_name,
          chairperson: editMeta.chairperson,
          meeting_summary: editMeta.meeting_summary,
          key_topics: editMeta.key_topics,
          key_decisions: editMeta.key_decisions,
        }),
      });
      if (!response.ok) throw new Error('Save failed');
      toast({ title: 'Metadata updated', description: 'Meeting metadata saved successfully.' });
      await fetchDocuments();
      setEditingDoc(null);
      setEditMeta(null);
    } catch {
      toast({ title: 'Could not save metadata', variant: 'destructive' });
    } finally {
      setIsSavingMeta(false);
    }
  };

  const toggleDocument = (id: number) => setSelectedDocumentIds((previous) => previous.includes(id) ? previous.filter((item) => item !== id) : [...previous, id]);
  const toggleAllDocuments = () => setSelectedDocumentIds((previous) => previous.length ? [] : readyDocuments.map((document) => document.id));
  const startNewChat = () => { setActiveSessionId(`session_${Date.now()}`); setMessages([]); };  return (
    <ProductDashboardLayout productName="Meeting Assistant" productRoute="/minutes-preparation" navigationItems={navigationItems}>
      <div className="flex h-[calc(100vh-2rem)] gap-4 overflow-hidden p-4 md:p-5">
        {/* Card 1: Document Scope Sidebar */}
        <Card className={cn("w-80 shrink-0 flex-col border-slate-200 bg-white shadow-sm transition-all duration-300", showScope && !isMaximized ? "flex" : "hidden")}>
          <CardHeader className="space-y-3 border-b pb-4">
            <div className="flex items-center justify-between">
              <Button onClick={startNewChat} className="flex-1 bg-[#005da4] hover:bg-[#004a83]"><PlusIcon className="mr-2 h-4 w-4" />New chat</Button>
              <Button variant="ghost" size="icon" className="ml-1 h-8 w-8 text-slate-400 hover:text-slate-600" onClick={() => setShowScope(false)} title="Hide document scope">
                <PanelLeftClose className="h-4 w-4" />
              </Button>
            </div>
            <div className="flex items-center justify-between"><span className="text-xs font-semibold uppercase tracking-wide text-slate-500">Document scope</span><button onClick={toggleAllDocuments} className="text-xs font-medium text-[#005da4]">{selectedDocumentIds.length ? 'Use all' : 'Select all'}</button></div>
          </CardHeader>
          <CardContent className="min-h-0 flex-1 space-y-3 p-3">
            <Button variant="outline" onClick={() => fileInputRef.current?.click()} disabled={isUploading} className="w-full border-dashed text-[#005da4]">
              {isUploading ? <LoaderCircle className="mr-2 h-4 w-4 animate-spin" /> : <FileUp className="mr-2 h-4 w-4" />}{isUploading ? 'Processing document…' : 'Add documents'}
            </Button>
            <input ref={fileInputRef} onChange={handleFileUpload} accept=".pdf,.docx,.pptx,.xlsx,.txt,.json,.png,.jpg,.jpeg,.tif,.tiff" type="file" hidden />
            <ScrollArea className="h-[calc(100%-58px)]">
              <div className="space-y-2 pr-2">
                {documents.length === 0 && <p className="rounded-lg bg-slate-50 p-3 text-xs leading-relaxed text-slate-500">Add a PDF, Word, PowerPoint, Excel, image, or text file. Documents remain scoped to your account.</p>}
                {documents.map((document) => <label key={document.id} className={cn('block cursor-pointer rounded-lg border p-2.5 transition-colors', selectedDocumentIds.includes(document.id) ? 'border-blue-200 bg-blue-50' : 'border-slate-100 hover:bg-slate-50')}>
                  <div className="flex gap-2"><Checkbox checked={selectedDocumentIds.includes(document.id)} disabled={document.status !== 'ready'} onCheckedChange={() => toggleDocument(document.id)} /><div className="min-w-0 flex-1">
                    {document.meeting_title ? (
                      <div className="truncate text-xs font-semibold text-slate-800">{document.meeting_title}</div>
                    ) : (
                      <div className="truncate text-xs font-medium text-slate-700">{document.filename}</div>
                    )}
                    {document.meeting_title && <div className="truncate text-[10px] text-slate-500 mt-0.5">{document.filename}</div>}
                    <div className="mt-1 flex flex-wrap items-center gap-1 text-[10px] text-slate-500">
                      <FileTextIcon className="h-3 w-3" />{document.file_type?.toUpperCase()} · {formatBytes(document.file_size)}{document.pages ? ` · ${document.pages} pg` : ''}
                    </div>
                    {document.meeting_date && (
                      <div className="mt-1 flex items-center gap-1 text-[10px] text-slate-600">
                        <CalendarDays className="h-3 w-3 text-blue-500" />{document.meeting_date}
                        {document.meeting_type && <span className="ml-1 rounded-full bg-blue-50 px-1.5 py-0.5 text-[9px] font-medium text-blue-700">{meetingTypeLabel[document.meeting_type] || document.meeting_type}</span>}
                      </div>
                    )}
                    {document.company_name && (
                      <div className="mt-0.5 flex items-center gap-1 text-[10px] text-slate-500">
                        <Building2 className="h-3 w-3" />{document.company_name}
                      </div>
                    )}
                    {(document.key_topics?.length ?? 0) > 0 && (
                      <div className="mt-1 flex flex-wrap gap-1">
                        {document.key_topics!.slice(0, 3).map((topic, i) => (
                          <span key={i} className="rounded-full bg-slate-100 px-1.5 py-0.5 text-[9px] text-slate-600">{topic.length > 25 ? topic.slice(0, 25) + '…' : topic}</span>
                        ))}
                      </div>
                    )}
                    <div className="mt-1 flex items-center justify-between">
                      <div className={cn('text-[10px] font-medium', document.status === 'ready' ? 'text-emerald-600' : document.status === 'failed' ? 'text-red-600' : 'text-amber-600')}>{document.status === 'ready' ? 'Ready' : document.error || document.status}</div>
                      {document.status === 'ready' && (
                        <button onClick={(e) => { e.preventDefault(); e.stopPropagation(); handleEditDocument(document); }} className="flex items-center gap-0.5 text-[10px] text-[#005da4] hover:text-[#004a83]">
                          <Edit3 className="h-3 w-3" />Edit
                        </button>
                      )}
                    </div>
                  </div></div>
                </label>)}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Card 2: Recent Conversations History Sidebar */}
        <Card className={cn("w-64 shrink-0 flex-col border-slate-200 bg-white shadow-sm transition-all duration-300", showHistory && !isMaximized ? "flex" : "hidden")}>
          <CardHeader className="flex flex-row items-center justify-between border-b py-3">
            <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">Recent conversations</span>
            <Button variant="ghost" size="icon" className="h-7 w-7 text-slate-400 hover:text-slate-600" onClick={() => setShowHistory(false)} title="Hide history">
              <PanelRightClose className="h-4 w-4" />
            </Button>
          </CardHeader>
          <CardContent className="min-h-0 flex-1 p-2"><ScrollArea className="h-full">{sessions.map((session) => <button key={session.id} onClick={() => setActiveSessionId(session.id)} className={cn('mb-1 flex w-full items-center gap-2 rounded-md px-2.5 py-2 text-left text-xs', activeSessionId === session.id ? 'bg-blue-50 font-medium text-[#005da4]' : 'text-slate-600 hover:bg-slate-50')}><MessageSquareIcon className="h-3.5 w-3.5 shrink-0" /><span className="truncate">{session.title}</span></button>)}</ScrollArea></CardContent>
        </Card>

        {/* Card 3: Aegis Intelligence Workspace Main Chat */}
        <Card className="min-w-0 flex flex-1 flex-col overflow-hidden border-slate-200 bg-slate-50/50 shadow-sm">
          <CardHeader className="shrink-0 border-b bg-white py-3 px-4">
            <div className="flex items-center justify-between gap-3">
              <div className="flex min-w-0 items-center gap-3">
                <div className="rounded-xl bg-[#e7f3fb] p-2 shrink-0">
                  <Sparkles className="h-5 w-5 text-[#005da4]" />
                </div>
                <div className="min-w-0">
                  <CardTitle className="text-base font-semibold text-slate-800 truncate">
                    Aegis Intelligence Workspace
                  </CardTitle>
                </div>
              </div>
              
              {/* Workspace UI Controls */}
              <div className="flex items-center gap-1 shrink-0">
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => setShowScope(!showScope)}
                  title={showScope && !isMaximized ? "Hide Scope" : "Show Scope"}
                  className="h-8 w-8 text-slate-700 border-slate-200 hover:bg-blue-50 hover:text-[#005da4]"
                >
                  {showScope && !isMaximized ? <PanelLeftClose className="h-4 w-4 text-[#005da4]" /> : <PanelLeft className="h-4 w-4 text-[#005da4]" />}
                </Button>

                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => setShowHistory(!showHistory)}
                  title={showHistory && !isMaximized ? "Hide History" : "Show History"}
                  className="h-8 w-8 text-slate-700 border-slate-200 hover:bg-blue-50 hover:text-[#005da4]"
                >
                  {showHistory && !isMaximized ? <PanelRightClose className="h-4 w-4 text-[#005da4]" /> : <History className="h-4 w-4 text-[#005da4]" />}
                </Button>

                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => setIsMaximized(!isMaximized)}
                  title={isMaximized ? "Restore view" : "Maximize view"}
                  className="h-8 w-8 text-slate-700 border-slate-200 hover:bg-blue-50 hover:text-[#005da4]"
                >
                  {isMaximized ? <Minimize2 className="h-4 w-4 text-[#005da4]" /> : <Maximize2 className="h-4 w-4 text-[#005da4]" />}
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent className="min-h-0 flex-1 overflow-hidden p-0 flex flex-col">
            <ScrollArea className="h-full flex-1">
              <div className="mx-auto max-w-4xl space-y-6 p-4 md:p-6 min-h-full flex flex-col justify-center">
                {messages.length === 0 && !isLoading && (
                  <div className="flex flex-1 flex-col items-center justify-center text-center my-auto py-6">
                    <div className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-100/80">
                      <BotIcon className="h-10 w-10 text-[#005da4]" />
                    </div>
                    <h2 className="mt-5 text-2xl font-semibold text-slate-800">Ask your documents, not your memory.</h2>
                    <p className="mt-2.5 max-w-xl text-sm leading-relaxed text-slate-500">
                      Use financial packs, board materials, meeting minutes, PowerPoint files, and spreadsheets. The assistant plans the search, verifies evidence, and clearly states limits.
                    </p>
                  </div>
                )}
                {messages.map((message, index) => (
                  <div key={`${message.timestamp}-${index}`} className={cn('flex', message.role === 'user' ? 'justify-end' : 'justify-start')}>
                    <div className={cn('flex max-w-[94%] gap-3 md:max-w-[86%]', message.role === 'user' && 'flex-row-reverse')}>
                      <Avatar className="mt-1 h-8 w-8 border border-slate-100">
                        <AvatarFallback className={message.role === 'user' ? 'bg-[#005da4] text-white' : 'bg-[#e7f3fb] text-[#005da4]'}>
                          {message.role === 'user' ? <UserIcon className="h-4 w-4" /> : <BotIcon className="h-4 w-4" />}
                        </AvatarFallback>
                      </Avatar>
                      <div className="min-w-0 space-y-2">
                        <div className={cn('rounded-2xl px-4 py-3 text-sm leading-6 shadow-sm', message.role === 'user' ? 'rounded-tr-sm bg-[#005da4] text-white' : 'rounded-tl-sm border border-slate-100 bg-white text-slate-700')}>
                          {message.role === 'assistant' ? <div className="aegis-chat-markdown" dangerouslySetInnerHTML={{ __html: renderMarkdown(message.content) }} /> : <div className="whitespace-pre-wrap">{message.content}</div>}
                        </div>
                        {message.role === 'assistant' && (
                          <div className="flex flex-wrap items-center gap-2 text-[10px]">
                            {message.retrievalMode && <span className="rounded-full bg-blue-50 px-2 py-1 font-medium text-[#005da4]">{modeLabel[message.retrievalMode] || 'Evidence search'}</span>}
                            {message.confidence && <span title={message.confidence.reason} className={cn('rounded-full px-2 py-1 font-medium', message.confidence.confidence === 'high' ? 'bg-emerald-50 text-emerald-700' : message.confidence.confidence === 'medium' ? 'bg-amber-50 text-amber-700' : 'bg-slate-100 text-slate-600')}>{message.confidence.confidence} confidence</span>}
                            {message.confidence?.potential_conflicts?.length ? <span className="flex items-center gap-1 text-amber-700"><AlertTriangle className="h-3 w-3" />Evidence needs review</span> : null}
                          </div>
                        )}
                        {message.sources?.length ? (
                          <div className="flex flex-wrap items-center gap-1.5">
                            <span className="mr-1 text-[10px] font-semibold uppercase tracking-wide text-slate-400">Evidence</span>
                            {message.sources.map((source) => (
                              <button key={`${source.document_id}-${source.chunk_index}`} onClick={() => setSelectedSource(source)} className="flex items-center gap-1 rounded-full border border-slate-200 bg-white px-2 py-1 text-[10px] text-slate-600 hover:border-blue-200 hover:text-[#005da4]">
                                <FileTextIcon className="h-3 w-3" />{source.document} · {source.location}
                              </button>
                            ))}
                          </div>
                        ) : null}
                      </div>
                    </div>
                  </div>
                ))}
                {isLoading && (
                  <div className="flex gap-3">
                    <div className="mt-1 rounded-full bg-[#e7f3fb] p-2">
                      <LoaderCircle className="h-4 w-4 animate-spin text-[#005da4]" />
                    </div>
                    <div className="rounded-2xl rounded-tl-sm border border-slate-100 bg-white px-4 py-3 text-xs text-slate-500">
                      <div className="flex items-center gap-2">
                        <Database className="h-3.5 w-3.5 text-[#005da4]" />Understanding request and checking evidence…
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messageEndRef} />
              </div>
            </ScrollArea>
          </CardContent>
          <CardFooter className="shrink-0 border-t bg-white p-3 md:p-4">
            <div className="mx-auto w-full max-w-4xl space-y-2">
              <div className="rounded-xl border border-slate-200 bg-white p-2.5 shadow-sm transition-all focus-within:border-[#005da4] focus-within:ring-2 focus-within:ring-blue-100">
                <Textarea
                  value={input}
                  onChange={(event) => setInput(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter' && !event.shiftKey) {
                      event.preventDefault();
                      handleSendMessage();
                    }
                  }}
                  placeholder="Ask about the selected documents or meeting minutes..."
                  className="min-h-[52px] max-h-[160px] resize-none border-0 bg-transparent p-1.5 text-sm text-slate-800 placeholder:text-slate-400 focus-visible:ring-0"
                />
                <div className="flex items-center justify-between gap-2 border-t border-slate-100 pt-2 px-1">
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => fileInputRef.current?.click()}
                      disabled={isUploading}
                      className="h-7 gap-1.5 px-2.5 text-xs font-medium text-[#005da4] border-slate-200 hover:bg-blue-50 hover:border-blue-300"
                    >
                      {isUploading ? (
                        <LoaderCircle className="h-3.5 w-3.5 animate-spin" />
                      ) : (
                        <FileUp className="h-3.5 w-3.5" />
                      )}
                      <span>{isUploading ? 'Uploading...' : 'Upload Document'}</span>
                    </Button>
                  </div>
                  <div className="ml-auto flex items-center gap-3">
                    <Button
                      onClick={handleSendMessage}
                      disabled={!input.trim() || isLoading}
                      size="sm"
                      className="bg-[#005da4] hover:bg-[#004a83] font-medium px-4 shadow-sm"
                    >
                      <SendIcon className="mr-1.5 h-3.5 w-3.5" /> Send
                    </Button>
                  </div>
                </div>
              </div>
              <p className="flex items-center gap-1 text-[10px] text-slate-400 px-1">
                <ShieldCheck className="h-3 w-3 text-emerald-600" /> Answers are limited to selected evidence and permitted structured records.
              </p>
            </div>
          </CardFooter>
        </Card>
      </div>
      <Dialog open={Boolean(selectedSource)} onOpenChange={(open) => !open && setSelectedSource(null)}><DialogContent className="max-w-2xl"><DialogHeader><DialogTitle className="pr-8 text-base">{selectedSource?.document}</DialogTitle></DialogHeader>{selectedSource && <div className="space-y-3"><div className="flex items-center gap-2 text-xs text-slate-500"><FileTextIcon className="h-4 w-4 text-[#005da4]" />{selectedSource.location} · Evidence relevance {Math.round(selectedSource.similarity * 100)}%</div><div className="max-h-72 overflow-auto rounded-lg bg-slate-50 p-3 text-sm leading-6 text-slate-700">{selectedSource.excerpt}</div><p className="text-xs text-slate-500">This excerpt is the evidence used for the answer. Full document preview can be added when Blob/document-view access is approved.</p></div>}</DialogContent></Dialog>

      {/* Meeting Metadata Edit Dialog */}
      <Dialog open={Boolean(editingDoc)} onOpenChange={(open) => { if (!open) { setEditingDoc(null); setEditMeta(null); } }}>
        <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-base">
              <Edit3 className="h-4 w-4 text-[#005da4]" />
              Meeting Metadata — {editingDoc?.filename}
            </DialogTitle>
          </DialogHeader>
          {editMeta ? (
            <div className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="mb-1 block text-xs font-medium text-slate-600">Meeting Title</label>
                  <input
                    type="text"
                    value={editMeta.meeting_title || ''}
                    onChange={(e) => setEditMeta({ ...editMeta, meeting_title: e.target.value })}
                    className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm focus:border-[#005da4] focus:ring-1 focus:ring-blue-100 focus:outline-none"
                    placeholder="e.g. Q2 Board Review"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-medium text-slate-600">Meeting Date</label>
                  <input
                    type="date"
                    value={editMeta.meeting_date || ''}
                    onChange={(e) => setEditMeta({ ...editMeta, meeting_date: e.target.value })}
                    className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm focus:border-[#005da4] focus:ring-1 focus:ring-blue-100 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-medium text-slate-600">Meeting Type</label>
                  <select
                    value={editMeta.meeting_type || ''}
                    onChange={(e) => setEditMeta({ ...editMeta, meeting_type: e.target.value })}
                    className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm focus:border-[#005da4] focus:ring-1 focus:ring-blue-100 focus:outline-none"
                  >
                    <option value="">— Select —</option>
                    {Object.entries(meetingTypeLabel).map(([key, label]) => (
                      <option key={key} value={key}>{label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="mb-1 block text-xs font-medium text-slate-600">Company / Organisation</label>
                  <input
                    type="text"
                    value={editMeta.company_name || ''}
                    onChange={(e) => setEditMeta({ ...editMeta, company_name: e.target.value })}
                    className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm focus:border-[#005da4] focus:ring-1 focus:ring-blue-100 focus:outline-none"
                    placeholder="e.g. Adani Enterprises"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-medium text-slate-600">Project / Initiative</label>
                  <input
                    type="text"
                    value={editMeta.project_name || ''}
                    onChange={(e) => setEditMeta({ ...editMeta, project_name: e.target.value })}
                    className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm focus:border-[#005da4] focus:ring-1 focus:ring-blue-100 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-medium text-slate-600">Chairperson</label>
                  <input
                    type="text"
                    value={editMeta.chairperson || ''}
                    onChange={(e) => setEditMeta({ ...editMeta, chairperson: e.target.value })}
                    className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm focus:border-[#005da4] focus:ring-1 focus:ring-blue-100 focus:outline-none"
                  />
                </div>
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-600">Key Topics (comma-separated)</label>
                <input
                  type="text"
                  value={(editMeta.key_topics || []).join(', ')}
                  onChange={(e) => setEditMeta({ ...editMeta, key_topics: e.target.value.split(',').map(t => t.trim()).filter(Boolean) })}
                  className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm focus:border-[#005da4] focus:ring-1 focus:ring-blue-100 focus:outline-none"
                  placeholder="vendor pricing, compliance audit, Q2 budget"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-600">Key Decisions (comma-separated)</label>
                <input
                  type="text"
                  value={(editMeta.key_decisions || []).join(', ')}
                  onChange={(e) => setEditMeta({ ...editMeta, key_decisions: e.target.value.split(',').map(t => t.trim()).filter(Boolean) })}
                  className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm focus:border-[#005da4] focus:ring-1 focus:ring-blue-100 focus:outline-none"
                  placeholder="Approved Q2 budget, Deferred vendor contract"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-600">Meeting Summary</label>
                <Textarea
                  value={editMeta.meeting_summary || ''}
                  onChange={(e) => setEditMeta({ ...editMeta, meeting_summary: e.target.value })}
                  className="min-h-[80px] text-sm"
                  placeholder="AI-generated or manual summary of this meeting…"
                />
              </div>
              {(editMeta.participants?.length ?? 0) > 0 && (
                <div>
                  <label className="mb-1 block text-xs font-medium text-slate-600">Participants ({editMeta.participants!.length})</label>
                  <div className="flex flex-wrap gap-1.5">
                    {editMeta.participants!.map((p, i) => (
                      <span key={i} className="rounded-full bg-slate-100 px-2 py-1 text-[10px] text-slate-600">
                        <Users className="mr-1 inline h-3 w-3" />{p.name}{p.role ? ` (${p.role})` : ''}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {editMeta.extraction_confidence && (
                <div className="flex items-center gap-2 text-[10px] text-slate-500">
                  <Tag className="h-3 w-3" />
                  Extraction: {editMeta.extraction_confidence}
                  {editMeta.user_edited && ` · Last edited: ${new Date(editMeta.user_edited).toLocaleDateString()}`}
                </div>
              )}
              <div className="flex justify-end gap-2 pt-2 border-t">
                <Button variant="outline" size="sm" onClick={() => { setEditingDoc(null); setEditMeta(null); }}>
                  <X className="mr-1 h-3.5 w-3.5" />Cancel
                </Button>
                <Button size="sm" onClick={handleSaveMetadata} disabled={isSavingMeta} className="bg-[#005da4] hover:bg-[#004a83]">
                  {isSavingMeta ? <LoaderCircle className="mr-1 h-3.5 w-3.5 animate-spin" /> : <Save className="mr-1 h-3.5 w-3.5" />}
                  Save Metadata
                </Button>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center py-8">
              <LoaderCircle className="h-6 w-6 animate-spin text-[#005da4]" />
            </div>
          )}
        </DialogContent>
      </Dialog>
    </ProductDashboardLayout>
  );
};

export default MinutesChatbot;
