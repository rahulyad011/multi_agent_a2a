"""Host-style Orchestrator Agent using LiteLLM with LLM-based routing."""
import asyncio
import json
import os
import uuid
from typing import Any, AsyncGenerator, Optional

import httpx
from litellm import acompletion
from a2a.client import A2ACardResolver, ClientConfig, ClientFactory
from a2a.types import (
    AgentCard,
    Message,
    Part,
    Role,
    Task,
    TaskState,
    TextPart,
    TransportProtocol,
)
from src.utils.remote_connection import RemoteAgentConnection


class HostOrchestrator:
    """Host-style orchestrator that uses LLM for intelligent agent routing.
    
    This orchestrator follows the host_agent pattern:
    - Uses LiteLLM for decision making
    - Dynamically discovers remote agents via A2A protocol
    - LLM analyzes query and decides which agent to use
    - Calls appropriate agent via A2A protocol
    """

    def __init__(
        self,
        remote_agent_urls: list[str],
        httpx_client: httpx.AsyncClient | None = None,
        model_name: str | None = None,
        llm_callable=None,
    ):
        """Initialize the host orchestrator.
        
        Args:
            remote_agent_urls: List of URLs for remote A2A agents
            httpx_client: Optional httpx client (will create if None)
            model_name: Optional LLM model name (defaults to gemini-2.0-flash)
            llm_callable: Optional custom LLM callable (e.g., ChatOCIGenAI instance)
                         If provided, this will be used instead of LiteLLM
        """
        print("[DEBUG] Initializing HostOrchestrator")
        print(f"[DEBUG] Remote agent URLs: {remote_agent_urls}")
        
        self.httpx_client = httpx_client or httpx.AsyncClient(timeout=60.0)
        self.own_httpx_client = httpx_client is None  # Track if we created it
        
        # Configure A2A client factory
        config = ClientConfig(
            httpx_client=self.httpx_client,
            supported_transports=[
                TransportProtocol.jsonrpc,
                TransportProtocol.http_json,
            ],
        )
        self.client_factory = ClientFactory(config)
        
        # Remote agent connections
        self.remote_agent_connections: dict[str, RemoteAgentConnection] = {}
        self.cards: dict[str, AgentCard] = {}
        self.agents_info: str = ''
        
        # Model configuration
        self.llm_callable = llm_callable
        self.model_name = model_name or os.getenv('LITELLM_MODEL', 'gemini/gemini-2.0-flash-001')
        
        if self.llm_callable:
            print("[DEBUG] Using custom LLM callable (e.g., OCI GenAI)")
        else:
            print(f"[DEBUG] Using LLM model: {self.model_name}")
        
        # Store URLs for lazy initialization
        self.remote_agent_urls = remote_agent_urls
        self._agents_initialized = False
        
        print("[DEBUG] HostOrchestrator initialized")
        print("[DEBUG] Note: Remote agents will be discovered on first use")

    async def _call_llm(self, messages: list[dict], temperature: float = 0.3, stream: bool = False):
        """Call LLM - either custom callable or LiteLLM.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Temperature for generation
            stream: Whether to stream the response
            
        Returns:
            Response object or async generator
        """
        if self.llm_callable:
            # Use custom LLM (e.g., ChatOCIGenAI)
            # Convert messages format for LangChain
            from langchain_core.messages import HumanMessage, SystemMessage
            
            langchain_messages = []
            for msg in messages:
                if msg['role'] == 'system':
                    langchain_messages.append(SystemMessage(content=msg['content']))
                elif msg['role'] == 'user':
                    langchain_messages.append(HumanMessage(content=msg['content']))
            
            if stream:
                # Return async generator for streaming
                async def stream_response():
                    async for chunk in self.llm_callable.astream(langchain_messages):
                        yield chunk
                return stream_response()
            else:
                # Return single response
                response = await self.llm_callable.ainvoke(langchain_messages)
                # Create a simple response object that matches LiteLLM format
                class SimpleResponse:
                    def __init__(self, content):
                        self.choices = [type('obj', (object,), {'message': type('obj', (object,), {'content': content})()})()]
                
                return SimpleResponse(response.content)
        else:
            # Use LiteLLM
            params = {
                "model": self.model_name,
                "messages": messages,
                "temperature": temperature,
            }
            if stream:
                params["stream"] = True
            return await acompletion(**params)

    async def ensure_agents_initialized(self):
        """Ensure remote agents are initialized (lazy initialization)."""
        if self._agents_initialized:
            return
        
        print(f"[DEBUG] Discovering {len(self.remote_agent_urls)} remote agents...")
        
        async with asyncio.TaskGroup() as task_group:
            for url in self.remote_agent_urls:
                task_group.create_task(self.retrieve_agent_card(url))
        
        self._agents_initialized = True
        print(f"[DEBUG] Agent discovery complete. Found {len(self.cards)} agents")
        print(f"[DEBUG] Available agents: {list(self.cards.keys())}")
    
    async def init_remote_agents(self, remote_agent_urls: list[str]):
        """Initialize connections to remote agents by fetching their agent cards.
        
        Deprecated: Use ensure_agents_initialized() instead.
        
        Args:
            remote_agent_urls: List of URLs for remote agents
        """
        await self.ensure_agents_initialized()

    async def retrieve_agent_card(self, url: str):
        """Retrieve and register an agent card from a remote agent.
        
        Args:
            url: The URL of the remote agent
        """
        print(f"[DEBUG] Fetching agent card from: {url}")
        
        try:
            card_resolver = A2ACardResolver(self.httpx_client, url)
            card = await card_resolver.get_agent_card()
            self.register_agent_card(card)
            print(f"[DEBUG] Successfully registered agent: {card.name}")
        except Exception as e:
            print(f"[DEBUG] ERROR: Failed to fetch agent card from {url}: {e}")
            raise

    def register_agent_card(self, card: AgentCard):
        """Register a remote agent and create connection.
        
        Args:
            card: The agent card to register
        """
        print(f"[DEBUG] Registering agent card: {card.name}")
        
        # Create connection to remote agent
        remote_connection = RemoteAgentConnection(self.client_factory, card)
        self.remote_agent_connections[card.name] = remote_connection
        self.cards[card.name] = card
        
        # Build agents info string for LLM prompt
        agent_info = []
        for agent_card in self.cards.values():
            agent_info.append({
                'name': agent_card.name,
                'description': agent_card.description,
                'skills': [skill.description for skill in agent_card.skills] if agent_card.skills else []
            })
        
        self.agents_info = '\n'.join([json.dumps(info, indent=2) for info in agent_info])
        print(f"[DEBUG] Updated agents info. Total agents: {len(self.cards)}")

    def get_system_prompt(self) -> str:
        """Generate the system prompt for the LLM.
        
        Returns:
            System prompt string
        """
        agents_list = ""
        if self.cards:
            for card in self.cards.values():
                agents_list += f"\n- **{card.name}**: {card.description}"
        else:
            agents_list = "\n(Agents will be discovered on first query)"
        
        return f"""You are an expert orchestrator that intelligently routes user requests to specialized AI agents.

**Available Agents:**{agents_list}

**Your Task:**
Analyze the user's query and determine which agent is most appropriate to handle it.

**Response Format:**
Respond ONLY with a JSON object in this exact format:
{{
    "agent": "agent_name_here",
    "reasoning": "brief explanation"
}}

**Guidelines:**
- For questions about documents, programming, concepts → use "Simple RAG Agent"
- For image captioning or image analysis → use "Image Captioning Agent"
- Choose the agent that best matches the query intent
- If no agent is appropriate, use "none"
"""

    async def route_query(self, query: str, original_message: Optional[Message] = None) -> AsyncGenerator[dict[str, Any], None]:
        """Route a query to the appropriate agent using LLM.
        
        Args:
            query: User query
            original_message: Optional original message with all parts (including images)
            
        Yields:
            Response chunks with 'content' and 'done' keys
        """
        print(f"[DEBUG] Routing query with LLM: '{query}'")
        
        # Ensure agents are discovered
        await self.ensure_agents_initialized()
        
        if not self.remote_agent_connections:
            yield {'content': "⚠️ No agents are available. Please ensure agents are running.", 'done': False}
            yield {'content': '', 'done': True}
            return
        
        try:
            # Call LLM to decide routing
            print("[DEBUG] Calling LLM for routing decision...")
            
            messages = [
                {"role": "system", "content": self.get_system_prompt()},
                {"role": "user", "content": query}
            ]
            
            response = await self._call_llm(messages, temperature=0.3)
            llm_response = response.choices[0].message.content
            print(f"[DEBUG] LLM response: {llm_response}")
            
            # Parse JSON response
            try:
                decision = json.loads(llm_response)
                agent_name = decision.get('agent')
                reasoning = decision.get('reasoning', '')
                
                print(f"[DEBUG] LLM decided: agent='{agent_name}', reasoning='{reasoning}'")
                
            except json.JSONDecodeError:
                print(f"[DEBUG] Failed to parse JSON, trying to extract agent name...")
                # Try to extract agent name from response
                agent_name = None
                for card in self.cards.values():
                    if card.name.lower() in llm_response.lower():
                        agent_name = card.name
                        break
                reasoning = "Extracted from LLM response"
            
            # Route to selected agent
            if agent_name and agent_name != "none" and agent_name in self.remote_agent_connections:
                print(f"[DEBUG] ===== ROUTING TO {agent_name} VIA A2A =====")
                
                # Send message to agent (forward original message if available)
                async for chunk in self._send_to_agent(agent_name, query, original_message=original_message):
                    yield chunk
            else:
                print("[DEBUG] No appropriate agent found or LLM chose 'none'")
                response_msg = (
                    f"I analyzed your query but couldn't determine an appropriate agent to handle it.\n\n"
                    f"Available agents:\n"
                )
                for card in self.cards.values():
                    response_msg += f"- **{card.name}**: {card.description}\n"
                
                response_msg += f"\nPlease try rephrasing your question or specify what you'd like help with."
                
                yield {'content': response_msg, 'done': False}
                yield {'content': '', 'done': True}
                
        except Exception as e:
            print(f"[DEBUG] ERROR in route_query: {e}")
            import traceback
            traceback.print_exc()
            
            error_msg = f"Error routing query: {str(e)}"
            yield {'content': error_msg, 'done': False}
            yield {'content': '', 'done': True}
    
    async def _send_to_agent(self, agent_name: str, query: str, original_message: Optional[Message] = None) -> AsyncGenerator[dict[str, Any], None]:
        """Send a query to a specific agent, collect response, and use LLM to summarize.
        
        Args:
            agent_name: Name of the target agent
            query: Query to send
            original_message: Optional original message with all parts (to preserve images, etc.)
            
        Yields:
            Response chunks (LLM-summarized)
        """
        print(f"[DEBUG] Sending to agent: {agent_name}")
        
        # Get client connection
        client = self.remote_agent_connections[agent_name]
        
        # Create A2A message - use original message parts if available, otherwise create new
        message_id = str(uuid.uuid4())
        if original_message and original_message.parts:
            # Forward all parts from original message (preserves images, etc.)
            print(f"[DEBUG] Forwarding original message with {len(original_message.parts)} parts")
            request_message = Message(
                role=Role.user,
                parts=original_message.parts,  # Forward all parts
                message_id=message_id,
            )
        else:
            # Create new message with just text
            print("[DEBUG] Creating new message with text only")
            request_message = Message(
                role=Role.user,
                parts=[Part(root=TextPart(text=query))],
                message_id=message_id,
            )
        
        print(f"[DEBUG] Sending A2A message (ID: {message_id})...")
        
        # Collect full response from remote agent
        collected_response = []
        artifacts_processed = 0
        
        # Get the A2A client and send message with streaming
        try:
            chunk_count = 0
            async for event in client.agent_client.send_message(request_message):
                chunk_count += 1
                
                # Handle Message response
                if isinstance(event, Message):
                    print(f"[DEBUG] Received Message response (chunk {chunk_count})")
                    for part in event.parts:
                        if part.root.kind == 'text':
                            collected_response.append(part.root.text)
                    continue
                
                # Handle Task or Event tuple
                if isinstance(event, tuple):
                    task, event_type = event
                else:
                    task = event
                
                print(f"[DEBUG] Received event {chunk_count}, task state: {task.status.state}, artifacts: {len(task.artifacts) if task.artifacts else 0}")
                
                # Extract and collect only NEW artifacts
                if task.artifacts:
                    total_artifacts = len(task.artifacts)
                    
                    # Only process artifacts we haven't seen yet
                    for idx in range(artifacts_processed, total_artifacts):
                        artifact = task.artifacts[idx]
                        artifact_name = artifact.name if hasattr(artifact, 'name') and artifact.name else 'default'
                        
                        print(f"[DEBUG] Collecting NEW artifact {idx + 1}/{total_artifacts} ('{artifact_name}')")
                        
                        for part in artifact.parts:
                            if part.root.kind == 'text' and part.root.text:
                                text = part.root.text
                                print(f"[DEBUG] Artifact {idx + 1}: Collected {len(text)} chars")
                                collected_response.append(text)
                    
                    # Update our count of processed artifacts
                    artifacts_processed = total_artifacts
                
                # Check if task is complete
                if task.status.state in [TaskState.completed, TaskState.failed, TaskState.canceled]:
                    print(f"[DEBUG] Task reached terminal state: {task.status.state}")
                    break
            
            print(f"[DEBUG] Received {chunk_count} events from {agent_name}")
            print(f"[DEBUG] Total artifacts collected: {artifacts_processed}")
            
            # Combine all collected response parts
            full_response = ''.join(collected_response)
            print(f"[DEBUG] Total response text: {len(full_response)} chars")
            
            # Use LLM to summarize/improve the response
            print(f"[DEBUG] Sending response to LLM for summarization...")
            async for chunk in self._summarize_with_llm(query, full_response, agent_name):
                yield chunk
            
            print(f"[DEBUG] ===== A2A CALL TO {agent_name} COMPLETE =====")
            
        except Exception as e:
            print(f"[DEBUG] ERROR in _send_to_agent: {e}")
            import traceback
            traceback.print_exc()
            yield {'content': f"\n\nError communicating with {agent_name}: {str(e)}", 'done': False}
            yield {'content': '', 'done': True}
    
    async def _summarize_with_llm(self, query: str, agent_response: str, agent_name: str) -> AsyncGenerator[dict[str, Any], None]:
        """Use LLM to summarize and improve the agent's response.
        
        Args:
            query: Original user query
            agent_response: Response from the remote agent
            agent_name: Name of the agent that provided the response
            
        Yields:
            Streaming response chunks from LLM
        """
        print(f"[DEBUG] Starting LLM summarization for {agent_name} response...")
        
        # Create prompt for LLM to summarize
        system_prompt = """You are an intelligent assistant that helps present information from specialized agents in a clear and concise way.

Your task:
1. Read the agent's response carefully
2. Present the key information in a well-formatted, easy-to-read manner
3. Maintain accuracy - don't add information not in the agent's response
4. Make the response conversational and helpful
5. If the agent returned multiple documents or results, organize them clearly

Keep your response focused and relevant to the user's query."""

        user_prompt = f"""User Query: {query}

Agent Response from {agent_name}:
{agent_response}

Please provide a clear, well-formatted summary of this information that directly answers the user's query."""

        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            # Stream LLM response
            print(f"[DEBUG] Streaming LLM summarization...")
            
            response = await self._call_llm(messages, temperature=0.7, stream=True)
            
            if self.llm_callable:
                # Custom LLM streaming (LangChain format)
                async for chunk in response:
                    content = chunk.content if hasattr(chunk, 'content') else str(chunk)
                    if content:
                        print(f"[DEBUG] LLM chunk: {len(content)} chars")
                        yield {'content': content, 'done': False}
            else:
                # LiteLLM streaming
                async for chunk in response:
                    if chunk.choices and len(chunk.choices) > 0:
                        delta_content = chunk.choices[0].delta.content
                        if delta_content:
                            print(f"[DEBUG] LLM chunk: {len(delta_content)} chars")
                            yield {'content': delta_content, 'done': False}
            
            # Send final done signal
            yield {'content': '', 'done': True}
            print(f"[DEBUG] LLM summarization complete")
            
        except Exception as e:
            print(f"[DEBUG] ERROR in LLM summarization: {e}")
            import traceback
            traceback.print_exc()
            
            # Fall back to original response if LLM fails
            print(f"[DEBUG] Falling back to original agent response")
            yield {'content': agent_response, 'done': False}
            yield {'content': '', 'done': True}

    async def cleanup(self):
        """Cleanup resources."""
        print("[DEBUG] Cleaning up HostOrchestrator")
        
        if self.own_httpx_client and self.httpx_client:
            print("[DEBUG] Closing httpx client")
            await self.httpx_client.aclose()

