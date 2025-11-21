# Integration Checklist - External Application/API

Use this checklist when integrating your external application or REST API with the orchestrator.

## Pre-Integration Requirements

- [ ] Python 3.10+ installed
- [ ] Your application/API is accessible (running locally or remotely)
- [ ] You understand your API's input/output format
- [ ] You have API credentials/keys if required

## Code Structure

- [ ] Created agent directory: `src/agents/your_agent_name/`
- [ ] Created `__init__.py` file
- [ ] Created `agent.py` with your application wrapper
- [ ] Created `executor.py` with A2A protocol bridge
- [ ] Created `main.py` with server entry point

## Agent Implementation (`agent.py`)

- [ ] Implemented `__init__(self, config)` method
- [ ] Implemented `stream_response(self, query)` async generator
- [ ] Added input transformation logic (A2A format → Your API format)
- [ ] Added output transformation logic (Your API format → A2A format)
- [ ] Added error handling for API failures
- [ ] Added logging for debugging

## Executor Implementation (`executor.py`)

- [ ] Extends `AgentExecutor` class
- [ ] Implements `execute()` method
- [ ] Implements `cancel()` method (or raises exception)
- [ ] Loads configuration from config file
- [ ] Streams responses via `event_queue`
- [ ] Sends completion status

## Server Setup (`main.py`)

- [ ] Loads agent card from config
- [ ] Creates `DefaultRequestHandler` with executor
- [ ] Creates `A2AStarletteApplication`
- [ ] Starts server on configured port
- [ ] Has fallback defaults if config fails

## Configuration

- [ ] Created `config/agents/your_agent_name.yaml`
- [ ] Set agent name, description, version
- [ ] Configured port and URL
- [ ] Defined capabilities (streaming, input/output modes)
- [ ] Added skills with examples
- [ ] Added agent-specific config (API URL, keys, etc.)
- [ ] Used environment variables for secrets (`${VAR_NAME}`)

## Orchestrator Registration

- [ ] Added agent URL to `config/orchestrator.yaml`
- [ ] Agent URL matches the port in agent config
- [ ] Orchestrator config includes all required agents

## Testing

- [ ] Agent starts without errors
- [ ] Agent responds to health check (`/.well-known/agent.json`)
- [ ] Agent processes test queries correctly
- [ ] Orchestrator discovers the agent
- [ ] Orchestrator routes queries to the agent
- [ ] Responses are formatted correctly
- [ ] Error handling works (API down, invalid input, etc.)

## Input/Output Format

- [ ] Documented expected input format
- [ ] Documented output format
- [ ] Input transformation handles all supported formats
- [ ] Output is user-friendly and well-formatted
- [ ] Streaming works correctly (for long responses)

## Security

- [ ] API keys stored in environment variables
- [ ] No hardcoded secrets in code
- [ ] Proper authentication headers
- [ ] Input validation to prevent injection attacks
- [ ] Error messages don't expose sensitive information

## Documentation

- [ ] README updated with your agent
- [ ] Configuration options documented
- [ ] Example queries provided
- [ ] Troubleshooting section added

## Deployment

- [ ] Agent runs in production environment
- [ ] Logs are properly configured
- [ ] Monitoring/health checks in place
- [ ] Error alerts configured (if needed)

## Quick Reference

### File Structure
```
src/agents/your_agent_name/
├── __init__.py
├── agent.py          # Your application wrapper
├── executor.py       # A2A protocol bridge
└── main.py           # Server entry point

config/agents/
└── your_agent_name.yaml  # Agent configuration
```

### Key Methods

**agent.py:**
- `__init__(self, config)` - Initialize your application/API client
- `stream_response(self, query)` - Process query and yield responses

**executor.py:**
- `execute(self, context, event_queue)` - A2A protocol handler
- `cancel(self, context, event_queue)` - Cancel handler

### Configuration Template
```yaml
agent:
  name: "Your Agent"
  description: "Description"
  port: 10006
  url: "http://localhost:10006"
  capabilities:
    streaming: true
  skills:
    - id: "skill_id"
      name: "Skill Name"
      examples: ["example1", "example2"]
  agent_config:
    api_url: "${API_URL}"
    api_key: "${API_KEY}"
```

## Need Help?

- Review sample implementation: `src/agents/external_api_agent/`
- Review ML model example: `src/agents/iris_classifier/`
- Check documentation: `docs/INTEGRATING_EXTERNAL_APPS.md`

