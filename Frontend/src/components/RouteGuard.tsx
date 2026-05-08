/**
 * RouteGuard Component
 * Protects routes based on user permissions
 * Shows access denied or request access UI if user doesn't have permission
 */

import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { getRouteDefinitions, type RouteDefinition } from '@/services/permissionService';

interface RouteGuardProps {
    children: React.ReactNode;
    requiredRoute: string;
    requireAdmin?: boolean;
    requireEdit?: boolean;
    fallbackPath?: string;
}

export const RouteGuard: React.FC<RouteGuardProps> = ({
    children,
    requiredRoute,
    requireAdmin = false,
    requireEdit = false,
    fallbackPath = '/access-denied',
}) => {
    const { isAuthenticated, isLoading, hasAccess, canAdmin, canEdit } = useAuth();
    const location = useLocation();

    // Show loading state
    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
        );
    }

    // Redirect to login if not authenticated
    if (!isAuthenticated) {
        return <Navigate to="/login" state={{ from: location }} replace />;
    }

    // Check if user has access to the route
    const userHasAccess = hasAccess(requiredRoute);

    if (!userHasAccess) {
        return <Navigate to={fallbackPath} state={{ requestedRoute: requiredRoute }} replace />;
    }

    // Check admin permission if required
    if (requireAdmin && !canAdmin(requiredRoute)) {
        return <Navigate to="/access-denied" state={{ reason: 'admin_required' }} replace />;
    }

    // Check edit permission if required
    if (requireEdit && !canEdit(requiredRoute)) {
        return <Navigate to="/access-denied" state={{ reason: 'edit_required' }} replace />;
    }

    // User has required permissions, render children
    return <>{children}</>;
};

/**
 * AccessDenied Component
 * Shows when user doesn't have permission to access a route
 */
export const AccessDenied: React.FC = () => {
    const location = useLocation();
    const { user } = useAuth();
    const state = location.state as { requestedRoute?: string; reason?: string } | null;
    const [routeDefinitions, setRouteDefinitions] = React.useState<RouteDefinition[]>([]);

    React.useEffect(() => {
        if (user) {
            getRouteDefinitions(user.email).then(setRouteDefinitions).catch(console.error);
        }
    }, [user]);

    const getRouteName = (routePath: string) => {
        const route = routeDefinitions.find(r => r.route_path === routePath);
        return route ? route.route_name : routePath;
    };

    const handleRequestAccess = () => {
        // Navigate to access request page with pre-filled route
        window.location.href = `/access-request?route=${encodeURIComponent(state?.requestedRoute || '')}`;
    };

    return (
        <div className="flex items-center justify-center min-h-screen bg-gray-50">
            <div className="max-w-md w-full bg-white shadow-lg rounded-lg p-8">
                <div className="text-center">
                    <svg
                        className="mx-auto h-16 w-16 text-red-500"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                    >
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                        />
                    </svg>
                    <h2 className="mt-4 text-2xl font-bold text-gray-900">Access Denied</h2>
                    <p className="mt-2 text-gray-600">
                        {state?.reason === 'admin_required'
                            ? `You need admin permissions to access ${state.requestedRoute ? getRouteName(state.requestedRoute) : 'this page'}.`
                            : state?.reason === 'edit_required'
                                ? `You need edit permissions to access ${state.requestedRoute ? getRouteName(state.requestedRoute) : 'this page'}.`
                                : `You do not have permission to access ${state?.requestedRoute ? getRouteName(state.requestedRoute) : 'this page'}.`}
                    </p>
                    {state?.requestedRoute && getRouteName(state.requestedRoute) && !getRouteName(state.requestedRoute).startsWith('/') && (
                        <p className="mt-2 text-sm text-gray-500">
                            Requested Application: <span className="font-semibold text-gray-700">{getRouteName(state.requestedRoute)}</span>
                        </p>
                    )}
                    {user && (
                        <p className="mt-4 text-xs text-gray-400">
                            Logged in as: <strong>{user.email}</strong>
                        </p>
                    )}
                </div>

                <div className="mt-6 space-y-3">
                    <button
                        onClick={handleRequestAccess}
                        className="w-full bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                    >
                        Request Access
                    </button>
                    <button
                        onClick={() => window.history.back()}
                        className="w-full bg-gray-200 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-300 transition-colors"
                    >
                        Go Back
                    </button>
                    <button
                        onClick={() => (window.location.href = '/')}
                        className="w-full bg-white text-gray-700 px-4 py-2 rounded-lg border border-gray-300 hover:bg-gray-50 transition-colors"
                    >
                        Go to Dashboard
                    </button>
                </div>
            </div>
        </div>
    );
};
