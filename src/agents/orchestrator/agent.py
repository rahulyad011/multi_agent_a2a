"""Orchestrator Agent that routes queries to appropriate agents."""
import json
from typing import Any, AsyncGenerator
import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    Message,
    MessageSendParams,
    SendStreamingMessageRequest,
    TextPart,
)
from uuid import uuid4


class OrchestratorAgent:
    """Orchestrator Agent that routes queries to specialized agents."""
    
    def __init__(
        self, 
        rag_agent_url: str = "http://localhost:10002",
        image_caption_agent_url: str = "http://localhost:10004"
    ):
        """Initialize the orchestrator agent.
        
        Args:
            rag_agent_url: URL of the RAG agent
            image_caption_agent_url: URL of the Image Captioning agent
        """
        print(f"[DEBUG] Initializing OrchestratorAgent")
        print(f"[DEBUG] RAG Agent URL: {rag_agent_url}")
        print(f"[DEBUG] Image Caption Agent URL: {image_caption_agent_url}")
        self.rag_agent_url = rag_agent_url
        self.image_caption_agent_url = image_caption_agent_url
        self.httpx_client = None
        self.rag_client = None
        self.image_caption_client = None
        print("[DEBUG] OrchestratorAgent initialized")
    
    async def _ensure_httpx_client(self) -> httpx.AsyncClient:
        """Ensure the httpx client is initialized."""
        if self.httpx_client is None:
            self.httpx_client = httpx.AsyncClient(timeout=30.0)
        return self.httpx_client
    
    async def _ensure_rag_client(self) -> A2AClient:
        """Ensure the RAG client is initialized."""
        if self.rag_client is None:
            print("[DEBUG] Initializing RAG agent A2A client...")
            httpx_client = await self._ensure_httpx_client()
            
            # Fetch the agent card
            print(f"[DEBUG] Fetching agent card from {self.rag_agent_url}")
            resolver = A2ACardResolver(
                httpx_client=httpx_client,
                base_url=self.rag_agent_url,
            )
            agent_card = await resolver.get_agent_card()
            print(f"[DEBUG] Agent card received: {agent_card.name}")
            
            # Create the A2A client
            self.rag_client = A2AClient(
                httpx_client=httpx_client,
                agent_card=agent_card
            )
            print("[DEBUG] RAG agent A2A client initialized")
        
        return self.rag_client
    
    async def _ensure_image_caption_client(self) -> A2AClient:
        """Ensure the Image Caption client is initialized."""
        if self.image_caption_client is None:
            print("[DEBUG] Initializing Image Caption agent A2A client...")
            httpx_client = await self._ensure_httpx_client()
            
            # Fetch the agent card
            print(f"[DEBUG] Fetching agent card from {self.image_caption_agent_url}")
            resolver = A2ACardResolver(
                httpx_client=httpx_client,
                base_url=self.image_caption_agent_url,
            )
            agent_card = await resolver.get_agent_card()
            print(f"[DEBUG] Agent card received: {agent_card.name}")
            
            # Create the A2A client
            self.image_caption_client = A2AClient(
                httpx_client=httpx_client,
                agent_card=agent_card
            )
            print("[DEBUG] Image Caption agent A2A client initialized")
        
        return self.image_caption_client
    
    def should_route_to_image_caption(self, query: str) -> bool:
        """Determine if the query should be routed to the Image Caption agent.
        
        Args:
            query: The user query
            
        Returns:
            True if query should be routed to Image Caption agent
        """
        query_lower = query.lower()
        
        # Check for image-related keywords or file paths
        image_keywords = ['caption', 'image', 'picture', 'photo', 'describe image']
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff']
        
        # Check if query contains image keywords
        has_image_keyword = any(keyword in query_lower for keyword in image_keywords)
        
        # Check if query contains image file extensions
        has_image_extension = any(ext in query_lower for ext in image_extensions)
        
        # Check if query looks like a file path
        looks_like_path = '/' in query or '\\' in query or query.startswith('~')
        
        return has_image_keyword or (has_image_extension and looks_like_path)
    
    def should_route_to_rag(self, query: str) -> bool:
        """Determine if the query should be routed to the RAG agent.
        
        This is a simple heuristic-based routing. In production, you might use
        a more sophisticated approach like a classifier or LLM.
        
        Args:
            query: The user query
            
        Returns:
            True if query should be routed to RAG agent
        """
        # Don't route to RAG if it should go to image caption
        if self.should_route_to_image_caption(query):
            return False
        
        # Keywords that suggest document search
        document_keywords = [
            'what', 'tell me about', 'explain', 'describe',
            'python', 'machine learning', 'vector', 'database',
            'a2a', 'protocol', 'chroma', 'programming'
        ]
        
        query_lower = query.lower()
        should_route = any(keyword in query_lower for keyword in document_keywords)
        
        return should_route
    
    async def _route_to_agent(
        self, 
        query: str, 
        agent_name: str, 
        client: A2AClient
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Generic method to route query to an agent via A2A.
        
        Args:
            query: The user query
            agent_name: Name of the agent for logging
            client: The A2A client to use
            
        Yields:
            Dict with 'content' and 'done' keys
        """
        try:
            # Create message for agent
            print(f"[DEBUG] Creating A2A message for {agent_name}")
            message = Message(
                role='user',
                parts=[TextPart(text=query)],
                message_id=uuid4().hex,
            )
            
            # Create send params
            params = MessageSendParams(
                id=uuid4().hex,
                message=message
            )
            
            # Create streaming request
            streaming_request = SendStreamingMessageRequest(
                id=uuid4().hex,
                params=params
            )
            
            print(f"[DEBUG] Sending streaming request to {agent_name} via A2A")
            print(f"[DEBUG] Request ID: {streaming_request.id}")
            
            # Stream response from agent
            stream_response = client.send_message_streaming(streaming_request)
            
            print(f"[DEBUG] Receiving streaming response from {agent_name}")
            chunk_count = 0
            async for chunk in stream_response:
                chunk_count += 1
                # Extract text from the chunk
                data = chunk.model_dump(mode='json', exclude_none=True)
                
                # Debug: print chunk structure
                if chunk_count == 1:
                    print(f"[DEBUG] First chunk structure: {json.dumps(data, indent=2)[:200]}...")
                
                # Extract text from artifact
                if 'result' in data and 'artifact' in data['result']:
                    artifact = data['result']['artifact']
                    if 'parts' in artifact and artifact['parts']:
                        text = artifact['parts'][0].get('text', '')
                        if text:
                            print(f"[DEBUG] Chunk {chunk_count}: forwarding {len(text)} chars")
                            yield {'content': text, 'done': False}
            
            print(f"[DEBUG] Received {chunk_count} chunks from {agent_name}")
            print("[DEBUG] ===== A2A CALL COMPLETE =====")
            yield {'content': '', 'done': True}
            
        except Exception as e:
            print(f"[DEBUG] ERROR: Failed to communicate with {agent_name}: {e}")
            error_msg = f"\n\n[Error: Could not reach {agent_name} - {str(e)}]"
            yield {'content': error_msg, 'done': False}
            yield {'content': '', 'done': True}
    
    async def stream_response(self, query: str) -> AsyncGenerator[dict[str, Any], None]:
        """Stream the response, routing to appropriate agent.
        
        Args:
            query: The user query
            
        Yields:
            Dict with 'content' and 'done' keys
        """
        print(f"[DEBUG] OrchestratorAgent processing query: '{query}'")
        print(f"[DEBUG] Determining routing...")
        
        # Check if query should go to image captioning agent
        if self.should_route_to_image_caption(query):
            print("[DEBUG] ===== ROUTING TO IMAGE CAPTION AGENT VIA A2A =====")
            image_client = await self._ensure_image_caption_client()
            async for chunk in self._route_to_agent(query, "Image Caption Agent", image_client):
                yield chunk
        
        # Check if query should go to RAG agent
        elif self.should_route_to_rag(query):
            print("[DEBUG] ===== ROUTING TO RAG AGENT VIA A2A =====")
            rag_client = await self._ensure_rag_client()
            async for chunk in self._route_to_agent(query, "RAG Agent", rag_client):
                yield chunk
        
        # Handle directly by orchestrator
        else:
            print("[DEBUG] Handling query directly (no routing)")
            response = (
                "I'm an orchestrator agent. I can help you with:\n\n"
                "**📚 Document Search** (via RAG Agent):\n"
                "- Python programming\n"
                "- Machine Learning\n"
                "- Vector Databases\n"
                "- A2A Protocol\n"
                "- ChromaDB\n\n"
                "**📷 Image Captioning** (via Image Caption Agent):\n"
                "- Caption images by providing file paths\n"
                "- Example: 'caption: /path/to/image.jpg'\n"
                "- Example: '/Users/username/Pictures/photo.png'\n\n"
                "Try asking:\n"
                "- 'What is Python?'\n"
                "- 'caption: /path/to/your/image.jpg'"
            )
            yield {'content': response, 'done': False}
            yield {'content': '', 'done': True}
    
    async def cleanup(self):
        """Cleanup resources."""
        if self.httpx_client:
            print("[DEBUG] Closing httpx client")
            await self.httpx_client.aclose()

