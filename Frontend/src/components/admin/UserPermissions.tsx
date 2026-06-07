/**
 * User Permissions Component
 * Proper table view: Application Scope | Active User | Assigned Role | Assignment Date | Actions
 */

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import {
    getRoutePermissions,
    assignPermission,
    revokePermission,
    getRouteDefinitions,
    type RouteDefinition,
} from '@/services/permissionService';
import { Button } from '@/components/ui/button';
import { Input }  from '@/components/ui/input';
import { Label }  from '@/components/ui/label';
import {
    Dialog, DialogContent, DialogDescription,
    DialogFooter, DialogHeader, DialogTitle, DialogTrigger,
} from '@/components/ui/dialog';
import {
    Search, UserPlus, Trash2, RefreshCcw,
    Shield, ShieldCheck, Edit3, Loader2,
    Users, AlertTriangle, ChevronDown, Calendar, Globe,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { toast } from 'sonner';

type Role = 'view' | 'edit' | 'admin';

const ROLE: Record<Role, { label: string; bg: string; text: string; ring: string }> = {
    view:  { label: 'Viewer', bg: 'bg-blue-50',   text: 'text-blue-700',   ring: 'ring-blue-200/60' },
    edit:  { label: 'Editor', bg: 'bg-amber-50',  text: 'text-amber-700',  ring: 'ring-amber-200/60' },
    admin: { label: 'Admin',  bg: 'bg-purple-50', text: 'text-purple-700', ring: 'ring-purple-200/60' },
};

const fmtDate = (iso: string) => {
    if (!iso) return '—';
    try {
        const d = new Date(iso.includes('Z') || iso.includes('+') ? iso : iso + 'Z');
        return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
    } catch { return iso; }
};

const TH = ({ children, className = '' }: { children: React.ReactNode; className?: string }) => (
    <th className={cn('px-4 py-3 text-left text-[11px] font-extrabold text-gray-400 uppercase tracking-widest whitespace-nowrap', className)}>
        {children}
    </th>
);

export const UserPermissions: React.FC = () => {
    const { user } = useAuth();
    const [selectedRoute, setSelectedRoute]     = useState('');
    const [routes, setRoutes]                   = useState<RouteDefinition[]>([]);
    const [permissions, setPermissions]         = useState<any[]>([]);
    const [loading, setLoading]                 = useState(false);
    const [routesLoading, setRoutesLoading]     = useState(true);
    const [error, setError]                     = useState<string | null>(null);
    const [search, setSearch]                   = useState('');

    // Add-user dialog
    const [addOpen, setAddOpen]     = useState(false);
    const [newEmail, setNewEmail]   = useState('');
    const [newRole, setNewRole]     = useState<Role>('view');
    const [adding, setAdding]       = useState(false);

    // Revoke dialog
    const [revokeTarget, setRevokeTarget] = useState<{ email: string } | null>(null);
    const [revoking, setRevoking]         = useState(false);

    const loadRoutes = async () => {
        if (!user) return;
        setRoutesLoading(true);
        try {
            const data = await getRouteDefinitions(user.email);
            setRoutes(data);
            if (data.length > 0) setSelectedRoute(s => s || data[0].route_path);
        } catch { toast.error('Failed to load application list'); }
        finally { setRoutesLoading(false); }
    };

    const loadPermissions = async () => {
        if (!user || !selectedRoute) return;
        setLoading(true); setError(null);
        try {
            const data = await getRoutePermissions(user.email, selectedRoute);
            setPermissions(data.permissions || []);
        } catch (err) {
            const msg = err instanceof Error ? err.message : 'Failed to load permissions';
            setError(msg); toast.error(msg);
        } finally { setLoading(false); }
    };

    useEffect(() => { loadRoutes(); }, [user]);
    useEffect(() => { if (selectedRoute) loadPermissions(); }, [selectedRoute, user]);

    const handleRoleChange = async (email: string, role: Role) => {
        if (!user) return;
        try {
            await assignPermission(user.email, email, selectedRoute, role);
            toast.success(`Role updated to ${ROLE[role].label} for ${email}`);
            setPermissions(p => p.map(x => x.email === email ? { ...x, permission_type: role } : x));
        } catch (err) {
            toast.error(err instanceof Error ? err.message : 'Failed to update role');
            loadPermissions();
        }
    };

    const handleRevoke = async () => {
        if (!user || !revokeTarget) return;
        setRevoking(true);
        try {
            await revokePermission(user.email, revokeTarget.email, selectedRoute);
            toast.success(`Access revoked for ${revokeTarget.email}`);
            setRevokeTarget(null);
            loadPermissions();
        } catch (err) { toast.error(err instanceof Error ? err.message : 'Revoke failed'); }
        finally { setRevoking(false); }
    };

    const handleAdd = async () => {
        if (!user || !newEmail.trim()) return;
        setAdding(true);
        try {
            await assignPermission(user.email, newEmail.trim(), selectedRoute, newRole);
            toast.success(`${newEmail.trim()} added as ${ROLE[newRole].label}`);
            setNewEmail(''); setAddOpen(false); loadPermissions();
        } catch (err) { toast.error(err instanceof Error ? err.message : 'Failed to add user'); }
        finally { setAdding(false); }
    };

    const filtered = permissions.filter(p =>
        p.email?.toLowerCase().includes(search.toLowerCase())
    );

    const currentApp = routes.find(r => r.route_path === selectedRoute);

    return (
        <div className="flex flex-col">
            {/* ── Header ── */}
            <div className="flex flex-col gap-4 p-5 border-b border-gray-100">
                {/* Row 1: title + add button */}
                <div className="flex items-center justify-between gap-3">
                    <div>
                        <h2 className="text-base font-extrabold text-[#002B49]">User Permissions</h2>
                        <p className="text-[11px] text-gray-400 font-medium mt-0.5">
                            Manage per-application access across the platform
                        </p>
                    </div>
                    <Dialog open={addOpen} onOpenChange={setAddOpen}>
                        <DialogTrigger asChild>
                            <Button className="gap-2 h-9 px-4 rounded-xl font-bold text-sm shadow-md shadow-primary/10">
                                <UserPlus className="h-4 w-4" /> Grant Access
                            </Button>
                        </DialogTrigger>
                        <DialogContent className="sm:max-w-md rounded-2xl border-none shadow-2xl">
                            <DialogHeader>
                                <DialogTitle className="text-lg font-extrabold text-[#002B49]">Grant User Access</DialogTitle>
                                <DialogDescription className="text-sm text-gray-500">
                                    Assign access for <strong>{currentApp?.route_name || selectedRoute}</strong>
                                </DialogDescription>
                            </DialogHeader>
                            <div className="space-y-5 py-4">
                                <div className="space-y-1.5">
                                    <Label className="text-xs font-bold text-gray-500 uppercase tracking-widest">Email Address</Label>
                                    <Input
                                        placeholder="employee@adani.com"
                                        className="h-11 rounded-xl border-gray-200 bg-gray-50 focus:bg-white"
                                        value={newEmail}
                                        onChange={e => setNewEmail(e.target.value)}
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label className="text-xs font-bold text-gray-500 uppercase tracking-widest">Assign Role</Label>
                                    <div className="grid grid-cols-3 gap-2">
                                        {(Object.keys(ROLE) as Role[]).map(r => (
                                            <button
                                                key={r} type="button"
                                                onClick={() => setNewRole(r)}
                                                className={cn(
                                                    'flex flex-col items-center gap-2 py-3 rounded-xl border-2 transition-all',
                                                    newRole === r ? 'border-primary bg-primary/5' : 'border-gray-100 hover:border-gray-200'
                                                )}
                                            >
                                                <div className={cn('p-1.5 rounded-full', newRole === r ? 'bg-primary text-white' : 'bg-gray-100 text-gray-400')}>
                                                    {r === 'view' ? <Shield className="h-4 w-4" /> : r === 'edit' ? <Edit3 className="h-4 w-4" /> : <ShieldCheck className="h-4 w-4" />}
                                                </div>
                                                <p className={cn('text-xs font-bold', newRole === r ? 'text-[#002B49]' : 'text-gray-500')}>{ROLE[r].label}</p>
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            </div>
                            <DialogFooter className="gap-2">
                                <Button variant="ghost" className="flex-1 rounded-xl h-11 font-bold" onClick={() => setAddOpen(false)}>Cancel</Button>
                                <Button className="flex-1 rounded-xl h-11 font-bold" onClick={handleAdd} disabled={adding || !newEmail.trim()}>
                                    {adding && <Loader2 className="h-4 w-4 animate-spin mr-2" />} Assign Access
                                </Button>
                            </DialogFooter>
                        </DialogContent>
                    </Dialog>
                </div>

                {/* Row 2: Application Scope selector + search + refresh */}
                <div className="flex flex-wrap items-center gap-3">
                    {/* Application Scope */}
                    <div className="flex flex-col gap-1">
                        <label className="text-[10px] font-extrabold text-gray-400 uppercase tracking-widest flex items-center gap-1">
                            <Globe className="h-3 w-3" /> Application Scope
                        </label>
                        <div className="relative">
                            <select
                                value={selectedRoute}
                                onChange={e => setSelectedRoute(e.target.value)}
                                disabled={routesLoading}
                                className="h-9 pl-3 pr-8 bg-white border border-gray-200 rounded-xl text-sm font-semibold text-[#002B49] appearance-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all disabled:opacity-50 min-w-[220px]"
                            >
                                {routesLoading
                                    ? <option>Loading applications…</option>
                                    : routes.length === 0
                                        ? <option value="">No applications found</option>
                                        : routes.map(r => <option key={r.route_path} value={r.route_path}>{r.route_name}</option>)
                                }
                            </select>
                            <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-gray-400 pointer-events-none" />
                        </div>
                    </div>

                    {/* Search */}
                    <div className="flex flex-col gap-1">
                        <label className="text-[10px] font-extrabold text-gray-400 uppercase tracking-widest">Search Users</label>
                        <div className="relative">
                            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-gray-400" />
                            <Input
                                placeholder="Filter by email…"
                                className="pl-8 h-9 w-52 rounded-xl border-gray-200 bg-white text-sm"
                                value={search}
                                onChange={e => setSearch(e.target.value)}
                            />
                        </div>
                    </div>

                    {/* Refresh */}
                    <button
                        onClick={loadPermissions}
                        className="self-end h-9 w-9 flex items-center justify-center rounded-xl bg-gray-50 border border-gray-200 text-gray-400 hover:text-primary hover:bg-primary/5 transition-all"
                    >
                        <RefreshCcw className={cn('h-3.5 w-3.5', loading && 'animate-spin')} />
                    </button>

                    {/* Count badge */}
                    <div className="self-end ml-auto flex items-center gap-1.5 bg-gray-50 border border-gray-100 px-3 py-1.5 rounded-xl">
                        <Users className="h-3.5 w-3.5 text-gray-400" />
                        <span className="text-[12px] font-bold text-gray-600">{filtered.length} User{filtered.length !== 1 ? 's' : ''}</span>
                    </div>
                </div>
            </div>

            {/* ── Table ── */}
            <div className="overflow-x-auto">
                {loading ? (
                    <div className="flex items-center justify-center py-24 gap-3">
                        <Loader2 className="h-7 w-7 animate-spin text-primary/30" />
                        <p className="text-sm text-gray-400 font-medium">Loading user permissions…</p>
                    </div>
                ) : error ? (
                    <div className="flex flex-col items-center justify-center py-20 gap-4">
                        <div className="h-14 w-14 rounded-full bg-red-50 flex items-center justify-center">
                            <AlertTriangle className="h-6 w-6 text-red-400" />
                        </div>
                        <p className="text-sm font-bold text-[#002B49]">Failed To Load Permissions</p>
                        <p className="text-xs text-gray-400 max-w-xs text-center">{error}</p>
                        <Button onClick={loadPermissions} size="sm" className="gap-2 rounded-xl">
                            <RefreshCcw className="h-3.5 w-3.5" /> Retry
                        </Button>
                    </div>
                ) : filtered.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-24 gap-3">
                        <div className="h-16 w-16 bg-gray-50 rounded-full flex items-center justify-center border-2 border-dashed border-gray-100">
                            <Users className="h-7 w-7 text-gray-200" />
                        </div>
                        <p className="text-sm font-bold text-[#002B49]">No Users Found</p>
                        <p className="text-xs text-gray-400">{search ? 'Try a different search term.' : 'No users have access to this application yet.'}</p>
                        {!search && (
                            <Button size="sm" className="gap-2 rounded-xl mt-1" onClick={() => setAddOpen(true)}>
                                <UserPlus className="h-3.5 w-3.5" /> Add First User
                            </Button>
                        )}
                    </div>
                ) : (
                    <table className="w-full">
                        <thead className="bg-gray-50 border-b border-gray-100">
                            <tr>
                                <TH className="pl-6">Active User</TH>
                                <TH>Application Scope</TH>
                                <TH>Assigned Role</TH>
                                <TH>Assignment Date</TH>
                                <TH>Assigned By</TH>
                                <TH className="text-right pr-6">Actions</TH>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-50">
                            {filtered.map(perm => {
                                const role = (perm.permission_type || 'view') as Role;
                                const cfg  = ROLE[role] || ROLE.view;
                                return (
                                    <tr key={perm.email} className="group hover:bg-gray-50/60 transition-colors">
                                        {/* Active User */}
                                        <td className="px-4 py-3.5 pl-6">
                                            <div className="flex items-center gap-2.5">
                                                <div className="h-8 w-8 rounded-lg bg-primary/5 ring-1 ring-primary/10 flex items-center justify-center font-black text-primary text-xs flex-shrink-0">
                                                    {perm.email?.charAt(0)?.toUpperCase()}
                                                </div>
                                                <p className="text-[13px] font-semibold text-[#002B49] truncate max-w-[180px]">{perm.email}</p>
                                            </div>
                                        </td>
                                        {/* Application Scope */}
                                        <td className="px-4 py-3.5">
                                            <div className="flex items-center gap-1.5">
                                                <Globe className="h-3 w-3 text-gray-300 flex-shrink-0" />
                                                <span className="text-[12px] font-semibold text-gray-600 truncate max-w-[140px]">
                                                    {currentApp?.route_name || selectedRoute.replace(/^\//, '')}
                                                </span>
                                            </div>
                                            <p className="text-[10px] text-gray-400 mt-0.5 pl-4">{selectedRoute}</p>
                                        </td>
                                        {/* Assigned Role — 3-way toggle */}
                                        <td className="px-4 py-3.5">
                                            <div className="flex items-center gap-2">
                                                <div className="inline-flex items-center bg-gray-100 rounded-lg p-0.5 gap-0.5">
                                                    {(Object.keys(ROLE) as Role[]).map(r => (
                                                        <button
                                                            key={r}
                                                            onClick={() => role !== r && handleRoleChange(perm.email, r)}
                                                            className={cn(
                                                                'px-2.5 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider transition-all',
                                                                role === r
                                                                    ? 'bg-white text-[#002B49] shadow-sm ring-1 ring-gray-200'
                                                                    : 'text-gray-400 hover:text-gray-600'
                                                            )}
                                                        >{ROLE[r].label}</button>
                                                    ))}
                                                </div>
                                                <span className={cn('hidden sm:inline-flex px-2 py-0.5 rounded-md text-[10px] font-extrabold uppercase ring-1 ring-inset', cfg.bg, cfg.text, cfg.ring)}>
                                                    {cfg.label}
                                                </span>
                                            </div>
                                        </td>
                                        {/* Assignment Date */}
                                        <td className="px-4 py-3.5">
                                            <div className="flex items-center gap-1.5 text-[12px] text-gray-600 font-medium">
                                                <Calendar className="h-3 w-3 text-gray-300 flex-shrink-0" />
                                                {fmtDate(perm.assigned_at)}
                                            </div>
                                        </td>
                                        {/* Assigned By */}
                                        <td className="px-4 py-3.5">
                                            <p className="text-[12px] text-gray-500 font-medium truncate max-w-[130px]">
                                                {perm.assigned_by || '—'}
                                            </p>
                                        </td>
                                        {/* Actions */}
                                        <td className="px-4 py-3.5 pr-6 text-right">
                                            <button
                                                onClick={() => setRevokeTarget({ email: perm.email })}
                                                className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-[11px] font-bold text-gray-400 hover:text-red-600 hover:bg-red-50 transition-all border border-transparent hover:border-red-100"
                                                title="Revoke access"
                                            >
                                                <Trash2 className="h-3.5 w-3.5" /> Revoke
                                            </button>
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                )}
            </div>

            {/* ── Revoke Confirm Modal ── */}
            <Dialog open={!!revokeTarget} onOpenChange={open => !open && setRevokeTarget(null)}>
                <DialogContent className="sm:max-w-sm rounded-2xl border-none shadow-2xl">
                    <DialogHeader>
                        <DialogTitle className="text-lg font-extrabold text-[#002B49]">Revoke Access?</DialogTitle>
                        <DialogDescription className="text-sm text-gray-500 pt-1">
                            Remove all access for <strong>{revokeTarget?.email}</strong> from{' '}
                            <strong>{currentApp?.route_name || selectedRoute}</strong>. They can re-apply later.
                        </DialogDescription>
                    </DialogHeader>
                    <DialogFooter className="gap-2 pt-2">
                        <Button variant="ghost" className="flex-1 rounded-xl h-11 font-bold" onClick={() => setRevokeTarget(null)}>Cancel</Button>
                        <Button variant="destructive" className="flex-1 rounded-xl h-11 font-bold bg-red-500 hover:bg-red-600" onClick={handleRevoke} disabled={revoking}>
                            {revoking ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Trash2 className="h-4 w-4 mr-2" />}
                            Revoke Access
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
};
