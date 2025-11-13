# Simple RAG Agent with Orchestrator

A demonstration of the A2A (Agent-to-Agent) protocol showing how an orchestrator agent can route queries to a specialized RAG (Retrieval Augmented Generation) agent using ChromaDB vector database.

## Architecture

```
User
  |
  v
Test Client (A2A Client)
  |
  | A2A Protocol
  v
Orchestrator Agent (Port 10003)
  |
  | A2A Protocol (routes document queries)
  v
RAG Agent (Port 10002)
  |
  v
ChromaDB Vector Database
```

## Components

### 1. RAG Agent (Port 10002)
- Uses **ChromaDB** vector database for document storage
- Uses **sentence-transformers** for text embeddings
- Pre-loaded with sample documents about:
  - Python programming
  - Machine Learning
  - Vector Databases
  - A2A Protocol
  - ChromaDB
- Provides semantic search over documents
- Exposes A2A protocol interface

**Files:**
- `agent.py` - RAG agent logic with ChromaDB integration
- `agent_executor.py` - A2A executor wrapper for the RAG agent
- `__main__.py` - Server startup for RAG agent

### 2. Orchestrator Agent (Port 10003)
- Routes queries to appropriate agents
- Uses simple keyword-based routing (can be enhanced with ML)
- Communicates with RAG agent via **A2A protocol**
- Routes document-related queries to RAG agent
- Handles other queries directly

**Files:**
- `orchestrator_agent.py` - Orchestrator logic with A2A client
- `orchestrator_executor.py` - A2A executor wrapper
- `orchestrator_main.py` - Server startup for orchestrator

### 3. Test Client
- Command-line interface to interact with the orchestrator
- Shows streaming responses in real-time
- Includes debug output to trace A2A calls

**Files:**
- `test_client.py` - Interactive CLI client

## Setup

### Prerequisites
- Python 3.10 or higher
- `uv` package manager (or use `pip`)

### Installation

1. Navigate to the project directory:
```bash
cd samples/python/agents/simple_rag_agent
```

2. Install dependencies using `uv`:
```bash
uv sync
```

Or using pip:
```bash
pip install -r requirements.txt
```

The main dependencies are:
- `a2a-sdk[http-server]` - A2A protocol implementation
- `chromadb` - Vector database
- `sentence-transformers` - Text embeddings
- `httpx` - HTTP client for A2A communication
- `uvicorn` - ASGI server

## Running the Demo

You need to run **two servers** (RAG Agent and Orchestrator) and then the client.

### Terminal 1: Start the RAG Agent

```bash
uv run .
```

You should see:
```
[DEBUG] Starting Simple RAG Agent server...
[DEBUG] Initializing SimpleRAGAgent with persist_directory: ./chroma_db
[DEBUG] Loading sentence transformer model...
[DEBUG] Getting or creating Chroma collection 'documents'
[DEBUG] Initializing with sample documents...
============================================================
Simple RAG Agent is running!
Access the agent at: http://localhost:10002
============================================================
```

### Terminal 2: Start the Orchestrator Agent

```bash
uv run orchestrator_main.py
```

You should see:
```
[DEBUG] Starting Orchestrator Agent server...
============================================================
Orchestrator Agent is running!
Access the agent at: http://localhost:10003
Note: Make sure RAG Agent is running on http://localhost:10002
============================================================
```

### Terminal 3: Run the Test Client

```bash
uv run test_client.py
```

You should see:
```
======================================================================
Welcome to the RAG Agent + Orchestrator Demo!
======================================================================

This demo shows A2A protocol in action:
1. You interact with the Orchestrator Agent (port 10003)
2. The Orchestrator routes document queries to RAG Agent (port 10002)
3. Communication happens via A2A protocol
...
```

## Example Queries

### Queries that Route to RAG Agent (via A2A)

These queries will be routed to the RAG agent via A2A protocol:

```
> What is Python?
> Tell me about machine learning
> Explain the A2A protocol
> What is ChromaDB?
> Describe vector databases
```

### Queries Handled Directly by Orchestrator

These queries are handled by the orchestrator directly:

```
> What can you help me with?
> Hello
> Help me with something random
```

## Tracing A2A Calls

The implementation includes extensive debug logging to help you trace A2A calls:

### RAG Agent Logs
```
[DEBUG] RAGAgentExecutor.execute() called
[DEBUG] Context ID: <id>
[DEBUG] Task ID: <id>
[DEBUG] User query: 'What is Python?'
[DEBUG] RAG Agent querying for: 'What is Python?' (n_results=3)
[DEBUG] Found 3 relevant documents
[DEBUG] Streaming chunk: done=False, content_length=...
```

### Orchestrator Logs
```
[DEBUG] OrchestratorAgent processing query: 'What is Python?'
[DEBUG] Determining routing for query: 'What is Python?'
[DEBUG] Should route to RAG: True
[DEBUG] ===== ROUTING TO RAG AGENT VIA A2A =====
[DEBUG] Fetching agent card from http://localhost:10002
[DEBUG] Agent card received: Simple RAG Agent
[DEBUG] Sending streaming request to RAG agent via A2A
[DEBUG] Request ID: <id>
[DEBUG] Receiving streaming response from RAG agent
[DEBUG] Chunk 1: forwarding 54 chars
...
[DEBUG] ===== A2A CALL COMPLETE =====
```

### Client Logs
```
[CLIENT DEBUG] Sending query to Orchestrator Agent...
[CLIENT DEBUG] Receiving streaming response...

--- Response ---
Based on the documents in my knowledge base, here's what I found:
...
[CLIENT DEBUG] Received 8 chunks
--- End Response ---
```

## Key A2A Concepts Demonstrated

### 1. Agent Card
Each agent exposes an agent card describing its capabilities:
```python
agent_card = AgentCard(
    name='Simple RAG Agent',
    description='A simple RAG agent...',
    url='http://localhost:10002/',
    capabilities=AgentCapabilities(streaming=True),
    skills=[skill],
)
```

### 2. A2A Client
The orchestrator uses an A2A client to communicate with the RAG agent:
```python
# Fetch agent card
resolver = A2ACardResolver(httpx_client, base_url)
agent_card = await resolver.get_agent_card()

# Create client
client = A2AClient(httpx_client, agent_card=agent_card)

# Send streaming message
stream = client.send_message_streaming(request)
async for chunk in stream:
    # Process response chunks
```

### 3. A2A Server
Both agents expose A2A server interfaces:
```python
server = A2AStarletteApplication(
    agent_card=agent_card,
    http_handler=request_handler
)
uvicorn.run(server.build(), host='0.0.0.0', port=10002)
```

### 4. Streaming Responses
The demo shows streaming responses flowing through the A2A protocol:
- Client sends query to Orchestrator
- Orchestrator streams request to RAG agent via A2A
- RAG agent streams back results via A2A
- Orchestrator forwards stream to client

## Project Structure

```
simple_rag_agent/
├── README.md                      # This file
├── pyproject.toml                 # Project dependencies
│
├── agent.py                       # RAG agent with ChromaDB
├── agent_executor.py              # A2A executor for RAG agent
├── __main__.py                    # RAG agent server startup
│
├── orchestrator_agent.py          # Orchestrator with A2A client
├── orchestrator_executor.py       # A2A executor for orchestrator
├── orchestrator_main.py           # Orchestrator server startup
│
├── test_client.py                 # Interactive test client
│
└── chroma_db/                     # ChromaDB persistent storage (created at runtime)
```

## How It Works

### 1. Initialization
- RAG agent starts on port 10002, initializes ChromaDB, loads sample documents
- Orchestrator starts on port 10003, configured to connect to RAG agent

### 2. Query Processing
- User sends query to orchestrator via test client
- Orchestrator analyzes query using keyword matching
- If query is document-related:
  - Orchestrator creates A2A client connection to RAG agent
  - Sends query via A2A protocol (JSON-RPC over HTTP)
  - RAG agent queries ChromaDB vector database
  - RAG agent streams results back via A2A
  - Orchestrator forwards stream to user
- If query is not document-related:
  - Orchestrator handles directly without A2A call

### 3. Vector Search (in RAG Agent)
- Query text is converted to embedding using sentence-transformers
- Embedding is compared against stored document embeddings
- Top K most similar documents are retrieved
- Results are formatted and streamed back

## Customization

### Add Your Own Documents

Edit `agent.py` and modify the `initialize_with_sample_docs()` method:

```python
sample_docs = [
    {
        'text': 'Your document text here...',
        'metadata': {'topic': 'Your Topic', 'category': 'Category'}
    },
    # Add more documents...
]
```

### Change Routing Logic

Edit `orchestrator_agent.py` and modify the `should_route_to_rag()` method:

```python
def should_route_to_rag(self, query: str) -> bool:
    # Implement your own routing logic
    # Could use ML classifier, LLM, or other heuristics
    pass
```

### Adjust Ports

- RAG Agent: Change port in `__main__.py` (default 10002)
- Orchestrator: Change port in `orchestrator_main.py` (default 10003)
- Update URLs in both orchestrator and client accordingly

## Troubleshooting

### "Could not connect to RAG agent"
- Ensure RAG agent is running on port 10002
- Check if port is already in use: `lsof -i :10002`

### "Could not connect to orchestrator"
- Ensure orchestrator is running on port 10003
- Check if port is already in use: `lsof -i :10003`

### ChromaDB Issues
- Delete `chroma_db/` directory and restart to reset database
- Ensure sufficient disk space for ChromaDB

### Dependency Issues
- Ensure Python 3.10+ is installed
- Try: `uv sync --reinstall` to reinstall dependencies

## Learning Points

This demo illustrates:
1. **A2A Protocol**: Agent-to-agent communication using standardized protocol
2. **RAG Architecture**: Retrieval Augmented Generation with vector databases
3. **Orchestration Pattern**: Routing queries to specialized agents
4. **Streaming**: Real-time streaming responses through multiple agents
5. **Debug Tracing**: Understanding the flow of A2A calls

## Next Steps

- Add more agents (e.g., calculator, weather, web search)
- Implement smarter routing using LLMs
- Add authentication/security
- Deploy agents to different machines
- Add monitoring and observability
- Implement more sophisticated RAG (reranking, hybrid search, etc.)

## License

This project is licensed under the terms of the Apache 2.0 License.

## Disclaimer

**Important**: The sample code provided is for demonstration purposes and illustrates the mechanics of the Agent-to-Agent (A2A) protocol. When building production applications, it is critical to treat any agent operating outside of your direct control as a potentially untrusted entity.

All data received from an external agent—including but not limited to its AgentCard, messages, artifacts, and task statuses—should be handled as untrusted input. Developers are responsible for implementing appropriate security measures, such as input validation and secure handling of credentials to protect their systems and users.

