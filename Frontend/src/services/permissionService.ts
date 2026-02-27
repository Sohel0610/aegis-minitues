/**
 * Permission Service
 * Handles route-based permission checks and management
 */

const API_BASE_URL = '';

export interface RoutePermission {
  route: string;
  permission_type: 'view' | 'admin' | 'edit';
  route_name: string;
  description?: string;
  can_view: boolean;
  can_edit: boolean;
  can_admin: boolean;
}

export interface UserPermissions {
  email: string;
  permissions: RoutePermission[];
  accessible_routes: string[];
}

export interface PermissionCheckResult {
  has_access: boolean;
  permission_type?: string;
  can_view: boolean;
  can_edit: boolean;
  can_admin: boolean;
  message?: string;
  can_request_access?: boolean;
}

export interface AccessRequest {
  email: string;
  name: string;
  requested_route: string;
  requested_permission: 'view' | 'admin' | 'edit';
  justification: string;
}

export interface AccessRequestResponse {
  id: number;
  email: string;
  name: string;
  requested_route: string;
  requested_permission: string;
  justification: string;
  status: 'pending' | 'approved' | 'rejected';
  requested_at: string;
  reviewed_by?: string;
  reviewed_at?: string;
  review_notes?: string;
}

export interface RouteDefinition {
  route_path: string;
  route_name: string;
  description?: string;
  application: string;
}

export interface AuditLog {
  id: number;
  email: string;
  event_type: string;
  event_details: string;
  ip_address?: string;
  user_agent?: string;
  timestamp: string;
  application: string;
}

export interface AuditLogsResponse {
  logs: AuditLog[];
  total: number;
  limit: number;
  offset: number;
}

/**
 * Get current user's permissions
 */
export const getUserPermissions = async (email: string): Promise<UserPermissions> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/users/me/permissions?email=${encodeURIComponent(email)}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'X-User-Email': email,
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch permissions: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching user permissions:', error);
    throw error;
  }
};

/**
 * Check if user has access to a specific route
 */
export const checkRoutePermission = async (
  email: string,
  route: string
): Promise<PermissionCheckResult> => {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/permissions/check?route=${encodeURIComponent(route)}&email=${encodeURIComponent(email)}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-User-Email': email,
        },
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to check permission: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error checking route permission:', error);
    throw error;
  }
};

/**
 * Submit an access request for a route
 */
export const submitAccessRequest = async (
  request: AccessRequest
): Promise<{ id: number; status: string; message: string }> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/access-requests`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-User-Email': request.email,
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to submit access request');
    }

    return await response.json();
  } catch (error) {
    console.error('Error submitting access request:', error);
    throw error;
  }
};

/**
 * Get all access requests (Admin only)
 */
export const getAccessRequests = async (
  email: string,
  status?: string,
  route?: string
): Promise<{ requests: AccessRequestResponse[]; total: number }> => {
  try {
    const params = new URLSearchParams();
    params.append('email', email);
    if (status) params.append('status', status);
    if (route) params.append('route', route);

    const response = await fetch(`${API_BASE_URL}/api/access-requests?${params.toString()}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'X-User-Email': email,
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch access requests: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching access requests:', error);
    throw error;
  }
};

/**
 * Approve an access request (Admin only)
 */
export const approveAccessRequest = async (
  adminEmail: string,
  requestId: number,
  reviewNotes?: string
): Promise<{ success: boolean; message: string }> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/access-requests/${requestId}/approve`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'X-User-Email': adminEmail,
      },
      body: JSON.stringify({ review_notes: reviewNotes }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to approve access request');
    }

    return await response.json();
  } catch (error) {
    console.error('Error approving access request:', error);
    throw error;
  }
};

/**
 * Reject an access request (Admin only)
 */
export const rejectAccessRequest = async (
  adminEmail: string,
  requestId: number,
  reviewNotes?: string
): Promise<{ success: boolean; message: string }> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/access-requests/${requestId}/reject`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'X-User-Email': adminEmail,
      },
      body: JSON.stringify({ review_notes: reviewNotes }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to reject access request');
    }

    return await response.json();
  } catch (error) {
    console.error('Error rejecting access request:', error);
    throw error;
  }
};

/**
 * Assign permission to a user (Admin only)
 */
export const assignPermission = async (
  adminEmail: string,
  userEmail: string,
  route: string,
  permissionType: 'view' | 'admin' | 'edit',
  notes?: string
): Promise<{ success: boolean; message: string }> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/permissions/assign`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-User-Email': adminEmail,
      },
      body: JSON.stringify({
        email: userEmail,
        route,
        permission_type: permissionType,
        notes,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to assign permission');
    }

    return await response.json();
  } catch (error) {
    console.error('Error assigning permission:', error);
    throw error;
  }
};

/**
 * Revoke permission from a user (Admin only)
 */
export const revokePermission = async (
  adminEmail: string,
  userEmail: string,
  route: string
): Promise<{ success: boolean; message: string }> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/permissions/revoke`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        'X-User-Email': adminEmail,
      },
      body: JSON.stringify({
        email: userEmail,
        route,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to revoke permission');
    }

    return await response.json();
  } catch (error) {
    console.error('Error revoking permission:', error);
    throw error;
  }
};

/**
 * Get all permissions for a route (Admin only)
 */
export const getRoutePermissions = async (
  adminEmail: string,
  route?: string
): Promise<any> => {
  try {
    const params = new URLSearchParams();
    params.append('email', adminEmail);
    if (route) params.append('route', route);

    const response = await fetch(`${API_BASE_URL}/api/permissions/all?${params.toString()}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'X-User-Email': adminEmail,
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch route permissions: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching route permissions:', error);
    throw error;
  }
};

/**
 * Get all route definitions (Admin only)
 */
export const getRouteDefinitions = async (email: string): Promise<RouteDefinition[]> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/route-definitions`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'X-User-Email': email,
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch route definitions: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching route definitions:', error);
    throw error;
  }
};

/**
 * Get audit logs (Admin only)
 */
export const getAuditLogs = async (
  email: string,
  limit: number = 50,
  offset: number = 0,
  eventType?: string
): Promise<AuditLogsResponse> => {
  try {
    const params = new URLSearchParams();
    params.append('limit', limit.toString());
    params.append('offset', offset.toString());
    if (eventType) params.append('event_type', eventType);

    const response = await fetch(`${API_BASE_URL}/api/audit-logs?${params.toString()}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'X-User-Email': email,
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch audit logs: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching audit logs:', error);
    throw error;
  }
};

/**
 * Helper function to check if user can access a route from cached permissions
 */
export const canAccessRoute = (
  permissions: RoutePermission[],
  route: string
): PermissionCheckResult => {
  const permission = permissions.find((p) => p.route === route);

  if (!permission) {
    return {
      has_access: false,
      can_view: false,
      can_edit: false,
      can_admin: false,
      message: 'No permission found for this route',
      can_request_access: true,
    };
  }

  return {
    has_access: true,
    permission_type: permission.permission_type,
    can_view: permission.can_view,
    can_edit: permission.can_edit,
    can_admin: permission.can_admin,
  };
};

/**
 * Helper function to check if user has admin permission on any route
 */
export const hasAnyAdminPermission = (permissions: RoutePermission[]): boolean => {
  return permissions.some((p) => p.can_admin);
};
