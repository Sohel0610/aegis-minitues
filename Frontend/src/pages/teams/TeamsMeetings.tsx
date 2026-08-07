import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useToast } from "@/components/ui/use-toast";
import ProductDashboardLayout from '@/components/layout/ProductDashboardLayout';
import { getMinutesNavItems } from '@/constants/minutesNavigation';
import {
  Video,
  Plus,
  Play,
  Square,
  FileText,
  Brain,
  BarChart3,
  Trash2,
  Eye,
  Upload,
  Loader2,
  Link as LinkIcon,
  Clock,
  Users,
  CheckCircle2,
  AlertCircle,
  BookOpen,
  ShieldCheck,
} from 'lucide-react';
import {
  Meeting,
  createMeeting,
  listMeetings,
  deleteMeeting,
  joinMeeting,
  leaveMeeting,
  fetchTranscript,
  uploadTranscript,
  generateMOM,
  analyzeMeeting,
} from '@/services/teamsService';

const statusConfig: Record<string, { label: string; color: string; icon: React.ReactNode }> = {
  pending:          { label: 'Pending',           color: 'bg-yellow-100 text-yellow-800', icon: <Clock className="h-3 w-3" /> },
  active:           { label: 'Bot Active',        color: 'bg-green-100 text-green-800',   icon: <Play className="h-3 w-3" /> },
  completed:        { label: 'Completed',         color: 'bg-blue-100 text-blue-800',     icon: <CheckCircle2 className="h-3 w-3" /> },
  transcript_ready: { label: 'Transcript Ready',  color: 'bg-purple-100 text-purple-800', icon: <FileText className="h-3 w-3" /> },
  mom_ready:        { label: 'MOM Ready',         color: 'bg-indigo-100 text-indigo-800', icon: <FileText className="h-3 w-3" /> },
  analyzed:         { label: 'Analyzed',          color: 'bg-emerald-100 text-emerald-800', icon: <Brain className="h-3 w-3" /> },
  failed:           { label: 'Failed',            color: 'bg-red-100 text-red-800',       icon: <AlertCircle className="h-3 w-3" /> },
};

export default function TeamsMeetings() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const navigationItems = getMinutesNavItems('teams');

  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [uploadMeetingId, setUploadMeetingId] = useState<string>('');
  const [newUrl, setNewUrl] = useState('');
  const [newTitle, setNewTitle] = useState('');
  const [vttContent, setVttContent] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [actionLoading, setActionLoading] = useState<Record<string, string>>({});

  const fetchMeetings = async () => {
    try {
      setIsLoading(true);
      const res = await listMeetings();
      setMeetings(res.data);
    } catch (err) {
      console.error('Failed to fetch meetings:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => { fetchMeetings(); }, []);

  const handleCreate = async () => {
    if (!newUrl.trim()) return;
    setSubmitting(true);
    try {
      await createMeeting(newUrl.trim(), newTitle.trim() || undefined);
      toast({ title: 'Meeting Created', description: 'Meeting record created successfully.' });
      setNewUrl('');
      setNewTitle('');
      setIsAddOpen(false);
      fetchMeetings();
    } catch (err: any) {
      toast({ title: 'Error', description: err.message, variant: 'destructive' });
    } finally {
      setSubmitting(false);
    }
  };

  const handleAction = async (meetingId: string, action: string) => {
    setActionLoading(prev => ({ ...prev, [meetingId]: action }));
    try {
      let result;
      switch (action) {
        case 'join':
          result = await joinMeeting(meetingId);
          toast({ title: result.success ? 'Bot Joined' : 'Join Failed', description: result.error || 'Bot is now in the meeting.', variant: result.success ? 'default' : 'destructive' });
          break;
        case 'leave':
          result = await leaveMeeting(meetingId);
          toast({ title: result.success ? 'Bot Left' : 'Leave Failed', description: result.error || 'Bot has left the meeting.' });
          break;
        case 'fetch-transcript':
          result = await fetchTranscript(meetingId);
          toast({ title: result.success ? 'Transcript Fetched' : 'Fetch Failed', description: result.error || `${result.segment_count || 0} segments retrieved.`, variant: result.success ? 'default' : 'destructive' });
          break;
        case 'generate-mom':
          result = await generateMOM(meetingId);
          toast({ title: result.success ? 'MOM Generated' : 'Generation Failed', description: result.error || 'AI MOM has been generated.', variant: result.success ? 'default' : 'destructive' });
          break;
        case 'analyze':
          result = await analyzeMeeting(meetingId);
          toast({ title: result.success ? 'Analysis Complete' : 'Analysis Failed', description: result.error || `${result.analysis_count || 0} insights generated.`, variant: result.success ? 'default' : 'destructive' });
          break;
        case 'delete':
          await deleteMeeting(meetingId);
          toast({ title: 'Deleted', description: 'Meeting record removed.' });
          break;
      }
      fetchMeetings();
    } catch (err: any) {
      toast({ title: 'Error', description: err.message, variant: 'destructive' });
    } finally {
      setActionLoading(prev => { const n = { ...prev }; delete n[meetingId]; return n; });
    }
  };

  const handleUploadVTT = async () => {
    if (!vttContent.trim() || !uploadMeetingId) return;
    setSubmitting(true);
    try {
      const result = await uploadTranscript(uploadMeetingId, vttContent.trim());
      toast({ title: result.success ? 'Transcript Uploaded' : 'Upload Failed', description: result.error || `${result.segment_count || 0} segments parsed.`, variant: result.success ? 'default' : 'destructive' });
      setVttContent('');
      setIsUploadOpen(false);
      fetchMeetings();
    } catch (err: any) {
      toast({ title: 'Error', description: err.message, variant: 'destructive' });
    } finally {
      setSubmitting(false);
    }
  };

  const getStatus = (status: string) => statusConfig[status] || statusConfig['pending'];

  const isActionLoading = (meetingId: string, action: string) => actionLoading[meetingId] === action;

  return (
    <ProductDashboardLayout
      productName="Minutes Generator"
      productRoute="/minutes-preparation"
      navigationItems={navigationItems}
    >
      <div className="p-6 md:p-8 space-y-6">
        {/* Header Banner */}
        <div className="rounded-2xl border border-blue-100 bg-gradient-to-r from-blue-50/70 via-indigo-50/40 to-white p-5 shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-start sm:items-center gap-3.5">
              <div className="rounded-xl bg-[#0066B3] p-3 text-white shadow-md shadow-blue-500/20">
                <Video className="h-6 w-6" />
              </div>
              <div>
                <div className="flex items-center gap-2.5">
                  <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Teams Meetings</h1>
                  <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200 text-xs font-semibold px-2.5 py-0.5">
                    Bot Integration
                  </Badge>
                </div>
                <p className="text-sm text-slate-500 mt-1">
                  Automated bot join, transcript retrieval, AI MOM generation & compliance insights
                </p>
              </div>
            </div>
            <Button onClick={() => setIsAddOpen(true)} className="bg-[#0066B3] hover:bg-[#0057B8] shadow-md shadow-blue-600/15 font-medium px-4">
              <Plus className="h-4 w-4 mr-2" /> Add Meeting Link
            </Button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card><CardContent className="pt-6"><div className="flex items-center gap-3"><Video className="h-8 w-8 text-blue-500" /><div><p className="text-2xl font-bold">{meetings.length}</p><p className="text-sm text-gray-500">Total Meetings</p></div></div></CardContent></Card>
          <Card><CardContent className="pt-6"><div className="flex items-center gap-3"><FileText className="h-8 w-8 text-purple-500" /><div><p className="text-2xl font-bold">{meetings.filter(m => ['transcript_ready', 'mom_ready', 'analyzed'].includes(m.status)).length}</p><p className="text-sm text-gray-500">Transcripts</p></div></div></CardContent></Card>
          <Card><CardContent className="pt-6"><div className="flex items-center gap-3"><FileText className="h-8 w-8 text-indigo-500" /><div><p className="text-2xl font-bold">{meetings.filter(m => ['mom_ready', 'analyzed'].includes(m.status)).length}</p><p className="text-sm text-gray-500">MOMs Generated</p></div></div></CardContent></Card>
          <Card><CardContent className="pt-6"><div className="flex items-center gap-3"><Brain className="h-8 w-8 text-emerald-500" /><div><p className="text-2xl font-bold">{meetings.filter(m => m.status === 'analyzed').length}</p><p className="text-sm text-gray-500">Analyzed</p></div></div></CardContent></Card>
        </div>

        {/* Meetings Table */}
        <Card>
          <CardHeader>
            <CardTitle>Meeting Records</CardTitle>
            <CardDescription>Click on a meeting row to view details, transcript, MOM, and insights.</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="flex justify-center py-12"><Loader2 className="h-8 w-8 animate-spin text-gray-400" /></div>
            ) : meetings.length === 0 ? (
              <div className="text-center py-12">
                <Video className="h-12 w-12 mx-auto text-gray-300 mb-4" />
                <p className="text-gray-500">No meetings yet. Click "Add Meeting" to get started.</p>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Title</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {meetings.map((m) => {
                    const st = getStatus(m.status);
                    return (
                      <TableRow key={m.id} className="cursor-pointer hover:bg-gray-50" onClick={() => navigate(`/minutes-preparation/teams/${m.id}`)}>
                        <TableCell>
                          <div>
                            <p className="font-medium">{m.title || 'Untitled Meeting'}</p>
                            <p className="text-xs text-gray-400 truncate max-w-[300px]">{m.meeting_url}</p>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge className={`${st.color} gap-1`}>{st.icon}{st.label}</Badge>
                        </TableCell>
                        <TableCell className="text-sm text-gray-500">
                          {new Date(m.created_at).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })}
                        </TableCell>
                        <TableCell className="text-right" onClick={(e) => e.stopPropagation()}>
                          <div className="flex items-center justify-end gap-1">
                            {m.status === 'pending' && (
                              <Button size="sm" variant="outline" onClick={() => handleAction(m.id, 'join')} disabled={!!actionLoading[m.id]}>
                                {isActionLoading(m.id, 'join') ? <Loader2 className="h-3 w-3 animate-spin" /> : <Play className="h-3 w-3" />}
                                <span className="ml-1 hidden sm:inline">Join</span>
                              </Button>
                            )}
                            {m.status === 'active' && (
                              <Button size="sm" variant="outline" onClick={() => handleAction(m.id, 'leave')} disabled={!!actionLoading[m.id]}>
                                {isActionLoading(m.id, 'leave') ? <Loader2 className="h-3 w-3 animate-spin" /> : <Square className="h-3 w-3" />}
                                <span className="ml-1 hidden sm:inline">Leave</span>
                              </Button>
                            )}
                            {['completed', 'pending'].includes(m.status) && (
                              <>
                                <Button size="sm" variant="outline" onClick={() => handleAction(m.id, 'fetch-transcript')} disabled={!!actionLoading[m.id]}>
                                  {isActionLoading(m.id, 'fetch-transcript') ? <Loader2 className="h-3 w-3 animate-spin" /> : <FileText className="h-3 w-3" />}
                                  <span className="ml-1 hidden sm:inline">Transcript</span>
                                </Button>
                                <Button size="sm" variant="outline" onClick={() => { setUploadMeetingId(m.id); setIsUploadOpen(true); }}>
                                  <Upload className="h-3 w-3" /><span className="ml-1 hidden sm:inline">Upload</span>
                                </Button>
                              </>
                            )}
                            {['transcript_ready', 'mom_ready', 'analyzed'].includes(m.status) && (
                              <Button size="sm" variant="outline" onClick={() => handleAction(m.id, 'generate-mom')} disabled={!!actionLoading[m.id]}>
                                {isActionLoading(m.id, 'generate-mom') ? <Loader2 className="h-3 w-3 animate-spin" /> : <FileText className="h-3 w-3" />}
                                <span className="ml-1 hidden sm:inline">MOM</span>
                              </Button>
                            )}
                            {['transcript_ready', 'mom_ready', 'analyzed'].includes(m.status) && (
                              <Button size="sm" variant="outline" onClick={() => handleAction(m.id, 'analyze')} disabled={!!actionLoading[m.id]}>
                                {isActionLoading(m.id, 'analyze') ? <Loader2 className="h-3 w-3 animate-spin" /> : <Brain className="h-3 w-3" />}
                                <span className="ml-1 hidden sm:inline">Analyze</span>
                              </Button>
                            )}
                            <Button size="sm" variant="ghost" className="text-red-500 hover:text-red-700" onClick={() => handleAction(m.id, 'delete')}>
                              <Trash2 className="h-3 w-3" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        {/* User Manual & Quick Guide Card for Non-Technical Users */}
        <Card className="border-blue-100 bg-gradient-to-r from-slate-50 via-blue-50/30 to-indigo-50/20 shadow-sm">
          <CardHeader className="border-b border-blue-100/60 pb-4">
            <div className="flex items-center gap-3">
              <div className="rounded-xl bg-[#0066B3]/10 p-2.5 text-[#0066B3]">
                <BookOpen className="h-5 w-5" />
              </div>
              <div>
                <CardTitle className="text-lg font-bold text-slate-800">User Manual — How MS Teams Integration Works</CardTitle>
                <CardDescription className="text-xs text-slate-500">
                  Step-by-step guide for non-technical users to manage meetings, transcripts, and AI MOMs
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="pt-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              
              {/* Step 1 */}
              <div className="rounded-xl border border-slate-200/80 bg-white p-4 space-y-2 shadow-2xs">
                <div className="flex items-center justify-between">
                  <span className="flex h-7 w-7 items-center justify-center rounded-full bg-blue-100 text-xs font-bold text-blue-700">1</span>
                  <LinkIcon className="h-4 w-4 text-blue-500" />
                </div>
                <h4 className="font-semibold text-sm text-slate-800">Add Teams Link</h4>
                <p className="text-xs text-slate-500 leading-relaxed">
                  Click <strong>"+ Add Meeting Link"</strong> and paste any Microsoft Teams meeting URL from your calendar or invite.
                </p>
              </div>

              {/* Step 2 */}
              <div className="rounded-xl border border-slate-200/80 bg-white p-4 space-y-2 shadow-2xs">
                <div className="flex items-center justify-between">
                  <span className="flex h-7 w-7 items-center justify-center rounded-full bg-purple-100 text-xs font-bold text-purple-700">2</span>
                  <Play className="h-4 w-4 text-purple-500" />
                </div>
                <h4 className="font-semibold text-sm text-slate-800">Bot & Transcript</h4>
                <p className="text-xs text-slate-500 leading-relaxed">
                  Click <strong>"Join"</strong> so the AI bot joins live, or click <strong>"Transcript"</strong> to fetch recorded transcripts post-meeting.
                </p>
              </div>

              {/* Step 3 */}
              <div className="rounded-xl border border-slate-200/80 bg-white p-4 space-y-2 shadow-2xs">
                <div className="flex items-center justify-between">
                  <span className="flex h-7 w-7 items-center justify-center rounded-full bg-indigo-100 text-xs font-bold text-indigo-700">3</span>
                  <FileText className="h-4 w-4 text-indigo-500" />
                </div>
                <h4 className="font-semibold text-sm text-slate-800">Generate AI MOM</h4>
                <p className="text-xs text-slate-500 leading-relaxed">
                  Click <strong>"MOM"</strong>. AI extracts attendees, agenda points, decisions, and action items with assignees & deadlines.
                </p>
              </div>

              {/* Step 4 */}
              <div className="rounded-xl border border-slate-200/80 bg-white p-4 space-y-2 shadow-2xs">
                <div className="flex items-center justify-between">
                  <span className="flex h-7 w-7 items-center justify-center rounded-full bg-emerald-100 text-xs font-bold text-emerald-700">4</span>
                  <Brain className="h-4 w-4 text-emerald-500" />
                </div>
                <h4 className="font-semibold text-sm text-slate-800">AI Risk & Insights</h4>
                <p className="text-xs text-slate-500 leading-relaxed">
                  Click <strong>"Analyze"</strong> to view speaker talk-time stats, meeting sentiment, risk flags, and topic distribution.
                </p>
              </div>

            </div>

            <div className="mt-4 rounded-lg bg-blue-50/60 p-3 text-xs text-blue-800 border border-blue-100 flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-blue-600 flex-shrink-0" />
              <span><strong>Quick Tip:</strong> Click on any meeting row in the table above to view the full transcript timeline, formatted MOM document, and visual insights dashboard!</span>
            </div>
          </CardContent>
        </Card>

        {/* Add Meeting Dialog */}
        <Dialog open={isAddOpen} onOpenChange={setIsAddOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add Teams Meeting</DialogTitle>
              <DialogDescription>Paste a Microsoft Teams meeting link to start tracking it.</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 pt-2">
              <div>
                <Label htmlFor="meeting-url">Teams Meeting URL *</Label>
                <Input id="meeting-url" placeholder="https://teams.microsoft.com/l/meetup-join/..." value={newUrl} onChange={(e) => setNewUrl(e.target.value)} />
              </div>
              <div>
                <Label htmlFor="meeting-title">Meeting Title (Optional)</Label>
                <Input id="meeting-title" placeholder="Q3 Board Review" value={newTitle} onChange={(e) => setNewTitle(e.target.value)} />
              </div>
              <Button onClick={handleCreate} disabled={submitting || !newUrl.trim()} className="w-full bg-[#0066B3] hover:bg-[#0057B8]">
                {submitting ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Plus className="h-4 w-4 mr-2" />}
                Create Meeting Record
              </Button>
            </div>
          </DialogContent>
        </Dialog>

        {/* Upload VTT Dialog */}
        <Dialog open={isUploadOpen} onOpenChange={setIsUploadOpen}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Upload VTT Transcript</DialogTitle>
              <DialogDescription>Paste VTT transcript content for manual testing without Graph API.</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 pt-2">
              <textarea
                className="w-full h-64 p-3 border rounded-md font-mono text-sm"
                placeholder={`WEBVTT\n\n00:00:01.000 --> 00:00:05.000\n<v John Doe>Hello everyone, welcome to the meeting.</v>\n\n00:00:06.000 --> 00:00:10.000\n<v Jane Smith>Thank you John, let's get started.</v>`}
                value={vttContent}
                onChange={(e) => setVttContent(e.target.value)}
              />
              <Button onClick={handleUploadVTT} disabled={submitting || !vttContent.trim()} className="w-full bg-[#0066B3] hover:bg-[#0057B8]">
                {submitting ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Upload className="h-4 w-4 mr-2" />}
                Upload & Parse Transcript
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </ProductDashboardLayout>
  );
}
