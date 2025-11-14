#!/bin/bash

# Script to stop all running agents

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=========================================="
echo "  Stopping All Agents"
echo "=========================================="
echo ""

# Function to kill process on port
kill_port() {
    local port=$1
    local name=$2
    local pid=$(lsof -ti:$port 2>/dev/null)
    
    if [ ! -z "$pid" ]; then
        echo -e "${YELLOW}Stopping $name on port $port (PID: $pid)${NC}"
        kill -9 $pid 2>/dev/null
        sleep 0.5
        echo -e "${GREEN}✓ $name stopped${NC}"
    else
        echo -e "  $name (port $port) - not running"
    fi
}

# Kill agents on their respective ports
kill_port 10002 "RAG Agent"
kill_port 10004 "Image Caption Agent"
kill_port 10003 "Orchestrator"
kill_port 8501 "Streamlit"

# Clean up PID files if they exist
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_DIR="$PROJECT_ROOT/.pids"

if [ -d "$PID_DIR" ]; then
    echo ""
    echo -e "${YELLOW}Cleaning up PID files...${NC}"
    rm -f "$PID_DIR"/*.pid
    echo -e "${GREEN}✓ PID files cleaned${NC}"
fi

echo ""
echo -e "${GREEN}All agents stopped successfully!${NC}"
echo ""

