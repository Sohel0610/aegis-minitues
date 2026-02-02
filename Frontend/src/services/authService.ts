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
   */
  login: async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/login`);
      if (!response.ok) {
        throw new Error("Failed to initiate login");
      }
      const data = await response.json();
      if (data.redirect_url) {
        window.location.href = data.redirect_url;
      }
    } catch (error) {
      console.error("Login failed:", error);
      throw error;
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
