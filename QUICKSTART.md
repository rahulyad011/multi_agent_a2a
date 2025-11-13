# Quick Start Guide

Get the Multi-Agent Orchestrator demo running in 3 steps!

## Prerequisites

- Python 3.10+
- `uv` package manager installed (or use `pip`)

## Step 1: Install Dependencies

```bash
cd samples/python/agents/simple_rag_agent
uv sync
```

## Step 2: Start the Servers

Open **4 terminal windows** in the `simple_rag_agent` directory:

### Terminal 1: RAG Agent
```bash
uv run .
```
Wait for: `Simple RAG Agent is running!`

### Terminal 2: Image Caption Agent
```bash
uv run image_caption_main.py
```
Wait for: `Image Captioning Agent is running!`
(First run downloads ~1GB BLIP model)

### Terminal 3: Orchestrator Agent
```bash
uv run orchestrator_main.py
```
Wait for: `Orchestrator Agent is running!`

### Terminal 4: Test Client
```bash
uv run test_client.py
```

## Step 3: Try it Out!

In the test client, try these queries:

### Document Search
```
> What is Python?
```

Watch the debug output to see:
1. Client sends query to Orchestrator (port 10003)
2. Orchestrator detects document query
3. **Orchestrator makes A2A call to RAG Agent (port 10002)**
4. RAG Agent searches ChromaDB
5. Results stream back through A2A protocol
6. Client displays the response

### Image Captioning
```
> caption: /absolute/path/to/your/image.jpg
```

Watch the debug output to see:
1. Client sends query to Orchestrator
2. Orchestrator detects image query
3. **Orchestrator makes A2A call to Image Caption Agent (port 10004)**
4. Image Caption Agent processes image with BLIP model
5. Caption streams back through A2A protocol
6. Client displays the caption

Try more queries:
```
> Tell me about machine learning
> Explain the A2A protocol
> caption: ~/Pictures/photo.png
> What can you do?
```

## What's Happening?

```
[You] 
  ↓ (HTTP + A2A)
[Orchestrator Agent on :10003]
  |
  |--- A2A Protocol --> [RAG Agent on :10002] --> ChromaDB
  |
  |--- A2A Protocol --> [Image Caption Agent on :10004] --> BLIP Model
```

## Debug Output

Look for these key debug messages:

**Orchestrator routing decision:**
```
[DEBUG] Should route to RAG: True
[DEBUG] ===== ROUTING TO RAG AGENT VIA A2A =====
```

**A2A communication:**
```
[DEBUG] Fetching agent card from http://localhost:10002
[DEBUG] Sending streaming request to RAG agent via A2A
[DEBUG] Receiving streaming response from RAG agent
```

**RAG Agent processing:**
```
[DEBUG] RAG Agent querying for: 'What is Python?'
[DEBUG] Found 3 relevant documents
```

**Image Caption Agent processing:**
```
[DEBUG] Image Caption Agent processing query: 'caption: /path/to/image.jpg'
[DEBUG] Extracted image path: '/path/to/image.jpg'
[DEBUG] Generated caption: 'a dog sitting on a couch'
```

## Troubleshooting

**Connection refused?**
- Make sure all agents are running
- RAG Agent (Terminal 1): "Simple RAG Agent is running!"
- Image Caption Agent (Terminal 2): "Image Captioning Agent is running!"
- Orchestrator (Terminal 3): "Orchestrator Agent is running!"

**Port already in use?**
- RAG Agent uses port 10002
- Orchestrator uses port 10003
- Image Caption Agent uses port 10004
- Stop other processes using these ports

**Image file not found?**
- Use absolute paths (e.g., `/Users/username/Pictures/image.jpg`)
- Check file exists: `ls /path/to/image.jpg`
- Verify file permissions

**Need to reset database?**
```bash
rm -rf chroma_db/
# Then restart the RAG agent
```

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Try modifying the sample documents in `agent.py`
- Experiment with different routing logic in `orchestrator_agent.py`
- Add more agents and expand the orchestration!

## Alternative: Use the Helper Script

```bash
./run_demo.sh
# Then choose option 1, 2, or 3
```

Have fun exploring A2A! 🚀

