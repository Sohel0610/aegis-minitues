# Modular FastAPI Server Structure

This directory contains the modular FastAPI server implementation for the Aegis application.

## File Structure

- `fastapi_server_modular.py` - Main FastAPI server file that imports and registers all modular routes
- `routes/` - Directory containing all modular route files:
  - `health.py` - Health check endpoints
  - `excel.py` - Excel data handling endpoints
  - `sebi.py` - SEBI data handling endpoints
  - `bse.py` - BSE data handling endpoints
  - `rbi.py` - RBI data handling endpoints
  - `analytics.py` - Analytics endpoints
  - `admin.py` - Admin authentication and email management endpoints
  - `directors.py` - Directors disclosure endpoints
  - `minutes.py` - Minutes generation endpoints
  - `ai_assistant.py` - AI Assistant endpoints
  - `__init__.py` - Makes the routes directory a Python package

## How It Works

The modular structure separates different functionality into individual route files. Each route file:

1. Creates its own FastAPI router
2. Defines its Pydantic models
3. Implements its endpoints
4. Exports the router for use in the main server file

The main server file (`fastapi_server_modular.py`) imports all route modules and registers their routers with the main FastAPI application.

## Benefits

1. **Maintainability** - Each functionality is isolated in its own file
2. **Scalability** - Easy to add new features without cluttering a single file
3. **Readability** - Clear separation of concerns
4. **Collaboration** - Multiple developers can work on different route files simultaneously
5. **Testing** - Individual route files can be tested in isolation

## Running the Server

To run the modular server:

```bash
cd backend
python fastapi_server_modular.py
```

The server will start on port 8000 by default.