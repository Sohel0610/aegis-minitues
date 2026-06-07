/**
 * Permission Service
 * Handles route-based permission checks and management
 */

const API_BASE_URL = '';

// ─── Auth Header Helper ───────────────────────────────────────────────────────
const getAuthHeaders = (email: string): HeadersInit => {
  const token = localStorage.getItem('aegis_auth_token');
  return {
    'Content-Type': 'application/json',
    'X-User-Email': email,
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
  };
};

// ─── Interfaces ───────────────────────────────────────────────────────────────

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

// ─── Endpoints ────────────────────────────────────────────────────────────────

/** Get current user's permissions */
export const getUserPermissions = async (email: string): Promise<UserPermissions> => {
  const response = await fetch(
    `${API_BASE_URL}/api/users/me/permissions?email=${encodeURIComponent(email)}`,
    { method: 'GET', headers: getAuthHeaders(email) }
  );
  if (!response.ok) throw new Error(`Failed to fetch permissions: ${response.statusText}`);
  return response.json();
};

/** Check if user has access to a specific route */
export const checkRoutePermission = async (email: string, route: string): Promise<PermissionCheckResult> => {
  const response = await fetch(
    `${API_BASE_URL}/api/permissions/check?route=${encodeURIComponent(route)}&email=${encodeURIComponent(email)}`,
    { method: 'GET', headers: getAuthHeaders(email) }
  );
  if (!response.ok) throw new Error(`Failed to check permission: ${response.statusText}`);
  return response.json();
};

/** Submit an access request for a route */
export const submitAccessRequest = async (
  request: AccessRequest
): Promise<{ id: number; status: string; message: string }> => {
  const response = await fetch(`${API_BASE_URL}/api/access-requests`, {
    method: 'POST',
    headers: getAuthHeaders(request.email),
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to submit access request');
  }
  return response.json();
};

/** Get all access requests (Admin only) */
export const getAccessRequests = async (
  email: string,
  status?: string,
  route?: string
): Promise<{ requests: AccessRequestResponse[]; total: number }> => {
  const params = new URLSearchParams();
  params.append('email', email);
  if (status) params.append('status', status);
  if (route) params.append('route', route);

  const response = await fetch(`${API_BASE_URL}/api/access-requests?${params.toString()}`, {
    method: 'GET',
    headers: getAuthHeaders(email),
  });
  if (!response.ok) throw new Error(`Failed to fetch access requests: ${response.statusText}`);
  return response.json();
};

/** Approve an access request (Admin only) */
export const approveAccessRequest = async (
  adminEmail: string,
  requestId: number,
  reviewNotes?: string
): Promise<{ success: boolean; message: string }> => {
  const response = await fetch(
    `${API_BASE_URL}/api/access-requests/${requestId}/approve?email=${encodeURIComponent(adminEmail)}`,
    {
      method: 'PUT',
      headers: getAuthHeaders(adminEmail),
      body: JSON.stringify({ review_notes: reviewNotes }),
    }
  );
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to approve access request');
  }
  return response.json();
};

/** Reject an access request (Admin only) */
export const rejectAccessRequest = async (
  adminEmail: string,
  requestId: number,
  reviewNotes?: string
): Promise<{ success: boolean; message: string }> => {
  const response = await fetch(
    `${API_BASE_URL}/api/access-requests/${requestId}/reject?email=${encodeURIComponent(adminEmail)}`,
    {
      method: 'PUT',
      headers: getAuthHeaders(adminEmail),
      body: JSON.stringify({ review_notes: reviewNotes }),
    }
  );
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to reject access request');
  }
  return response.json();
};

/** Assign permission to a user (Admin only) */
export const assignPermission = async (
  adminEmail: string,
  userEmail: string,
  route: string,
  permissionType: 'view' | 'admin' | 'edit',
  notes?: string
): Promise<{ success: boolean; message: string }> => {
  const response = await fetch(`${API_BASE_URL}/api/permissions/assign`, {
    method: 'POST',
    headers: getAuthHeaders(adminEmail),
    body: JSON.stringify({ email: userEmail, route, permission_type: permissionType, notes }),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to assign permission');
  }
  return response.json();
};

/** Revoke permission from a user (Admin only) */
export const revokePermission = async (
  adminEmail: string,
  userEmail: string,
  route: string
): Promise<{ success: boolean; message: string }> => {
  const response = await fetch(
    `${API_BASE_URL}/api/permissions/revoke?email=${encodeURIComponent(adminEmail)}`,
    {
      method: 'DELETE',
      headers: getAuthHeaders(adminEmail),
      body: JSON.stringify({ email: userEmail, route }),
    }
  );
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to revoke permission');
  }
  return response.json();
};

/** Get all permissions for a route (Admin only) — returns list of users */
export const getRoutePermissions = async (
  adminEmail: string,
  route?: string
): Promise<{ permissions: any[]; total: number }> => {
  const params = new URLSearchParams();
  params.append('email', adminEmail);
  if (route) params.append('route', route);

  const response = await fetch(`${API_BASE_URL}/api/permissions/all?${params.toString()}`, {
    method: 'GET',
    headers: getAuthHeaders(adminEmail),
  });
  if (!response.ok) throw new Error(`Failed to fetch route permissions: ${response.statusText}`);
  return response.json();
};

/** Get all route definitions */
export const getRouteDefinitions = async (email: string): Promise<RouteDefinition[]> => {
  const response = await fetch(`${API_BASE_URL}/api/route-definitions`, {
    method: 'GET',
    headers: getAuthHeaders(email),
  });
  if (!response.ok) throw new Error(`Failed to fetch route definitions: ${response.statusText}`);
  const data = await response.json();
  // Backend returns display_name, normalize to route_name for frontend
  return (Array.isArray(data) ? data : []).map((r: any) => ({
    route_path: r.route_path,
    route_name: r.display_name || r.route_name || r.route_path,
    application: r.module_name || r.application || '',
    description: r.description,
  }));
};

/** Get audit logs (Admin only) */
export const getAuditLogs = async (
  email: string,
  limit: number = 50,
  offset: number = 0,
  eventType?: string
): Promise<AuditLogsResponse> => {
  const params = new URLSearchParams();
  params.append('limit', limit.toString());
  params.append('offset', offset.toString());
  if (eventType) params.append('event_type', eventType);

  const response = await fetch(`${API_BASE_URL}/api/audit-logs?${params.toString()}`, {
    method: 'GET',
    headers: getAuthHeaders(email),
  });
  if (!response.ok) throw new Error(`Failed to fetch audit logs: ${response.statusText}`);
  const data = await response.json();
  // Normalize timestamp field (backend returns created_at)
  return {
    ...data,
    logs: (data.logs || []).map((l: any) => ({
      ...l,
      timestamp: l.timestamp || l.created_at || '',
    })),
  };
};

// ─── Local Helpers ────────────────────────────────────────────────────────────

export const canAccessRoute = (permissions: RoutePermission[], route: string): PermissionCheckResult => {
  const permission = permissions.find((p) => p.route === route);
  if (!permission) {
    return { has_access: false, can_view: false, can_edit: false, can_admin: false, message: 'No permission found', can_request_access: true };
  }
  return { has_access: true, permission_type: permission.permission_type, can_view: permission.can_view, can_edit: permission.can_edit, can_admin: permission.can_admin };
};

export const hasAnyAdminPermission = (permissions: RoutePermission[]): boolean =>
  permissions.some((p) => p.can_admin);

// ─── Admin Management ─────────────────────────────────────────────────────────

/** Get all platform-level admins (from user_roles table) */
export const getPlatformAdmins = async (
  adminEmail: string
): Promise<{ admins: any[]; total: number }> => {
  const response = await fetch(
    `${API_BASE_URL}/api/admin/platform-admins?email=${encodeURIComponent(adminEmail)}`,
    { method: 'GET', headers: getAuthHeaders(adminEmail) }
  );
  if (!response.ok) throw new Error(`Failed to fetch platform admins: ${response.statusText}`);
  return response.json();
};

/** Grant a global platform role to a user (e.g. admin) */
export const grantPlatformRole = async (
  adminEmail: string,
  targetEmail: string,
  role: string = 'admin'
): Promise<{ success: boolean; message: string }> => {
  const response = await fetch(
    `${API_BASE_URL}/api/admin/grant-role?email=${encodeURIComponent(adminEmail)}`,
    {
      method: 'POST',
      headers: getAuthHeaders(adminEmail),
      body: JSON.stringify({ target_email: targetEmail, role }),
    }
  );
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to grant role');
  }
  return response.json();
};

/** Revoke a global platform role from a user */
export const revokePlatformRole = async (
  adminEmail: string,
  targetEmail: string
): Promise<{ success: boolean; message: string }> => {
  const response = await fetch(
    `${API_BASE_URL}/api/admin/revoke-role?email=${encodeURIComponent(adminEmail)}`,
    {
      method: 'DELETE',
      headers: getAuthHeaders(adminEmail),
      body: JSON.stringify({ target_email: targetEmail }),
    }
  );
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to revoke role');
  }
  return response.json();
};

/** Get all users with any route permission (platform-wide view) */
export const getAllPlatformUsers = async (
  adminEmail: string
): Promise<{ users: any[]; total: number }> => {
  const response = await fetch(
    `${API_BASE_URL}/api/admin/all-users?email=${encodeURIComponent(adminEmail)}`,
    { method: 'GET', headers: getAuthHeaders(adminEmail) }
  );
  if (!response.ok) throw new Error(`Failed to fetch platform users: ${response.statusText}`);
  return response.json();
};

