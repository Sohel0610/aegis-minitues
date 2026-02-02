import React, { useEffect } from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';

interface ProtectedRouteProps {
    children?: React.ReactNode;
    allowedRoles?: string[];
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, allowedRoles }) => {
    const { user, isAuthenticated, isLoading, login } = useAuth();
    const location = useLocation();

    useEffect(() => {
        if (!isLoading && !isAuthenticated) {
            // Automatically trigger login if not authenticated
            login();
        }
    }, [isLoading, isAuthenticated, login]);

    if (isLoading) {
        // Show a simple loading state while checking auth
        return (
            <div className="flex h-screen w-full items-center justify-center bg-white">
                <div className="flex flex-col items-center gap-4">
                    <div className="h-12 w-12 animate-spin rounded-full border-4 border-gray-200 border-t-[#0B74B0]"></div>
                    <p className="text-gray-500 font-medium">Authenticating...</p>
                </div>
            </div>
        );
    }

    if (!isAuthenticated) {
        // If not authenticated (and login triggered), return null or a placeholder
        // The useEffect above handles the redirect to SSO
        return null;
    }

    if (allowedRoles && user) {
        const hasPermission = allowedRoles.some(role => user.roles.includes(role)) || user.roles.includes('admin');
        if (!hasPermission) {
            return <Navigate to="/" replace />;
        }
    }

    return children ? <>{children}</> : <Outlet />;
};

export default ProtectedRoute;
