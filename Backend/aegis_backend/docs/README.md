# SharePoint Integration API

This API provides endpoints for integrating with SharePoint, including loading Excel data directly from SharePoint URLs.

## Environment Configuration

To configure the SharePoint integration, update the following variables in your `.env` file:

```env
# SharePoint Configuration
SHAREPOINT_TENANT_ID="your-tenant-id"
SHAREPOINT_CLIENT_ID="your-client-id"
SHAREPOINT_CLIENT_SECRET="your-client-secret"
SHAREPOINT_SITE_NAME="your-site-name"
SHAREPOINT_FILE_URL="/sites/yoursite/Shared Documents/your-file.xlsx"

PORT=3001
```

## Endpoints

### Load Excel Data from SharePoint URL in Environment Variables

- **GET** `/excel-data-from-env`
- Loads Excel data from the SharePoint file URL specified in the `SHAREPOINT_FILE_URL` environment variable
- Returns JSON data with the Excel content

Example:
```bash
curl http://localhost:8001/excel-data-from-env
```

### Load Excel Data from Dynamic SharePoint URL

- **POST** `/excel-data-from-sharepoint`
- Loads Excel data from a dynamically provided SharePoint file URL
- Accepts JSON with `file_url` and optional `sheet_name` parameters

Example:
```bash
curl -X POST http://localhost:8001/excel-data-from-sharepoint \
  -H "Content-Type: application/json" \
  -d '{"file_url": "/sites/yoursite/Shared Documents/data.xlsx", "sheet_name": "Sheet1"}'
```

## Frontend Integration

The frontend includes a SharePoint loader component that can:
1. Load data from a SharePoint URL specified in the backend `.env` file
2. Load data from a dynamically provided SharePoint URL

To use the environment-based loading:
1. Configure `SHAREPOINT_FILE_URL` in the backend `.env` file
2. Click the "Load from ENV" button in the ExcelView component