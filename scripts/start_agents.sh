#!/bin/bash

# Script to start all agents with health checks and keep orchestrator logs visible
# The Streamlit app can be started separately in another terminal

set -e  # Exit on error

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log files
LOG_DIR="$PROJECT_ROOT/logs"
mkdir -p "$LOG_DIR"
RAG_LOG="$LOG_DIR/rag_agent.log"
IMAGE_LOG="$LOG_DIR/image_caption_agent.log"
ORCH_LOG="$LOG_DIR/orchestrator.log"

# PID files
PID_DIR="$PROJECT_ROOT/.pids"
mkdir -p "$PID_DIR"
RAG_PID="$PID_DIR/rag_agent.pid"
IMAGE_PID="$PID_DIR/image_caption_agent.pid"

echo "=========================================="
echo "  Multi-Agent A2A System - Agent Starter"
echo "=========================================="
echo ""

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to kill process on port
kill_port() {
    local port=$1
    local pid=$(lsof -ti:$port)
    if [ ! -z "$pid" ]; then
        echo -e "${YELLOW}Killing existing process on port $port (PID: $pid)${NC}"
        kill -9 $pid 2>/dev/null || true
        sleep 1
    fi
}

# Function to wait for agent to be ready
wait_for_agent() {
    local name=$1
    local port=$2
    local max_wait=30
    local count=0
    
    echo -e "${BLUE}Waiting for $name to be ready on port $port...${NC}"
    
    while [ $count -lt $max_wait ]; do
        if check_port $port; then
            echo -e "${GREEN}✓ $name is ready!${NC}"
            return 0
        fi
        sleep 1
        count=$((count + 1))
        echo -n "."
    done
    
    echo ""
    echo -e "${RED}✗ $name failed to start within ${max_wait}s${NC}"
    return 1
}

# Function to test agent with HTTP request
test_agent() {
    local name=$1
    local port=$2
    local max_attempts=3
    local attempt=1
    
    echo -e "${BLUE}Testing $name...${NC}"
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "http://localhost:$port/.well-known/agent.json" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ $name responded successfully!${NC}"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 1
    done
    
    echo -e "${RED}✗ $name is not responding to requests${NC}"
    return 1
}

# Cleanup function for graceful shutdown
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down agents...${NC}"
    
    # Kill background agents
    if [ -f "$RAG_PID" ]; then
        kill $(cat "$RAG_PID") 2>/dev/null || true
        rm -f "$RAG_PID"
    fi
    
    if [ -f "$IMAGE_PID" ]; then
        kill $(cat "$IMAGE_PID") 2>/dev/null || true
        rm -f "$IMAGE_PID"
    fi
    
    # Kill any remaining processes on our ports
    kill_port 10002
    kill_port 10004
    kill_port 10003
    
    echo -e "${GREEN}All agents stopped.${NC}"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Check for existing processes and clean up
echo -e "${BLUE}Checking for existing agents...${NC}"
if check_port 10002; then
    kill_port 10002
fi
if check_port 10004; then
    kill_port 10004
fi
if check_port 10003; then
    kill_port 10003
fi

echo ""
echo "=========================================="
echo "  Starting Agents"
echo "=========================================="
echo ""

# Start RAG Agent in background
echo -e "${BLUE}1. Starting RAG Agent (port 10002)...${NC}"
nohup uv run src/agents/simple_rag/main.py > "$RAG_LOG" 2>&1 &
echo $! > "$RAG_PID"
echo -e "   Log: $RAG_LOG"
echo -e "   PID: $(cat $RAG_PID)"

# Wait for RAG agent to be ready
if ! wait_for_agent "RAG Agent" 10002; then
    echo -e "${RED}Failed to start RAG Agent. Check log: $RAG_LOG${NC}"
    cleanup
fi

# Test RAG agent
if ! test_agent "RAG Agent" 10002; then
    echo -e "${RED}RAG Agent health check failed. Check log: $RAG_LOG${NC}"
    cleanup
fi

echo ""

# Start Image Caption Agent in background
echo -e "${BLUE}2. Starting Image Caption Agent (port 10004)...${NC}"
nohup uv run src/agents/image_caption/main.py > "$IMAGE_LOG" 2>&1 &
echo $! > "$IMAGE_PID"
echo -e "   Log: $IMAGE_LOG"
echo -e "   PID: $(cat $IMAGE_PID)"

# Wait for Image Caption agent to be ready
if ! wait_for_agent "Image Caption Agent" 10004; then
    echo -e "${RED}Failed to start Image Caption Agent. Check log: $IMAGE_LOG${NC}"
    cleanup
fi

# Test Image Caption agent
if ! test_agent "Image Caption Agent" 10004; then
    echo -e "${RED}Image Caption Agent health check failed. Check log: $IMAGE_LOG${NC}"
    cleanup
fi

echo ""

# Give agents a moment to fully initialize
echo -e "${BLUE}Allowing agents to fully initialize...${NC}"
sleep 2

echo ""
echo "=========================================="
echo "  ✓ All Agents Started Successfully!"
echo "=========================================="
echo ""
echo -e "${GREEN}Running agents:${NC}"
echo "  • RAG Agent:           http://localhost:10002"
echo "  • Image Caption Agent: http://localhost:10004"
echo ""
echo -e "${BLUE}Logs:${NC}"
echo "  • RAG Agent:           $RAG_LOG"
echo "  • Image Caption Agent: $IMAGE_LOG"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "  1. Start Orchestrator (will show logs below)"
echo "  2. In another terminal, start Streamlit:"
echo -e "     ${BLUE}uv run streamlit run app.py${NC}"
echo ""
echo "=========================================="
echo ""
echo -e "${GREEN}Press Enter to start Orchestrator and view logs...${NC}"
read -p ""

echo ""
echo "=========================================="
echo "  Starting Orchestrator (port 10003)"
echo "=========================================="
echo ""
echo -e "${BLUE}Orchestrator logs will appear below.${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop all agents.${NC}"
echo ""
echo "=========================================="
echo ""

# Start Orchestrator in foreground (logs will be visible)
# When this exits or is interrupted, cleanup will be called
uv run src/agents/orchestrator/main_host.py

# If orchestrator exits normally, clean up
cleanup

