/**
 * MS Teams API Service
 * Frontend client for all Teams meeting endpoints.
 */

const API_BASE = '/api/teams';

export interface Meeting {
  id: string;
  meeting_url: string;
  title: string | null;
  call_id: string | null;
  status: string;
  company_id: number | null;
  scheduled_at: string | null;
  started_at: string | null;
  ended_at: string | null;
  created_at: string;
}

export interface MeetingListResponse {
  data: Meeting[];
  count: number;
}

export interface TranscriptSegment {
  speaker: string;
  start_time: string;
  end_time: string;
  text: string;
}

export interface TranscriptData {
  id: string | null;
  meeting_id: string;
  raw_vtt: string | null;
  structured_json: TranscriptSegment[] | null;
  full_text: string | null;
  participants: string[];
  participant_count: number;
  duration_minutes: number;
  created_at: string | null;
}

export interface ActionItem {
  task: string;
  assignee: string;
  deadline: string;
}

export interface AgendaItem {
  topic: string;
  discussion_summary: string;
  decisions: string[];
  action_items: ActionItem[];
}

export interface MOMData {
  meeting_title: string;
  meeting_date: string;
  meeting_duration: string;
  attendees: string[];
  absentees?: string[];
  agenda_items: AgendaItem[];
  key_highlights: string[];
  next_steps: string[];
  next_meeting: string;
  additional_notes?: string;
}

export interface MOMResponse {
  id: string | null;
  meeting_id: string;
  mom_json: MOMData | null;
  mom_html: string | null;
  version: number;
  generated_at: string | null;
}

export interface InsightData {
  id: string | null;
  meeting_id: string;
  insight_type: string;
  insight_json: any;
  generated_at: string | null;
}

export interface InsightsListResponse {
  data: InsightData[];
  count: number;
}

export interface MeetingDetail {
  meeting: Meeting;
  has_transcript: boolean;
  transcript_summary: any;
  has_mom: boolean;
  mom_summary: any;
  insight_count: number;
}

// ── Meeting CRUD ──

export async function createMeeting(meetingUrl: string, title?: string): Promise<Meeting> {
  const res = await fetch(`${API_BASE}/meetings`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ meeting_url: meetingUrl, title: title || null }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function listMeetings(): Promise<MeetingListResponse> {
  const res = await fetch(`${API_BASE}/meetings`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getMeeting(id: string): Promise<MeetingDetail> {
  const res = await fetch(`${API_BASE}/meetings/${id}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function deleteMeeting(id: string): Promise<{ success: boolean }> {
  const res = await fetch(`${API_BASE}/meetings/${id}`, { method: 'DELETE' });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// ── Bot Join / Leave ──

export async function joinMeeting(id: string): Promise<any> {
  const res = await fetch(`${API_BASE}/meetings/${id}/join`, { method: 'POST' });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function leaveMeeting(id: string): Promise<any> {
  const res = await fetch(`${API_BASE}/meetings/${id}/leave`, { method: 'POST' });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// ── Transcript ──

export async function fetchTranscript(id: string): Promise<any> {
  const res = await fetch(`${API_BASE}/meetings/${id}/fetch-transcript`, { method: 'POST' });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function uploadTranscript(id: string, vttContent: string): Promise<any> {
  const res = await fetch(`${API_BASE}/meetings/${id}/upload-transcript`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ vtt_content: vttContent }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getTranscript(id: string): Promise<TranscriptData> {
  const res = await fetch(`${API_BASE}/meetings/${id}/transcript`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// ── MOM ──

export async function generateMOM(id: string): Promise<any> {
  const res = await fetch(`${API_BASE}/meetings/${id}/generate-mom`, { method: 'POST' });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getMOM(id: string): Promise<MOMResponse> {
  const res = await fetch(`${API_BASE}/meetings/${id}/mom`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// ── Analysis ──

export async function analyzeMeeting(id: string): Promise<any> {
  const res = await fetch(`${API_BASE}/meetings/${id}/analyze`, { method: 'POST' });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getInsights(id: string): Promise<InsightsListResponse> {
  const res = await fetch(`${API_BASE}/meetings/${id}/insights`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
