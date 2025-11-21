#!/bin/bash

# Launch script for Streamlit App
# This script starts the Streamlit web interface for testing the Multi-Agent A2A system

echo "=========================================="
echo "  Multi-Agent A2A - Streamlit Interface"
echo "=========================================="
echo ""

# Check if in correct directory
if [ ! -f "app.py" ]; then
    echo "Error: app.py not found!"
    echo "Please run this script from the project root directory."
    exit 1
fi

# Check if agents are running
check_agent() {
    local port=$1
    local name=$2
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "  ✓ $name (port $port) - running"
        return 0
    else
        echo "  ✗ $name (port $port) - NOT running"
        return 1
    fi
}

echo "📝 Checking if agents are running..."
echo ""

all_running=true
check_agent 10002 "RAG Agent" || all_running=false
check_agent 10004 "Image Caption Agent" || all_running=false
check_agent 10005 "Iris Classifier Agent" || all_running=false
check_agent 10003 "Orchestrator" || all_running=false

echo ""

if [ "$all_running" = false ]; then
    echo "⚠️  Some agents are not running!"
    echo ""
    echo "Please start the agents first:"
    echo "  bash scripts/start_agents.sh"
    echo ""
    read -p "Do you want to continue anyway? (y/n): " response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "Exiting. Please start the agents first."
        exit 1
    fi
    echo ""
fi

echo "=========================================="
echo ""

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "⚠️  Streamlit not found. Installing dependencies..."
    uv sync
    echo ""
fi

echo "🚀 Starting Streamlit app..."
echo ""
echo "The app will open in your browser at: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the app"
echo ""
echo "=========================================="
echo ""

# Launch Streamlit
uv run streamlit run app.py

