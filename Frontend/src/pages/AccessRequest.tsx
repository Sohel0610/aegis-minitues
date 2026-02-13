/**
 * Access Request Page
 * Allows users to request access to routes they don't have permission for
 */

import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { submitAccessRequest } from '@/services/permissionService';

const AVAILABLE_ROUTES = [
    { path: '/bse-alerts', name: 'BSE Alerts', description: 'BSE regulatory alerts and notifications' },
    { path: '/rbi-dashboard', name: 'RBI Dashboard', description: 'RBI compliance dashboard' },
    { path: '/sebi-dashboard', name: 'SEBI Dashboard', description: 'SEBI regulatory dashboard' },
    { path: '/insider-trading', name: 'Insider Trading', description: 'Insider trading monitoring and compliance' },
    { path: '/directors-disclosure', name: 'Directors Disclosure', description: 'Directors disclosure management with tabs' },
    { path: '/minutes-preparation', name: 'Minutes Preparation', description: 'Board meeting minutes preparation' },
];

export const AccessRequest: React.FC = () => {
    const { user, accessibleRoutes } = useAuth();
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();

    const [selectedRoute, setSelectedRoute] = useState('');
    const [permissionType, setPermissionType] = useState<'view' | 'admin'>('view');
    const [justification, setJustification] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState(false);

    useEffect(() => {
        // Pre-fill route if passed in query params
        const route = searchParams.get('route');
        if (route) {
            setSelectedRoute(route);
        }
    }, [searchParams]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!user) {
            setError('You must be logged in to request access');
            return;
        }

        if (!selectedRoute) {
            setError('Please select a route');
            return;
        }

        if (!justification.trim()) {
            setError('Please provide a justification for your request');
            return;
        }

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
            setTimeout(() => {
                navigate('/dashboard');
            }, 3000);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to submit access request');
        } finally {
            setLoading(false);
        }
    };

    // Filter out routes user already has access to
    const availableRoutes = AVAILABLE_ROUTES.filter(
        (route) => !accessibleRoutes.includes(route.path)
    );

    if (success) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
                <div className="max-w-md w-full bg-white shadow-lg rounded-lg p-8 text-center">
                    <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-green-100 mb-4">
                        <svg
                            className="h-10 w-10 text-green-600"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                        >
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M5 13l4 4L19 7"
                            />
                        </svg>
                    </div>
                    <h2 className="text-2xl font-bold text-gray-900 mb-2">Request Submitted!</h2>
                    <p className="text-gray-600 mb-4">
                        Your access request has been submitted successfully. An administrator will review it within
                        24-48 hours.
                    </p>
                    <p className="text-sm text-gray-500">Redirecting to dashboard...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
            <div className="max-w-2xl mx-auto">
                <div className="bg-white shadow-lg rounded-lg p-8">
                    <div className="mb-8">
                        <h1 className="text-3xl font-bold text-gray-900">Request Access</h1>
                        <p className="mt-2 text-gray-600">
                            Request permission to access specific routes and features in the system.
                        </p>
                    </div>

                    {error && (
                        <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
                            <div className="flex">
                                <svg
                                    className="h-5 w-5 text-red-400"
                                    fill="none"
                                    viewBox="0 0 24 24"
                                    stroke="currentColor"
                                >
                                    <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth={2}
                                        d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                                    />
                                </svg>
                                <p className="ml-3 text-sm text-red-700">{error}</p>
                            </div>
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-6">
                        {/* User Info */}
                        <div className="bg-gray-50 rounded-lg p-4">
                            <p className="text-sm text-gray-600">
                                <strong>Requesting as:</strong> {user?.name} ({user?.email})
                            </p>
                        </div>

                        {/* Route Selection */}
                        <div>
                            <label htmlFor="route" className="block text-sm font-medium text-gray-700 mb-2">
                                Select Route <span className="text-red-500">*</span>
                            </label>
                            <select
                                id="route"
                                value={selectedRoute}
                                onChange={(e) => setSelectedRoute(e.target.value)}
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                required
                            >
                                <option value="">-- Select a route --</option>
                                {availableRoutes.map((route) => (
                                    <option key={route.path} value={route.path}>
                                        {route.name} - {route.description}
                                    </option>
                                ))}
                            </select>
                            {availableRoutes.length === 0 && (
                                <p className="mt-2 text-sm text-gray-500">
                                    You already have access to all available routes.
                                </p>
                            )}
                        </div>

                        {/* Permission Type */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Permission Type <span className="text-red-500">*</span>
                            </label>
                            <div className="space-y-2">
                                <label className="flex items-center">
                                    <input
                                        type="radio"
                                        value="view"
                                        checked={permissionType === 'view'}
                                        onChange={(e) => setPermissionType(e.target.value as 'view')}
                                        className="mr-2"
                                    />
                                    <span className="text-sm">
                                        <strong>View</strong> - Read-only access to view data
                                    </span>
                                </label>
                                <label className="flex items-center">
                                    <input
                                        type="radio"
                                        value="admin"
                                        checked={permissionType === 'admin'}
                                        onChange={(e) => setPermissionType(e.target.value as 'admin')}
                                        className="mr-2"
                                    />
                                    <span className="text-sm">
                                        <strong>Admin</strong> - Full access to view, edit, and manage data
                                    </span>
                                </label>
                            </div>
                        </div>

                        {/* Justification */}
                        <div>
                            <label htmlFor="justification" className="block text-sm font-medium text-gray-700 mb-2">
                                Justification <span className="text-red-500">*</span>
                            </label>
                            <textarea
                                id="justification"
                                value={justification}
                                onChange={(e) => setJustification(e.target.value)}
                                rows={4}
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                placeholder="Please explain why you need access to this route..."
                                required
                            />
                            <p className="mt-1 text-sm text-gray-500">
                                Provide a clear business justification for your access request.
                            </p>
                        </div>

                        {/* Actions */}
                        <div className="flex gap-4">
                            <button
                                type="submit"
                                disabled={loading || availableRoutes.length === 0}
                                className="flex-1 bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors font-medium"
                            >
                                {loading ? 'Submitting...' : 'Submit Request'}
                            </button>
                            <button
                                type="button"
                                onClick={() => navigate(-1)}
                                className="px-6 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors font-medium"
                            >
                                Cancel
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
};
