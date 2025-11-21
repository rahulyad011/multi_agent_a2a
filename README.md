# Multi-Agent A2A System

A plug-and-play multi-agent system demonstrating the A2A (Agent-to-Agent) protocol with RAG capabilities, image captioning, ML pipeline classification, and intelligent orchestration.

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- UV package manager (recommended) or pip
- LLM API key (for orchestrator - Google/OpenAI)

### Installation

```bash
# Install dependencies
uv sync
# or
pip install -r requirements.txt
```

### Start All Agents

```bash
# Start all agents (RAG, Image Caption, Iris Classifier, Orchestrator)
bash scripts/start_agents.sh

# In a new terminal, start Streamlit
uv run streamlit run app.py
```

Open browser to `http://localhost:8501` for the web interface!

## 📁 Project Structure

```
multi_agent_a2a/
├── src/
│   ├── agents/              # Agent implementations
│   │   ├── simple_rag/      # RAG Agent (port 10002)
│   │   ├── image_caption/   # Image Caption Agent (port 10004)
│   │   ├── iris_classifier/ # ML Pipeline Agent (port 10005)
│   │   └── orchestrator/   # Orchestrator Agent (port 10003)
│   └── utils/               # Shared utilities
├── config/
│   ├── agents/              # Agent configuration files
│   └── orchestrator.yaml    # Orchestrator configuration
├── scripts/                 # Utility scripts
├── tests/                   # Test scripts
└── app.py                   # Streamlit web interface
```

## 🎯 Agents

### 1. Simple RAG Agent (Port 10002)
- Document storage and retrieval using ChromaDB
- Vector similarity search
- Entry: `uv run src/agents/simple_rag/main.py`

### 2. Image Caption Agent (Port 10004)
- Generate captions for images using BLIP model
- Entry: `uv run src/agents/image_caption/main.py`

### 3. Iris Classifier Agent (Port 10005)
- ML pipeline for iris flower classification
- Random Forest classifier (scikit-learn)
- **Train model first**: `uv run src/agents/iris_classifier/train.py`
- Entry: `uv run src/agents/iris_classifier/main.py`

### 4. Orchestrator Agent (Port 10003)
- LLM-based intelligent routing to specialized agents
- Entry: `uv run src/agents/orchestrator/main_host.py`

## 🧪 Testing

### Test Iris Classifier via Orchestrator

```bash
# Run the test script
uv run python tests/test_iris_classifier.py
```

Or test manually:
```bash
# Start all agents first
bash scripts/start_agents.sh

# Then test via Streamlit or CLI
uv run streamlit run app.py
```

### Test Queries

**Iris Classifier (JSON format):**
```json
{"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}
```

**Iris Classifier (List format):**
```
[5.1, 3.5, 1.4, 0.2]
```

**Iris Classifier (Space-separated):**
```
5.1 3.5 1.4 0.2
```

**RAG Agent:**
- "What is Python?"
- "Tell me about machine learning"

**Image Caption:**
- Upload image and ask: "What is in this image?"

## 🔧 Configuration

All agents use YAML configuration files in `config/agents/`:
- `simple_rag.yaml`
- `image_caption.yaml`
- `iris_classifier.yaml`

Orchestrator configuration: `config/orchestrator.yaml`

## 🛠️ Adding New Agents

1. Create agent directory: `src/agents/your_agent/`
2. Create three files: `agent.py`, `executor.py`, `main.py`
3. Create config: `config/agents/your_agent.yaml`
4. Add to orchestrator config: `config/orchestrator.yaml`

See existing agents for reference.

## 📦 Dependencies

- `a2a-sdk` - Agent-to-Agent protocol
- `chromadb` - Vector database
- `sentence-transformers` - Text embeddings
- `transformers` & `torch` - Image captioning
- `scikit-learn` - ML pipeline
- `litellm` - LLM orchestration
- `streamlit` - Web interface
- `pyyaml` - Configuration management

## 🔑 Environment Variables

For LLM-based orchestrator:
```bash
export GOOGLE_API_KEY="your-key"
# or
export OPENAI_API_KEY="your-key"
```

Or create `.env` file:
```
GOOGLE_API_KEY=your-key-here
```

## 🆘 Troubleshooting

**Port already in use:**
```bash
bash scripts/stop_agents.sh
```

**Check agent status:**
```bash
bash scripts/check_agents.sh
```

**Agent not discovered:**
- Ensure all agents are running before starting orchestrator
- Restart orchestrator to discover new agents

## 📄 License

See repository for license information.
