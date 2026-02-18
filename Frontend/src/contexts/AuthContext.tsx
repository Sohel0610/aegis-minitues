import React, { createContext, useContext, useEffect, useState } from "react";
import { authService, User } from "@/services/authService";
import { useLocation, useNavigate } from "react-router-dom";

interface AuthContextType {
    user: User | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    ssoEnabled: boolean | null;
    login: () => Promise<void>;
    logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [ssoEnabled, setSsoEnabled] = useState<boolean | null>(null);
    const location = useLocation();
    const navigate = useNavigate();

    useEffect(() => {
        // Check for token and user info in URL parameters (callback from SSO)
        const searchParams = new URLSearchParams(location.search);
        const tokenParams = searchParams.get("token");

        if (tokenParams) {
            // Extract user info from URL
            const email = searchParams.get("email");
            const name = searchParams.get("name");
            const rolesStr = searchParams.get("roles");

            if (email) {
                const newUser: User = {
                    id: email, // Using email as ID for now since backend doesn't pass ID in query
                    email,
                    name: name || email,
                    roles: rolesStr ? rolesStr.split(",") : [],
                };

                // Save to local storage
                localStorage.setItem("aegis_auth_token", tokenParams);
                localStorage.setItem("aegis_user", JSON.stringify(newUser));

                setUser(newUser);

                // Clean up URL
                navigate(location.pathname, { replace: true });
            }
        } else {
            // Check local storage
            const storedToken = localStorage.getItem("aegis_auth_token");
            const storedUser = localStorage.getItem("aegis_user");

            if (storedToken && storedUser) {
                try {
                    setUser(JSON.parse(storedUser));
                } catch (e) {
                    console.error("Failed to parse stored user", e);
                    localStorage.removeItem("aegis_auth_token");
                    localStorage.removeItem("aegis_user");
                }
            }
        }

        setIsLoading(false);
    }, [location, navigate]);

    useEffect(() => {
        authService.getConfig().then(config => setSsoEnabled(config.sso_enabled));
    }, []);

    const login = async () => {
        const result = await authService.login();

        // If SSO was disabled, authService.login returns user and token directly
        if (result && result.sso_enabled === false && result.user && result.token) {
            localStorage.setItem("aegis_auth_token", result.token);
            localStorage.setItem("aegis_user", JSON.stringify(result.user));
            setUser(result.user);
        }
    };

    const logout = async () => {
        await authService.logout();
        localStorage.removeItem("aegis_auth_token");
        localStorage.removeItem("aegis_user");
        setUser(null);
        navigate("/");
    };

    return (
        <AuthContext.Provider value={{ user, isAuthenticated: !!user, isLoading, ssoEnabled, login, logout }}>
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
