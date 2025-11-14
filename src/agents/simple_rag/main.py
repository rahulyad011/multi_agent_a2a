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


if __name__ == '__main__':
    print("[DEBUG] Starting Simple RAG Agent server...")
    
    # Define agent skill
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
    
    # Define agent card
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
    
    print(f"[DEBUG] Agent Card: {agent_card.name}")
    print(f"[DEBUG] Agent URL: {agent_card.url}")
    print(f"[DEBUG] Streaming enabled: {agent_card.capabilities.streaming}")
    
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
    
    # Start the server
    print("[DEBUG] Starting server on http://0.0.0.0:10002")
    print("=" * 60)
    print("Simple RAG Agent is running!")
    print("Access the agent at: http://localhost:10002")
    print("=" * 60)
    
    import uvicorn
    uvicorn.run(server.build(), host='0.0.0.0', port=10002)

