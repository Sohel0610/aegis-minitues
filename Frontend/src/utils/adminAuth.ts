/**
 * Admin authentication utility functions
 */

// Define types for API responses
interface AdminLoginRequest {
  username: string;
  password: string;
}

interface AdminLoginResponse {
  success: boolean;
  message: string;
  token?: string;
}

/**
 * Check if user is authenticated as admin
 * @returns boolean indicating if user is admin
 */
export const isAdmin = (): boolean => {
  try {
    const adminToken = localStorage.getItem('adminToken');
    const isAdminStatus = localStorage.getItem('isAdmin');
    
    // Check if we have a valid admin token and status
    return adminToken !== null && isAdminStatus === 'true';
  } catch (error) {
    console.error('Error checking admin status:', error);
    return false;
  }
};

/**
 * Authenticate admin user with provided credentials
 * @param username - Admin username
 * @param password - Admin password
 * @returns Promise<boolean> indicating if authentication was successful
 */
export const authenticateAdmin = async (username: string, password: string): Promise<boolean> => {
  try {
    // Use relative path since frontend and backend are served from the same origin
    const response = await fetch(`/admin/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username,
        password
      })
    });
    
    if (response.ok) {
      const result: AdminLoginResponse = await response.json();
      
      if (result.success) {
        // Store authentication data in localStorage
        localStorage.setItem('isAdmin', 'true');
        if (result.token) {
          localStorage.setItem('adminToken', result.token);
        }
        return true;
      }
    }
    
    // Authentication failed
    return false;
  } catch (error) {
    console.error('Error authenticating admin:', error);
    return false;
  }
};

/**
 * Logout admin user
 */
export const logoutAdmin = (): void => {
  try {
    localStorage.removeItem('isAdmin');
    localStorage.removeItem('adminToken');
  } catch (error) {
    console.error('Error logging out admin:', error);
  }
};