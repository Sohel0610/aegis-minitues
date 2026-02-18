export interface User {
  id: string;
  email: string;
  name: string;
  roles: string[];
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
}

const API_BASE_URL = "/api/auth";

export const authService = {
  /**
   * Initiates the SSO login process
   * Gets the redirect URL from backend and redirects the window
   * If SSO is disabled, returns mock user data
   */
  login: async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/login`);
      if (!response.ok) {
        throw new Error("Failed to initiate login");
      }
      const data = await response.json();

      // If SSO is disabled, handle local login with mock user
      if (data.sso_enabled === false && data.mock_user) {
        return {
          sso_enabled: false,
          user: {
            id: data.mock_user.email,
            email: data.mock_user.email,
            name: data.mock_user.name,
            roles: data.mock_user.roles
          },
          token: data.mock_user.token
        };
      }

      if (data.redirect_url) {
        window.location.href = data.redirect_url;
      }

      return { sso_enabled: true };
    } catch (error) {
      console.error("Login failed:", error);
      throw error;
    }
  },

  /**
   * Checks if SSO is enabled on the backend
   */
  getConfig: async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/config`);
      if (!response.ok) return { sso_enabled: true };
      return await response.json();
    } catch (error) {
      return { sso_enabled: true };
    }
  },

  /**
   * Logs out the user
   */
  logout: async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/logout`, {
        method: "POST",
      });
      if (!response.ok) {
        // Continue with local logout even if backend fails
        console.warn("Backend logout failed");
      }
      // Return true to indicate local cleanup should proceed
      return true;
    } catch (error) {
      console.error("Logout error:", error);
      return true; // Always return true to ensure local cleanup
    }
  },

  /**
   * Gets the current user from session (backend check)
   * This is useful to validate if the token is still valid
   */
  getCurrentUser: async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/me`);
      if (!response.ok) {
        return null;
      }
      return await response.json();
    } catch (error) {
      return null;
    }
  }
};
