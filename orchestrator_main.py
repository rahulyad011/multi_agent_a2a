"""Main entry point for the Orchestrator Agent server."""
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from orchestrator_executor import OrchestratorAgentExecutor


if __name__ == '__main__':
    print("[DEBUG] Starting Orchestrator Agent server...")
    
    # Define agent skill
    skill = AgentSkill(
        id='query_routing',
        name='Query Routing',
        description='Routes user queries to appropriate specialized agents: RAG agent for document search, Image Captioning agent for image analysis',
        tags=['orchestrator', 'routing', 'rag', 'image-caption', 'a2a'],
        examples=[
            'What is Python?',
            'Tell me about machine learning',
            'caption: /path/to/image.jpg',
            'What can you help me with?'
        ],
    )
    
    # Define agent card
    agent_card = AgentCard(
        name='Orchestrator Agent',
        description='An orchestrator that routes queries to specialized agents (RAG and Image Captioning) via A2A protocol',
        url='http://localhost:10003/',
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill],
    )
    
    print(f"[DEBUG] Agent Card: {agent_card.name}")
    print(f"[DEBUG] Agent URL: {agent_card.url}")
    print(f"[DEBUG] Streaming enabled: {agent_card.capabilities.streaming}")
    
    # Create request handler with the orchestrator agent executor
    print("[DEBUG] Creating request handler...")
    request_handler = DefaultRequestHandler(
        agent_executor=OrchestratorAgentExecutor(
            rag_agent_url="http://localhost:10002",
            image_caption_agent_url="http://localhost:10004"
        ),
        task_store=InMemoryTaskStore(),
    )
    
    # Create A2A server application
    print("[DEBUG] Creating A2A server application...")
    server = A2AStarletteApplication(
        agent_card=agent_card, http_handler=request_handler
    )
    
    # Start the server
    print("[DEBUG] Starting server on http://0.0.0.0:10003")
    print("=" * 60)
    print("Orchestrator Agent is running!")
    print("Access the agent at: http://localhost:10003")
    print("")
    print("Connected Agents:")
    print("  - RAG Agent: http://localhost:10002")
    print("  - Image Caption Agent: http://localhost:10004")
    print("=" * 60)
    
    import uvicorn
    uvicorn.run(server.build(), host='0.0.0.0', port=10003)

