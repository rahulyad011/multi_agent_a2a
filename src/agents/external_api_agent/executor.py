"""Agent Executor for the External API Agent."""
from typing import override

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import (
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
)
from a2a.utils import new_text_artifact
from src.agents.external_api_agent.agent import ExternalAPIAgent
from src.utils.config_loader import ConfigLoader


class ExternalAPIAgentExecutor(AgentExecutor):
    """Executor for the External API Agent.
    
    This executor bridges the ExternalAPIAgent with the A2A protocol.
    It handles:
    - Extracting user input from A2A context
    - Calling the agent's stream_response method
    - Streaming responses back via A2A event queue
    - Managing task lifecycle
    """
    
    def __init__(self, config: dict | None = None):
        """Initialize the executor with the external API agent.
        
        Args:
            config: Optional configuration dictionary. If None, loads from config file.
        """
        print("[DEBUG] Initializing ExternalAPIAgentExecutor")
        
        # Load configuration
        if config is None:
            config_loader = ConfigLoader()
            try:
                agent_config = config_loader.load_agent_config("external_api_agent")
                config = agent_config.agent_config
            except Exception as e:
                print(f"[DEBUG] Warning: Could not load config, using defaults: {e}")
                config = {}
        
        # Initialize agent with config
        self.agent = ExternalAPIAgent(config)
        
        print("[DEBUG] ExternalAPIAgentExecutor ready")
    
    @override
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Execute the external API agent with the given context.
        
        This method:
        1. Extracts user input from A2A context
        2. Calls agent's stream_response method
        3. Streams responses back via A2A event queue
        4. Sends completion status
        
        Args:
            context: Request context containing the user query
            event_queue: Queue for sending events back to the client
        """
        print(f"[DEBUG] ExternalAPIAgentExecutor.execute() called")
        print(f"[DEBUG] Context ID: {context.context_id}")
        print(f"[DEBUG] Task ID: {context.task_id}")
        
        # Extract user input from A2A context
        query = context.get_user_input()
        print(f"[DEBUG] User query: '{query}'")
        
        if not context.message:
            print("[DEBUG] ERROR: No message provided in context")
            raise Exception('No message provided')
        
        # Stream response from agent
        print("[DEBUG] Starting to stream response from External API agent")
        async for event in self.agent.stream_response(query):
            print(f"[DEBUG] Streaming chunk: done={event['done']}, content_length={len(event['content'])}")
            
            # Create artifact update event for A2A protocol
            message = TaskArtifactUpdateEvent(
                context_id=context.context_id,  # type: ignore
                task_id=context.task_id,  # type: ignore
                artifact=new_text_artifact(
                    name='external_api_result',
                    text=event['content'],
                ),
            )
            await event_queue.enqueue_event(message)
            
            if event['done']:
                print("[DEBUG] Streaming complete")
                break
        
        # Send completion status
        print("[DEBUG] Sending task completion status")
        status = TaskStatusUpdateEvent(
            context_id=context.context_id,  # type: ignore
            task_id=context.task_id,  # type: ignore
            status=TaskStatus(state=TaskState.completed),
            final=True,
        )
        await event_queue.enqueue_event(status)
        print("[DEBUG] ExternalAPIAgentExecutor.execute() finished")
    
    @override
    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        """Cancel the current task (not supported)."""
        print("[DEBUG] ExternalAPIAgentExecutor.cancel() called - not supported")
        raise Exception('cancel not supported')
    
    async def cleanup(self):
        """Cleanup resources."""
        if hasattr(self, 'agent'):
            await self.agent.cleanup()

