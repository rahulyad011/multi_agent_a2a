"""Main entry point for the Iris Classifier Agent server."""
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from src.agents.iris_classifier.executor import IrisClassifierAgentExecutor
from src.utils.config_loader import ConfigLoader


def create_agent_card_from_config() -> AgentCard:
    """Create agent card from configuration file.
    
    Returns:
        AgentCard object
    """
    config_loader = ConfigLoader()
    agent_config = config_loader.load_agent_config("iris_classifier")
    
    # Convert skills from config
    skills = []
    for skill_data in agent_config.skills:
        skill = AgentSkill(
            id=skill_data.get('id', 'iris_classification'),
            name=skill_data.get('name', 'Iris Classification'),
            description=skill_data.get('description', 'Classify iris flowers'),
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
    print("[DEBUG] Starting Iris Classifier Agent server...")
    
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
            id='iris_classification',
            name='Iris Flower Classification',
            description='Classify iris flowers into setosa, versicolor, or virginica using Random Forest',
            tags=['ml', 'classification', 'iris', 'random-forest', 'scikit-learn'],
            examples=[
                '{"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}',
                '[5.1, 3.5, 1.4, 0.2]',
                '5.1 3.5 1.4 0.2',
            ],
        )
        
        agent_card = AgentCard(
            name='Iris Classifier Agent',
            description='ML Pipeline Agent for Iris flower classification using Random Forest',
            url='http://localhost:10005/',
            version='1.0.0',
            default_input_modes=['text'],
            default_output_modes=['text'],
            capabilities=AgentCapabilities(streaming=True),
            skills=[skill],
        )
    
    # Create request handler with the agent executor
    print("[DEBUG] Creating request handler...")
    request_handler = DefaultRequestHandler(
        agent_executor=IrisClassifierAgentExecutor(),
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
        agent_config = config_loader.load_agent_config("iris_classifier")
        port = agent_config.port
    except Exception:
        port = 10005  # Default port
    
    # Start the server
    print(f"[DEBUG] Starting server on http://0.0.0.0:{port}")
    print("=" * 60)
    print("🌺 Iris Classifier Agent is running!")
    print("=" * 60)
    print(f"Access the agent at: http://localhost:{port}")
    print()
    print("💡 Example queries:")
    print('  - {"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}')
    print('  - [5.1, 3.5, 1.4, 0.2]')
    print('  - 5.1 3.5 1.4 0.2')
    print()
    print("⚠️  Note: Make sure to train the model first:")
    print("   python src/agents/iris_classifier/train.py")
    print("=" * 60)
    
    import uvicorn
    uvicorn.run(server.build(), host='0.0.0.0', port=port)

