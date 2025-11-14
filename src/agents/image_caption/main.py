"""Main entry point for the Image Captioning Agent server."""
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from src.agents.image_caption.executor import ImageCaptioningAgentExecutor


if __name__ == '__main__':
    print("[DEBUG] Starting Image Captioning Agent server...")
    
    # Define agent skill
    skill = AgentSkill(
        id='image_captioning',
        name='Image Captioning',
        description='Generate descriptive captions for images using AI vision models',
        tags=['image', 'caption', 'vision', 'ai', 'blip'],
        examples=[
            'caption: /path/to/image.jpg',
            '/Users/username/Pictures/photo.png',
            'describe: ~/Downloads/sunset.jpg'
        ],
    )
    
    # Define agent card
    agent_card = AgentCard(
        name='Image Captioning Agent',
        description='An AI agent that generates descriptive captions for images using the BLIP vision model',
        url='http://localhost:10004/',
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill],
    )
    
    print(f"[DEBUG] Agent Card: {agent_card.name}")
    print(f"[DEBUG] Agent URL: {agent_card.url}")
    print(f"[DEBUG] Streaming enabled: {agent_card.capabilities.streaming}")
    
    # Create request handler with the image captioning agent executor
    print("[DEBUG] Creating request handler...")
    request_handler = DefaultRequestHandler(
        agent_executor=ImageCaptioningAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )
    
    # Create A2A server application
    print("[DEBUG] Creating A2A server application...")
    server = A2AStarletteApplication(
        agent_card=agent_card, http_handler=request_handler
    )
    
    # Start the server
    print("[DEBUG] Starting server on http://0.0.0.0:10004")
    print("=" * 60)
    print("Image Captioning Agent is running!")
    print("Access the agent at: http://localhost:10004")
    print("=" * 60)
    
    import uvicorn
    uvicorn.run(server.build(), host='0.0.0.0', port=10004)

