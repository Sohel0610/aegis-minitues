import React, { createContext, useContext, useEffect, useState } from "react";
import { authService, User } from "@/services/authService";
import { useLocation, useNavigate } from "react-router-dom";
import { getUserPermissions, type RoutePermission } from "@/services/permissionService";

interface AuthContextType {
    user: User | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    permissions: RoutePermission[];
    accessibleRoutes: string[];
    hasAccess: (route: string) => boolean;
    canView: (route: string) => boolean;
    canEdit: (route: string) => boolean;
    canAdmin: (route: string) => boolean;
    isAdmin: boolean;
    login: () => Promise<void>;
    logout: () => Promise<void>;
    refreshPermissions: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [permissions, setPermissions] = useState<RoutePermission[]>([]);
    const [accessibleRoutes, setAccessibleRoutes] = useState<string[]>([]);
    const location = useLocation();
    const navigate = useNavigate();

    // Load permissions for a user
    const loadPermissions = async (userEmail: string) => {
        try {
            const userPerms = await getUserPermissions(userEmail);
            setPermissions(userPerms.permissions);
            setAccessibleRoutes(userPerms.accessible_routes);

            // Store permissions in localStorage for offline access
            localStorage.setItem("aegis_permissions", JSON.stringify(userPerms.permissions));
            localStorage.setItem("aegis_accessible_routes", JSON.stringify(userPerms.accessible_routes));
        } catch (error) {
            console.error("Failed to load permissions:", error);
            // Load from localStorage as fallback
            const storedPerms = localStorage.getItem("aegis_permissions");
            const storedRoutes = localStorage.getItem("aegis_accessible_routes");
            if (storedPerms && storedRoutes) {
                setPermissions(JSON.parse(storedPerms));
                setAccessibleRoutes(JSON.parse(storedRoutes));
            }
        }
    };

    const isInitialized = React.useRef(false);

    useEffect(() => {
        // Prevent multiple initializations
        if (isInitialized.current) return;

        const initAuth = async () => {
            const searchParams = new URLSearchParams(window.location.search);
            const tokenParams = searchParams.get("token");

            try {
                if (tokenParams) {
                    // Handle SSO Callback
                    const email = searchParams.get("email");
                    const name = searchParams.get("name");
                    const hasAccessFlag = searchParams.get("has_access") === "true";

                    if (email) {
                        const newUser: User = { id: email, email, name: name || email, roles: [] };
                        localStorage.setItem("aegis_auth_token", tokenParams);
                        localStorage.setItem("aegis_user", JSON.stringify(newUser));
                        setUser(newUser);

                        await loadPermissions(email);

                        // Mark as initialized and clear loading BEFORE navigation
                        isInitialized.current = true;
                        setIsLoading(false);
                        navigate("/", { replace: true });
                        return;
                    }
                } else {
                    // Handle Existing Session
                    const storedToken = localStorage.getItem("aegis_auth_token");
                    const storedUser = localStorage.getItem("aegis_user");

                    if (storedToken && storedUser) {
                        const parsedUser = JSON.parse(storedUser);
                        setUser(parsedUser);

                        // Load cache for better initial UX
                        const storedPerms = localStorage.getItem("aegis_permissions");
                        const storedRoutes = localStorage.getItem("aegis_accessible_routes");
                        if (storedPerms && storedRoutes) {
                            setPermissions(JSON.parse(storedPerms));
                            setAccessibleRoutes(JSON.parse(storedRoutes));
                        }

                        // Always refresh permissions to ensure they are up to date
                        await loadPermissions(parsedUser.email);
                    }
                }
            } catch (error) {
                console.error("Auth initialization error:", error);
            } finally {
                // Ensure loading is cleared ONLY once
                if (!isInitialized.current) {
                    isInitialized.current = true;
                    setIsLoading(false);
                }
            }
        };

        initAuth();
    }, [navigate]);

    const login = async () => {
        await authService.login();
    };

    const logout = async () => {
        await authService.logout();
        localStorage.removeItem("aegis_auth_token");
        localStorage.removeItem("aegis_user");
        localStorage.removeItem("aegis_permissions");
        localStorage.removeItem("aegis_accessible_routes");
        setUser(null);
        setPermissions([]);
        setAccessibleRoutes([]);
        navigate("/");
    };

    const refreshPermissions = async () => {
        if (user?.email) {
            await loadPermissions(user.email);
        }
    };

    // Helper functions
    const normalizeRoute = (r: string) => r.replace(/\/+$/, "").replace(/^\/*/, "/").toLowerCase();

    const isAdmin = permissions.some(p => p.can_admin);

    const hasAccess = (route: string): boolean => {
        if (isAdmin) return true;
        const normalized = normalizeRoute(route);
        return accessibleRoutes.some(r => normalizeRoute(r) === normalized);
    };

    const canView = (route: string): boolean => {
        if (isAdmin) return true;
        const normalized = normalizeRoute(route);
        const perm = permissions.find(p => normalizeRoute(p.route) === normalized);
        return perm?.can_view || false;
    };

    const canEdit = (route: string): boolean => {
        if (isAdmin) return true;
        const normalized = normalizeRoute(route);
        const perm = permissions.find(p => normalizeRoute(p.route) === normalized);
        return perm?.can_edit || false;
    };

    const canAdmin = (route: string): boolean => {
        if (isAdmin) return true;
        const normalized = normalizeRoute(route);
        const perm = permissions.find(p => normalizeRoute(p.route) === normalized);
        return perm?.can_admin || false;
    };

    return (
        <AuthContext.Provider
            value={{
                user,
                isAuthenticated: !!user,
                isLoading,
                permissions,
                accessibleRoutes,
                hasAccess,
                canView,
                canEdit,
                canAdmin,
                isAdmin,
                login,
                logout,
                refreshPermissions
            }}
        >
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error("useAuth must be used within an AuthProvider");
    }
    return context;
};
