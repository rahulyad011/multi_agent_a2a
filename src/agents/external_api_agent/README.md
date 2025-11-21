# External API Agent - Sample Implementation

This is a **complete sample implementation** demonstrating how to integrate an external REST API endpoint with the orchestrator using the A2A protocol.

## Purpose

This agent serves as a **reference implementation** showing:
- How to wrap an external REST API
- Input/output transformation patterns
- Error handling
- A2A protocol integration
- Configuration management

## Structure

```
external_api_agent/
├── agent.py          # Wraps external REST API
├── executor.py       # A2A protocol bridge
├── main.py           # Server entry point
└── README.md         # This file
```

## How It Works

### 1. Agent (`agent.py`)
- **Initializes** HTTP client for API calls
- **Transforms** A2A input format to your API format
- **Calls** external REST API
- **Transforms** API response to A2A format
- **Streams** response back

### 2. Executor (`executor.py`)
- **Receives** A2A protocol requests
- **Extracts** user input from context
- **Calls** agent's `stream_response()` method
- **Streams** responses via A2A event queue
- **Manages** task lifecycle

### 3. Main (`main.py`)
- **Loads** configuration from YAML
- **Creates** agent card with metadata
- **Starts** A2A server
- **Handles** configuration errors gracefully

## Configuration

Edit `config/agents/external_api_agent.yaml`:

```yaml
agent_config:
  api_url: "${EXTERNAL_API_URL:http://localhost:8000/api/predict}"
  api_key: "${EXTERNAL_API_KEY:}"
  timeout: 30.0
```

Set environment variables:
```bash
export EXTERNAL_API_URL="https://your-api.com/predict"
export EXTERNAL_API_KEY="your-api-key"
```

## Usage

### 1. Configure Your API

Edit the config file with your API details.

### 2. Start the Agent

```bash
uv run python src/agents/external_api_agent/main.py
```

### 3. Register with Orchestrator

Add to `config/orchestrator.yaml`:
```yaml
remote_agent_urls:
  - "http://localhost:10006"  # External API Agent
```

### 4. Test

```bash
# Start orchestrator
uv run python src/agents/orchestrator/main_host.py

# Test via Streamlit
uv run streamlit run app.py
```

## Customization

### For Your API

1. **Modify `_transform_input()`** in `agent.py`:
   - Adapt to your API's expected input format
   - Handle different input types (JSON, text, etc.)

2. **Modify `_transform_output()`** in `agent.py`:
   - Format your API's response for display
   - Add any additional processing

3. **Update `call_api()`** in `agent.py`:
   - Change HTTP method (GET, POST, PUT, etc.)
   - Add custom headers
   - Handle authentication

### For ML Models

See `iris_classifier/` for ML model integration example.

## Key Concepts

### Input Transformation
```python
# A2A provides: "5.1 3.5 1.4 0.2"
# Your API expects: {"features": [5.1, 3.5, 1.4, 0.2]}
def _transform_input(self, query: str) -> dict:
    values = [float(x) for x in query.split()]
    return {'features': values}
```

### Output Transformation
```python
# Your API returns: {"prediction": "class_a", "confidence": 0.95}
# A2A displays: "Prediction: class_a\nConfidence: 95%"
def _transform_output(self, api_response: dict) -> str:
    return f"Prediction: {api_response['prediction']}\n"
```

### Streaming
```python
async def stream_response(self, query: str):
    result = await self.call_api(query)
    yield {'content': formatted_result, 'done': False}
    yield {'content': '', 'done': True}
```

## Testing

### Test Agent Directly
```bash
# Start agent
uv run python src/agents/external_api_agent/main.py

# Test with curl
curl http://localhost:10006/.well-known/agent.json
```

### Test via Orchestrator
```bash
# Start all agents
bash scripts/start_agents.sh

# Test in Streamlit
uv run streamlit run app.py
```

## Common Modifications

### 1. Different HTTP Method
```python
# Change from POST to GET
response = await self.client.get(
    self.api_url,
    params={'query': query}
)
```

### 2. Custom Authentication
```python
# Add custom auth header
self.headers['X-Custom-Auth'] = self.api_key
```

### 3. Streaming API Response
```python
async def stream_response(self, query: str):
    async with self.client.stream('POST', self.api_url, json=...) as response:
        async for chunk in response.aiter_text():
            yield {'content': chunk, 'done': False}
    yield {'content': '', 'done': True}
```

### 4. Batch Processing
```python
async def stream_response(self, query: str):
    # Process multiple items
    items = json.loads(query)
    for item in items:
        result = await self.call_api(item)
        yield {'content': f"{result}\n", 'done': False}
    yield {'content': '', 'done': True}
```

## Error Handling

The sample includes error handling for:
- HTTP errors (4xx, 5xx)
- Network timeouts
- Invalid responses
- Connection failures

Customize error messages in `stream_response()` method.

## Next Steps

1. **Copy** this directory: `cp -r external_api_agent your_agent_name`
2. **Modify** `agent.py` for your API
3. **Update** configuration file
4. **Test** independently
5. **Register** with orchestrator
6. **Deploy**

## See Also

- Full documentation: `docs/INTEGRATING_EXTERNAL_APPS.md`
- Integration checklist: `docs/INTEGRATION_CHECKLIST.md`
- ML model example: `src/agents/iris_classifier/`

