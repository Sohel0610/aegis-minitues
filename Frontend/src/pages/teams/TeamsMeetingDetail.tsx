import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useToast } from "@/components/ui/use-toast";
import ProductDashboardLayout from '@/components/layout/ProductDashboardLayout';
import { getMinutesNavItems } from '@/constants/minutesNavigation';
import {
  ArrowLeft,
  FileText,
  Brain,
  BarChart3,
  Clock,
  Users,
  CheckCircle2,
  Loader2,
  Download,
  Play,
  MessageSquare,
  Target,
  AlertTriangle,
  TrendingUp,
  User,
} from 'lucide-react';
import {
  getMeeting,
  getTranscript,
  getMOM,
  getInsights,
  generateMOM,
  analyzeMeeting,
  fetchTranscript,
  MeetingDetail,
  TranscriptData,
  MOMResponse,
  InsightsListResponse,
} from '@/services/teamsService';

export default function TeamsMeetingDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const navigationItems = getMinutesNavItems('teams');

  const [meeting, setMeeting] = useState<MeetingDetail | null>(null);
  const [transcript, setTranscript] = useState<TranscriptData | null>(null);
  const [mom, setMOM] = useState<MOMResponse | null>(null);
  const [insights, setInsights] = useState<InsightsListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState('');

  const loadData = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const meetingData = await getMeeting(id);
      setMeeting(meetingData);

      // Load transcript if available
      if (meetingData.has_transcript) {
        try { const t = await getTranscript(id); setTranscript(t); } catch { /* not available */ }
      }
      // Load MOM if available
      if (meetingData.has_mom) {
        try { const m = await getMOM(id); setMOM(m); } catch { /* not available */ }
      }
      // Load insights
      if (meetingData.insight_count > 0) {
        try { const i = await getInsights(id); setInsights(i); } catch { /* not available */ }
      }
    } catch (err) {
      toast({ title: 'Error', description: 'Failed to load meeting data.', variant: 'destructive' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, [id]);

  const handleGenerateMOM = async () => {
    if (!id) return;
    setActionLoading('mom');
    try {
      const result = await generateMOM(id);
      toast({ title: result.success ? 'MOM Generated' : 'Failed', description: result.error || 'AI MOM has been generated.' });
      loadData();
    } catch (err: any) {
      toast({ title: 'Error', description: err.message, variant: 'destructive' });
    } finally {
      setActionLoading('');
    }
  };

  const handleAnalyze = async () => {
    if (!id) return;
    setActionLoading('analyze');
    try {
      const result = await analyzeMeeting(id);
      toast({ title: result.success ? 'Analysis Complete' : 'Failed', description: result.error || `${result.analysis_count} insights generated.` });
      loadData();
    } catch (err: any) {
      toast({ title: 'Error', description: err.message, variant: 'destructive' });
    } finally {
      setActionLoading('');
    }
  };

  const handleFetchTranscript = async () => {
    if (!id) return;
    setActionLoading('transcript');
    try {
      const result = await fetchTranscript(id);
      toast({ title: result.success ? 'Transcript Fetched' : 'Failed', description: result.error || 'Transcript retrieved from Graph API.' });
      loadData();
    } catch (err: any) {
      toast({ title: 'Error', description: err.message, variant: 'destructive' });
    } finally {
      setActionLoading('');
    }
  };

  if (loading) {
    return (
      <ProductDashboardLayout productName="Minutes Generator" productRoute="/minutes-preparation" navigationItems={navigationItems}>
        <div className="flex justify-center items-center h-64"><Loader2 className="h-8 w-8 animate-spin text-gray-400" /></div>
      </ProductDashboardLayout>
    );
  }

  if (!meeting) {
    return (
      <ProductDashboardLayout productName="Minutes Generator" productRoute="/minutes-preparation" navigationItems={navigationItems}>
        <div className="text-center py-12"><p className="text-gray-500">Meeting not found.</p></div>
      </ProductDashboardLayout>
    );
  }

  const m = meeting.meeting;

  return (
    <ProductDashboardLayout productName="Minutes Generator" productRoute="/minutes-preparation" navigationItems={navigationItems}>
      <div className="p-6 md:p-8 space-y-6">
        {/* Header Banner */}
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-start gap-3.5">
              <Button variant="outline" size="sm" onClick={() => navigate('/minutes-preparation/teams')} className="mt-1 h-9 px-3 border-slate-200 text-slate-700 hover:bg-slate-50">
                <ArrowLeft className="h-4 w-4 mr-1.5" /> Back
              </Button>
              <div>
                <div className="flex items-center gap-2.5 flex-wrap">
                  <h1 className="text-2xl font-bold text-slate-900 tracking-tight">{m.title || 'Untitled Meeting'}</h1>
                  <Badge className="bg-blue-50 text-blue-700 border-blue-200 text-xs font-semibold px-2.5 py-0.5 capitalize">
                    {m.status.replace('_', ' ')}
                  </Badge>
                </div>
                <p className="text-xs text-slate-400 mt-1 truncate max-w-xl flex items-center gap-1.5">
                  <Video className="h-3.5 w-3.5 text-blue-600 flex-shrink-0" />
                  <a href={m.meeting_url} target="_blank" rel="noopener noreferrer" className="hover:text-blue-600 hover:underline truncate">
                    {m.meeting_url}
                  </a>
                </p>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center gap-2.5 flex-wrap">
              {!meeting.has_transcript && (
                <Button onClick={handleFetchTranscript} disabled={!!actionLoading} className="bg-[#0066B3] hover:bg-[#0057B8] font-medium shadow-sm">
                  {actionLoading === 'transcript' ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <FileText className="h-4 w-4 mr-2" />}
                  Fetch Transcript
                </Button>
              )}
              {meeting.has_transcript && (
                <Button onClick={handleGenerateMOM} disabled={!!actionLoading} className="bg-indigo-600 hover:bg-indigo-700 font-medium shadow-sm">
                  {actionLoading === 'mom' ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <FileText className="h-4 w-4 mr-2" />}
                  {meeting.has_mom ? 'Regenerate MOM' : 'Generate MOM'}
                </Button>
              )}
              {meeting.has_transcript && (
                <Button onClick={handleAnalyze} disabled={!!actionLoading} className="bg-emerald-600 hover:bg-emerald-700 font-medium shadow-sm">
                  {actionLoading === 'analyze' ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Brain className="h-4 w-4 mr-2" />}
                  {meeting.insight_count > 0 ? 'Re-Analyze' : 'Run AI Analysis'}
                </Button>
              )}
            </div>
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card><CardContent className="pt-6"><div className="flex items-center gap-3"><Clock className="h-6 w-6 text-blue-500" /><div><p className="text-sm text-gray-500">Status</p><p className="font-semibold capitalize">{m.status.replace('_', ' ')}</p></div></div></CardContent></Card>
          <Card><CardContent className="pt-6"><div className="flex items-center gap-3"><Users className="h-6 w-6 text-purple-500" /><div><p className="text-sm text-gray-500">Participants</p><p className="font-semibold">{transcript?.participant_count || 0}</p></div></div></CardContent></Card>
          <Card><CardContent className="pt-6"><div className="flex items-center gap-3"><Clock className="h-6 w-6 text-indigo-500" /><div><p className="text-sm text-gray-500">Duration</p><p className="font-semibold">{transcript?.duration_minutes ? `${transcript.duration_minutes} min` : 'N/A'}</p></div></div></CardContent></Card>
          <Card><CardContent className="pt-6"><div className="flex items-center gap-3"><Brain className="h-6 w-6 text-emerald-500" /><div><p className="text-sm text-gray-500">Insights</p><p className="font-semibold">{meeting.insight_count}</p></div></div></CardContent></Card>
        </div>

        {/* Tabbed Content */}
        <Tabs defaultValue={meeting.has_transcript ? "transcript" : "info"} className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="info">Info</TabsTrigger>
            <TabsTrigger value="transcript" disabled={!meeting.has_transcript}>Transcript</TabsTrigger>
            <TabsTrigger value="mom" disabled={!meeting.has_mom}>MOM</TabsTrigger>
            <TabsTrigger value="insights" disabled={meeting.insight_count === 0}>Insights</TabsTrigger>
          </TabsList>

          {/* Info Tab */}
          <TabsContent value="info">
            <Card>
              <CardHeader><CardTitle>Meeting Information</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                <div className="grid grid-cols-2 gap-4">
                  <div><p className="text-sm text-gray-500">Title</p><p className="font-medium">{m.title || 'Untitled'}</p></div>
                  <div><p className="text-sm text-gray-500">Status</p><p className="font-medium capitalize">{m.status.replace('_', ' ')}</p></div>
                  <div><p className="text-sm text-gray-500">Created</p><p className="font-medium">{new Date(m.created_at).toLocaleString('en-IN')}</p></div>
                  <div><p className="text-sm text-gray-500">Call ID</p><p className="font-medium text-sm">{m.call_id || 'N/A'}</p></div>
                </div>
                <div><p className="text-sm text-gray-500">Meeting URL</p><a href={m.meeting_url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline text-sm break-all">{m.meeting_url}</a></div>
                {transcript?.participants && transcript.participants.length > 0 && (
                  <div>
                    <p className="text-sm text-gray-500 mb-2">Participants</p>
                    <div className="flex flex-wrap gap-2">
                      {transcript.participants.map((p, i) => (
                        <Badge key={i} variant="outline" className="gap-1"><User className="h-3 w-3" />{p}</Badge>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Transcript Tab */}
          <TabsContent value="transcript">
            <Card>
              <CardHeader>
                <CardTitle>Meeting Transcript</CardTitle>
                <CardDescription>{transcript?.participant_count || 0} participants • {transcript?.duration_minutes || 0} minutes</CardDescription>
              </CardHeader>
              <CardContent>
                {transcript?.structured_json && Array.isArray(transcript.structured_json) ? (
                  <div className="space-y-3 max-h-[600px] overflow-y-auto pr-2">
                    {transcript.structured_json.map((seg, idx) => (
                      <div key={idx} className="flex gap-3 p-3 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors">
                        <div className="flex-shrink-0 w-20 text-xs text-gray-400 pt-1 font-mono">{seg.start_time?.substring(0, 8)}</div>
                        <div className="flex-1">
                          <p className="text-sm font-semibold text-blue-700">{seg.speaker}</p>
                          <p className="text-sm text-gray-700">{seg.text}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <pre className="whitespace-pre-wrap text-sm bg-gray-50 p-4 rounded-lg max-h-[600px] overflow-y-auto">{transcript?.full_text || 'No transcript content available.'}</pre>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* MOM Tab */}
          <TabsContent value="mom">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Minutes of Meeting</CardTitle>
                    <CardDescription>AI-generated from transcript • Version {mom?.version || 1}</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {mom?.mom_json ? (
                  <div className="space-y-6">
                    {/* Meeting Info */}
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4 p-4 bg-blue-50 rounded-lg">
                      <div><p className="text-xs text-gray-500">Title</p><p className="font-medium text-sm">{(mom.mom_json as any).meeting_title || 'N/A'}</p></div>
                      <div><p className="text-xs text-gray-500">Date</p><p className="font-medium text-sm">{(mom.mom_json as any).meeting_date || 'N/A'}</p></div>
                      <div><p className="text-xs text-gray-500">Duration</p><p className="font-medium text-sm">{(mom.mom_json as any).meeting_duration || 'N/A'}</p></div>
                    </div>

                    {/* Attendees */}
                    {(mom.mom_json as any).attendees?.length > 0 && (
                      <div>
                        <h3 className="font-semibold text-gray-800 mb-2 flex items-center gap-2"><Users className="h-4 w-4" /> Attendees</h3>
                        <div className="flex flex-wrap gap-2">
                          {(mom.mom_json as any).attendees.map((a: string, i: number) => (
                            <Badge key={i} variant="outline">{a}</Badge>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Agenda Items */}
                    {(mom.mom_json as any).agenda_items?.length > 0 && (
                      <div className="space-y-4">
                        <h3 className="font-semibold text-gray-800 flex items-center gap-2"><MessageSquare className="h-4 w-4" /> Agenda & Discussion</h3>
                        {(mom.mom_json as any).agenda_items.map((item: any, idx: number) => (
                          <Card key={idx} className="border-l-4 border-l-blue-500">
                            <CardContent className="pt-4 space-y-3">
                              <h4 className="font-semibold">{idx + 1}. {item.topic}</h4>
                              <p className="text-sm text-gray-600">{item.discussion_summary}</p>
                              {item.decisions?.length > 0 && (
                                <div>
                                  <p className="text-sm font-medium text-green-700 mb-1">✅ Decisions:</p>
                                  <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                                    {item.decisions.map((d: string, i: number) => <li key={i}>{d}</li>)}
                                  </ul>
                                </div>
                              )}
                              {item.action_items?.length > 0 && (
                                <div>
                                  <p className="text-sm font-medium text-orange-700 mb-1">📋 Action Items:</p>
                                  <div className="space-y-2">
                                    {item.action_items.map((a: any, i: number) => (
                                      <div key={i} className="flex items-center gap-3 bg-orange-50 p-2 rounded text-sm">
                                        <Target className="h-4 w-4 text-orange-500 flex-shrink-0" />
                                        <span className="flex-1">{a.task}</span>
                                        <Badge variant="outline" className="text-xs">{a.assignee}</Badge>
                                        <span className="text-xs text-gray-400">{a.deadline}</span>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    )}

                    {/* Key Highlights */}
                    {(mom.mom_json as any).key_highlights?.length > 0 && (
                      <div>
                        <h3 className="font-semibold text-gray-800 mb-2 flex items-center gap-2"><TrendingUp className="h-4 w-4" /> Key Highlights</h3>
                        <ul className="space-y-1">
                          {(mom.mom_json as any).key_highlights.map((h: string, i: number) => (
                            <li key={i} className="text-sm text-gray-600 flex items-start gap-2"><CheckCircle2 className="h-4 w-4 text-green-500 flex-shrink-0 mt-0.5" />{h}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Next Steps */}
                    {(mom.mom_json as any).next_steps?.length > 0 && (
                      <div>
                        <h3 className="font-semibold text-gray-800 mb-2">📌 Next Steps</h3>
                        <ul className="space-y-1">
                          {(mom.mom_json as any).next_steps.map((n: string, i: number) => (
                            <li key={i} className="text-sm text-gray-600 flex items-start gap-2"><Play className="h-4 w-4 text-blue-500 flex-shrink-0 mt-0.5" />{n}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ) : mom?.mom_html ? (
                  <div dangerouslySetInnerHTML={{ __html: mom.mom_html }} className="prose max-w-none" />
                ) : (
                  <p className="text-gray-500 text-center py-8">No MOM generated yet. Click "Generate MOM" to create one.</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Insights Tab */}
          <TabsContent value="insights">
            <div className="space-y-4">
              {insights?.data.map((insight) => (
                <Card key={insight.id}>
                  <CardHeader>
                    <CardTitle className="capitalize flex items-center gap-2">
                      {insight.insight_type === 'sentiment' && <TrendingUp className="h-5 w-5 text-blue-500" />}
                      {insight.insight_type === 'key_decisions' && <CheckCircle2 className="h-5 w-5 text-green-500" />}
                      {insight.insight_type === 'risk_compliance' && <AlertTriangle className="h-5 w-5 text-red-500" />}
                      {insight.insight_type === 'topic_distribution' && <BarChart3 className="h-5 w-5 text-purple-500" />}
                      {insight.insight_type === 'speaker_stats' && <Users className="h-5 w-5 text-indigo-500" />}
                      {insight.insight_type.replace('_', ' ')}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {/* Sentiment */}
                    {insight.insight_type === 'sentiment' && insight.insight_json && (
                      <div className="space-y-3">
                        <div className="flex items-center gap-4">
                          <Badge className={`${insight.insight_json.overall_sentiment === 'positive' ? 'bg-green-100 text-green-800' : insight.insight_json.overall_sentiment === 'negative' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'}`}>
                            {insight.insight_json.overall_sentiment} ({Math.round((insight.insight_json.overall_score || 0) * 100)}%)
                          </Badge>
                          <span className="text-sm text-gray-600">{insight.insight_json.meeting_mood}</span>
                        </div>
                        {insight.insight_json.speaker_sentiments?.map((s: any, i: number) => (
                          <div key={i} className="flex items-center gap-3 p-2 bg-gray-50 rounded">
                            <User className="h-4 w-4" />
                            <span className="font-medium text-sm w-32">{s.speaker}</span>
                            <Badge variant="outline" className="text-xs">{s.sentiment}</Badge>
                            <div className="flex-1 bg-gray-200 rounded-full h-2"><div className="bg-blue-500 h-2 rounded-full" style={{ width: `${(s.score || 0.5) * 100}%` }} /></div>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Key Decisions */}
                    {insight.insight_type === 'key_decisions' && insight.insight_json?.decisions && (
                      <div className="space-y-3">
                        {insight.insight_json.decisions.map((d: any, i: number) => (
                          <div key={i} className="p-3 border rounded-lg">
                            <p className="font-medium text-sm">{d.decision}</p>
                            <p className="text-xs text-gray-500 mt-1">{d.context}</p>
                            <div className="flex gap-2 mt-2">
                              <Badge variant="outline" className="text-xs">{d.impact} impact</Badge>
                              <Badge variant="outline" className="text-xs">{d.category}</Badge>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Risk/Compliance */}
                    {insight.insight_type === 'risk_compliance' && insight.insight_json && (
                      <div className="space-y-3">
                        <Badge className={`${insight.insight_json.overall_risk_level === 'high' ? 'bg-red-100 text-red-800' : insight.insight_json.overall_risk_level === 'medium' ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-800'}`}>
                          Overall Risk: {insight.insight_json.overall_risk_level}
                        </Badge>
                        {insight.insight_json.risk_flags?.map((f: any, i: number) => (
                          <div key={i} className="p-3 border-l-4 border-l-red-400 bg-red-50 rounded">
                            <p className="text-sm font-medium">{f.flag}</p>
                            <div className="flex gap-2 mt-1">
                              <Badge variant="outline" className="text-xs">{f.severity}</Badge>
                              <Badge variant="outline" className="text-xs">{f.category}</Badge>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Topic Distribution */}
                    {insight.insight_type === 'topic_distribution' && insight.insight_json?.topics && (
                      <div className="space-y-3">
                        {insight.insight_json.meeting_efficiency_score !== undefined && (
                          <p className="text-sm text-gray-600">Meeting Efficiency: <span className="font-bold">{insight.insight_json.meeting_efficiency_score}/100</span></p>
                        )}
                        {insight.insight_json.topics.map((t: any, i: number) => (
                          <div key={i} className="space-y-1">
                            <div className="flex items-center justify-between">
                              <span className="text-sm font-medium">{t.topic}</span>
                              <span className="text-xs text-gray-500">{t.coverage_percent}%</span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2.5">
                              <div className="bg-purple-500 h-2.5 rounded-full" style={{ width: `${t.coverage_percent}%` }} />
                            </div>
                            <p className="text-xs text-gray-500">{t.description}</p>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Speaker Stats */}
                    {insight.insight_type === 'speaker_stats' && insight.insight_json?.speakers && (
                      <div className="space-y-3">
                        <p className="text-sm text-gray-600">{insight.insight_json.total_speakers} speakers • {insight.insight_json.total_words} total words</p>
                        {insight.insight_json.speakers.map((s: any, i: number) => (
                          <div key={i} className="space-y-1">
                            <div className="flex items-center justify-between">
                              <span className="text-sm font-medium flex items-center gap-2"><User className="h-3 w-3" />{s.speaker}</span>
                              <span className="text-xs text-gray-500">{s.talk_percentage}% • {s.total_words} words</span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2.5">
                              <div className="bg-indigo-500 h-2.5 rounded-full" style={{ width: `${s.talk_percentage}%` }} />
                            </div>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Fallback for unknown types */}
                    {!['sentiment', 'key_decisions', 'risk_compliance', 'topic_distribution', 'speaker_stats'].includes(insight.insight_type) && (
                      <pre className="text-xs bg-gray-50 p-4 rounded overflow-auto max-h-64">{JSON.stringify(insight.insight_json, null, 2)}</pre>
                    )}
                  </CardContent>
                </Card>
              ))}

              {(!insights || insights.data.length === 0) && (
                <Card><CardContent className="py-12 text-center text-gray-500">No insights available. Click "Analyze" to generate AI insights.</CardContent></Card>
              )}
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </ProductDashboardLayout>
  );
}
