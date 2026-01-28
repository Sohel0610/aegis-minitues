@echo off
REM Script to start the development environment

echo Starting AI Agents Marketplace development environment...

REM Check if dist directory exists
if exist ..\Frontend\dist (
    echo Found built React app, starting simple HTTP server...
    python serve.py
) else (
    echo No built React app found, starting development servers...
    echo Make sure you have Python and Node.js installed!
    
    REM Start backend and frontend in separate processes
    start "Backend" /D aegis_backend python fastapi_server.py
    start "Frontend" /D ..\Frontend npm run dev
    
    echo.
    echo Servers started:
    echo Backend: http://localhost
    echo Frontend: http://localhost:5173
    echo.
    echo Press any key to stop servers...
    pause >nul
    
    REM Kill the processes (this is a simplified approach)
    taskkill /f /im python.exe 2>nul
    taskkill /f /im node.exe 2>nul
)

echo Development environment stopped.