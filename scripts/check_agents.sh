#!/bin/bash

# Script to check if all agents are running and accessible

echo "=========================================="
echo "  Agent Status Check"
echo "=========================================="
echo ""

check_agent() {
    local port=$1
    local name=$2
    local url=$3
    
    echo -n "Checking $name (port $port)... "
    
    # Check if port is listening
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -n "✓ Running "
        
        # Check if agent card is accessible
        if curl -s -f "$url/.well-known/agent.json" > /dev/null 2>&1; then
            echo "✓ Accessible"
            return 0
        else
            echo "✗ Not accessible (port open but agent card not responding)"
            return 1
        fi
    else
        echo "✗ Not running"
        return 1
    fi
}

all_ok=true

check_agent 10002 "RAG Agent" "http://localhost:10002" || all_ok=false
check_agent 10004 "Image Caption Agent" "http://localhost:10004" || all_ok=false
check_agent 10005 "Iris Classifier Agent" "http://localhost:10005" || all_ok=false
check_agent 10003 "Orchestrator" "http://localhost:10003" || all_ok=false

echo ""
echo "=========================================="

if [ "$all_ok" = true ]; then
    echo "✓ All agents are running and accessible!"
    echo ""
    echo "If orchestrator is not discovering agents, try:"
    echo "  1. Restart the orchestrator"
    echo "  2. Check orchestrator logs for discovery errors"
else
    echo "✗ Some agents are not running or not accessible"
    echo ""
    echo "Please start missing agents:"
    echo "  bash scripts/start_agents.sh"
fi

echo "=========================================="

