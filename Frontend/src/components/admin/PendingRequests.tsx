/**
 * Pending Requests Component – fully fixed & redesigned
 * • Proper error state UI
 * • Rejection modal (replaces browser prompt)
 * • Full dates with year
 * • Application friendly name always resolved
 */

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import {
    getAccessRequests,
    approveAccessRequest,
    rejectAccessRequest,
    getRouteDefinitions,
    type AccessRequestResponse,
    type RouteDefinition
} from '@/services/permissionService';
import { Button } from '@/components/ui/button';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import {
    CheckCircle,
    XCircle,
    Calendar,
    Mail,
    Globe,
    Info,
    RefreshCw,
    Loader2,
    Inbox,
    Shield,
    AlertTriangle,
    Clock,
    User,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { toast } from 'sonner';

const fmtDate = (iso: string) => {
    try {
        return new Date(iso + (iso.includes('Z') || iso.includes('+') ? '' : 'Z'))
            .toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
    } catch { return iso; }
};

const fmtTime = (iso: string) => {
    try {
        return new Date(iso + (iso.includes('Z') || iso.includes('+') ? '' : 'Z'))
            .toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
    } catch { return ''; }
};

export const PendingRequests: React.FC = () => {
    const { user } = useAuth();
    const [requests, setRequests] = useState<AccessRequestResponse[]>([]);
    const [routeMap, setRouteMap] = useState<Record<string, string>>({});
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [processingId, setProcessingId] = useState<number | null>(null);

    // Rejection modal state
    const [rejectTarget, setRejectTarget] = useState<AccessRequestResponse | null>(null);
    const [rejectReason, setRejectReason] = useState('');
    const [rejecting, setRejecting] = useState(false);

    // Status filter
    const [statusFilter, setStatusFilter] = useState<'pending' | 'approved' | 'rejected' | ''>('pending');

    const loadData = async () => {
        if (!user) return;
        setError(null);
        try {
            setLoading(true);
            const [reqsData, routesData] = await Promise.all([
                getAccessRequests(user.email, statusFilter || undefined),
                getRouteDefinitions(user.email),
            ]);
            setRequests(reqsData.requests);
            const map: Record<string, string> = {};
            routesData.forEach((r: RouteDefinition) => { map[r.route_path] = r.route_name; });
            setRouteMap(map);
        } catch (err) {
            const msg = err instanceof Error ? err.message : 'Failed to load access requests';
            setError(msg);
            toast.error(msg);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { loadData(); }, [user, statusFilter]);

    const getRouteName = (path: string) => routeMap[path] || path.replace(/^\//, '').replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

    const handleApprove = async (req: AccessRequestResponse) => {
        if (!user) return;
        setProcessingId(req.id);
        try {
            await approveAccessRequest(user.email, req.id);
            toast.success(`✅ Access approved for ${req.name}`);
            await loadData();
        } catch (err) {
            toast.error(err instanceof Error ? err.message : 'Failed to approve request');
        } finally {
            setProcessingId(null);
        }
    };

    const openRejectModal = (req: AccessRequestResponse) => {
        setRejectTarget(req);
        setRejectReason('');
    };

    const handleReject = async () => {
        if (!user || !rejectTarget) return;
        setRejecting(true);
        try {
            await rejectAccessRequest(user.email, rejectTarget.id, rejectReason.trim() || undefined);
            toast.success(`Request from ${rejectTarget.name} rejected`);
            setRejectTarget(null);
            await loadData();
        } catch (err) {
            toast.error(err instanceof Error ? err.message : 'Failed to reject request');
        } finally {
            setRejecting(false);
        }
    };

    const statusColor: Record<string, string> = {
        pending:  'bg-amber-50 text-amber-700 ring-amber-200/60',
        approved: 'bg-emerald-50 text-emerald-700 ring-emerald-200/60',
        rejected: 'bg-red-50 text-red-700 ring-red-200/60',
    };

    const permColor = (p: string) =>
        p === 'admin' ? 'bg-purple-50 text-purple-700 ring-purple-200/50' : 'bg-blue-50 text-blue-700 ring-blue-200/50';

    // ─── Loading ───────────────────────────────────────────────────────────────
    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center py-32 gap-6">
                <div className="relative">
                    <div className="h-16 w-16 rounded-full border-4 border-primary/10 border-t-primary animate-spin" />
                    <Shield className="absolute inset-0 m-auto h-6 w-6 text-primary/40 animate-pulse" />
                </div>
                <div className="text-center space-y-1">
                    <p className="text-[#002B49] font-bold text-lg">Loading Requests</p>
                    <p className="text-gray-400 text-xs font-medium uppercase tracking-widest">Checking queue...</p>
                </div>
            </div>
        );
    }

    // ─── Error ─────────────────────────────────────────────────────────────────
    if (error) {
        return (
            <div className="flex flex-col items-center justify-center py-32 px-6 gap-5">
                <div className="h-20 w-20 rounded-full bg-red-50 flex items-center justify-center border border-red-100">
                    <AlertTriangle className="h-9 w-9 text-red-400" />
                </div>
                <div className="text-center space-y-1">
                    <p className="text-base font-bold text-[#002B49]">Failed to Load Requests</p>
                    <p className="text-sm text-gray-500 max-w-xs">{error}</p>
                </div>
                <Button onClick={loadData} className="gap-2 h-10 rounded-xl">
                    <RefreshCw className="h-4 w-4" /> Try Again
                </Button>
            </div>
        );
    }

    return (
        <div className="flex flex-col h-full">
            {/* Header + Filters */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-5 border-b border-gray-100">
                <div>
                    <h2 className="text-lg font-extrabold text-[#002B49] tracking-tight">Access Requests</h2>
                    <p className="text-[11px] font-bold text-gray-400 uppercase tracking-widest mt-0.5">
                        {requests.length} {statusFilter || 'total'} request{requests.length !== 1 ? 's' : ''}
                    </p>
                </div>
                <div className="flex items-center gap-2">
                    {(['pending', 'approved', 'rejected', ''] as const).map((s) => (
                        <button
                            key={s}
                            onClick={() => setStatusFilter(s)}
                            className={cn(
                                'px-3 py-1.5 rounded-lg text-[11px] font-bold uppercase tracking-wider transition-all',
                                statusFilter === s
                                    ? 'bg-primary text-white shadow-sm'
                                    : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
                            )}
                        >
                            {s || 'All'}
                        </button>
                    ))}
                    <button
                        onClick={loadData}
                        className="h-8 w-8 flex items-center justify-center rounded-lg bg-gray-50 border border-gray-100 text-gray-400 hover:text-primary hover:bg-primary/5 transition-all"
                    >
                        <RefreshCw className="h-3.5 w-3.5" />
                    </button>
                </div>
            </div>

            {/* Cards */}
            <div className="flex-1 overflow-y-auto p-5">
                {requests.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-24 gap-4">
                        <div className="h-20 w-20 bg-gray-50 rounded-full flex items-center justify-center border-2 border-dashed border-gray-100">
                            <Inbox className="h-9 w-9 text-gray-200" />
                        </div>
                        <p className="text-base font-bold text-[#002B49]">Queue is Clear</p>
                        <p className="text-sm text-gray-400 text-center max-w-xs">
                            No {statusFilter} access requests at this time.
                        </p>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
                        {requests.map((req) => (
                            <div
                                key={req.id}
                                className="group relative bg-white border border-gray-100 rounded-2xl shadow-sm hover:shadow-md transition-all duration-300 overflow-hidden"
                            >
                                {/* Left accent bar by permission type */}
                                <div className={cn(
                                    'absolute top-0 left-0 w-1.5 h-full',
                                    req.requested_permission === 'admin' ? 'bg-purple-400' : 'bg-primary'
                                )} />

                                <div className="pl-5 pr-5 pt-4 pb-4 space-y-3">
                                    {/* Top row: avatar + name + status badges */}
                                    <div className="flex items-start justify-between gap-3">
                                        <div className="flex items-center gap-3">
                                            <div className="h-10 w-10 rounded-xl bg-primary/5 ring-1 ring-primary/10 flex items-center justify-center font-black text-primary text-base flex-shrink-0">
                                                {req.name?.charAt(0)?.toUpperCase() || '?'}
                                            </div>
                                            <div>
                                                <p className="font-extrabold text-[#002B49] text-sm leading-tight">{req.name}</p>
                                                <div className="flex items-center gap-1 text-[11px] text-gray-400 font-medium mt-0.5">
                                                    <Mail className="h-3 w-3" />
                                                    <span className="truncate max-w-[200px]">{req.email}</span>
                                                </div>
                                            </div>
                                        </div>
                                        <div className="flex flex-col items-end gap-1.5 flex-shrink-0">
                                            <span className={cn('px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider ring-1 ring-inset', permColor(req.requested_permission))}>
                                                {req.requested_permission}
                                            </span>
                                            <span className={cn('px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider ring-1 ring-inset', statusColor[req.status])}>
                                                {req.status}
                                            </span>
                                        </div>
                                    </div>

                                    {/* Info row: app + date */}
                                    <div className="grid grid-cols-2 gap-2">
                                        <div className="bg-gray-50 rounded-xl p-2.5 border border-gray-100">
                                            <p className="text-[9px] font-extrabold text-gray-400 uppercase tracking-widest">Application</p>
                                            <div className="flex items-center gap-1.5 mt-1">
                                                <Globe className="h-3 w-3 text-primary/60 flex-shrink-0" />
                                                <span className="text-[12px] font-bold text-[#002B49] truncate">{getRouteName(req.requested_route)}</span>
                                            </div>
                                        </div>
                                        <div className="bg-gray-50 rounded-xl p-2.5 border border-gray-100">
                                            <p className="text-[9px] font-extrabold text-gray-400 uppercase tracking-widest">Requested</p>
                                            <div className="flex items-center gap-1.5 mt-1">
                                                <Calendar className="h-3 w-3 text-gray-400 flex-shrink-0" />
                                                <div>
                                                    <p className="text-[12px] font-bold text-[#002B49] leading-tight">{fmtDate(req.requested_at)}</p>
                                                    <p className="text-[10px] text-gray-400">{fmtTime(req.requested_at)}</p>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Justification */}
                                    {req.justification && (
                                        <div className="relative bg-blue-50/50 border border-blue-100 rounded-xl p-3 overflow-hidden">
                                            <Info className="absolute right-2 top-2 h-5 w-5 text-blue-200" />
                                            <p className="text-[11px] font-bold text-blue-800/60 uppercase tracking-widest mb-1">Justification</p>
                                            <p className="text-[12px] text-gray-700 italic leading-relaxed pr-5 line-clamp-2">"{req.justification}"</p>
                                        </div>
                                    )}

                                    {/* Review info (if already reviewed) */}
                                    {req.reviewed_by && (
                                        <div className="flex items-center gap-2 text-[11px] text-gray-400">
                                            <User className="h-3 w-3" />
                                            <span>Reviewed by <strong className="text-gray-600">{req.reviewed_by}</strong></span>
                                            {req.reviewed_at && <span>on {fmtDate(req.reviewed_at)}</span>}
                                        </div>
                                    )}

                                    {/* Actions — only show for pending */}
                                    {req.status === 'pending' && (
                                        <div className="flex gap-2 pt-1">
                                            <Button
                                                variant="ghost"
                                                className="flex-1 h-9 rounded-xl text-xs font-bold text-gray-400 hover:text-red-500 hover:bg-red-50 border border-transparent hover:border-red-100 transition-all"
                                                onClick={() => openRejectModal(req)}
                                                disabled={processingId === req.id}
                                            >
                                                <XCircle className="h-4 w-4 mr-1.5" /> Reject
                                            </Button>
                                            <Button
                                                className="flex-[1.5] h-9 rounded-xl bg-primary text-white text-xs font-bold shadow-md shadow-primary/10 hover:shadow-primary/20 transition-all active:scale-[0.98]"
                                                onClick={() => handleApprove(req)}
                                                disabled={processingId === req.id}
                                            >
                                                {processingId === req.id
                                                    ? <Loader2 className="h-4 w-4 animate-spin mr-1.5" />
                                                    : <CheckCircle className="h-4 w-4 mr-1.5" />
                                                }
                                                Approve Access
                                            </Button>
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* ── Rejection Modal ── */}
            <Dialog open={!!rejectTarget} onOpenChange={(open) => !open && setRejectTarget(null)}>
                <DialogContent className="sm:max-w-md rounded-2xl border-none shadow-2xl">
                    <DialogHeader>
                        <DialogTitle className="text-lg font-extrabold text-[#002B49]">Reject Access Request</DialogTitle>
                        <DialogDescription className="text-sm text-gray-500 pt-1">
                            Rejecting request from <strong>{rejectTarget?.name}</strong> for{' '}
                            <strong>{rejectTarget ? getRouteName(rejectTarget.requested_route) : ''}</strong>
                        </DialogDescription>
                    </DialogHeader>
                    <div className="py-4 space-y-3">
                        <label className="block text-xs font-bold text-gray-500 uppercase tracking-widest">
                            Reason for Rejection <span className="text-gray-400 normal-case font-normal">(optional)</span>
                        </label>
                        <textarea
                            value={rejectReason}
                            onChange={(e) => setRejectReason(e.target.value)}
                            placeholder="e.g. Access not required for current role..."
                            rows={3}
                            className="w-full px-3 py-2.5 rounded-xl border border-gray-200 bg-gray-50 text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary focus:bg-white transition-all resize-none outline-none"
                        />
                    </div>
                    <DialogFooter className="gap-2">
                        <Button variant="ghost" className="flex-1 rounded-xl h-11 font-bold" onClick={() => setRejectTarget(null)}>
                            Cancel
                        </Button>
                        <Button
                            variant="destructive"
                            className="flex-1 rounded-xl h-11 font-bold bg-red-500 hover:bg-red-600"
                            onClick={handleReject}
                            disabled={rejecting}
                        >
                            {rejecting ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <XCircle className="h-4 w-4 mr-2" />}
                            Confirm Reject
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
};
