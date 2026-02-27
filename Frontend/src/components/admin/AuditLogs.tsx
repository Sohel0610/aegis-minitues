/**
 * Audit Logs Component
 * View authentication and permission audit logs with pagination and filtering
 */

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { getAuditLogs, type AuditLog } from '@/services/permissionService';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow
} from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
    History,
    Filter,
    ChevronLeft,
    ChevronRight,
    RefreshCcw,
    Activity,
    User,
    Clock,
    Info,
    Loader2,
    CheckCircle,
    XCircle
} from 'lucide-react';
import { toast } from 'sonner';

export const AuditLogs: React.FC = () => {
    const { user } = useAuth();
    const [logs, setLogs] = useState<AuditLog[]>([]);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(true);
    const [offset, setOffset] = useState(0);
    const [eventType, setEventType] = useState<string>('');
    const LIMIT = 15;

    const eventTypes = [
        { value: '', label: 'All Activities' },
        { value: 'permission_assigned', label: 'Permission Assigned' },
        { value: 'permission_updated', label: 'Permission Updated' },
        { value: 'permission_revoked', label: 'Permission Revoked' },
        { value: 'access_requested', label: 'Access Requested' },
        { value: 'access_approved', label: 'Access Approved' },
        { value: 'access_rejected', label: 'Access Rejected' },
    ];

    const loadLogs = async () => {
        if (!user) return;

        setLoading(true);
        try {
            const data = await getAuditLogs(user.email, LIMIT, offset, eventType || undefined);
            setLogs(data.logs);
            setTotal(data.total);
        } catch (err) {
            console.error('Failed to load audit logs:', err);
            toast.error('Failed to load activity history');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadLogs();
    }, [user, offset, eventType]);

    const handleNext = () => {
        if (offset + LIMIT < total) {
            setOffset(offset + LIMIT);
        }
    };

    const handlePrev = () => {
        if (offset - LIMIT >= 0) {
            setOffset(offset - LIMIT);
        }
    };

    const formatEventDetails = (detailsStr: string) => {
        try {
            const details = JSON.parse(detailsStr);
            if (details.target_email || details.user_email) {
                return (
                    <div className="flex flex-col gap-1.5 py-1">
                        <div className="flex items-center gap-2">
                            <span className="text-[10px] font-bold text-gray-400 uppercase tracking-tighter w-12 shrink-0">Target</span>
                            <span className="text-xs font-semibold text-[#002B49] truncate">{details.target_email || details.user_email}</span>
                        </div>
                        {details.route && (
                            <div className="flex items-center gap-2">
                                <span className="text-[10px] font-bold text-gray-400 uppercase tracking-tighter w-12 shrink-0">App</span>
                                <span className="text-[11px] font-medium text-gray-600 truncate">{details.route}</span>
                            </div>
                        )}
                        {details.permission_type && (
                            <div className="flex items-center gap-2">
                                <span className="text-[10px] font-bold text-gray-400 uppercase tracking-tighter w-12 shrink-0">Role</span>
                                <span className="text-[10px] font-bold text-primary uppercase tracking-widest">{details.permission_type}</span>
                            </div>
                        )}
                    </div>
                );
            }
            return <span className="text-[11px] text-gray-400 italic">Static System Event</span>;
        } catch (e) {
            return <span className="text-[11px] text-gray-500 font-medium">{detailsStr}</span>;
        }
    };

    const getEventBadge = (type: string) => {
        switch (type) {
            case 'permission_assigned':
            case 'access_approved':
                return (
                    <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-emerald-50 text-emerald-700 ring-1 ring-inset ring-emerald-200/50">
                        <CheckCircle className="h-3 w-3" />
                        <span className="text-[10px] font-extrabold uppercase tracking-wider">Granted</span>
                    </div>
                );
            case 'permission_updated':
                return (
                    <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-primary/5 text-primary ring-1 ring-inset ring-primary/20">
                        <RefreshCcw className="h-3 w-3" />
                        <span className="text-[10px] font-extrabold uppercase tracking-wider">Updated</span>
                    </div>
                );
            case 'permission_revoked':
            case 'access_rejected':
                return (
                    <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-red-50 text-red-700 ring-1 ring-inset ring-red-200/50">
                        <XCircle className="h-3 w-3" />
                        <span className="text-[10px] font-extrabold uppercase tracking-wider">Revoked</span>
                    </div>
                );
            case 'access_requested':
                return (
                    <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-amber-50 text-amber-700 ring-1 ring-inset ring-amber-200/50">
                        <Clock className="h-3 w-3" />
                        <span className="text-[10px] font-extrabold uppercase tracking-wider">Requested</span>
                    </div>
                );
            default:
                return <Badge variant="outline" className="text-[10px] font-bold uppercase border-gray-100">{type.replace('_', ' ')}</Badge>;
        }
    };

    return (
        <div className="space-y-6 h-full flex flex-col">
            {/* Controls */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 px-6 pt-6">
                <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-xl bg-primary/5 border border-primary/10 flex items-center justify-center text-primary shadow-sm">
                        <History className="h-5 w-5" />
                    </div>
                    <div>
                        <h2 className="text-xl font-extrabold text-[#002B49] tracking-tight">Audit Ledger</h2>
                        <p className="text-[11px] font-bold text-gray-400 uppercase tracking-widest">System Activity Logs</p>
                    </div>
                </div>

                <div className="flex items-center gap-3">
                    <div className="relative">
                        <Filter className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-primary/60" />
                        <select
                            value={eventType}
                            onChange={(e) => {
                                setEventType(e.target.value);
                                setOffset(0);
                            }}
                            className="pl-9 h-11 w-52 bg-gray-50/50 border border-gray-100 rounded-xl text-sm font-semibold text-[#002B49] appearance-none focus:ring-2 focus:ring-primary/10 focus:border-primary transition-all pr-8"
                        >
                            {eventTypes.map(t => (
                                <option key={t.value} value={t.value}>{t.label}</option>
                            ))}
                        </select>
                        <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
                            <ChevronRight className="h-4 w-4 text-gray-400 rotate-90" />
                        </div>
                    </div>
                    <Button variant="outline" size="icon" className="h-11 w-11 rounded-xl border-gray-100 bg-gray-50 text-gray-400 hover:text-primary hover:bg-primary/5 transition-all" onClick={loadLogs}>
                        <RefreshCcw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                    </Button>
                </div>
            </div>

            {/* Logs Table */}
            <div className="flex-1 overflow-hidden px-6 pb-6">
                <div className="h-full border border-gray-100 rounded-2xl overflow-hidden flex flex-col bg-gray-50/30">
                    <div className="flex-1 overflow-y-auto scrollbar-hide">
                        <Table>
                            <TableHeader className="bg-white sticky top-0 z-10 border-b border-gray-100">
                                <TableRow className="hover:bg-transparent border-none">
                                    <TableHead className="text-xs font-bold text-gray-400 uppercase tracking-widest h-14 pl-6">Timestamp</TableHead>
                                    <TableHead className="text-xs font-bold text-gray-400 uppercase tracking-widest h-14">Initiator</TableHead>
                                    <TableHead className="text-xs font-bold text-gray-400 uppercase tracking-widest h-14">Command</TableHead>
                                    <TableHead className="text-xs font-bold text-gray-400 uppercase tracking-widest h-14">Impact</TableHead>
                                    <TableHead className="text-xs font-bold text-gray-400 uppercase tracking-widest h-14 text-right pr-8">Source</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody className="bg-white divide-y divide-gray-50">
                                {loading ? (
                                    <TableRow className="hover:bg-transparent border-none">
                                        <TableCell colSpan={5} className="h-96 text-center">
                                            <div className="flex flex-col items-center justify-center gap-4">
                                                <div className="relative">
                                                    <div className="h-12 w-12 rounded-full border-2 border-primary/10 border-t-primary animate-spin"></div>
                                                </div>
                                                <p className="text-xs font-bold text-gray-400 uppercase tracking-widest">Compiling Records...</p>
                                            </div>
                                        </TableCell>
                                    </TableRow>
                                ) : logs.length > 0 ? (
                                    logs.map((log) => (
                                        <TableRow key={log.id} className="group hover:bg-[#F8FAFC]/50 transition-colors border-none">
                                            <TableCell className="py-4 pl-6">
                                                <div className="flex flex-col">
                                                    <span className="text-[12px] font-bold text-[#002B49]">
                                                        {new Date(log.timestamp).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' })}
                                                    </span>
                                                    <div className="flex items-center gap-1.5 text-[10px] text-gray-400 font-medium">
                                                        <Clock className="h-2.5 w-2.5" />
                                                        {new Date(log.timestamp).toLocaleTimeString(undefined, {
                                                            hour: '2-digit',
                                                            minute: '2-digit'
                                                        })}
                                                    </div>
                                                </div>
                                            </TableCell>
                                            <TableCell className="py-4">
                                                <div className="flex items-center gap-3">
                                                    <div className="h-8 w-8 rounded-full bg-gray-50 flex items-center justify-center font-bold text-[10px] text-gray-400 border border-gray-100 uppercase">
                                                        {log.email.charAt(0)}
                                                    </div>
                                                    <div className="flex flex-col">
                                                        <span className="text-[12px] font-bold text-[#002B49] truncate max-w-[150px]">{log.email}</span>
                                                        <span className="text-[10px] text-gray-400 font-medium">Administrator</span>
                                                    </div>
                                                </div>
                                            </TableCell>
                                            <TableCell className="py-4">
                                                {getEventBadge(log.event_type)}
                                            </TableCell>
                                            <TableCell className="py-4">
                                                {formatEventDetails(log.event_details)}
                                            </TableCell>
                                            <TableCell className="py-4 text-right pr-8">
                                                <span className="inline-flex items-center px-2 py-1 rounded-md bg-gray-50 border border-gray-100 text-[9px] font-extrabold text-gray-500 uppercase tracking-tight">
                                                    {log.application}
                                                </span>
                                            </TableCell>
                                        </TableRow>
                                    ))
                                ) : (
                                    <TableRow className="hover:bg-transparent border-none">
                                        <TableCell colSpan={5} className="h-96 text-center">
                                            <div className="flex flex-col items-center justify-center gap-4 animate-in fade-in zoom-in duration-500">
                                                <div className="h-20 w-20 rounded-full bg-gray-50 flex items-center justify-center border-2 border-dashed border-gray-100">
                                                    <Activity className="h-8 w-8 text-gray-200" />
                                                </div>
                                                <div className="space-y-1">
                                                    <p className="text-sm font-bold text-[#002B49]">No activities recorded</p>
                                                    <p className="text-xs text-gray-400 font-medium uppercase tracking-widest">Logs will appear as actions are taken</p>
                                                </div>
                                            </div>
                                        </TableCell>
                                    </TableRow>
                                )}
                            </TableBody>
                        </Table>
                    </div>

                    {/* Pagination Bottom Bar */}
                    <div className="h-16 px-6 bg-white border-t border-gray-100 flex items-center justify-between">
                        <p className="text-[11px] font-bold text-gray-400 uppercase tracking-widest">
                            <span className="text-primary">{offset + 1}</span> to <span className="text-primary">{Math.min(offset + LIMIT, total)}</span> of {total} events
                        </p>
                        <div className="flex items-center gap-1.5">
                            <Button
                                variant="ghost"
                                size="sm"
                                className="h-9 px-3 rounded-lg text-xs font-bold gap-1 transform transition-all active:scale-[0.95] hover:bg-gray-50 border border-transparent hover:border-gray-100"
                                onClick={handlePrev}
                                disabled={offset === 0 || loading}
                            >
                                <ChevronLeft className="h-3.5 w-3.5" />
                                Prev
                            </Button>
                            <div className="h-6 w-px bg-gray-100 mx-1"></div>
                            <Button
                                variant="ghost"
                                size="sm"
                                className="h-9 px-3 rounded-lg text-xs font-bold gap-1 transform transition-all active:scale-[0.95] hover:bg-gray-50 border border-transparent hover:border-gray-100"
                                onClick={handleNext}
                                disabled={offset + LIMIT >= total || loading}
                            >
                                Next
                                <ChevronRight className="h-3.5 w-3.5" />
                            </Button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};
