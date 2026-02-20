#!/bin/bash

# Backend Startup Script for Production Minutes Chatbot
# This script starts the FastAPI backend server

echo "============================================"
echo "🚀 Starting Minutes Chatbot Backend"
echo "============================================"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found!"
    echo "   Please create .env file from .env.example"
    echo "   cp .env.example .env"
    echo "   Then edit .env with your credentials"
    exit 1
fi

# Activate virtual environment
if [ ! -d "venv" ]; then
    echo "❌ Error: Virtual environment not found!"
    echo "   Please create it first:"
    echo "   python3 -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p uploads
mkdir -p logs

# Start backend
echo "🚀 Starting backend on port 8000..."
echo "   URL: http://localhost:8000"
echo "   Docs: http://localhost:8000/docs"
echo "   Press CTRL+C to stop"
echo "============================================"

uvicorn main:app --host 0.0.0.0 --port 8000 --reload
