@echo off
echo Starting PowerApp services with Nginx reverse proxy...

echo Starting backend server...
start "Backend Server" /min cmd /c "cd aegis_backend && python fastapi_server.py"

timeout /t 5 /nobreak >nul

echo Starting frontend development server...
start "Frontend Server" /min cmd /c "cd ..\Frontend && npm run dev"

timeout /t 10 /nobreak >nul

echo Starting Nginx...
start "Nginx" /min cmd /c "nginx -c %~dp0nginx\nginx-windows-ssl.conf"

echo.
echo Services started:
echo - Frontend development server: http://localhost:8080
echo - Backend API server: http://localhost
echo - Nginx reverse proxy: https://localhost
echo.
echo Press any key to stop all services...
pause >nul

echo Stopping services...
taskkill /f /im nginx.exe
taskkill /f /im python.exe
taskkill /f /im node.exe

echo Services stopped.