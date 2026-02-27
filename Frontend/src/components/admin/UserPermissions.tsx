/**
 * User Permissions Component
 * View and manage all user permissions with role switching and search
 */

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import {
    getRoutePermissions,
    assignPermission,
    revokePermission,
    getRouteDefinitions,
    type RouteDefinition
} from '@/services/permissionService';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
    DialogFooter,
} from "@/components/ui/dialog";
import { cn } from '@/lib/utils';
import {
    Search,
    UserPlus,
    Trash2,
    RefreshCcw,
    Shield,
    ShieldCheck,
    Check,
    AlertCircle,
    Loader2,
    ChevronRight,
    Users
} from 'lucide-react';
import { toast } from 'sonner';

export const UserPermissions: React.FC = () => {
    const { user } = useAuth();
    const [selectedRoute, setSelectedRoute] = useState('/bse-alerts');
    const [routeDefinitions, setRouteDefinitions] = useState<RouteDefinition[]>([]);
    const [permissions, setPermissions] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');

    // Add User State
    const [isAddUserOpen, setIsAddUserOpen] = useState(false);
    const [newUserEmail, setNewUserEmail] = useState('');
    const [newUserRole, setNewUserRole] = useState<'view' | 'admin' | 'edit'>('view');
    const [isSubmitting, setIsSubmitting] = useState(false);

    const loadRoutes = async () => {
        if (!user) return;
        try {
            const routes = await getRouteDefinitions(user.email);
            setRouteDefinitions(routes);
            if (routes.length > 0 && !routes.find(r => r.route_path === selectedRoute)) {
                setSelectedRoute(routes[0].route_path);
            }
        } catch (err) {
            console.error('Failed to load route definitions:', err);
            toast.error('Failed to load application list');
        }
    };

    const loadPermissions = async () => {
        if (!user) return;

        setLoading(true);
        try {
            const data = await getRoutePermissions(user.email, selectedRoute);
            setPermissions(data.permissions || []);
        } catch (err) {
            console.error('Failed to load permissions:', err);
            toast.error('Failed to load user permissions');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadRoutes();
    }, [user]);

    useEffect(() => {
        loadPermissions();
    }, [selectedRoute, user]);

    const handleRoleSwitch = async (targetEmail: string, newRole: 'view' | 'admin' | 'edit') => {
        if (!user) return;

        try {
            setLoading(true);
            await assignPermission(user.email, targetEmail, selectedRoute, newRole, `Role changed to ${newRole}`);
            toast.success(`Permission updated for ${targetEmail}`);
            await loadPermissions();
        } catch (err) {
            console.error('Failed to update permission:', err);
            toast.error('Failed to update permission');
        } finally {
            setLoading(false);
        }
    };

    const handleRevoke = async (targetEmail: string) => {
        if (!user) return;

        if (!confirm(`Are you sure you want to revoke all access for ${targetEmail} on this application?`)) {
            return;
        }

        try {
            setLoading(true);
            await revokePermission(user.email, targetEmail, selectedRoute);
            toast.success(`Access revoked for ${targetEmail}`);
            await loadPermissions();
        } catch (err) {
            console.error('Failed to revoke permission:', err);
            toast.error('Failed to revoke permission');
        } finally {
            setLoading(false);
        }
    };

    const handleAddUser = async () => {
        if (!user || !newUserEmail) return;

        setIsSubmitting(true);
        try {
            await assignPermission(user.email, newUserEmail, selectedRoute, newUserRole, 'Directly added by admin');
            toast.success(`User ${newUserEmail} added successfully`);
            setNewUserEmail('');
            setIsAddUserOpen(false);
            await loadPermissions();
        } catch (err) {
            console.error('Failed to add user:', err);
            toast.error(err instanceof Error ? err.message : 'Failed to add user');
        } finally {
            setIsSubmitting(false);
        }
    };

    const filteredPermissions = permissions.filter(p =>
        p.email.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const currentRouteDef = routeDefinitions.find(r => r.route_path === selectedRoute);

    return (
        <div className="space-y-6 h-full flex flex-col">
            {/* Controls Header */}
            <div className="flex flex-col xl:flex-row xl:items-end justify-between gap-4 px-6 pt-6">
                <div className="flex-1 space-y-2">
                    <Label className="text-[11px] font-bold text-gray-400 uppercase tracking-wider">Application Scope</Label>
                    <div className="relative max-w-sm">
                        <Shield className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-primary/60" />
                        <select
                            value={selectedRoute}
                            onChange={(e) => setSelectedRoute(e.target.value)}
                            className="w-full h-11 pl-10 pr-4 bg-gray-50/50 border border-gray-100 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all text-sm font-semibold text-[#002B49] appearance-none"
                        >
                            {routeDefinitions.map((route) => (
                                <option key={route.route_path} value={route.route_path}>
                                    {route.route_name}
                                </option>
                            ))}
                        </select>
                        <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
                            <ChevronRight className="h-4 w-4 text-gray-400 rotate-90" />
                        </div>
                    </div>
                </div>

                <div className="flex flex-wrap items-center gap-3">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                        <Input
                            placeholder="Filter by email..."
                            className="pl-9 w-full sm:w-64 h-11 rounded-xl border-gray-100 bg-gray-50/50 focus:bg-white transition-all text-sm font-medium"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                        />
                    </div>

                    <Dialog open={isAddUserOpen} onOpenChange={setIsAddUserOpen}>
                        <DialogTrigger asChild>
                            <Button className="h-11 px-5 gap-2 rounded-xl shadow-lg shadow-primary/10 transition-transform active:scale-[0.98]">
                                <UserPlus className="h-4 w-4 " />
                                <span className="text-sm font-bold">Grant Access</span>
                            </Button>
                        </DialogTrigger>
                        <DialogContent className="sm:max-w-md rounded-2xl border-none shadow-2xl">
                            <DialogHeader>
                                <DialogTitle className="text-xl font-extrabold text-[#002B49] tracking-tight">Add New Access</DialogTitle>
                                <DialogDescription className="text-gray-500 font-medium pt-1">
                                    Set permissions for <strong>{currentRouteDef?.route_name || selectedRoute}</strong>
                                </DialogDescription>
                            </DialogHeader>
                            <div className="space-y-5 py-6">
                                <div className="space-y-2">
                                    <Label htmlFor="email" className="text-xs font-bold text-gray-500 uppercase tracking-widest px-1">Email ID</Label>
                                    <Input
                                        id="email"
                                        placeholder="employee@adani.com"
                                        className="h-12 rounded-xl border-gray-100 bg-gray-50/50 focus:bg-white"
                                        value={newUserEmail}
                                        onChange={(e) => setNewUserEmail(e.target.value)}
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label className="text-xs font-bold text-gray-500 uppercase tracking-widest px-1">Role Assignment</Label>
                                    <div className="grid grid-cols-2 gap-3">
                                        <button
                                            type="button"
                                            className={cn(
                                                "flex flex-col items-center gap-2 p-4 rounded-xl border-2 transition-all group",
                                                newUserRole === 'view'
                                                    ? "border-primary bg-primary/5 shadow-[0_0_0_1px_rgba(0,93,164,0.1)]"
                                                    : "border-gray-50 bg-white hover:border-gray-200"
                                            )}
                                            onClick={() => setNewUserRole('view')}
                                        >
                                            <div className={cn(
                                                "p-2 rounded-full",
                                                newUserRole === 'view' ? "bg-primary text-white" : "bg-gray-100 text-gray-400 group-hover:bg-gray-200"
                                            )}>
                                                <Shield className="h-5 w-5" />
                                            </div>
                                            <div className="text-center">
                                                <p className={cn("text-sm font-bold", newUserRole === 'view' ? "text-[#002B49]" : "text-gray-600")}>Viewer</p>
                                                <p className="text-[10px] text-gray-400 font-medium">Read-only access</p>
                                            </div>
                                        </button>
                                        <button
                                            type="button"
                                            className={cn(
                                                "flex flex-col items-center gap-2 p-4 rounded-xl border-2 transition-all group",
                                                newUserRole === 'admin'
                                                    ? "border-primary bg-primary/5 shadow-[0_0_0_1px_rgba(0,93,164,0.1)]"
                                                    : "border-gray-50 bg-white hover:border-gray-200"
                                            )}
                                            onClick={() => setNewUserRole('admin')}
                                        >
                                            <div className={cn(
                                                "p-2 rounded-full",
                                                newUserRole === 'admin' ? "bg-primary text-white" : "bg-gray-100 text-gray-400 group-hover:bg-gray-200"
                                            )}>
                                                <ShieldCheck className="h-5 w-5" />
                                            </div>
                                            <div className="text-center">
                                                <p className={cn("text-sm font-bold", newUserRole === 'admin' ? "text-[#002B49]" : "text-gray-600")}>Admin</p>
                                                <p className="text-[10px] text-gray-400 font-medium">Full management</p>
                                            </div>
                                        </button>
                                    </div>
                                </div>
                            </div>
                            <DialogFooter className="gap-2">
                                <Button variant="ghost" className="rounded-xl h-12 font-bold flex-1" onClick={() => setIsAddUserOpen(false)}>Cancel</Button>
                                <Button className="rounded-xl h-12 font-bold flex-1" onClick={handleAddUser} disabled={isSubmitting || !newUserEmail}>
                                    {isSubmitting ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                                    Assign Access
                                </Button>
                            </DialogFooter>
                        </DialogContent>
                    </Dialog>

                    <Button variant="outline" size="icon" className="h-11 w-11 rounded-xl border-gray-100 bg-gray-50 text-gray-400 hover:text-primary hover:bg-primary/5 transition-all active:rotate-180 duration-500" onClick={loadPermissions}>
                        <RefreshCcw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                    </Button>
                </div>
            </div>

            {/* Permissions Table Region */}
            <div className="flex-1 overflow-hidden px-6 pb-6">
                <div className="h-full border border-gray-100 rounded-2xl overflow-hidden flex flex-col bg-gray-50/30">
                    <Table>
                        <TableHeader className="bg-white sticky top-0 z-10 border-b border-gray-100">
                            <TableRow className="hover:bg-transparent border-none">
                                <TableHead className="text-xs font-bold text-gray-400 uppercase tracking-widest h-14 pl-6">Active User</TableHead>
                                <TableHead className="text-xs font-bold text-gray-400 uppercase tracking-widest h-14 text-center">Assigned Role</TableHead>
                                <TableHead className="text-xs font-bold text-gray-400 uppercase tracking-widest h-14 whitespace-nowrap">Assignment Date</TableHead>
                                <TableHead className="text-xs font-bold text-gray-400 uppercase tracking-widest h-14 text-right pr-8">Actions</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody className="bg-white divide-y divide-gray-50">
                            {filteredPermissions.length > 0 ? (
                                filteredPermissions.map((perm) => (
                                    <TableRow key={perm.email} className="group hover:bg-[#F8FAFC]/50 transition-colors border-none">
                                        <TableCell className="py-4 pl-6">
                                            <div className="flex flex-col">
                                                <span className="text-sm font-bold text-[#002B49] leading-tight">{perm.email}</span>
                                                <span className="text-[10px] text-gray-400 font-medium">Mapped User</span>
                                            </div>
                                        </TableCell>
                                        <TableCell className="py-4">
                                            <div className="flex items-center justify-center">
                                                <div className="inline-flex p-1 bg-gray-100/80 rounded-xl gap-1 ring-1 ring-inset ring-gray-200/50">
                                                    <button
                                                        onClick={() => handleRoleSwitch(perm.email, 'view')}
                                                        className={cn(
                                                            "px-4 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider transition-all",
                                                            perm.permission_type === 'view'
                                                                ? "bg-white text-primary shadow-sm ring-1 ring-gray-200"
                                                                : "text-gray-400 hover:text-gray-600"
                                                        )}
                                                    >
                                                        Viewer
                                                    </button>
                                                    <button
                                                        onClick={() => handleRoleSwitch(perm.email, 'admin')}
                                                        className={cn(
                                                            "px-4 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider transition-all",
                                                            perm.permission_type === 'admin'
                                                                ? "bg-white text-primary shadow-sm ring-1 ring-gray-200"
                                                                : "text-gray-400 hover:text-gray-600"
                                                        )}
                                                    >
                                                        Admin
                                                    </button>
                                                </div>
                                            </div>
                                        </TableCell>
                                        <TableCell className="py-4">
                                            <div className="flex flex-col">
                                                <span className="text-[12px] font-bold text-gray-600">
                                                    {new Date(perm.assigned_at).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })}
                                                </span>
                                                <span className="text-[10px] text-gray-400 font-medium uppercase tracking-tighter">Verified</span>
                                            </div>
                                        </TableCell>
                                        <TableCell className="py-4 text-right pr-8">
                                            <Button
                                                variant="ghost"
                                                size="icon"
                                                className="h-9 w-9 text-gray-300 hover:text-red-500 hover:bg-red-50 rounded-lg transition-all"
                                                onClick={() => handleRevoke(perm.email)}
                                            >
                                                <Trash2 className="h-4 w-4" />
                                            </Button>
                                        </TableCell>
                                    </TableRow>
                                ))
                            ) : (
                                <TableRow className="hover:bg-transparent border-none">
                                    <TableCell colSpan={4} className="h-80 text-center">
                                        <div className="flex flex-col items-center justify-center gap-4 animate-in fade-in zoom-in duration-500">
                                            <div className="h-20 w-20 rounded-full bg-gray-50 flex items-center justify-center mb-2">
                                                <Search className="h-8 w-8 text-gray-200" />
                                            </div>
                                            <div className="space-y-1">
                                                <p className="text-sm font-bold text-[#002B49]">No results found</p>
                                                <p className="text-xs text-gray-400 font-medium">Try adjusting your filter or adding a new user.</p>
                                            </div>
                                            <Button variant="outline" size="sm" className="h-9 rounded-lg border-gray-200" onClick={() => setSearchQuery('')}>
                                                Clear Search
                                            </Button>
                                        </div>
                                    </TableCell>
                                </TableRow>
                            )}
                        </TableBody>
                    </Table>
                </div>
            </div>
        </div>
    );
};
