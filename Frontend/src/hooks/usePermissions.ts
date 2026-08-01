/**
 * usePermissions Hook
 * Custom React hook for managing route-based permissions
 */

import { useState, useEffect, useCallback } from 'react';
import {
    getUserPermissions,
    checkRoutePermission,
    canAccessRoute,
    hasAnyAdminPermission,
    type RoutePermission,
    type UserPermissions,
    type PermissionCheckResult,
} from '../services/permissionService';

export interface UsePermissionsReturn {
    permissions: RoutePermission[];
    accessibleRoutes: string[];
    loading: boolean;
    error: string | null;
    hasAccess: (route: string) => boolean;
    canView: (route: string) => boolean;
    canEdit: (route: string) => boolean;
    canAdmin: (route: string) => boolean;
    isAdmin: boolean;
    refreshPermissions: () => Promise<void>;
    checkPermission: (route: string) => PermissionCheckResult;
}

export const usePermissions = (userEmail: string | null): UsePermissionsReturn => {
    const [permissions, setPermissions] = useState<RoutePermission[]>([]);
    const [accessibleRoutes, setAccessibleRoutes] = useState<string[]>([]);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    const loadPermissions = useCallback(async () => {
        if (!userEmail) {
            setPermissions([]);
            setAccessibleRoutes([]);
            setLoading(false);
            return;
        }

        try {
            setLoading(true);
            setError(null);

            const userPerms: UserPermissions = await getUserPermissions(userEmail);
            setPermissions(userPerms.permissions);
            setAccessibleRoutes(userPerms.accessible_routes);
        } catch (err) {
            console.error('Failed to load permissions:', err);
            setError(err instanceof Error ? err.message : 'Failed to load permissions');
            setPermissions([]);
            setAccessibleRoutes([]);
        } finally {
            setLoading(false);
        }
    }, [userEmail]);

    useEffect(() => {
        loadPermissions();
    }, [loadPermissions]);

    const hasAccess = useCallback(
        (route: string): boolean => {
            return accessibleRoutes.includes(route);
        },
        [accessibleRoutes]
    );

    const checkPermission = useCallback(
        (route: string): PermissionCheckResult => {
            return canAccessRoute(permissions, route);
        },
        [permissions]
    );

    const canView = useCallback(
        (route: string): boolean => {
            const result = checkPermission(route);
            return result.can_view;
        },
        [checkPermission]
    );

    const canEdit = useCallback(
        (route: string): boolean => {
            const result = checkPermission(route);
            return result.can_edit;
        },
        [checkPermission]
    );

    const canAdmin = useCallback(
        (route: string): boolean => {
            const result = checkPermission(route);
            return result.can_admin;
        },
        [checkPermission]
    );

    const isAdmin = useCallback((): boolean => {
        return hasAnyAdminPermission(permissions);
    }, [permissions]);

    const refreshPermissions = useCallback(async () => {
        await loadPermissions();
    }, [loadPermissions]);

    return {
        permissions,
        accessibleRoutes,
        loading,
        error,
        hasAccess,
        canView,
        canEdit,
        canAdmin,
        isAdmin: isAdmin(),
        refreshPermissions,
        checkPermission,
    };
};
