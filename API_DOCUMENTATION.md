# Company Management & Audit API Documentation

## Base URL
```
http://localhost:5173/api
```

---

## 🏢 Company Management Endpoints

### 1. List Companies (with filtering)

**GET** `/verticals/{vertical_id}/companies`

**Description:** Get all companies in a vertical with optional meeting type filtering

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `vertical_id` | path | Yes | ID of the business vertical |
| `q` | query | No | Search query for company name |
| `meeting_type_filter` | query | No | Filter by meeting type (e.g., "Board Meeting") |
| `limit` | query | No | Max results (default: 100) |
| `offset` | query | No | Pagination offset (default: 0) |

**Meeting Type Options:**
- `Board Meeting`
- `Audit Committee`
- `Nomination and Remuneration Committee`
- `Stakeholders Relationship Committee`
- `CSR Committee`
- `Risk Management Committee`
- `AGM`
- `EGM`

**Example Request:**
```bash
curl -X GET "http://localhost:5173/api/verticals/1/companies?meeting_type_filter=Board Meeting&limit=50" \
  -H "Cookie: session_token=..."
```

**Response:**
```json
{
  "data": [
    {
      "id": 1,
      "name": "ADANI GREEN ENERGY LIMITED",
      "code": "AGEL",
      "cin": "U40106GJ2015PLC083964",
      "type": "Public Limited",
      "vertical_id": 1,
      "status": "Active",
      "secretary_name": "Kuntal Chandya",
      "created_by": "admin@company.com",
      "created_at": "2025-01-01T10:00:00",
      "updated_by": null,
      "updated_at": null,
      "total_meetings": 86,
      "last_meeting_date": "2025-01-28",
      "last_meeting_number": "86TH",
      "next_meeting_number": "87TH"
    }
  ],
  "count": 1
}
```

---

### 2. Create Company

**POST** `/verticals/{vertical_id}/companies`

**Description:** Add a new company to a vertical

**Authentication:** Required (session token)

**Request Body:**
```json
{
  "name": "New Company Limited",
  "code": "NCL",
  "cin": "U12345KA2025PLC123456",
  "type": "Public Limited",
  "secretary_name": "John Doe",
  "status": "Active"
}
```

**Field Details:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Company name (must be unique) |
| `code` | string | No | Company code (auto-generated if not provided) |
| `cin` | string | No | Corporate Identification Number |
| `type` | string | No | "Public Limited" or "Private Limited" |
| `secretary_name` | string | No | Company Secretary name |
| `status` | string | No | "Active" or "Inactive" (default: "Active") |

**Example Request:**
```bash
curl -X POST "http://localhost:5173/api/verticals/1/companies" \
  -H "Content-Type: application/json" \
  -H "Cookie: session_token=..." \
  -d '{
    "name": "Adani New Ventures Limited",
    "cin": "U99999MH2025PLC999999",
    "type": "Public Limited",
    "secretary_name": "Jane Smith",
    "status": "Active"
  }'
```

**Response:**
```json
{
  "id": 150,
  "name": "Adani New Ventures Limited",
  "code": "ANVL",
  "cin": "U99999MH2025PLC999999",
  "type": "Public Limited",
  "vertical_id": 1,
  "status": "Active",
  "secretary_name": "Jane Smith",
  "created_by": "admin@company.com",
  "created_at": "2025-01-15T14:30:00",
  "updated_by": null,
  "updated_at": null
}
```

**Error Responses:**
- `400` - Company name is required
- `409` - Company name already exists
- `503` - Database connection unavailable

---

### 3. Update Company

**PUT** `/companies/{company_id}`

**Description:** Update company details (partial updates supported)

**Authentication:** Required

**Request Body:**
```json
{
  "name": "Updated Company Name",
  "secretary_name": "New Secretary",
  "status": "Inactive"
}
```

**Note:** Only provided fields will be updated. All fields are optional.

**Example Request:**
```bash
curl -X PUT "http://localhost:5173/api/companies/150" \
  -H "Content-Type: application/json" \
  -H "Cookie: session_token=..." \
  -d '{
    "secretary_name": "Updated Secretary Name",
    "status": "Inactive"
  }'
```

**Response:** Same as Create Company response with updated fields

**Error Responses:**
- `400` - No fields provided for update
- `404` - Company not found
- `409` - New company name conflicts with existing

---

### 4. Delete Company

**DELETE** `/companies/{company_id}?confirm=true`

**Description:** Delete company and all related records (DESTRUCTIVE)

**Authentication:** Required (usually admin only)

**Query Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `confirm` | boolean | Yes | Must be `true` to proceed (safety check) |

**Example Request:**
```bash
curl -X DELETE "http://localhost:5173/api/companies/150?confirm=true" \
  -H "Cookie: session_token=..."
```

**Response:**
```json
{
  "success": true,
  "message": "Company 'Adani New Ventures Limited' deleted successfully",
  "company_id": 150,
  "company_name": "Adani New Ventures Limited",
  "deleted_records": {
    "meetings": 25,
    "attendance_records": 100,
    "directors": 8,
    "agendas": 10,
    "governance_records": 5,
    "total": 148
  },
  "deleted_by": "admin@company.com",
  "deleted_at": "2025-01-15T15:45:00"
}
```

**What Gets Deleted:**
- Company record
- All meetings/minutes
- All attendance records
- All director mappings
- All agendas
- All governance records

**Error Responses:**
- `400` - Confirmation required (missing `confirm=true`)
- `404` - Company not found

---

## 📋 Audit Log Endpoints

### 5. List Audit Logs

**GET** `/audit-logs`

**Description:** Get audit logs with comprehensive filtering

**Authentication:** Required

**Query Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `entity_type` | string | No | Filter by entity type (`company`, `meeting`, `user`) |
| `entity_id` | integer | No | Filter by specific entity ID |
| `action` | string | No | Filter by action (`created`, `updated`, `deleted`) |
| `company_name` | string | No | Filter by company name |
| `performed_by` | string | No | Filter by user email (admin only) |
| `date_from` | string | No | Start date (YYYY-MM-DD) |
| `date_to` | string | No | End date (YYYY-MM-DD) |
| `limit` | integer | No | Max results (default: 100, max: 1000) |
| `offset` | integer | No | Pagination offset |

**RBAC:**
- **Regular users:** Can only see their own actions
- **Admin users:** Can see all actions

**Example Request:**
```bash
curl -X GET "http://localhost:5173/api/audit-logs?entity_type=company&action=created&limit=50" \
  -H "Cookie: session_token=..."
```

**Response:**
```json
{
  "data": [
    {
      "id": 1234,
      "entity_type": "company",
      "entity_id": 150,
      "entity_name": "Adani New Ventures Limited",
      "action": "created",
      "performed_by": "admin@company.com",
      "performed_at": "2025-01-15T14:30:00",
      "old_data": null,
      "new_data": {
        "id": 150,
        "name": "Adani New Ventures Limited",
        "code": "ANVL",
        "cin": "U99999MH2025PLC999999"
      },
      "remarks": "Company 'Adani New Ventures Limited' added to system",
      "vertical_id": 1,
      "company_name": "Adani New Ventures Limited",
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0..."
    }
  ],
  "count": 1,
  "total_count": 1234
}
```

---

### 6. Audit Log Summary

**GET** `/audit-logs/summary`

**Description:** Get audit statistics and summary

**Authentication:** Required

**Example Request:**
```bash
curl -X GET "http://localhost:5173/api/audit-logs/summary" \
  -H "Cookie: session_token=..."
```

**Response:**
```json
{
  "total_actions": 5678,
  "recent_24h": 125,
  "actions_by_type": [
    {"action": "created", "count": 234},
    {"action": "updated", "count": 456},
    {"action": "deleted", "count": 12}
  ],
  "actions_by_entity": [
    {"entity_type": "company", "count": 150},
    {"entity_type": "meeting", "count": 450}
  ],
  "top_users": [
    {"user": "admin@company.com", "actions": 234},
    {"user": "user1@company.com", "actions": 189}
  ]
}
```

**Note:** `top_users` is only visible to admin users

---

### 7. Company Audit History

**GET** `/companies/{company_id}/audit-history`

**Description:** Get complete audit trail for a specific company

**Authentication:** Required

**Query Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `limit` | integer | No | Max results (default: 50) |
| `offset` | integer | No | Pagination offset |

**Example Request:**
```bash
curl -X GET "http://localhost:5173/api/companies/150/audit-history?limit=50" \
  -H "Cookie: session_token=..."
```

**Response:** Same structure as List Audit Logs

**Note:** This endpoint works even for deleted companies by searching audit logs

---

### 8. Company Timeline

**GET** `/companies/{company_id}/audit-timeline`

**Description:** Get visual timeline of company history

**Authentication:** Required

**Example Request:**
```bash
curl -X GET "http://localhost:5173/api/companies/150/audit-timeline" \
  -H "Cookie: session_token=..."
```

**Response:**
```json
{
  "company_id": 150,
  "company_name": "Adani New Ventures Limited",
  "total_events": 15,
  "timeline": [
    {
      "id": 1,
      "timestamp": "2025-01-15T14:30:00",
      "action": "created",
      "entity_type": "company",
      "performed_by": "admin@company.com",
      "description": "Company 'Adani New Ventures Limited' added to system"
    },
    {
      "id": 2,
      "timestamp": "2025-01-16T09:15:00",
      "action": "updated",
      "entity_type": "company",
      "performed_by": "user@company.com",
      "description": "Company 'Adani New Ventures Limited' updated. Changed fields: secretary_name, status",
      "changes": [
        {
          "field": "secretary_name",
          "from": "John Doe",
          "to": "Jane Smith"
        },
        {
          "field": "status",
          "from": "Active",
          "to": "Inactive"
        }
      ]
    }
  ]
}
```

---

## 🔐 Authentication

All endpoints require authentication via session cookie.

**Headers Required:**
```
Cookie: session_token=<your_session_token>
```

**Getting Session Token:**
Use the existing authentication endpoint (not part of this implementation).

---

## 📊 Response Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad Request (invalid parameters) |
| 401 | Unauthorized (no session) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Not Found |
| 409 | Conflict (duplicate name) |
| 500 | Internal Server Error |
| 503 | Service Unavailable (DB connection issue) |

---

## 🧪 Testing with cURL

### Test Company Creation
```bash
curl -X POST "http://localhost:5173/api/verticals/1/companies" \
  -H "Content-Type: application/json" \
  -H "Cookie: session_token=YOUR_TOKEN" \
  -d '{
    "name": "Test Company Ltd",
    "cin": "U99999MH2025PLC000001",
    "type": "Public Limited",
    "secretary_name": "Test Secretary"
  }'
```

### Test Company Update
```bash
curl -X PUT "http://localhost:5173/api/companies/150" \
  -H "Content-Type: application/json" \
  -H "Cookie: session_token=YOUR_TOKEN" \
  -d '{
    "secretary_name": "Updated Secretary"
  }'
```

### Test Company Deletion
```bash
curl -X DELETE "http://localhost:5173/api/companies/150?confirm=true" \
  -H "Cookie: session_token=YOUR_TOKEN"
```

### Test Audit Logs
```bash
curl -X GET "http://localhost:5173/api/audit-logs?entity_type=company&limit=10" \
  -H "Cookie: session_token=YOUR_TOKEN"
```

---

## 📝 Notes

1. **Transaction Safety:** All operations are wrapped in database transactions
2. **Audit Trail:** Every action is automatically logged with user, timestamp, IP, and changes
3. **Cascade Delete:** Deleting a company removes all related records
4. **Partial Updates:** Update endpoint only modifies provided fields
5. **Auto-generation:** Company codes are auto-generated if not provided
6. **RBAC:** Access control based on user roles (to be fully implemented)

---

## 🔍 Common Use Cases

### 1. Adding a New Company
1. Call POST `/verticals/{id}/companies` with company details
2. Company code is auto-generated (e.g., "AGEL" from "Adani Green Energy Limited")
3. Action is logged in audit_logs table

### 2. Filtering Companies by Meeting Type
1. Call GET `/verticals/{id}/companies?meeting_type_filter=Board Meeting`
2. Returns only companies that have Board Meetings
3. Includes meeting statistics (count, last date, next number)

### 3. Tracking Changes to a Company
1. Call GET `/companies/{id}/audit-history`
2. See complete history with before/after values
3. Or use `/companies/{id}/audit-timeline` for visual timeline

### 4. Viewing System Activity
1. Call GET `/audit-logs/summary` for overview
2. Call GET `/audit-logs` with filters for detailed logs
3. Filter by date range, user, action type, etc.

---

## 🎯 Frontend Integration Tips

1. **Company Cards:** Show `total_meetings`, `last_meeting_number`, `next_meeting_number` when filtered
2. **Add Company Form:** Code field can be optional (auto-generated)
3. **Delete Confirmation:** Always show what will be deleted (use returned counts)
4. **Audit Log Table:** Use pagination, show IP and user agent in tooltips
5. **Timeline View:** Use timeline response for visual representation

---

**For more details, see `IMPLEMENTATION_SUMMARY.md`**
