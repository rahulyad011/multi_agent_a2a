# Integrating External Applications/REST APIs with Orchestrator

This guide explains how to integrate your existing application, REST API endpoint, or ML model with the multi-agent orchestrator system using the A2A protocol.

## Overview

The orchestrator uses the A2A (Agent-to-Agent) protocol to communicate with agents. To integrate your external application, you need to create an **Agent Wrapper** that:

1. **Wraps your application/API** - Handles initialization and calls
2. **Implements A2A protocol** - Converts between A2A messages and your API format
3. **Streams responses** - Provides real-time streaming responses to the orchestrator

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Your External Application / REST API                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ - ML Model (PyTorch, TensorFlow, scikit-learn)        │  │
│  │ - REST API Endpoint (Flask, FastAPI, Django)          │  │
│  │ - Microservice (gRPC, HTTP)                           │  │
│  │ - Any Python Application                              │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                        │
                        │ Wrap in Agent
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  Agent Wrapper (Your Integration Layer)                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ agent.py: Your application wrapper                    │  │
│  │ executor.py: A2A protocol bridge                     │  │
│  │ main.py: A2A server setup                            │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                        │
                        │ A2A Protocol (HTTP/JSON-RPC)
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  Orchestrator Agent                                          │
│  - Routes queries intelligently                             │
│  - Manages agent discovery                                  │
│  - Handles A2A communication                                │
└─────────────────────────────────────────────────────────────┘
```

## What You Need

### 1. Your Application/API
- **REST API**: Any HTTP endpoint (Flask, FastAPI, Django, etc.)
- **ML Model**: Trained model file (PyTorch, TensorFlow, scikit-learn, etc.)
- **Service**: Any Python application or service
- **External API**: Third-party API you want to wrap

### 2. Integration Requirements
- **Python 3.10+**
- **A2A SDK**: Already included in dependencies
- **HTTP Client**: For REST API calls (httpx, requests)
- **Configuration**: YAML config file for your agent

### 3. Code Structure
You need to create 3 files:
- `agent.py` - Wraps your application/API
- `executor.py` - A2A protocol bridge
- `main.py` - A2A server entry point

## Step-by-Step Integration

### Step 1: Create Agent Directory

```bash
mkdir -p src/agents/your_agent_name
touch src/agents/your_agent_name/__init__.py
```

### Step 2: Create Agent Wrapper (`agent.py`)

This file wraps your application/API and handles the core logic.

**For REST API:**
```python
import httpx
from typing import Any, AsyncGenerator

class YourAPIAgent:
    """Agent wrapper for your REST API."""
    
    def __init__(self, config: dict):
        self.api_url = config.get('api_url')
        self.api_key = config.get('api_key')
        self.timeout = config.get('timeout', 30.0)
        self.client = httpx.AsyncClient(timeout=self.timeout)
    
    async def process(self, input_data: str) -> dict:
        """Call your REST API."""
        headers = {}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        
        response = await self.client.post(
            self.api_url,
            json={'input': input_data},
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    
    async def stream_response(self, query: str) -> AsyncGenerator[dict[str, Any], None]:
        """Stream response from your API."""
        result = await self.process(query)
        
        # Format response for streaming
        yield {'content': f"Result: {result.get('output', result)}\n", 'done': False}
        yield {'content': '', 'done': True}
```

**For ML Model:**
```python
import pickle
import numpy as np
from typing import Any, AsyncGenerator

class YourMLAgent:
    """Agent wrapper for your ML model."""
    
    def __init__(self, config: dict):
        model_path = config.get('model_path')
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)
    
    def predict(self, features: list[float]) -> dict:
        """Run prediction."""
        features_array = np.array(features).reshape(1, -1)
        prediction = self.model.predict(features_array)[0]
        probabilities = self.model.predict_proba(features_array)[0]
        
        return {
            'prediction': prediction,
            'probabilities': probabilities.tolist()
        }
    
    async def stream_response(self, query: str) -> AsyncGenerator[dict[str, Any], None]:
        """Stream prediction results."""
        # Parse input (JSON, list, etc.)
        import json
        features = json.loads(query)
        
        result = self.predict(features)
        
        yield {'content': f"Prediction: {result['prediction']}\n", 'done': False}
        yield {'content': f"Confidence: {max(result['probabilities']):.2%}\n", 'done': False}
        yield {'content': '', 'done': True}
```

### Step 3: Create A2A Executor (`executor.py`)

This file bridges your agent with the A2A protocol.

```python
from typing import override
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import (
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
)
from a2a.utils import new_text_artifact
from src.agents.your_agent_name.agent import YourAPIAgent
from src.utils.config_loader import ConfigLoader

class YourAPIAgentExecutor(AgentExecutor):
    """A2A executor for your API agent."""
    
    def __init__(self, config: dict | None = None):
        if config is None:
            config_loader = ConfigLoader()
            try:
                agent_config = config_loader.load_agent_config("your_agent_name")
                config = agent_config.agent_config
            except Exception as e:
                print(f"[DEBUG] Warning: Could not load config: {e}")
                config = {}
        
        self.agent = YourAPIAgent(config)
    
    @override
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Execute agent and stream response via A2A."""
        query = context.get_user_input()
        
        # Stream response from your agent
        async for event in self.agent.stream_response(query):
            message = TaskArtifactUpdateEvent(
                context_id=context.context_id,
                task_id=context.task_id,
                artifact=new_text_artifact(
                    name='result',
                    text=event['content'],
                ),
            )
            await event_queue.enqueue_event(message)
            
            if event['done']:
                break
        
        # Send completion status
        status = TaskStatusUpdateEvent(
            context_id=context.context_id,
            task_id=context.task_id,
            status=TaskStatus(state=TaskState.completed),
            final=True,
        )
        await event_queue.enqueue_event(status)
    
    @override
    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        """Cancel task."""
        raise Exception('cancel not supported')
```

### Step 4: Create Server Entry Point (`main.py`)

```python
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from src.agents.your_agent_name.executor import YourAPIAgentExecutor
from src.utils.config_loader import ConfigLoader

def create_agent_card_from_config() -> AgentCard:
    """Create agent card from configuration."""
    config_loader = ConfigLoader()
    agent_config = config_loader.load_agent_config("your_agent_name")
    
    skills = []
    for skill_data in agent_config.skills:
        skill = AgentSkill(
            id=skill_data.get('id', 'your_skill'),
            name=skill_data.get('name', 'Your Skill'),
            description=skill_data.get('description', ''),
            tags=skill_data.get('tags', []),
            examples=skill_data.get('examples', []),
        )
        skills.append(skill)
    
    agent_card = AgentCard(
        name=agent_config.name,
        description=agent_config.description,
        url=agent_config.url,
        version=agent_config.version,
        default_input_modes=agent_config.capabilities.get('input_modes', ['text']),
        default_output_modes=agent_config.capabilities.get('output_modes', ['text']),
        capabilities=AgentCapabilities(
            streaming=agent_config.capabilities.get('streaming', True)
        ),
        skills=skills,
    )
    
    return agent_card

if __name__ == '__main__':
    print("[DEBUG] Starting Your API Agent server...")
    
    try:
        agent_card = create_agent_card_from_config()
    except Exception as e:
        print(f"[DEBUG] Warning: Could not load config: {e}")
        # Fallback defaults
        agent_card = AgentCard(
            name='Your API Agent',
            description='Your agent description',
            url='http://localhost:10006/',
            version='1.0.0',
            default_input_modes=['text'],
            default_output_modes=['text'],
            capabilities=AgentCapabilities(streaming=True),
            skills=[],
        )
    
    request_handler = DefaultRequestHandler(
        agent_executor=YourAPIAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )
    
    server = A2AStarletteApplication(
        agent_card=agent_card, http_handler=request_handler
    )
    
    try:
        config_loader = ConfigLoader()
        agent_config = config_loader.load_agent_config("your_agent_name")
        port = agent_config.port
    except Exception:
        port = 10006
    
    import uvicorn
    uvicorn.run(server.build(), host='0.0.0.0', port=port)
```

### Step 5: Create Configuration File

Create `config/agents/your_agent_name.yaml`:

```yaml
agent:
  name: "Your API Agent"
  description: "Description of what your agent does"
  version: "1.0.0"
  port: 10006
  url: "http://localhost:10006"
  
  capabilities:
    streaming: true
    input_modes: ["text"]
    output_modes: ["text"]
  
  skills:
    - id: "your_skill"
      name: "Your Skill Name"
      description: "What this skill does"
      tags: ["tag1", "tag2"]
      examples:
        - "Example query 1"
        - "Example query 2"
  
  agent_config:
    # Your application-specific configuration
    api_url: "${YOUR_API_URL:http://localhost:8000/api/predict}"
    api_key: "${YOUR_API_KEY:}"
    timeout: 30.0
    # Or for ML models:
    # model_path: "./models/your_model.pkl"
```

### Step 6: Register with Orchestrator

Edit `config/orchestrator.yaml`:

```yaml
orchestrator:
  remote_agent_urls:
    - "http://localhost:10002"  # RAG Agent
    - "http://localhost:10004"  # Image Caption Agent
    - "http://localhost:10005"  # Iris Classifier Agent
    - "http://localhost:10006"  # Your API Agent  <-- Add this
```

## Input/Output Transformation

### Input Transformation

**A2A Input → Your API Format:**

```python
# A2A provides query as string
query = context.get_user_input()  # e.g., "5.1 3.5 1.4 0.2"

# Transform to your API format
import json
if query.strip().startswith('{'):
    # JSON format
    api_input = json.loads(query)
else:
    # Parse other formats
    api_input = {'data': query.split()}
```

### Output Transformation

**Your API Output → A2A Format:**

```python
# Your API returns
api_response = {
    'result': 'prediction',
    'confidence': 0.95
}

# Transform to A2A streaming format
async def stream_response(self, query: str):
    api_result = await self.call_api(query)
    
    # Format for A2A
    yield {'content': f"Result: {api_result['result']}\n", 'done': False}
    yield {'content': f"Confidence: {api_result['confidence']:.2%}\n", 'done': False}
    yield {'content': '', 'done': True}
```

## Common Patterns

### Pattern 1: REST API Integration

```python
class RESTAPIAgent:
    async def stream_response(self, query: str):
        response = await self.http_client.post(
            self.api_url,
            json={'query': query}
        )
        result = response.json()
        
        yield {'content': result['output'], 'done': False}
        yield {'content': '', 'done': True}
```

### Pattern 2: ML Model Integration

```python
class MLModelAgent:
    async def stream_response(self, query: str):
        features = self.parse_input(query)
        prediction = self.model.predict(features)
        
        yield {'content': f"Prediction: {prediction}\n", 'done': False}
        yield {'content': '', 'done': True}
```

### Pattern 3: Streaming API Response

```python
class StreamingAPIAgent:
    async def stream_response(self, query: str):
        async with self.http_client.stream('POST', self.api_url, json={'query': query}) as response:
            async for chunk in response.aiter_text():
                yield {'content': chunk, 'done': False}
        yield {'content': '', 'done': True}
```

## Testing Your Integration

1. **Test Agent Independently:**
   ```bash
   uv run python src/agents/your_agent_name/main.py
   ```

2. **Test via Orchestrator:**
   ```bash
   # Start all agents
   bash scripts/start_agents.sh
   
   # Test via Streamlit
   uv run streamlit run app.py
   ```

3. **Verify Discovery:**
   - Check orchestrator logs for agent discovery
   - Verify agent appears in available agents list

## Best Practices

1. **Error Handling**: Always handle API failures gracefully
2. **Timeout Management**: Set appropriate timeouts for external calls
3. **Input Validation**: Validate and sanitize inputs
4. **Logging**: Add debug logging for troubleshooting
5. **Configuration**: Use environment variables for secrets
6. **Streaming**: Stream responses for better UX

## Example: See Sample Implementation

A complete sample implementation is available in:
- `src/agents/external_api_agent/` - Sample REST API integration
- `src/agents/iris_classifier/` - Sample ML model integration

## Next Steps

1. Review the sample implementation
2. Adapt it to your use case
3. Create your agent files
4. Add configuration
5. Register with orchestrator
6. Test and deploy!

