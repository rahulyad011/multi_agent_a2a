"""Main entry point for the Simple RAG Agent server."""
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from src.agents.simple_rag.executor import SimpleRAGAgentExecutor
from src.utils.config_loader import ConfigLoader


def create_agent_card_from_config() -> AgentCard:
    """Create agent card from configuration file.
    
    Returns:
        AgentCard object
    """
    config_loader = ConfigLoader()
    agent_config = config_loader.load_agent_config("simple_rag")
    
    # Convert skills from config
    skills = []
    for skill_data in agent_config.skills:
        skill = AgentSkill(
            id=skill_data.get('id', 'document_search'),
            name=skill_data.get('name', 'Document Search'),
            description=skill_data.get('description', 'Search through documents'),
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
    print("[DEBUG] Starting Simple RAG Agent server...")
    
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
            id='document_search',
            name='Document Search',
            description='Search through documents using vector similarity to find relevant information',
            tags=['rag', 'search', 'documents', 'vector-db'],
            examples=[
                'What do you know about Python?',
                'Tell me about machine learning',
                'Explain the A2A protocol'
            ],
        )
        
        agent_card = AgentCard(
            name='Simple RAG Agent',
            description='A simple RAG agent that uses ChromaDB to search through documents and provide relevant information',
            url='http://localhost:10002/',
            version='1.0.0',
            default_input_modes=['text'],
            default_output_modes=['text'],
            capabilities=AgentCapabilities(streaming=True),
            skills=[skill],
        )
    
    # Create request handler with the RAG agent executor
    print("[DEBUG] Creating request handler...")
    request_handler = DefaultRequestHandler(
        agent_executor=SimpleRAGAgentExecutor(),
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
        agent_config = config_loader.load_agent_config("simple_rag")
        port = agent_config.port
    except Exception:
        port = 10002  # Default port
    
    # Start the server
    print(f"[DEBUG] Starting server on http://0.0.0.0:{port}")
    print("=" * 60)
    print("Simple RAG Agent is running!")
    print(f"Access the agent at: http://localhost:{port}")
    print("=" * 60)
    
    import uvicorn
    uvicorn.run(server.build(), host='0.0.0.0', port=port)

