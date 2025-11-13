#!/bin/bash
# Quick start script for the Multi-Agent Orchestrator demo

echo "========================================"
echo "Multi-Agent Orchestrator Demo"
echo "========================================"
echo ""
echo "This script will help you run the demo."
echo ""
echo "You need to run THREE servers + client in separate terminals:"
echo ""
echo "Terminal 1 - RAG Agent:"
echo "  cd samples/python/agents/simple_rag_agent"
echo "  uv run ."
echo ""
echo "Terminal 2 - Image Caption Agent:"
echo "  cd samples/python/agents/simple_rag_agent"
echo "  uv run image_caption_main.py"
echo ""
echo "Terminal 3 - Orchestrator:"
echo "  cd samples/python/agents/simple_rag_agent"
echo "  uv run orchestrator_main.py"
echo ""
echo "Terminal 4 - Test Client:"
echo "  cd samples/python/agents/simple_rag_agent"
echo "  uv run test_client.py"
echo ""
echo "========================================"
echo ""
echo "Choose an option:"
echo "  1) Start RAG Agent (port 10002)"
echo "  2) Start Image Caption Agent (port 10004)"
echo "  3) Start Orchestrator (port 10003)"
echo "  4) Start Test Client"
echo "  5) Show help"
echo ""
read -p "Enter option (1-5): " option

case $option in
  1)
    echo ""
    echo "Starting RAG Agent on port 10002..."
    echo ""
    uv run .
    ;;
  2)
    echo ""
    echo "Starting Image Caption Agent on port 10004..."
    echo ""
    uv run image_caption_main.py
    ;;
  3)
    echo ""
    echo "Starting Orchestrator on port 10003..."
    echo "Make sure RAG Agent (10002) and Image Caption Agent (10004) are running!"
    echo ""
    uv run orchestrator_main.py
    ;;
  4)
    echo ""
    echo "Starting Test Client..."
    echo "Make sure all three agents are running!"
    echo ""
    uv run test_client.py
    ;;
  5)
    echo ""
    cat README.md
    ;;
  *)
    echo "Invalid option"
    exit 1
    ;;
esac

