/**
 * Admin Management Component
 * Platform-wide admin management:
 *  - List all platform admins
 *  - Add new admin
 *  - Remove existing admin
 *  - All-users view across apps
 */

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import {
    getPlatformAdmins, grantPlatformRole, revokePlatformRole, getAllPlatformUsers,
} from '@/services/permissionService';
import { Button } from '@/components/ui/button';
import { Input }  from '@/components/ui/input';
import { Label }  from '@/components/ui/label';
import {
    Dialog, DialogContent, DialogDescription,
    DialogFooter, DialogHeader, DialogTitle,
} from '@/components/ui/dialog';
import {
    UserPlus, Trash2, RefreshCcw, ShieldCheck, Users,
    AlertTriangle, Loader2, Globe, Shield, Search, Crown,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { toast } from 'sonner';

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

type Tab = 'admins' | 'allusers';

export const AdminManagement: React.FC = () => {
    const { user } = useAuth();
    const [activeTab, setActiveTab]   = useState<Tab>('admins');
    const [admins, setAdmins]         = useState<any[]>([]);
    const [allUsers, setAllUsers]     = useState<any[]>([]);
    const [loading, setLoading]       = useState(true);
    const [error, setError]           = useState<string | null>(null);
    const [search, setSearch]         = useState('');

    // Add admin dialog
    const [addOpen, setAddOpen]     = useState(false);
    const [newEmail, setNewEmail]   = useState('');
    const [adding, setAdding]       = useState(false);

    // Remove admin dialog
    const [removeTarget, setRemoveTarget] = useState<{ email: string; role: string } | null>(null);
    const [removing, setRemoving]         = useState(false);

    const loadAdmins = async () => {
        if (!user) return;
        setLoading(true); setError(null);
        try {
            const data = await getPlatformAdmins(user.email);
            setAdmins(data.admins || []);
        } catch (err) {
            const msg = err instanceof Error ? err.message : 'Failed to load platform admins';
            setError(msg); toast.error(msg);
        } finally { setLoading(false); }
    };

    const loadAllUsers = async () => {
        if (!user) return;
        setLoading(true); setError(null);
        try {
            const data = await getAllPlatformUsers(user.email);
            setAllUsers(data.users || []);
        } catch (err) {
            const msg = err instanceof Error ? err.message : 'Failed to load platform users';
            setError(msg); toast.error(msg);
        } finally { setLoading(false); }
    };

    useEffect(() => {
        if (activeTab === 'admins') loadAdmins();
        else loadAllUsers();
    }, [user, activeTab]);

    const handleAddAdmin = async () => {
        if (!user || !newEmail.trim()) return;
        setAdding(true);
        try {
            await grantPlatformRole(user.email, newEmail.trim(), 'admin');
            toast.success(`${newEmail.trim()} added as platform admin`);
            setNewEmail(''); setAddOpen(false); loadAdmins();
        } catch (err) { toast.error(err instanceof Error ? err.message : 'Failed to add admin'); }
        finally { setAdding(false); }
    };

    const handleRemove = async () => {
        if (!user || !removeTarget) return;
        if (removeTarget.email.toLowerCase() === user.email.toLowerCase()) {
            toast.error("You cannot remove your own admin access");
            setRemoveTarget(null); return;
        }
        setRemoving(true);
        try {
            await revokePlatformRole(user.email, removeTarget.email);
            toast.success(`Admin access removed for ${removeTarget.email}`);
            setRemoveTarget(null); loadAdmins();
        } catch (err) { toast.error(err instanceof Error ? err.message : 'Failed to remove admin'); }
        finally { setRemoving(false); }
    };

    const filteredAdmins  = admins.filter(a   => a.email?.toLowerCase().includes(search.toLowerCase()));
    const filteredUsers   = allUsers.filter(u  => u.email?.toLowerCase().includes(search.toLowerCase()));

    return (
        <div className="flex flex-col">
            {/* ── Header ── */}
            <div className="p-5 border-b border-gray-100 space-y-4">
                <div className="flex items-center justify-between">
                    <div>
                        <h2 className="text-base font-extrabold text-[#002B49]">Admin Management</h2>
                        <p className="text-[11px] text-gray-400 font-medium mt-0.5">
                            Manage platform administrators and view all user permissions
                        </p>
                    </div>
                    {activeTab === 'admins' && (
                        <Button
                            className="gap-2 h-9 px-4 rounded-xl font-bold text-sm shadow-md shadow-primary/10"
                            onClick={() => setAddOpen(true)}
                        >
                            <UserPlus className="h-4 w-4" /> Add Admin
                        </Button>
                    )}
                </div>

                {/* Sub-tabs + search */}
                <div className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-1 bg-gray-100 rounded-xl p-1">
                        {([
                            { id: 'admins'   as Tab, label: 'Platform Admins', Icon: Crown },
                            { id: 'allusers' as Tab, label: 'All Users',       Icon: Users },
                        ]).map(({ id, label, Icon }) => (
                            <button
                                key={id}
                                onClick={() => setActiveTab(id)}
                                className={cn(
                                    'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[12px] font-bold transition-all',
                                    activeTab === id ? 'bg-white text-[#002B49] shadow-sm' : 'text-gray-500 hover:text-gray-700'
                                )}
                            >
                                <Icon className="h-3.5 w-3.5" />
                                {label}
                                <span className="text-[10px] font-extrabold text-gray-400">
                                    ({activeTab === id ? (id === 'admins' ? admins.length : allUsers.length) : '…'})
                                </span>
                            </button>
                        ))}
                    </div>
                    <div className="relative">
                        <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-gray-400" />
                        <Input
                            placeholder="Search by email…"
                            className="pl-8 h-9 w-52 rounded-xl border-gray-200 bg-white text-sm"
                            value={search}
                            onChange={e => setSearch(e.target.value)}
                        />
                    </div>
                    <button
                        onClick={() => activeTab === 'admins' ? loadAdmins() : loadAllUsers()}
                        className="h-9 w-9 flex items-center justify-center rounded-xl bg-gray-50 border border-gray-200 text-gray-400 hover:text-primary hover:bg-primary/5 transition-all"
                    >
                        <RefreshCcw className={cn('h-3.5 w-3.5', loading && 'animate-spin')} />
                    </button>
                </div>
            </div>

            {/* ── Content ── */}
            {loading ? (
                <div className="flex items-center justify-center py-24 gap-3">
                    <Loader2 className="h-7 w-7 animate-spin text-primary/30" />
                    <p className="text-sm text-gray-400 font-medium">Loading…</p>
                </div>
            ) : error ? (
                <div className="flex flex-col items-center justify-center py-20 gap-4">
                    <div className="h-14 w-14 rounded-full bg-red-50 flex items-center justify-center">
                        <AlertTriangle className="h-6 w-6 text-red-400" />
                    </div>
                    <p className="text-sm font-bold text-[#002B49]">Failed To Load Data</p>
                    <p className="text-xs text-gray-400 max-w-xs text-center">{error}</p>
                    <Button onClick={() => activeTab === 'admins' ? loadAdmins() : loadAllUsers()} size="sm" className="gap-2 rounded-xl">
                        <RefreshCcw className="h-3.5 w-3.5" /> Retry
                    </Button>
                </div>
            ) : activeTab === 'admins' ? (
                /* ── Platform Admins Table ── */
                filteredAdmins.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-20 gap-3">
                        <div className="h-16 w-16 bg-gray-50 rounded-full flex items-center justify-center border-2 border-dashed border-gray-100">
                            <ShieldCheck className="h-7 w-7 text-gray-200" />
                        </div>
                        <p className="text-sm font-bold text-[#002B49]">No Platform Admins Found</p>
                        <Button size="sm" className="gap-2 rounded-xl mt-1" onClick={() => setAddOpen(true)}>
                            <UserPlus className="h-3.5 w-3.5" /> Add First Admin
                        </Button>
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead className="bg-gray-50 border-b border-gray-100">
                                <tr>
                                    <TH className="pl-6">Administrator</TH>
                                    <TH>Platform Role</TH>
                                    <TH>Granted On</TH>
                                    <TH>Granted By</TH>
                                    <TH className="text-right pr-6">Actions</TH>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-50 bg-white">
                                {filteredAdmins.map(admin => {
                                    const isMe = admin.email?.toLowerCase() === user?.email?.toLowerCase();
                                    return (
                                        <tr key={admin.email} className="group hover:bg-gray-50/60 transition-colors">
                                            <td className="px-4 py-3.5 pl-6">
                                                <div className="flex items-center gap-2.5">
                                                    <div className={cn(
                                                        'h-8 w-8 rounded-lg flex items-center justify-center font-black text-xs flex-shrink-0',
                                                        isMe ? 'bg-primary text-white' : 'bg-purple-50 text-purple-600 ring-1 ring-purple-200/50'
                                                    )}>
                                                        {admin.email?.charAt(0)?.toUpperCase()}
                                                    </div>
                                                    <div>
                                                        <p className="text-[13px] font-semibold text-[#002B49] truncate max-w-[200px]">{admin.email}</p>
                                                        {isMe && <span className="text-[10px] font-bold text-primary">You</span>}
                                                    </div>
                                                </div>
                                            </td>
                                            <td className="px-4 py-3.5">
                                                <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-purple-50 text-purple-700 ring-1 ring-inset ring-purple-200/60">
                                                    <Crown className="h-3 w-3" />
                                                    <span className="text-[10px] font-extrabold uppercase tracking-wider">
                                                        {admin.role || 'Admin'}
                                                    </span>
                                                </div>
                                            </td>
                                            <td className="px-4 py-3.5">
                                                <p className="text-[12px] font-medium text-gray-600">{fmtDate(admin.granted_at)}</p>
                                            </td>
                                            <td className="px-4 py-3.5">
                                                <p className="text-[12px] text-gray-500 font-medium truncate max-w-[140px]">
                                                    {admin.granted_by || '—'}
                                                </p>
                                            </td>
                                            <td className="px-4 py-3.5 pr-6 text-right">
                                                {isMe ? (
                                                    <span className="text-[11px] text-gray-300 font-medium">Cannot remove yourself</span>
                                                ) : (
                                                    <button
                                                        onClick={() => setRemoveTarget({ email: admin.email, role: admin.role })}
                                                        className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-[11px] font-bold text-gray-400 hover:text-red-600 hover:bg-red-50 transition-all border border-transparent hover:border-red-100"
                                                    >
                                                        <Trash2 className="h-3.5 w-3.5" /> Remove Admin
                                                    </button>
                                                )}
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                )
            ) : (
                /* ── All Users Table ── */
                filteredUsers.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-20 gap-3">
                        <div className="h-16 w-16 bg-gray-50 rounded-full flex items-center justify-center border-2 border-dashed border-gray-100">
                            <Users className="h-7 w-7 text-gray-200" />
                        </div>
                        <p className="text-sm font-bold text-[#002B49]">No Users Found</p>
                        <p className="text-xs text-gray-400">{search ? 'Try a different search.' : 'No users have any permissions yet.'}</p>
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead className="bg-gray-50 border-b border-gray-100">
                                <tr>
                                    <TH className="pl-6">User</TH>
                                    <TH>Application</TH>
                                    <TH>Assigned Role</TH>
                                    <TH>Assignment Date</TH>
                                    <TH className="pr-6">Assigned By</TH>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-50 bg-white">
                                {filteredUsers.map((u, i) => (
                                    <tr key={`${u.email}-${u.route_path}-${i}`} className="group hover:bg-gray-50/60 transition-colors">
                                        <td className="px-4 py-3.5 pl-6">
                                            <div className="flex items-center gap-2.5">
                                                <div className="h-8 w-8 rounded-lg bg-primary/5 ring-1 ring-primary/10 flex items-center justify-center font-black text-primary text-xs flex-shrink-0">
                                                    {u.email?.charAt(0)?.toUpperCase()}
                                                </div>
                                                <p className="text-[13px] font-semibold text-[#002B49] truncate max-w-[180px]">{u.email}</p>
                                            </div>
                                        </td>
                                        <td className="px-4 py-3.5">
                                            <div className="flex items-center gap-1.5">
                                                <Globe className="h-3 w-3 text-gray-300" />
                                                <span className="text-[12px] text-gray-600 font-medium">{u.route_path || '—'}</span>
                                            </div>
                                        </td>
                                        <td className="px-4 py-3.5">
                                            <span className={cn(
                                                'inline-flex px-2 py-0.5 rounded-md text-[10px] font-extrabold uppercase ring-1 ring-inset',
                                                u.permission_type === 'admin' ? 'bg-purple-50 text-purple-700 ring-purple-200/60' :
                                                u.permission_type === 'edit'  ? 'bg-amber-50  text-amber-700  ring-amber-200/60'  :
                                                'bg-blue-50 text-blue-700 ring-blue-200/60'
                                            )}>
                                                {u.permission_type || 'Viewer'}
                                            </span>
                                        </td>
                                        <td className="px-4 py-3.5">
                                            <p className="text-[12px] text-gray-600 font-medium">{fmtDate(u.assigned_at)}</p>
                                        </td>
                                        <td className="px-4 py-3.5 pr-6">
                                            <p className="text-[12px] text-gray-400 font-medium truncate max-w-[130px]">{u.assigned_by || '—'}</p>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )
            )}

            {/* ── Add Admin Dialog ── */}
            <Dialog open={addOpen} onOpenChange={setAddOpen}>
                <DialogContent className="sm:max-w-sm rounded-2xl border-none shadow-2xl">
                    <DialogHeader>
                        <DialogTitle className="text-lg font-extrabold text-[#002B49]">Add Platform Admin</DialogTitle>
                        <DialogDescription className="text-sm text-gray-500 pt-1">
                            This user will gain full admin access across the Aegis platform.
                        </DialogDescription>
                    </DialogHeader>
                    <div className="py-4 space-y-3">
                        <Label className="text-xs font-bold text-gray-500 uppercase tracking-widest">Email Address</Label>
                        <Input
                            placeholder="employee@adani.com"
                            className="h-11 rounded-xl border-gray-200 bg-gray-50 focus:bg-white"
                            value={newEmail}
                            onChange={e => setNewEmail(e.target.value)}
                        />
                        <div className="flex items-center gap-2 p-3 bg-purple-50 rounded-xl border border-purple-100">
                            <ShieldCheck className="h-4 w-4 text-purple-500 flex-shrink-0" />
                            <p className="text-[11px] text-purple-700 font-medium">
                                Platform Admins can manage all users, approve access requests, and configure any application.
                            </p>
                        </div>
                    </div>
                    <DialogFooter className="gap-2">
                        <Button variant="ghost" className="flex-1 rounded-xl h-11 font-bold" onClick={() => setAddOpen(false)}>Cancel</Button>
                        <Button className="flex-1 rounded-xl h-11 font-bold" onClick={handleAddAdmin} disabled={adding || !newEmail.trim()}>
                            {adding && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
                            Add Admin
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* ── Remove Confirm Dialog ── */}
            <Dialog open={!!removeTarget} onOpenChange={open => !open && setRemoveTarget(null)}>
                <DialogContent className="sm:max-w-sm rounded-2xl border-none shadow-2xl">
                    <DialogHeader>
                        <DialogTitle className="text-lg font-extrabold text-[#002B49]">Remove Admin Access?</DialogTitle>
                        <DialogDescription className="text-sm text-gray-500 pt-1">
                            <strong>{removeTarget?.email}</strong> will lose all administrative privileges across the Aegis platform.
                        </DialogDescription>
                    </DialogHeader>
                    <DialogFooter className="gap-2 pt-2">
                        <Button variant="ghost" className="flex-1 rounded-xl h-11 font-bold" onClick={() => setRemoveTarget(null)}>Cancel</Button>
                        <Button variant="destructive" className="flex-1 rounded-xl h-11 font-bold bg-red-500 hover:bg-red-600" onClick={handleRemove} disabled={removing}>
                            {removing ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Trash2 className="h-4 w-4 mr-2" />}
                            Remove Admin
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
};
