/**
 * Admin Panel Page
 * Central dashboard for managing permissions, access requests, and viewing audit logs.
 * Features a premium layout with intuitive navigation and clear feedback.
 */

import React, { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Navigate } from 'react-router-dom';
import { PendingRequests } from '@/components/admin/PendingRequests';
import { UserPermissions } from '@/components/admin/UserPermissions';
import { AuditLogs } from '@/components/admin/AuditLogs';
import {
    ClipboardList,
    Users,
    Activity,
    Settings,
    ShieldCheck,
    ChevronRight,
    LayoutDashboard
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

type TabType = 'requests' | 'permissions' | 'audit';

export const AdminPanel: React.FC = () => {
    const { isAdmin, isLoading } = useAuth();
    const [activeTab, setActiveTab] = useState<TabType>('requests');

    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-[60vh]">
                <div className="flex flex-col items-center gap-4">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
                    <p className="text-muted-foreground font-medium">Authenticating Admin...</p>
                </div>
            </div>
        );
    }

    if (!isAdmin) {
        return <Navigate to="/access-denied" replace />;
    }

    const tabs = [
        {
            id: 'requests' as TabType,
            name: 'Pending Requests',
            icon: ClipboardList,
            description: 'Review and approve access applications'
        },
        {
            id: 'permissions' as TabType,
            name: 'User Permissions',
            icon: Users,
            description: 'Manage roles and application access'
        },
        {
            id: 'audit' as TabType,
            name: 'Activity Logs',
            icon: Activity,
            description: 'Monitor all administrative changes'
        },
    ];

    return (
        <div className="min-h-screen bg-[#FDFDFD]">
            {/* Header / Banner */}
            <div className="bg-white border-b border-gray-100 shadow-[0_1px_2px_rgba(0,0,0,0.03)]">
                <div className="max-w-[1400px] mx-auto px-6 py-6 lg:py-8">
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                        <div className="space-y-1">
                            <div className="flex items-center gap-2 text-[10px] lg:text-xs font-bold text-primary uppercase tracking-widest mb-1 bg-primary/5 w-fit px-2 py-1 rounded-full">
                                <ShieldCheck className="h-3 w-3" />
                                <span>Administrative Controls</span>
                            </div>
                            <h1 className="text-2xl lg:text-3xl font-extrabold text-[#002B49] tracking-tight">Access Control Center</h1>
                            <p className="text-gray-500 text-sm max-w-2xl leading-relaxed">
                                Manage user permissions and security requests for the Aegis platform.
                            </p>
                        </div>

                        <div className="flex items-center gap-4 md:self-end">
                            <div className="hidden sm:block text-right">
                                <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">System Status</p>
                                <div className="flex items-center gap-2 mt-0.5 bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-100">
                                    <div className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse"></div>
                                    <span className="text-[11px] font-bold text-emerald-700">Secured</span>
                                </div>
                            </div>
                            <div className="hidden sm:block h-8 w-px bg-gray-100 mx-1"></div>
                            <Button variant="outline" size="sm" className="gap-2 border-gray-200 hover:bg-gray-50 text-gray-700 h-9 rounded-lg" onClick={() => window.location.href = '/'}>
                                <LayoutDashboard className="h-4 w-4" />
                                <span className="text-xs font-semibold">Exit Panel</span>
                            </Button>
                        </div>
                    </div>
                </div>
            </div>

            <div className="max-w-[1400px] mx-auto px-6 py-8">
                <div className="flex flex-col lg:flex-row gap-8 lg:items-start">
                    {/* Sidebar Navigation */}
                    <div className="lg:w-72 shrink-0 flex flex-col gap-1.5">
                        <p className="px-3 text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-2">Main Navigation</p>
                        {tabs.map((tab) => {
                            const Icon = tab.icon;
                            const isActive = activeTab === tab.id;
                            return (
                                <button
                                    key={tab.id}
                                    onClick={() => setActiveTab(tab.id)}
                                    className={cn(
                                        "w-full flex items-center gap-3.5 p-3 rounded-xl transition-all duration-300 text-left group relative",
                                        isActive
                                            ? "bg-primary/5 text-primary shadow-[inset_0_0_0_1px_rgba(0,93,164,0.1)]"
                                            : "text-gray-500 hover:bg-gray-50 hover:text-gray-900"
                                    )}
                                >
                                    <div className={cn(
                                        "p-2 rounded-lg transition-all duration-300",
                                        isActive
                                            ? "bg-primary text-white shadow-lg shadow-primary/20 scale-105"
                                            : "bg-gray-50 text-gray-400 group-hover:bg-gray-100 group-hover:text-primary/70"
                                    )}>
                                        <Icon className="h-4 w-4" />
                                    </div>
                                    <div className="flex-1">
                                        <span className={cn(
                                            "font-bold text-sm tracking-tight",
                                            isActive ? "text-[#002B49]" : "text-gray-600 group-hover:text-[#002B49]"
                                        )}>
                                            {tab.name}
                                        </span>
                                    </div>
                                    {isActive && (
                                        <div className="absolute right-3 h-1.5 w-1.5 rounded-full bg-primary animate-in zoom-in duration-300"></div>
                                    )}
                                </button>
                            );
                        })}

                        <div className="mt-6 px-3">
                            <div className="bg-gray-50 rounded-2xl p-5 border border-gray-100 flex flex-col gap-3">
                                <div className="h-8 w-8 rounded-lg bg-gray-200/50 flex items-center justify-center">
                                    <Settings className="h-4 w-4 text-gray-400" />
                                </div>
                                <div className="space-y-1">
                                    <h4 className="font-bold text-xs text-[#002B49]">Administrator Access</h4>
                                    <p className="text-[10px] text-gray-500 leading-relaxed font-medium">
                                        Need help with permissions? Consult the documentation for role definitions.
                                    </p>
                                </div>
                                <Button variant="ghost" size="sm" className="w-full text-[10px] h-7 font-bold hover:bg-white border border-transparent hover:border-gray-100 text-primary">
                                    System Docs
                                </Button>
                            </div>
                        </div>
                    </div>

                    {/* Content Area */}
                    <div className="flex-1 min-w-0">
                        <div className="bg-white rounded-2xl border border-gray-100 shadow-[0_4px_20px_rgba(0,0,0,0.02)] min-h-[650px] overflow-hidden">
                            <div className="animate-in fade-in slide-in-from-bottom-2 duration-700 ease-out h-full">
                                {activeTab === 'requests' && <PendingRequests />}
                                {activeTab === 'permissions' && <UserPermissions />}
                                {activeTab === 'audit' && <AuditLogs />}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};
