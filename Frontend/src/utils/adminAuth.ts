/**
 * DEPRECATED: Legacy admin authentication utilities
 * These functions are stubs for backward compatibility only.
 * All admin features should now use SSO-based route permissions.
 * 
 * TODO: Remove all calls to these functions and replace with SSO permission checks
 */

export const isAdmin = (): boolean => {
    // Always return false - admin features disabled
    // Use SSO route permissions instead
    return false;
};

export const authenticateAdmin = async (username: string, password: string): Promise<boolean> => {
    // Legacy admin login disabled
    // Use SSO login instead
    console.warn('Legacy admin authentication is disabled. Please use SSO login.');
    return false;
};

export const logoutAdmin = (): void => {
    // No-op - use SSO logout instead
    console.warn('Legacy admin logout is disabled. Please use SSO logout.');
};
