"""Main entry point for the External API Agent server."""
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from src.agents.external_api_agent.executor import ExternalAPIAgentExecutor
from src.utils.config_loader import ConfigLoader


def create_agent_card_from_config() -> AgentCard:
    """Create agent card from configuration file.
    
    Returns:
        AgentCard object with agent metadata
    """
    config_loader = ConfigLoader()
    agent_config = config_loader.load_agent_config("external_api_agent")
    
    # Convert skills from config
    skills = []
    for skill_data in agent_config.skills:
        skill = AgentSkill(
            id=skill_data.get('id', 'external_api'),
            name=skill_data.get('name', 'External API'),
            description=skill_data.get('description', 'Call external REST API'),
            tags=skill_data.get('tags', []),
            examples=skill_data.get('examples', []),
        )
        skills.append(skill)
    
    # Create agent card
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
    print("[DEBUG] Starting External API Agent server...")
    
    # Load configuration
    try:
        agent_card = create_agent_card_from_config()
        print(f"[DEBUG] Agent Card: {agent_card.name}")
        print(f"[DEBUG] Agent URL: {agent_card.url}")
        print(f"[DEBUG] Streaming enabled: {agent_card.capabilities.streaming}")
    except Exception as e:
        print(f"[DEBUG] Warning: Could not load config, using defaults: {e}")
        # Fallback to default configuration
        skill = AgentSkill(
            id='external_api',
            name='External API',
            description='Call external REST API endpoint',
            tags=['api', 'rest', 'http'],
            examples=[
                'Query external API',
                'Call API endpoint',
            ],
        )
        
        agent_card = AgentCard(
            name='External API Agent',
            description='Sample agent that wraps an external REST API endpoint',
            url='http://localhost:10006/',
            version='1.0.0',
            default_input_modes=['text'],
            default_output_modes=['text'],
            capabilities=AgentCapabilities(streaming=True),
            skills=[skill],
        )
    
    # Create request handler with the agent executor
    print("[DEBUG] Creating request handler...")
    request_handler = DefaultRequestHandler(
        agent_executor=ExternalAPIAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )
    
    # Create A2A server application
    print("[DEBUG] Creating A2A server application...")
    server = A2AStarletteApplication(
        agent_card=agent_card, http_handler=request_handler
    )
    
    # Get port from config or use default
    try:
        config_loader = ConfigLoader()
        agent_config = config_loader.load_agent_config("external_api_agent")
        port = agent_config.port
    except Exception:
        port = 10006  # Default port
    
    # Start the server
    print(f"[DEBUG] Starting server on http://0.0.0.0:{port}")
    print("=" * 60)
    print("🌐 External API Agent is running!")
    print("=" * 60)
    print(f"Access the agent at: http://localhost:{port}")
    print()
    print("💡 This is a sample implementation showing how to:")
    print("   - Wrap an external REST API")
    print("   - Transform input/output formats")
    print("   - Integrate with the orchestrator")
    print()
    print("⚠️  Configure your API URL in:")
    print("   config/agents/external_api_agent.yaml")
    print("=" * 60)
    
    import uvicorn
    uvicorn.run(server.build(), host='0.0.0.0', port=port)

