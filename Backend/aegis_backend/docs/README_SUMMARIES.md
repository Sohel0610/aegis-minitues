# Document Summaries Implementation

This implementation adds functionality to generate and display summaries of director disclosure documents instead of showing the full content.

## Features

1. **Database Storage**: Added a `document_summaries` table to store generated summaries
2. **LLM Integration**: Integration with Groq LLM for generating document summaries
3. **API Endpoints**: 
   - GET `/api/directors-disclosures/{id}/summary` - Retrieve document summary
   - POST `/api/directors-disclosures/{id}/generate-summary` - Generate document summary
4. **Frontend Integration**: Updated UI to display summaries instead of full document content

## Database Schema

The `document_summaries` table has the following structure:

```sql
CREATE TABLE document_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    director_name TEXT NOT NULL,
    din TEXT,
    file_path TEXT NOT NULL,
    summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## API Endpoints

### Get Document Summary
```
GET /api/directors-disclosures/{disclosure_id}/summary
```

Returns a JSON object with the document summary:
```json
{
  "id": 1,
  "director_name": "John Doe",
  "din": "12345678",
  "file_path": "John Doe_MBP.docx",
  "summary": "This is a summary of the document...",
  "created_at": "2023-01-01T00:00:00",
  "updated_at": "2023-01-01T00:00:00"
}
```

### Generate Document Summary
```
POST /api/directors-disclosures/{disclosure_id}/generate-summary
```

Returns a JSON object with the generation result:
```json
{
  "success": true,
  "message": "Summary generated successfully",
  "summary": "This is a summary of the document..."
}
```

## Implementation Details

### Backend Files

1. `llm_utils.py` - Contains functions for:
   - Extracting text from DOCX files
   - Generating summaries using Groq LLM
   - Saving/retrieving summaries from database

2. `add_summaries_table.py` - Script to create the summaries table in the database

3. `fastapi_server.py` - Updated with new endpoints for summary retrieval and generation

### Frontend Files

1. `DirectorsDisclosureDataSource.tsx` - Updated to:
   - Display summaries instead of full content
   - Add "Generate Summary" button
   - Show loading states during summary generation

## Setup

1. Ensure required packages are installed:
   ```bash
   pip install python-docx groq
   ```

2. Add the summaries table to the database:
   ```bash
   python add_summaries_table.py
   ```

3. Set up environment variables for Groq:
   ```bash
   export GROQ_API_KEY=your_groq_api_key
   export USE_GROQ=true
   ```

## Usage

1. When a user clicks "View" on a disclosure, they will see a summary instead of the full document
2. Users can click "Generate Summary" to create a new summary using the LLM
3. Previously generated summaries are cached in the database for faster retrieval

## Error Handling

- If LLM generation fails, a placeholder summary is shown
- If DOCX processing fails, an appropriate error message is displayed
- All errors are logged for debugging purposes