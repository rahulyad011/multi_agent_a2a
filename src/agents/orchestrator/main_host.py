"""Main entry point for the Host-style Orchestrator Agent server."""
import os
from dotenv import load_dotenv
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from src.agents.orchestrator.executor_host import HostOrchestratorExecutor


if __name__ == '__main__':
    # Load environment variables from .env file
    load_dotenv()
    print("[DEBUG] Loaded environment variables from .env file")
    print("[DEBUG] Starting Host-style Orchestrator Agent server...")
    
    # Define agent skill
    skill = AgentSkill(
        id='intelligent_routing',
        name='Intelligent Query Routing',
        description='Uses LLM to intelligently route queries to specialized agents: RAG agent for document search, Image Captioning agent for image analysis',
        tags=['orchestrator', 'routing', 'llm', 'rag', 'image-caption', 'a2a'],
        examples=[
            'What is Python?',
            'Tell me about machine learning',
            'caption: /path/to/image.jpg',
            'What agents are available?'
        ],
    )
    
    # Define agent card
    agent_card = AgentCard(
        name='Host Orchestrator Agent',
        description='LLM-powered host orchestrator that intelligently routes queries to specialized agents (RAG and Image Captioning) via A2A protocol',
        url='http://localhost:10003/',
        version='2.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill],
    )
    
    print(f"[DEBUG] Agent Card: {agent_card.name}")
    print(f"[DEBUG] Agent URL: {agent_card.url}")
    print(f"[DEBUG] Streaming enabled: {agent_card.capabilities.streaming}")
    
    # Check if OCI GenAI is configured
    llm_callable = None
    model_name = os.getenv('LITELLM_MODEL', 'gemini/gemini-2.0-flash-001')
    
    # If OCI environment variables are set, use OCI GenAI
    if os.getenv('OCI_COMPARTMENT_ID') and os.getenv('OCI_GENAI_ENDPOINT'):
        try:
            import oci
            from src.utils.oci_llm import configure_llm_chat
            
            # Load OCI config
            oci_config = oci.config.from_file()
            
            # Configure OCI GenAI LLM
            llm_callable = configure_llm_chat(
                config=oci_config,
                model_id=os.getenv('OCI_MODEL_ID', 'cohere.command-r-plus'),
                service_endpoint=os.getenv('OCI_GENAI_ENDPOINT'),
                compartment_id=os.getenv('OCI_COMPARTMENT_ID'),
                max_tokens=int(os.getenv('OCI_MAX_TOKENS', '2000'))
            )
            print(f"[DEBUG] Using OCI GenAI: {os.getenv('OCI_MODEL_ID', 'cohere.command-r-plus')}")
        except Exception as e:
            print(f"[DEBUG] Warning: Could not configure OCI GenAI: {e}")
            print(f"[DEBUG] Falling back to LiteLLM with model: {model_name}")
    else:
        print(f"[DEBUG] LLM Model: {model_name}")
    
    # Configure remote agents
    remote_agent_urls = [
        "http://localhost:10002",  # RAG Agent
        "http://localhost:10004",  # Image Caption Agent
    ]
    print(f"[DEBUG] Remote Agents: {remote_agent_urls}")
    
    # Create request handler with the host orchestrator agent executor
    print("[DEBUG] Creating request handler with HostOrchestratorExecutor...")
    request_handler = DefaultRequestHandler(
        agent_executor=HostOrchestratorExecutor(
            remote_agent_urls=remote_agent_urls,
            model_name=model_name,
            llm_callable=llm_callable,
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
    print("🤖 Host Orchestrator Agent is running!")
    print("=" * 60)
    print("Access the agent at: http://localhost:10003")
    print("")
    print("🧠 Using LLM for intelligent routing")
    if llm_callable:
        print(f"   Provider: OCI GenAI ({os.getenv('OCI_MODEL_ID', 'cohere.command-r-plus')})")
    else:
        print(f"   Model: {model_name}")
    print("")
    print("🔗 Connected Agents (A2A Protocol):")
    print("   • RAG Agent: http://localhost:10002")
    print("   • Image Caption Agent: http://localhost:10004")
    print("")
    print("💡 The LLM will automatically route queries to the right agent!")
    print("=" * 60)
    
    import uvicorn
    uvicorn.run(server.build(), host='0.0.0.0', port=10003)

