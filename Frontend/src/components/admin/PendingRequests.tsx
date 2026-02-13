/**
 * Pending Requests Component
 * Shows and manages pending access requests with friendly names and improved UI
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
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';
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
    Shield
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { toast } from 'sonner';

export const PendingRequests: React.FC = () => {
    const { user } = useAuth();
    const [requests, setRequests] = useState<AccessRequestResponse[]>([]);
    const [routeDefinitions, setRouteDefinitions] = useState<RouteDefinition[]>([]);
    const [loading, setLoading] = useState(true);
    const [processingId, setProcessingId] = useState<number | null>(null);

    const loadData = async () => {
        if (!user) return;

        try {
            setLoading(true);
            const [reqsData, routesData] = await Promise.all([
                getAccessRequests(user.email, 'pending'),
                getRouteDefinitions(user.email)
            ]);
            setRequests(reqsData.requests);
            setRouteDefinitions(routesData);
        } catch (err) {
            console.error('Failed to load data:', err);
            toast.error('Failed to load access requests');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadData();
    }, [user]);

    const getRouteName = (routePath: string) => {
        const route = routeDefinitions.find(r => r.route_path === routePath);
        return route ? route.route_name : routePath;
    };

    const handleApprove = async (requestId: number) => {
        if (!user) return;

        setProcessingId(requestId);
        try {
            await approveAccessRequest(user.email, requestId);
            toast.success('Access request approved');
            await loadData();
        } catch (err) {
            toast.error(err instanceof Error ? err.message : 'Failed to approve request');
        } finally {
            setProcessingId(null);
        }
    };

    const handleReject = async (requestId: number) => {
        if (!user) return;

        const reason = prompt('Please provide a reason for rejection (optional):');
        if (reason === null) return;

        setProcessingId(requestId);
        try {
            await rejectAccessRequest(user.email, requestId, reason || undefined);
            toast.success('Access request rejected');
            await loadData();
        } catch (err) {
            toast.error(err instanceof Error ? err.message : 'Failed to reject request');
        } finally {
            setProcessingId(null);
        }
    };

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center py-32 gap-6 bg-white rounded-2xl">
                <div className="relative">
                    <div className="h-16 w-16 rounded-full border-4 border-primary/10 border-t-primary animate-spin"></div>
                    <Shield className="absolute inset-0 m-auto h-6 w-6 text-primary/40 animate-pulse" />
                </div>
                <div className="text-center space-y-1">
                    <p className="text-[#002B49] font-bold text-lg">Scanning Requests</p>
                    <p className="text-gray-400 text-xs font-medium uppercase tracking-widest">Checking security queue...</p>
                </div>
            </div>
        );
    }

    if (requests.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center py-32 px-6">
                <div className="w-24 h-24 bg-gray-50 rounded-full flex items-center justify-center mb-6 relative">
                    <div className="absolute inset-0 rounded-full border-2 border-dashed border-gray-100 animate-[spin_10s_linear_infinite]"></div>
                    <Inbox className="h-10 w-10 text-gray-200" />
                </div>
                <h3 className="text-xl font-extrabold text-[#002B49] tracking-tight">Queue is Clear</h3>
                <p className="text-gray-400 max-w-[280px] text-center mt-2 text-sm font-medium leading-relaxed">
                    No pending access requests at this time. All users are currently up to date.
                </p>
                <Button variant="outline" className="mt-8 gap-2.5 h-11 px-6 rounded-xl border-gray-100 hover:bg-gray-50 text-[#002B49] font-bold transition-all active:scale-[0.97]" onClick={loadData}>
                    <RefreshCw className="h-4 w-4" />
                    Refresh Queue
                </Button>
            </div>
        );
    }

    return (
        <div className="flex flex-col h-full bg-white">
            <div className="flex justify-between items-center p-6 border-b border-gray-50">
                <div className="space-y-1">
                    <h2 className="text-xl font-extrabold text-[#002B49] tracking-tight">Pending Approval</h2>
                    <p className="text-[11px] font-bold text-gray-400 uppercase tracking-widest">Access Request Queue</p>
                </div>
                <div className="flex items-center gap-2 bg-primary/5 px-3 py-1.5 rounded-full border border-primary/10">
                    <div className="h-1.5 w-1.5 rounded-full bg-primary"></div>
                    <span className="text-[11px] font-extrabold text-[#002B49]">{requests.length} Requests</span>
                </div>
            </div>

            <div className="flex-1 overflow-y-auto p-6 scrollbar-hide">
                <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                    {requests.map((request) => (
                        <div key={request.id} className="group relative flex flex-col bg-white border border-gray-100 rounded-2xl shadow-[0_2px_15px_-3px_rgba(0,0,0,0.02)] hover:shadow-[0_8px_30px_rgb(0,0,0,0.04)] transition-all duration-500 overflow-hidden">
                            {/* Card Header Label */}
                            <div className={cn(
                                "absolute top-0 left-0 w-1.5 h-full transition-all duration-500 group-hover:w-2",
                                request.requested_permission === 'admin' ? "bg-purple-500" : "bg-primary"
                            )}></div>

                            <div className="p-5 space-y-5">
                                <div className="flex justify-between items-start gap-4">
                                    <div className="flex gap-4">
                                        <div className="h-12 w-12 rounded-xl bg-gray-50/50 flex items-center justify-center ring-1 ring-gray-100 group-hover:ring-primary/20 transition-all">
                                            <div className="h-8 w-8 rounded-lg bg-white shadow-sm flex items-center justify-center font-bold text-primary group-hover:scale-110 transition-transform">
                                                {request.name.charAt(0)}
                                            </div>
                                        </div>
                                        <div className="space-y-0.5 mt-0.5">
                                            <h4 className="font-extrabold text-[#002B49] tracking-tight line-clamp-1">{request.name}</h4>
                                            <div className="flex items-center gap-1.5 text-xs text-gray-400 font-medium tracking-tight">
                                                <Mail className="h-3 w-3 " />
                                                {request.email}
                                            </div>
                                        </div>
                                    </div>
                                    <div className={cn(
                                        "px-2.5 py-1 rounded-lg text-[10px] uppercase font-bold tracking-wider ring-1 ring-inset",
                                        request.requested_permission === 'admin'
                                            ? "bg-purple-50 text-purple-700 ring-purple-200/50"
                                            : "bg-primary/5 text-primary ring-primary/20"
                                    )}>
                                        {request.requested_permission}
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <div className="p-3 bg-gray-50/50 rounded-xl border border-gray-100/50 space-y-1 group-hover:bg-white transition-colors">
                                        <p className="text-[10px] font-extrabold text-gray-400 uppercase tracking-widest pl-0.5">Application</p>
                                        <div className="flex items-center gap-2">
                                            <Globe className="h-3.5 w-3.5 text-primary/60" />
                                            <span className="text-[12px] font-bold text-[#002B49] truncate">{getRouteName(request.requested_route)}</span>
                                        </div>
                                    </div>
                                    <div className="p-3 bg-gray-50/50 rounded-xl border border-gray-100/50 space-y-1 group-hover:bg-white transition-colors">
                                        <p className="text-[10px] font-extrabold text-gray-400 uppercase tracking-widest pl-0.5">Request Date</p>
                                        <div className="flex items-center gap-2">
                                            <Calendar className="h-3.5 w-3.5 text-gray-400" />
                                            <span className="text-[12px] font-bold text-[#002B49]">{new Date(request.requested_at).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' })}</span>
                                        </div>
                                    </div>
                                </div>

                                {request.justification && (
                                    <div className="relative p-4 rounded-xl bg-[#F8FAFC] border border-gray-50 overflow-hidden">
                                        <Info className="absolute -right-1 -top-1 h-8 w-8 text-primary/5 opacity-40" />
                                        <p className="text-[13px] text-gray-600 font-medium leading-relaxed italic pr-2">
                                            "{request.justification}"
                                        </p>
                                    </div>
                                )}

                                <div className="flex gap-3 pt-1">
                                    <Button
                                        variant="ghost"
                                        className="flex-1 h-11 rounded-xl text-xs font-bold text-gray-400 hover:text-red-500 hover:bg-red-50 transition-all border border-transparent hover:border-red-100"
                                        onClick={() => handleReject(request.id)}
                                        disabled={processingId === request.id}
                                    >
                                        <XCircle className="h-4 w-4 mr-2" />
                                        Reject
                                    </Button>
                                    <Button
                                        className="flex-[1.5] h-11 rounded-xl bg-primary text-white text-xs font-bold shadow-lg shadow-primary/10 hover:shadow-primary/20 transition-all active:scale-[0.98]"
                                        onClick={() => handleApprove(request.id)}
                                        disabled={processingId === request.id}
                                    >
                                        {processingId === request.id ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <CheckCircle className="h-4 w-4 mr-2" />}
                                        Approve Access
                                    </Button>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};
