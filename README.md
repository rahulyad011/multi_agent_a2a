# Simple RAG Agent - Multi-Agent System

A multi-agent system demonstrating the A2A (Agent-to-Agent) protocol with RAG capabilities, image captioning, and intelligent orchestration.

## 🚀 Quick Start

### Option 1: Quick Start (Recommended)
```bash
# Terminal 1 - Start all agents (RAG, Image Caption, Orchestrator)
bash scripts/start_agents.sh

# Terminal 2 - Start Streamlit web interface
uv run streamlit run app.py
```

The script will:
- ✅ Start RAG Agent (port 10002) in background
- ✅ Start Image Caption Agent (port 10004) in background
- ✅ Test each agent to ensure they're working
- ✅ Start Orchestrator (port 10003) with visible logs
- ✅ Provide clear status updates

Open your browser to `http://localhost:8501` for the web interface!

### Option 2: Manual Setup

1. **Install Dependencies:**
```bash
uv sync
```

2. **Start the Agents** (in separate terminals):

```bash
# Terminal 1 - RAG Agent
uv run src/agents/simple_rag/main.py

# Terminal 2 - Image Caption Agent
uv run src/agents/image_caption/main.py

# Terminal 3 - Orchestrator (keyword-based)
uv run src/agents/orchestrator/main.py

# Terminal 4 - Test Client or Streamlit
uv run tests/test_client.py
# or
uv run streamlit run app.py
```

## 📁 Project Structure

```
simple_rag_agent/
├── src/                          # Source code
│   ├── agents/                   # All agent implementations
│   │   ├── simple_rag/          # Simple RAG Agent
│   │   │   ├── agent.py         # RAG Agent implementation
│   │   │   ├── executor.py      # RAG Agent executor
│   │   │   └── main.py          # RAG Agent server entry point
│   │   ├── orchestrator/        # Orchestrator Agent
│   │   │   ├── agent.py         # Keyword-based orchestrator
│   │   │   ├── agent_host.py    # LLM-based host orchestrator
│   │   │   ├── executor.py      # Keyword-based executor
│   │   │   ├── executor_host.py # LLM-based executor
│   │   │   ├── main.py          # Keyword-based server
│   │   │   └── main_host.py     # LLM-based server
│   │   └── image_caption/       # Image Captioning Agent
│   │       ├── agent.py         # Image caption agent
│   │       ├── executor.py      # Image caption executor
│   │       └── main.py          # Image caption server
│   └── utils/                   # Shared utilities
│       └── remote_connection.py # Remote agent connection helper
├── tests/                       # Test files
│   └── test_client.py          # Interactive test client
├── scripts/                     # Shell scripts and utilities
│   ├── start_agents.sh         # Start all agents (recommended)
│   ├── stop_agents.sh          # Stop all agents
│   ├── run_streamlit.sh        # Launch Streamlit
│   └── run_demo.sh             # Legacy script
├── docs/                        # (Empty - reserved for future docs)
├── chroma_db/                   # Persistent ChromaDB data
├── __main__.py                  # Default entry point (runs RAG agent)
├── pyproject.toml              # Project configuration
└── uv.lock                     # Dependency lock file
```

## 🎯 Components

### 1. Simple RAG Agent (Port 10002)
- **Purpose**: Document storage and retrieval using ChromaDB
- **Features**: Vector similarity search, pre-loaded sample documents
- **Entry Point**: `uv run src/agents/simple_rag/main.py`

### 2. Orchestrator Agent (Port 10003)
Two implementations available:

**Keyword-based** (`agent.py`, `main.py`):
- Simple heuristic routing based on keywords
- No API keys required
- Entry: `uv run src/agents/orchestrator/main.py`

**LLM-based** (`agent_host.py`, `main_host.py`):
- Intelligent routing using LiteLLM
- Requires API key (Google/OpenAI)
- Entry: `uv run src/agents/orchestrator/main_host.py`

Routes queries to appropriate specialized agents via A2A protocol.

### 3. Image Caption Agent (Port 10004)
- **Purpose**: Generate descriptive captions for images
- **Model**: BLIP (Salesforce/blip-image-captioning-base)
- **Entry Point**: `uv run src/agents/image_caption/main.py`

### 4. Test Interfaces

**CLI Test Client:**
- **Purpose**: Interactive command-line client to test the orchestrator
- **Entry Point**: `uv run tests/test_client.py`
- **Features**: Text-based interaction, streaming console output

**Streamlit Web App:**
- **Purpose**: Beautiful web interface for testing and demos
- **Entry Point**: `uv run streamlit run app.py` or `bash scripts/run_streamlit.sh`
- **URL**: http://localhost:8501
- **Features**: 
  - Modern chat interface with message history
  - One-click example queries for RAG and image captioning
  - Visual connection status and agent information
  - Optional debug mode for troubleshooting
  - Architecture overview display
  - Real-time streaming responses

## 🛠️ Running Individual Components

```bash
# RAG Agent only
uv run src/agents/simple_rag/main.py

# Image Caption Agent only
uv run src/agents/image_caption/main.py

# Orchestrator (keyword-based)
uv run src/agents/orchestrator/main.py

# Orchestrator (LLM-based, requires API key)
uv run src/agents/orchestrator/main_host.py

# Test Client (CLI)
uv run tests/test_client.py

# Streamlit Web App
uv run streamlit run app.py

# Default entry point (runs RAG Agent)
uv run .
```

## 🧪 Example Usage

### Using the Streamlit Web App (Recommended)

1. **Start all agents**: `bash scripts/start_agents.sh`
   - This starts RAG Agent, Image Caption Agent, and Orchestrator
   - Health checks ensure all agents are working
   - Orchestrator logs will be visible in this terminal
2. **Launch Streamlit** (in a new terminal): `uv run streamlit run app.py`
3. **Open browser**: Navigate to http://localhost:8501
4. **Connect**: Click "🔌 Connect" button
5. **Try example queries**: Click any example in the sidebar or type your own

The Streamlit app provides:
- Visual chat interface with full history
- Pre-loaded example queries you can click
- Connection status monitoring
- Debug mode for troubleshooting

### Using the CLI Test Client

Once all agents are running, try these queries in the test client:

**Document Search:**
```
> What is Python?
> Tell me about machine learning
> Explain vector databases
> What is the A2A protocol?
```

**Image Captioning:**
```
> caption: /path/to/your/image.jpg
> /Users/username/Pictures/photo.png
> describe: ~/Downloads/sunset.jpg
```

## 💻 Import Structure

All imports use absolute paths from `src`:

```python
# Agent imports
from src.agents.simple_rag.agent import SimpleRAGAgent
from src.agents.orchestrator.agent import OrchestratorAgent
from src.agents.image_caption.agent import ImageCaptioningAgent

# Executor imports
from src.agents.simple_rag.executor import SimpleRAGAgentExecutor
from src.agents.orchestrator.executor import OrchestratorAgentExecutor
from src.agents.image_caption.executor import ImageCaptioningAgentExecutor

# Utility imports
from src.utils.remote_connection import RemoteAgentConnection
```

## 📦 Requirements

- Python 3.10+
- uv (package manager)
- Dependencies listed in `pyproject.toml`

### Key Dependencies:
- `chromadb` - Vector database
- `sentence-transformers` - Text embeddings
- `transformers` & `torch` - Image captioning
- `a2a` - Agent-to-Agent protocol
- `litellm` - LLM orchestration (optional)
- `streamlit` - Web interface for testing

## 🔑 API Keys (for LLM-based Orchestrator)

Set environment variables for LLM access:
```bash
export GOOGLE_API_KEY="your-key"
# OR
export OPENAI_API_KEY="your-key"
```

Or create a `.env` file in the project root:
```bash
GOOGLE_API_KEY=your-key-here
```


## 🏗️ Architecture Benefits

1. **Clear Separation of Concerns** - Each agent has its own directory
2. **Modular Design** - Easy to add new agents or utilities
3. **Better Organization** - Documentation, tests, and scripts are separated
4. **Scalability** - Easy to navigate and maintain as the project grows
5. **Standard Python Layout** - Follows Python best practices
6. **Clean Imports** - Explicit import paths are more maintainable

## 🔄 Migration Notes

This project has been restructured for better organization. Key changes:

**Old Structure → New Structure:**
- Root-level agent files → `src/agents/{agent_name}/`
- Documentation files → `docs/`
- Test files → `tests/`
- Scripts → `scripts/`

All imports updated from relative to absolute paths using `src` as the base package.

## 📄 License

See the main repository for license information.

## 🤝 Contributing

This is a sample project demonstrating the A2A protocol. Feel free to extend and modify for your use case.

## 🛠️ Utility Scripts

The project includes helpful scripts in the `scripts/` directory:

- **`start_agents.sh`** - Start all agents with health checks (recommended)
- **`stop_agents.sh`** - Stop all running agents
- **`run_streamlit.sh`** - Launch Streamlit with agent status checks
- **`run_demo.sh`** - Legacy script (redirects to start_agents.sh)

## 🆘 Troubleshooting

### General Issues

**Port already in use:**
```bash
# Easy way - use the stop script
bash scripts/stop_agents.sh

# Manual way - check and kill processes
lsof -i :10002  # RAG Agent
lsof -i :10003  # Orchestrator
lsof -i :10004  # Image Caption Agent
lsof -i :8501   # Streamlit

# Kill specific process
kill -9 <PID>
```

**Import errors:**
Make sure you're running from the project root directory.

**ChromaDB persistence issues:**
Delete the `chroma_db/` directory to reset the vector database.

### Streamlit App Issues

**Connection failed:**
1. Verify orchestrator is running on port 10003
2. Check the URL is correct (default: http://localhost:10003)
3. Ensure no firewall is blocking the connection

**Streamlit port 8501 busy:**
```bash
streamlit run app.py --server.port 8502
```

**Agents not responding:**
1. Verify all agents are running (check ports 10002, 10003, 10004)
2. Enable debug mode in Streamlit sidebar for more details
3. Try clicking "🔄 Reset" and reconnecting

**Event loop errors:**
If you see event loop related errors, restart the Streamlit app:
```bash
# Press Ctrl+C to stop, then restart
uv run streamlit run app.py
```

**Slow first image caption:**
This is normal - the BLIP model needs to load into memory on first use. Subsequent requests will be faster.

---

**Note:** This project demonstrates the A2A (Agent-to-Agent) protocol with multiple specialized agents communicating through a central orchestrator. Each agent can be run independently or as part of the multi-agent system.
