/**
 * Activity Logs Component
 * Clean columns: Date & Time | User | Action Type | Details | Application
 * Fixed timestamp (normalized created_at → timestamp in service)
 */

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { getAuditLogs, type AuditLog } from '@/services/permissionService';
import { Button } from '@/components/ui/button';
import {
    History, Filter, ChevronLeft, ChevronRight, RefreshCcw,
    Activity, Clock, CheckCircle, XCircle, AlertTriangle, Loader2,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { toast } from 'sonner';

const fmtDate = (iso: string) => {
    if (!iso) return { date: '—', time: '' };
    try {
        const d = new Date(iso.includes('Z') || iso.includes('+') ? iso : iso + 'Z');
        return {
            date: d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }),
            time: d.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' }),
        };
    } catch { return { date: iso, time: '' }; }
};

const EVENT_META: Record<string, { label: string; bg: string; text: string; ring: string; Icon: React.FC<any> }> = {
    permission_assigned: { label: 'Granted',    bg: 'bg-emerald-50', text: 'text-emerald-700', ring: 'ring-emerald-200/60', Icon: CheckCircle },
    permission_updated:  { label: 'Updated',    bg: 'bg-blue-50',    text: 'text-blue-700',    ring: 'ring-blue-200/60',    Icon: RefreshCcw  },
    permission_revoked:  { label: 'Revoked',    bg: 'bg-red-50',     text: 'text-red-700',     ring: 'ring-red-200/60',     Icon: XCircle     },
    access_requested:    { label: 'Requested',  bg: 'bg-amber-50',   text: 'text-amber-700',   ring: 'ring-amber-200/60',   Icon: Clock       },
    access_approved:     { label: 'Approved',   bg: 'bg-emerald-50', text: 'text-emerald-700', ring: 'ring-emerald-200/60', Icon: CheckCircle },
    access_rejected:     { label: 'Rejected',   bg: 'bg-red-50',     text: 'text-red-700',     ring: 'ring-red-200/60',     Icon: XCircle     },
    login:               { label: 'Login',      bg: 'bg-indigo-50',  text: 'text-indigo-700',  ring: 'ring-indigo-200/60',  Icon: CheckCircle },
    admin_granted:       { label: 'Admin Added', bg: 'bg-emerald-50', text: 'text-emerald-700', ring: 'ring-emerald-200/60', Icon: CheckCircle },
    admin_revoked:       { label: 'Admin Revoked', bg: 'bg-red-50',  text: 'text-red-700',     ring: 'ring-red-200/60',     Icon: XCircle     },
};

const DEFAULT_META = { label: 'System', bg: 'bg-gray-50', text: 'text-gray-600', ring: 'ring-gray-200/60', Icon: Activity };

const parseDetails = (raw: string) => {
    try { return JSON.parse(raw); } catch { return { raw }; }
};

const TH = ({ children, className = '' }: { children: React.ReactNode; className?: string }) => (
    <th className={cn('px-4 py-3 text-left text-[11px] font-extrabold text-gray-400 uppercase tracking-widest whitespace-nowrap', className)}>
        {children}
    </th>
);

const EVENT_TYPES = [
    { value: '',                    label: 'All Activities'      },
    { value: 'permission_assigned', label: 'Permission Granted'  },
    { value: 'permission_updated',  label: 'Permission Updated'  },
    { value: 'permission_revoked',  label: 'Permission Revoked'  },
    { value: 'access_requested',    label: 'Access Requested'    },
    { value: 'access_approved',     label: 'Access Approved'     },
    { value: 'access_rejected',     label: 'Access Rejected'     },
];

export const AuditLogs: React.FC = () => {
    const { user } = useAuth();
    const [logs, setLogs]         = useState<AuditLog[]>([]);
    const [total, setTotal]       = useState(0);
    const [loading, setLoading]   = useState(true);
    const [error, setError]       = useState<string | null>(null);
    const [offset, setOffset]     = useState(0);
    const [filter, setFilter]     = useState('');
    const LIMIT = 15;

    const load = async () => {
        if (!user) return;
        setLoading(true); setError(null);
        try {
            const data = await getAuditLogs(user.email, LIMIT, offset, filter || undefined);
            setLogs(data.logs || []);
            setTotal(data.total || 0);
        } catch (err) {
            const msg = err instanceof Error ? err.message : 'Failed to load activity logs';
            setError(msg); toast.error(msg);
        } finally { setLoading(false); }
    };

    useEffect(() => { load(); }, [user, offset, filter]);

    const totalPages = Math.ceil(total / LIMIT);
    const currentPage = Math.floor(offset / LIMIT) + 1;

    return (
        <div className="flex flex-col">
            {/* ── Controls ── */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-5 border-b border-gray-100">
                <div>
                    <h2 className="text-base font-extrabold text-[#002B49]">Activity Logs</h2>
                    <p className="text-[11px] text-gray-400 font-medium mt-0.5">
                        {total > 0 ? `${total} total events recorded` : 'Complete audit trail of all system actions'}
                    </p>
                </div>
                <div className="flex items-center gap-2">
                    <div className="flex items-center gap-1.5 bg-gray-50 border border-gray-100 rounded-xl px-3 py-1.5">
                        <Filter className="h-3 w-3 text-gray-400" />
                        <select
                            value={filter}
                            onChange={e => { setFilter(e.target.value); setOffset(0); }}
                            className="bg-transparent text-[12px] font-semibold text-[#002B49] appearance-none outline-none cursor-pointer pr-1"
                        >
                            {EVENT_TYPES.map(t => (
                                <option key={t.value} value={t.value}>{t.label}</option>
                            ))}
                        </select>
                    </div>
                    <button
                        onClick={load}
                        className="h-9 w-9 flex items-center justify-center rounded-xl bg-gray-50 border border-gray-100 text-gray-400 hover:text-primary hover:bg-primary/5 transition-all"
                    >
                        <RefreshCcw className={cn('h-3.5 w-3.5', loading && 'animate-spin')} />
                    </button>
                </div>
            </div>

            {/* ── Table ── */}
            {loading ? (
                <div className="flex items-center justify-center py-24 gap-3">
                    <Loader2 className="h-7 w-7 animate-spin text-primary/30" />
                    <p className="text-sm text-gray-400 font-medium">Loading activity logs…</p>
                </div>
            ) : error ? (
                <div className="flex flex-col items-center justify-center py-20 gap-4">
                    <div className="h-14 w-14 rounded-full bg-red-50 flex items-center justify-center">
                        <AlertTriangle className="h-6 w-6 text-red-400" />
                    </div>
                    <p className="text-sm font-bold text-[#002B49]">Failed To Load Logs</p>
                    <p className="text-xs text-gray-400 max-w-xs text-center">{error}</p>
                    <Button onClick={load} size="sm" className="gap-2 rounded-xl">
                        <RefreshCcw className="h-3.5 w-3.5" /> Retry
                    </Button>
                </div>
            ) : logs.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-24 gap-3">
                    <div className="h-16 w-16 bg-gray-50 rounded-full flex items-center justify-center border-2 border-dashed border-gray-100">
                        <History className="h-7 w-7 text-gray-200" />
                    </div>
                    <p className="text-sm font-bold text-[#002B49]">No Activities Found</p>
                    <p className="text-xs text-gray-400">
                        {filter ? 'Try selecting a different filter.' : 'Logs will appear as actions are taken.'}
                    </p>
                </div>
            ) : (
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead className="bg-gray-50 border-b border-gray-100">
                            <tr>
                                <TH className="pl-6">Date &amp; Time</TH>
                                <TH>User</TH>
                                <TH>Action Type</TH>
                                <TH>Details</TH>
                                <TH className="pr-6 text-right">Application</TH>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-50 bg-white">
                            {logs.map(log => {
                                const ts   = fmtDate(log.timestamp || (log as any).created_at || '');
                                const meta = EVENT_META[log.event_type] || DEFAULT_META;
                                const Icon = meta.Icon;
                                const det  = parseDetails(log.event_details || '{}');

                                return (
                                    <tr key={log.id} className="group hover:bg-gray-50/60 transition-colors">
                                        {/* Date & Time */}
                                        <td className="px-4 py-3.5 pl-6">
                                            <p className="text-[12px] font-bold text-[#002B49]">{ts.date}</p>
                                            {ts.time && (
                                                <div className="flex items-center gap-1 mt-0.5">
                                                    <Clock className="h-2.5 w-2.5 text-gray-300" />
                                                    <span className="text-[10px] text-gray-400 font-medium">{ts.time}</span>
                                                </div>
                                            )}
                                        </td>

                                        {/* User */}
                                        <td className="px-4 py-3.5">
                                            <div className="flex items-center gap-2">
                                                <div className="h-7 w-7 rounded-lg bg-gray-50 border border-gray-100 flex items-center justify-center font-bold text-[10px] text-gray-400 uppercase flex-shrink-0">
                                                    {log.email?.charAt(0)}
                                                </div>
                                                <p className="text-[12px] font-semibold text-[#002B49] truncate max-w-[160px]">
                                                    {log.email}
                                                </p>
                                            </div>
                                        </td>

                                        {/* Action Type */}
                                        <td className="px-4 py-3.5">
                                            <div className={cn('inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg ring-1 ring-inset', meta.bg, meta.text, meta.ring)}>
                                                <Icon className="h-3 w-3" />
                                                <span className="text-[10px] font-extrabold uppercase tracking-wider">{meta.label}</span>
                                            </div>
                                        </td>

                                        {/* Details */}
                                        <td className="px-4 py-3.5 max-w-xs">
                                            {det.raw ? (
                                                <p className="text-[12px] text-gray-500 font-medium truncate">{det.raw}</p>
                                            ) : (
                                                <div className="space-y-0.5">
                                                    {log.event_type === 'login' ? (
                                                        <p className="text-[11px] text-gray-600 font-semibold truncate">
                                                            SSO Login: <span className="text-emerald-600">Success</span>
                                                        </p>
                                                    ) : (
                                                        <>
                                                            {(det.target_email || det.user_email) && (
                                                                <p className="text-[11px] text-gray-600 font-semibold truncate">
                                                                    Target: <span className="text-[#002B49]">{det.target_email || det.user_email}</span>
                                                                </p>
                                                            )}
                                                            {det.role && (
                                                                <p className="text-[11px] text-gray-500 truncate">
                                                                    Role: <span className="text-purple-600 font-semibold uppercase">{det.role}</span>
                                                                </p>
                                                            )}
                                                            {det.route && (
                                                                <p className="text-[11px] text-gray-400 font-medium truncate">Route: {det.route}</p>
                                                            )}
                                                            {det.permission_type && (
                                                                <span className="inline-block px-1.5 py-0.5 bg-primary/5 text-primary rounded text-[10px] font-bold uppercase">
                                                                    {det.permission_type}
                                                                </span>
                                                            )}
                                                            {!det.target_email && !det.user_email && !det.route && !det.role && (
                                                                <p className="text-[11px] text-gray-400 italic">System event</p>
                                                            )}
                                                        </>
                                                    )}
                                                </div>
                                            )}
                                        </td>

                                        {/* Application */}
                                        <td className="px-4 py-3.5 pr-6 text-right">
                                            <span className="inline-flex items-center px-2 py-0.5 rounded-md bg-gray-50 border border-gray-100 text-[10px] font-bold text-gray-500 uppercase tracking-tight">
                                                {log.application || 'System'}
                                            </span>
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            )}

            {/* ── Pagination ── */}
            {total > 0 && (
                <div className="flex items-center justify-between px-6 py-3 border-t border-gray-100 bg-white">
                    <p className="text-[11px] font-bold text-gray-400">
                        Showing <span className="text-[#002B49]">{offset + 1}</span>–<span className="text-[#002B49]">{Math.min(offset + LIMIT, total)}</span> of <span className="text-[#002B49]">{total}</span> events
                    </p>
                    <div className="flex items-center gap-1">
                        <Button
                            variant="ghost" size="sm"
                            className="h-8 px-3 rounded-lg text-xs font-bold gap-1 hover:bg-gray-50"
                            onClick={() => setOffset(o => Math.max(0, o - LIMIT))}
                            disabled={offset === 0 || loading}
                        >
                            <ChevronLeft className="h-3.5 w-3.5" /> Prev
                        </Button>
                        <span className="px-3 text-[11px] font-bold text-gray-500">
                            Page {currentPage} of {totalPages}
                        </span>
                        <Button
                            variant="ghost" size="sm"
                            className="h-8 px-3 rounded-lg text-xs font-bold gap-1 hover:bg-gray-50"
                            onClick={() => setOffset(o => o + LIMIT)}
                            disabled={offset + LIMIT >= total || loading}
                        >
                            Next <ChevronRight className="h-3.5 w-3.5" />
                        </Button>
                    </div>
                </div>
            )}
        </div>
    );
};
