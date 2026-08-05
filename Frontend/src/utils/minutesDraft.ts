/**
 * Minutes form draft helpers — localStorage + optional server sync.
 * Keyed by company + meeting type + committee + date so drafts don't collide.
 */

export interface MinutesDraftPayload {
  currentStep: number;
  formData: Record<string, unknown>;
  updatedAt?: string;
}

export function buildMinutesDraftKey(
  companyName?: string,
  meetingType?: string,
  meetingDate?: string,
  committeeName?: string,
): string {
  const parts = [
    (companyName || '').trim(),
    (meetingType || '').trim(),
    (committeeName || '').trim(),
    (meetingDate || '').trim(),
  ];
  return `minutes_draft_v1:${parts.join('|')}`;
}

export function isDraftKeyReady(key: string): boolean {
  // Need at least company + date to avoid writing a generic empty draft
  const body = key.replace(/^minutes_draft_v1:/, '');
  const [company, , , date] = body.split('|');
  return Boolean(company && date);
}

export function readLocalDraft(key: string): MinutesDraftPayload | null {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== 'object') return null;
    return {
      currentStep: typeof parsed.currentStep === 'number' ? parsed.currentStep : 0,
      formData: parsed.formData || {},
      updatedAt: parsed.updatedAt,
    };
  } catch {
    return null;
  }
}

export function writeLocalDraft(key: string, payload: MinutesDraftPayload): void {
  const data = {
    ...payload,
    updatedAt: new Date().toISOString(),
  };
  localStorage.setItem(key, JSON.stringify(data));
  // Keep legacy session key in sync for older code paths
  try {
    sessionStorage.setItem('minutes_form_draft', JSON.stringify(data));
  } catch {
    /* ignore */
  }
}

export function clearLocalDraft(key: string): void {
  try {
    localStorage.removeItem(key);
  } catch {
    /* ignore */
  }
  try {
    sessionStorage.removeItem('minutes_form_draft');
  } catch {
    /* ignore */
  }
}

export async function saveDraftToServer(
  key: string,
  meta: {
    company_name: string;
    meeting_type: string;
    meeting_date: string;
    committee_name?: string;
    current_step: number;
    form_data: Record<string, unknown>;
  },
): Promise<{ ok: boolean; updated_at?: string }> {
  try {
    const res = await fetch('/api/minutes-drafts', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        draft_key: key,
        company_name: meta.company_name,
        meeting_type: meta.meeting_type,
        meeting_date: meta.meeting_date,
        committee_name: meta.committee_name || '',
        current_step: meta.current_step,
        form_data: meta.form_data,
      }),
    });
    if (!res.ok) return { ok: false };
    const data = await res.json();
    return { ok: true, updated_at: data.updated_at };
  } catch {
    return { ok: false };
  }
}

export async function loadDraftFromServer(key: string): Promise<MinutesDraftPayload | null> {
  try {
    const res = await fetch(`/api/minutes-drafts?draft_key=${encodeURIComponent(key)}`);
    if (res.status === 404) return null;
    if (!res.ok) return null;
    const data = await res.json();
    return {
      currentStep: data.current_step ?? 0,
      formData: data.form_data || {},
      updatedAt: data.updated_at,
    };
  } catch {
    return null;
  }
}

export async function deleteDraftFromServer(key: string): Promise<void> {
  try {
    await fetch(`/api/minutes-drafts?draft_key=${encodeURIComponent(key)}`, { method: 'DELETE' });
  } catch {
    /* ignore offline */
  }
}
