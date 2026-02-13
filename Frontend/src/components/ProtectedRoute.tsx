/**
 * ProtectedRoute Component
 * Updated to use route-based permissions instead of role-based access
 */

import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';

interface ProtectedRouteProps {
    children: React.ReactNode;
    requiredRoute?: string;
    requireAdmin?: boolean;
    requireEdit?: boolean;
    allowedRoles?: string[]; // Deprecated, kept for backward compatibility
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
    children,
    requiredRoute,
    requireAdmin = false,
    requireEdit = false,
    allowedRoles, // Deprecated
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
        return <Navigate to="/" state={{ from: location }} replace />;
    }

    // If no route specified, just check authentication
    if (!requiredRoute) {
        return <>{children}</>;
    }

    // Check if user has access to the route
    const userHasAccess = hasAccess(requiredRoute);

    if (!userHasAccess) {
        return <Navigate to="/access-denied" state={{ requestedRoute: requiredRoute }} replace />;
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

export default ProtectedRoute;
