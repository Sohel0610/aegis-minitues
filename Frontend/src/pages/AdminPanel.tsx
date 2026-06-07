/**
 * Admin Panel Page – Complete Professional Redesign
 * Fixes:
 *  • Sticky left sidebar (never scrolls with content)
 *  • Az (Title Case) on all labels
 *  • Overview tab with live stats
 *  • Admin Management tab
 *  • Responsive at 100% zoom
 */

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Navigate } from 'react-router-dom';
import { PendingRequests }   from '@/components/admin/PendingRequests';
import { UserPermissions }   from '@/components/admin/UserPermissions';
import { AuditLogs }         from '@/components/admin/AuditLogs';
import { AdminManagement }   from '@/components/admin/AdminManagement';
import { getAccessRequests, getRouteDefinitions } from '@/services/permissionService';
import {
    LayoutDashboard, ClipboardList, Users,
    Activity, ShieldCheck, Shield,
    Clock, CheckCircle2, XCircle, AppWindow,
    ArrowRight, Loader2, UserCog,
} from 'lucide-react';
import { cn } from '@/lib/utils';

type TabType = 'overview' | 'requests' | 'permissions' | 'admins' | 'audit';

interface Stats { pending: number; approved: number; rejected: number; totalApps: number; }

export const AdminPanel: React.FC = () => {
    const { isAdmin, isLoading, user } = useAuth();
    const [activeTab, setActiveTab]   = useState<TabType>('overview');
    const [stats, setStats]           = useState<Stats>({ pending: 0, approved: 0, rejected: 0, totalApps: 0 });
    const [statsLoading, setStatsLoading] = useState(true);

    useEffect(() => {
        if (!user || !isAdmin) return;
        (async () => {
            setStatsLoading(true);
            try {
                const [p, a, r, routes] = await Promise.allSettled([
                    getAccessRequests(user.email, 'pending'),
                    getAccessRequests(user.email, 'approved'),
                    getAccessRequests(user.email, 'rejected'),
                    getRouteDefinitions(user.email),
                ]);
                setStats({
                    pending:   p.status  === 'fulfilled' ? p.value.total   : 0,
                    approved:  a.status  === 'fulfilled' ? a.value.total   : 0,
                    rejected:  r.status  === 'fulfilled' ? r.value.total   : 0,
                    totalApps: routes.status === 'fulfilled' ? routes.value.length : 0,
                });
            } finally { setStatsLoading(false); }
        })();
    }, [user, isAdmin]);

    if (isLoading) return (
        <div className="flex items-center justify-center min-h-screen bg-[#F8FAFC]">
            <div className="flex flex-col items-center gap-3">
                <Loader2 className="h-10 w-10 animate-spin text-primary/40" />
                <p className="text-sm font-semibold text-gray-400">Authenticating Admin Session…</p>
            </div>
        </div>
    );

    if (!isAdmin) return <Navigate to="/access-denied" replace />;

    const tabs: { id: TabType; label: string; Icon: React.FC<any>; badge?: number | null }[] = [
        { id: 'overview',     label: 'Overview',          Icon: LayoutDashboard },
        { id: 'requests',     label: 'Pending Requests',  Icon: ClipboardList, badge: stats.pending || null },
        { id: 'permissions',  label: 'User Permissions',  Icon: Users },
        { id: 'admins',       label: 'Admin Management',  Icon: UserCog },
        { id: 'audit',        label: 'Activity Logs',     Icon: Activity },
    ];

    const statCards = [
        { label: 'Pending Requests', value: stats.pending,   Icon: Clock,        color: 'text-amber-500',   bg: 'bg-amber-50',   border: 'border-amber-100', tab: 'requests'    as TabType },
        { label: 'Total Approved',   value: stats.approved,  Icon: CheckCircle2, color: 'text-emerald-500', bg: 'bg-emerald-50', border: 'border-emerald-100', tab: 'requests'   as TabType },
        { label: 'Total Rejected',   value: stats.rejected,  Icon: XCircle,      color: 'text-red-400',     bg: 'bg-red-50',     border: 'border-red-100',   tab: 'requests'    as TabType },
        { label: 'Applications',     value: stats.totalApps, Icon: AppWindow,    color: 'text-primary',     bg: 'bg-primary/5',  border: 'border-primary/10', tab: 'permissions' as TabType },
    ];

    return (
        /* Full-page fixed layout — sidebar never moves */
        <div className="flex h-screen overflow-hidden bg-[#F8FAFC]" style={{ fontFamily: "'Inter', sans-serif" }}>

            {/* ─────────────────── Fixed Left Sidebar ─────────────────── */}
            <aside className="w-60 shrink-0 bg-white border-r border-gray-100 flex flex-col h-full shadow-sm">
                {/* Top accent */}
                <div className="h-0.5 bg-gradient-to-r from-primary via-blue-400 to-transparent" />

                {/* Brand */}
                <div className="flex items-center gap-2.5 px-5 py-4 border-b border-gray-100">
                    <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center shadow-md shadow-primary/20">
                        <ShieldCheck className="h-4 w-4 text-white" />
                    </div>
                    <div>
                        <p className="text-xs font-extrabold text-[#002B49] leading-tight">Access Control</p>
                        <p className="text-[10px] text-gray-400 font-semibold">Aegis Admin Panel</p>
                    </div>
                </div>

                {/* Navigation */}
                <nav className="flex-1 overflow-y-auto px-3 py-3 space-y-0.5">
                    <p className="px-3 pb-2 pt-1 text-[9px] font-extrabold text-gray-400 uppercase tracking-widest">Navigation</p>
                    {tabs.map(({ id, label, Icon, badge }) => {
                        const active = activeTab === id;
                        return (
                            <button
                                key={id}
                                onClick={() => setActiveTab(id)}
                                className={cn(
                                    'w-full flex items-center justify-between gap-2.5 px-3 py-2.5 rounded-xl text-left transition-all duration-200 group',
                                    active
                                        ? 'bg-primary/8 shadow-[inset_0_0_0_1.5px_rgba(0,93,164,0.12)]'
                                        : 'hover:bg-gray-50'
                                )}
                            >
                                <div className="flex items-center gap-2.5">
                                    <div className={cn(
                                        'p-1.5 rounded-lg transition-all',
                                        active ? 'bg-primary text-white shadow-md shadow-primary/25' : 'bg-gray-100 text-gray-400 group-hover:bg-gray-200'
                                    )}>
                                        <Icon className="h-3.5 w-3.5" />
                                    </div>
                                    <span className={cn('text-[13px] font-semibold', active ? 'text-[#002B49]' : 'text-gray-500 group-hover:text-gray-700')}>
                                        {label}
                                    </span>
                                </div>
                                {badge != null && badge > 0 && (
                                    <span className="h-5 min-w-[20px] px-1.5 rounded-full bg-amber-500 text-white text-[10px] font-extrabold flex items-center justify-center">
                                        {badge}
                                    </span>
                                )}
                            </button>
                        );
                    })}
                </nav>

                {/* User info footer */}
                <div className="px-4 py-3 border-t border-gray-100">
                    <div className="flex items-center gap-2.5 p-2.5 bg-gray-50 rounded-xl">
                        <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center font-extrabold text-primary text-sm flex-shrink-0">
                            {(user?.name || user?.email || 'A').charAt(0).toUpperCase()}
                        </div>
                        <div className="min-w-0">
                            <p className="text-[11px] font-bold text-[#002B49] truncate">{user?.name || 'Administrator'}</p>
                            <p className="text-[10px] text-gray-400 truncate">{user?.email}</p>
                        </div>
                    </div>
                    <button
                        onClick={() => window.location.href = '/'}
                        className="w-full mt-2 flex items-center justify-center gap-1.5 py-1.5 rounded-lg text-[11px] font-semibold text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-all"
                    >
                        <LayoutDashboard className="h-3 w-3" /> Exit To Dashboard
                    </button>
                </div>
            </aside>

            {/* ─────────────────── Scrollable Content Area ─────────────────── */}
            <main className="flex-1 overflow-y-auto min-w-0">
                {/* Top header bar */}
                <div className="sticky top-0 z-20 bg-white border-b border-gray-100 shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
                    <div className="flex items-center justify-between px-6 py-3">
                        <div>
                            <h1 className="text-base font-extrabold text-[#002B49] tracking-tight">
                                {tabs.find(t => t.id === activeTab)?.label}
                            </h1>
                            <p className="text-[11px] text-gray-400 font-medium">
                                Aegis Platform · Access Control Centre
                            </p>
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="flex items-center gap-1.5 bg-emerald-50 px-2.5 py-1 rounded-lg border border-emerald-100">
                                <div className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                                <span className="text-[11px] font-bold text-emerald-700">System Active</span>
                            </div>
                            <div className="flex items-center gap-1.5 bg-primary/5 px-2.5 py-1 rounded-lg border border-primary/10">
                                <Shield className="h-3 w-3 text-primary" />
                                <span className="text-[11px] font-bold text-primary">Admin</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Tab content */}
                <div className="p-6">

                    {/* ── Overview ── */}
                    {activeTab === 'overview' && (
                        <div className="space-y-6 max-w-5xl">
                            {/* Stats row */}
                            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                                {statCards.map(({ label, value, Icon, color, bg, border, tab }) => (
                                    <button
                                        key={label}
                                        onClick={() => setActiveTab(tab)}
                                        className={cn(
                                            'group text-left bg-white border rounded-2xl p-5 hover:shadow-md transition-all duration-300',
                                            border
                                        )}
                                    >
                                        <div className={cn('h-10 w-10 rounded-xl flex items-center justify-center mb-3', bg)}>
                                            <Icon className={cn('h-5 w-5', color)} />
                                        </div>
                                        <p className="text-3xl font-extrabold text-[#002B49] leading-none mb-1">
                                            {statsLoading ? <span className="text-gray-300">—</span> : value}
                                        </p>
                                        <p className="text-[11px] text-gray-400 font-bold uppercase tracking-widest">{label}</p>
                                        <div className={cn('flex items-center gap-1 mt-2 text-[10px] font-semibold transition-colors', color)}>
                                            <span>View Details</span>
                                            <ArrowRight className="h-3 w-3 group-hover:translate-x-0.5 transition-transform" />
                                        </div>
                                    </button>
                                ))}
                            </div>

                            {/* Quick actions */}
                            <div className="bg-white border border-gray-100 rounded-2xl p-5">
                                <h3 className="text-sm font-extrabold text-[#002B49] mb-4">Quick Actions</h3>
                                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                                    {[
                                        { tab: 'requests'    as TabType, Icon: ClipboardList, label: 'Review Requests',   sub: `${stats.pending} pending`,      bg: 'bg-amber-50',  border: 'border-amber-100',  text: 'text-amber-800',  sub_text: 'text-amber-600'  },
                                        { tab: 'permissions' as TabType, Icon: Users,         label: 'Manage Users',      sub: 'Grant or revoke access',        bg: 'bg-blue-50',   border: 'border-blue-100',   text: 'text-blue-800',   sub_text: 'text-blue-500'   },
                                        { tab: 'admins'      as TabType, Icon: UserCog,       label: 'Admin Management',  sub: 'Add or remove admins',          bg: 'bg-purple-50', border: 'border-purple-100', text: 'text-purple-800', sub_text: 'text-purple-500' },
                                        { tab: 'audit'       as TabType, Icon: Activity,      label: 'Activity Logs',     sub: 'All system events',             bg: 'bg-gray-50',   border: 'border-gray-200',   text: 'text-gray-700',   sub_text: 'text-gray-500'   },
                                    ].map(({ tab, Icon, label, sub, bg, border, text, sub_text }) => (
                                        <button
                                            key={tab}
                                            onClick={() => setActiveTab(tab)}
                                            className={cn('flex items-center gap-3 p-4 rounded-xl border text-left hover:shadow-sm transition-all', bg, border)}
                                        >
                                            <div className={cn('h-9 w-9 rounded-xl flex items-center justify-center flex-shrink-0', bg)}>
                                                <Icon className={cn('h-4 w-4', text)} />
                                            </div>
                                            <div>
                                                <p className={cn('text-sm font-bold', text)}>{label}</p>
                                                <p className={cn('text-[11px] font-medium', sub_text)}>{sub}</p>
                                            </div>
                                        </button>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}

                    {activeTab === 'requests'    && <div className="bg-white rounded-2xl border border-gray-100 shadow-sm"><PendingRequests /></div>}
                    {activeTab === 'permissions' && <div className="bg-white rounded-2xl border border-gray-100 shadow-sm"><UserPermissions /></div>}
                    {activeTab === 'admins'      && <div className="bg-white rounded-2xl border border-gray-100 shadow-sm"><AdminManagement /></div>}
                    {activeTab === 'audit'       && <div className="bg-white rounded-2xl border border-gray-100 shadow-sm"><AuditLogs /></div>}

                </div>
            </main>
        </div>
    );
};
