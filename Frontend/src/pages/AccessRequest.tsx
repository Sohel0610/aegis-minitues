/**
 * Access Request Page
 * Allows signed-in users to request access to specific routes.
 * Auto-fills name and email from SSO user context.
 */

import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { submitAccessRequest } from '@/services/permissionService';
import { cn } from "@/lib/utils";
import {
    ShieldCheck,
    Globe,
    Lock,
    CheckCircle,
    AlertCircle,
    Loader2,
    ArrowLeft,
    User,
    Mail,
    FileText,
} from 'lucide-react';

const AVAILABLE_ROUTES = [
    { path: '/bse-alerts',             name: 'BSE Alerts',             description: 'BSE regulatory alerts and notifications' },
    { path: '/rbi-dashboard',          name: 'RBI Dashboard',          description: 'RBI compliance dashboard' },
    { path: '/sebi-dashboard',         name: 'SEBI Dashboard',         description: 'SEBI regulatory dashboard' },
    { path: '/insider-trading',        name: 'Insider Trading',        description: 'Insider trading monitoring and compliance' },
    { path: '/directors-disclosure',   name: 'Directors Disclosure',   description: 'Directors disclosure management' },
    { path: '/minutes-preparation',    name: 'Minutes Preparation',    description: 'Board meeting minutes preparation' },
];

export const AccessRequest: React.FC = () => {
    const { user, isLoading, isAuthenticated, accessibleRoutes, login } = useAuth();
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();

    const [selectedRoute, setSelectedRoute] = useState('');
    const [permissionType, setPermissionType] = useState<'view' | 'admin'>('view');
    const [justification, setJustification] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState(false);

    useEffect(() => {
        const route = searchParams.get('route');
        if (route) setSelectedRoute(route);
    }, [searchParams]);

    // Routes the user doesn't already have
    const availableRoutes = AVAILABLE_ROUTES.filter(
        (route) => !(accessibleRoutes || []).includes(route.path)
    );

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!user) { setError('You must be signed in to request access.'); return; }
        if (!selectedRoute) { setError('Please select an application.'); return; }
        if (!justification.trim()) { setError('Please provide a justification for your request.'); return; }

        setLoading(true);
        setError(null);
        try {
            await submitAccessRequest({
                email: user.email,
                name: user.name || user.email,
                requested_route: selectedRoute,
                requested_permission: permissionType,
                justification: justification.trim(),
            });
            setSuccess(true);
            setTimeout(() => navigate('/dashboard'), 4000);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to submit request. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    // ── Loading state ──────────────────────────────────────────────────────────
    if (isLoading) {
        return (
            <div className="min-h-screen bg-[#F8FAFC] flex items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-primary/40" />
            </div>
        );
    }

    // ── Not authenticated ──────────────────────────────────────────────────────
    if (!isAuthenticated || !user) {
        return (
            <div className="min-h-screen bg-[#F8FAFC] flex items-center justify-center px-4">
                <div className="max-w-md w-full bg-white rounded-2xl shadow-lg border border-gray-100 p-8 text-center space-y-5">
                    <div className="h-16 w-16 bg-primary/5 rounded-full flex items-center justify-center mx-auto">
                        <Lock className="h-8 w-8 text-primary" />
                    </div>
                    <div>
                        <h2 className="text-xl font-extrabold text-[#002B49]">Sign In Required</h2>
                        <p className="text-sm text-gray-500 mt-2">
                            You must be signed in with your corporate account to request access.
                        </p>
                    </div>
                    <button
                        onClick={() => login()}
                        className="w-full py-3 rounded-xl bg-primary text-white font-bold text-sm hover:bg-primary/90 transition-all"
                    >
                        Sign In with SSO
                    </button>
                    <button onClick={() => navigate(-1)} className="text-xs text-gray-400 hover:text-gray-600 font-medium">
                        ← Go Back
                    </button>
                </div>
            </div>
        );
    }

    // ── Success state ──────────────────────────────────────────────────────────
    if (success) {
        return (
            <div className="min-h-screen bg-[#F8FAFC] flex items-center justify-center px-4">
                <div className="max-w-md w-full bg-white rounded-2xl shadow-lg border border-gray-100 p-8 text-center space-y-5">
                    <div className="h-16 w-16 bg-emerald-50 rounded-full flex items-center justify-center mx-auto border border-emerald-100">
                        <CheckCircle className="h-9 w-9 text-emerald-500" />
                    </div>
                    <div>
                        <h2 className="text-xl font-extrabold text-[#002B49]">Request Submitted!</h2>
                        <p className="text-sm text-gray-600 mt-2 leading-relaxed">
                            Your access request has been sent to the administrator. You'll receive an email
                            confirmation shortly.
                        </p>
                        <p className="text-sm text-gray-400 mt-3">
                            Expected review time: <strong className="text-gray-600">24–48 hours</strong>
                        </p>
                    </div>
                    <p className="text-xs text-gray-400">Redirecting to dashboard...</p>
                </div>
            </div>
        );
    }

    // ── Main form ──────────────────────────────────────────────────────────────
    return (
        <div className="min-h-screen bg-[#F8FAFC] py-10 px-4">
            <div className="max-w-xl mx-auto">
                {/* Back button */}
                <button
                    onClick={() => navigate(-1)}
                    className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-gray-700 font-semibold mb-4 transition-colors"
                >
                    <ArrowLeft className="h-3.5 w-3.5" /> Back
                </button>

                <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
                    {/* Header */}
                    <div className="bg-[#002B49] px-6 py-5 text-white">
                        <div className="flex items-center gap-3">
                            <div className="h-10 w-10 rounded-xl bg-white/10 flex items-center justify-center">
                                <ShieldCheck className="h-5 w-5 text-white" />
                            </div>
                            <div>
                                <h1 className="text-lg font-extrabold tracking-tight">Request Access</h1>
                                <p className="text-xs text-white/60 font-medium">Aegis Platform · Access Management</p>
                            </div>
                        </div>
                    </div>

                    <form onSubmit={handleSubmit} className="p-6 space-y-5">
                        {/* Error alert */}
                        {error && (
                            <div className="flex items-start gap-3 bg-red-50 border border-red-100 rounded-xl p-4">
                                <AlertCircle className="h-4 w-4 text-red-500 mt-0.5 flex-shrink-0" />
                                <p className="text-sm text-red-700 font-medium">{error}</p>
                            </div>
                        )}

                        {/* ── Auto-filled user info (read-only) ── */}
                        <div className="bg-gray-50 border border-gray-100 rounded-xl p-4 space-y-2">
                            <p className="text-[10px] font-extrabold text-gray-400 uppercase tracking-widest mb-3">Requesting As</p>
                            <div className="flex items-center gap-2.5">
                                <div className="h-9 w-9 rounded-lg bg-primary/5 ring-1 ring-primary/10 flex items-center justify-center font-black text-primary text-sm flex-shrink-0">
                                    {user.name?.charAt(0)?.toUpperCase() || user.email?.charAt(0)?.toUpperCase()}
                                </div>
                                <div>
                                    <div className="flex items-center gap-1.5 text-sm font-bold text-[#002B49]">
                                        <User className="h-3.5 w-3.5 text-gray-400" />
                                        {user.name || 'Your Name'}
                                    </div>
                                    <div className="flex items-center gap-1.5 text-xs text-gray-500 font-medium mt-0.5">
                                        <Mail className="h-3 w-3 text-gray-400" />
                                        {user.email}
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* ── Application Selection ── */}
                        <div className="space-y-2">
                            <label htmlFor="route" className="block text-xs font-extrabold text-gray-500 uppercase tracking-widest">
                                Application <span className="text-red-400">*</span>
                            </label>
                            <div className="relative">
                                <Globe className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                                <select
                                    id="route"
                                    value={selectedRoute}
                                    onChange={(e) => setSelectedRoute(e.target.value)}
                                    className="w-full h-11 pl-10 pr-4 border border-gray-200 rounded-xl bg-gray-50 focus:bg-white focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all text-sm font-semibold text-[#002B49] appearance-none outline-none"
                                    required
                                >
                                    <option value="">— Select an application —</option>
                                    {availableRoutes.map((route) => (
                                        <option key={route.path} value={route.path}>
                                            {route.name}
                                        </option>
                                    ))}
                                </select>
                            </div>
                            {selectedRoute && (
                                <p className="text-xs text-gray-400 pl-1">
                                    {AVAILABLE_ROUTES.find(r => r.path === selectedRoute)?.description}
                                </p>
                            )}
                            {availableRoutes.length === 0 && (
                                <p className="text-xs text-emerald-600 font-medium pl-1 flex items-center gap-1">
                                    <CheckCircle className="h-3.5 w-3.5" />
                                    You already have access to all available applications.
                                </p>
                            )}
                        </div>

                        {/* ── Permission Type ── */}
                        <div className="space-y-2">
                            <label className="block text-xs font-extrabold text-gray-500 uppercase tracking-widest">
                                Access Level <span className="text-red-400">*</span>
                            </label>
                            <div className="grid grid-cols-2 gap-3">
                                {([
                                    { value: 'view',  title: 'View Only',     desc: 'Read-only access to view data and reports' },
                                    { value: 'admin', title: 'Full Access',   desc: 'View, edit, export, and manage content' },
                                ] as const).map((opt) => (
                                    <label
                                        key={opt.value}
                                        className={cn(
                                            'flex flex-col gap-1.5 p-4 rounded-xl border-2 cursor-pointer transition-all',
                                            permissionType === opt.value
                                                ? 'border-primary bg-primary/5 shadow-sm'
                                                : 'border-gray-100 bg-white hover:border-gray-200'
                                        )}
                                    >
                                        <input
                                            type="radio"
                                            value={opt.value}
                                            checked={permissionType === opt.value}
                                            onChange={() => setPermissionType(opt.value)}
                                            className="sr-only"
                                        />
                                        <div className="flex items-center gap-2">
                                            <div className={cn(
                                                'h-3.5 w-3.5 rounded-full border-2 flex items-center justify-center flex-shrink-0',
                                                permissionType === opt.value ? 'border-primary' : 'border-gray-300'
                                            )}>
                                                {permissionType === opt.value && (
                                                    <div className="h-1.5 w-1.5 rounded-full bg-primary" />
                                                )}
                                            </div>
                                            <span className={cn('text-sm font-bold', permissionType === opt.value ? 'text-[#002B49]' : 'text-gray-600')}>
                                                {opt.title}
                                            </span>
                                        </div>
                                        <p className="text-[11px] text-gray-400 font-medium pl-5 leading-snug">{opt.desc}</p>
                                    </label>
                                ))}
                            </div>
                        </div>

                        {/* ── Justification ── */}
                        <div className="space-y-2">
                            <label htmlFor="justification" className="block text-xs font-extrabold text-gray-500 uppercase tracking-widest">
                                Business Justification <span className="text-red-400">*</span>
                            </label>
                            <div className="relative">
                                <FileText className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                                <textarea
                                    id="justification"
                                    value={justification}
                                    onChange={(e) => setJustification(e.target.value)}
                                    rows={4}
                                    className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl bg-gray-50 focus:bg-white focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all text-sm resize-none outline-none"
                                    placeholder="Explain why you need access to this application and how it relates to your role..."
                                    required
                                />
                            </div>
                            <p className="text-[11px] text-gray-400 pl-1">
                                {justification.length} characters · Clear business reason helps faster approval
                            </p>
                        </div>

                        {/* ── Actions ── */}
                        <div className="flex gap-3 pt-1">
                            <button
                                type="button"
                                onClick={() => navigate(-1)}
                                className="flex-shrink-0 px-5 py-3 border border-gray-200 rounded-xl text-sm font-bold text-gray-600 hover:bg-gray-50 transition-colors"
                            >
                                Cancel
                            </button>
                            <button
                                type="submit"
                                disabled={loading || availableRoutes.length === 0}
                                className="flex-1 py-3 rounded-xl bg-primary text-white font-bold text-sm hover:bg-primary/90 disabled:bg-gray-300 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2 shadow-lg shadow-primary/20"
                            >
                                {loading ? (
                                    <><Loader2 className="h-4 w-4 animate-spin" /> Submitting...</>
                                ) : (
                                    <><ShieldCheck className="h-4 w-4" /> Submit Access Request</>
                                )}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
};

// cn helper
function cn(...classes: (string | boolean | undefined)[]) {
    return classes.filter(Boolean).join(' ');
}
