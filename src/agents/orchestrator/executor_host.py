"""Executor for Host-style Orchestrator using LiteLLM."""
from typing import override
import httpx

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import (
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
)
from a2a.utils import new_text_artifact
from src.agents.orchestrator.agent_host import HostOrchestrator


class HostOrchestratorExecutor(AgentExecutor):
    """Executor for Host-style Orchestrator using LiteLLM for intelligent routing."""
    
    def __init__(
        self,
        remote_agent_urls: list[str],
        model_name: str | None = None,
        llm_callable=None,
    ):
        """Initialize the executor with the host orchestrator.
        
        Args:
            remote_agent_urls: List of URLs for remote A2A agents
            model_name: Optional LLM model name
            llm_callable: Optional custom LLM callable (e.g., ChatOCIGenAI instance)
        """
        print("[DEBUG] Initializing HostOrchestratorExecutor")
        print(f"[DEBUG] Remote agent URLs: {remote_agent_urls}")
        
        # Create shared httpx client
        self.httpx_client = httpx.AsyncClient(timeout=60.0)
        
        # Create host orchestrator
        self.host = HostOrchestrator(
            remote_agent_urls=remote_agent_urls,
            httpx_client=self.httpx_client,
            model_name=model_name,
            llm_callable=llm_callable,
        )
        
        print("[DEBUG] HostOrchestratorExecutor initialized")
        print("[DEBUG] Note: Remote agents will be discovered on first query")
    
    @override
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Execute the host orchestrator with the given context.
        
        This method:
        1. Gets the user query
        2. Uses LiteLLM to decide which remote agent to call
        3. Calls the selected agent via A2A protocol
        4. Streams responses back to the client
        
        Args:
            context: Request context containing the user query
            event_queue: Queue for sending events back to the client
        """
        print(f"[DEBUG] HostOrchestratorExecutor.execute() called")
        print(f"[DEBUG] Context ID: {context.context_id}")
        print(f"[DEBUG] Task ID: {context.task_id}")
        
        query = context.get_user_input()
        print(f"[DEBUG] User query: '{query}'")
        
        if not context.message:
            print("[DEBUG] ERROR: No message provided in context")
            raise Exception('No message provided')
        
        print("[DEBUG] Starting LLM-based routing")
        
        try:
            # Use host orchestrator to route query with LLM
            # Pass the original message to preserve image parts
            print("[DEBUG] Calling host.route_query()...")
            original_message = context.message if context.message else None
            
            async for event in self.host.route_query(query, original_message=original_message):
                print(f"[DEBUG] Streaming chunk: done={event['done']}, content_length={len(event['content'])}")
                
                # Stream to client
                message = TaskArtifactUpdateEvent(
                    context_id=context.context_id,  # type: ignore
                    task_id=context.task_id,  # type: ignore
                    artifact=new_text_artifact(
                        name='orchestrator_result',
                        text=event['content'],
                    ),
                )
                await event_queue.enqueue_event(message)
                
                if event['done']:
                    print("[DEBUG] Routing and execution complete")
                    break
        
        except Exception as e:
            print(f"[DEBUG] ERROR: Exception in execution: {e}")
            import traceback
            traceback.print_exc()
            
            error_msg = f"\n\n❌ Error: {str(e)}\n\nPlease try again or rephrase your request."
            
            message = TaskArtifactUpdateEvent(
                context_id=context.context_id,  # type: ignore
                task_id=context.task_id,  # type: ignore
                artifact=new_text_artifact(
                    name='orchestrator_result',
                    text=error_msg,
                ),
            )
            await event_queue.enqueue_event(message)
        
        # Send completion status
        print("[DEBUG] Sending task completion status")
        status = TaskStatusUpdateEvent(
            context_id=context.context_id,  # type: ignore
            task_id=context.task_id,  # type: ignore
            status=TaskStatus(state=TaskState.completed),
            final=True,
        )
        await event_queue.enqueue_event(status)
        print("[DEBUG] HostOrchestratorExecutor.execute() finished")
    
    @override
    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        """Cancel the current task (not supported)."""
        print("[DEBUG] HostOrchestratorExecutor.cancel() called - not supported")
        raise Exception('cancel not supported')
    
    async def cleanup(self):
        """Cleanup resources."""
        print("[DEBUG] Cleaning up HostOrchestratorExecutor")
        await self.host.cleanup()
        if self.httpx_client:
            await self.httpx_client.aclose()

