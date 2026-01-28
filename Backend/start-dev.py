#!/usr/bin/env python3
"""
Script to start both backend and frontend servers for development
"""

import subprocess
import sys
import os
import signal
import time

# Global variables to track processes
processes = []

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\nShutting down servers...")
    for proc in processes:
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
    sys.exit(0)

def start_backend():
    """Start the FastAPI backend"""
    print("Starting FastAPI backend...")
    backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'aegis_backend')
    proc = subprocess.Popen([
        sys.executable, '-m', 'uvicorn', 
        'fastapi_server:app', 
        '--host', 'localhost', 
        '--port', '8000'
    ], cwd=backend_dir)
    processes.append(proc)
    return proc

def start_frontend():
    """Start the React development server"""
    print("Starting React frontend...")
    proc = subprocess.Popen([
        'npm', 'run', 'dev'
    ], cwd=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Frontend'))
    processes.append(proc)
    return proc

def start_simple_server():
    """Start a simple HTTP server to serve the built React app"""
    print("Starting simple HTTP server for built React app...")
    proc = subprocess.Popen([
        sys.executable, 'serve.py'
    ])
    processes.append(proc)
    return proc

def main():
    """Main function to start all servers"""
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Start backend
        backend_proc = start_backend()
        time.sleep(2)  # Give backend time to start
        
        # Check if dist directory exists
        dist_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Frontend', 'dist')
        if os.path.exists(dist_dir):
            # Start simple HTTP server for built app
            frontend_proc = start_simple_server()
        else:
            # Start React development server
            frontend_proc = start_frontend()
        
        print("\nServers started successfully!")
        print("Backend: http://localhost")
        if os.path.exists(dist_dir):
            print("Frontend (built): http://localhost:8001")
        else:
            print("Frontend (dev): http://localhost:5173")
        print("\nPress Ctrl+C to stop all servers")
        
        # Wait for processes to complete
        try:
            backend_proc.wait()
            frontend_proc.wait()
        except KeyboardInterrupt:
            pass
            
    except Exception as e:
        print(f"Error starting servers: {e}")
        signal_handler(None, None)

if __name__ == "__main__":
    main()