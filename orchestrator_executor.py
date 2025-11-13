"""Executor for the Orchestrator Agent."""
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
from orchestrator_agent import OrchestratorAgent


class OrchestratorAgentExecutor(AgentExecutor):
    """Executor for the Orchestrator Agent."""
    
    def __init__(
        self, 
        rag_agent_url: str = "http://localhost:10002",
        image_caption_agent_url: str = "http://localhost:10004"
    ):
        """Initialize the executor with the orchestrator agent."""
        print("[DEBUG] Initializing OrchestratorAgentExecutor")
        print(f"[DEBUG] RAG Agent URL: {rag_agent_url}")
        print(f"[DEBUG] Image Caption Agent URL: {image_caption_agent_url}")
        self.agent = OrchestratorAgent(
            rag_agent_url=rag_agent_url,
            image_caption_agent_url=image_caption_agent_url
        )
        print("[DEBUG] OrchestratorAgentExecutor ready")
    
    @override
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Execute the orchestrator agent with the given context.
        
        Args:
            context: Request context containing the user query
            event_queue: Queue for sending events back to the client
        """
        print(f"[DEBUG] OrchestratorExecutor.execute() called")
        print(f"[DEBUG] Context ID: {context.context_id}")
        print(f"[DEBUG] Task ID: {context.task_id}")
        
        query = context.get_user_input()
        print(f"[DEBUG] User query: '{query}'")
        
        if not context.message:
            print("[DEBUG] ERROR: No message provided in context")
            raise Exception('No message provided')
        
        # Stream response from orchestrator
        print("[DEBUG] Starting to stream response from orchestrator")
        try:
            async for event in self.agent.stream_response(query):
                print(f"[DEBUG] Orchestrator streaming chunk: done={event['done']}, content_length={len(event['content'])}")
                
                # Create artifact update event
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
                    print("[DEBUG] Orchestrator streaming complete")
                    break
        finally:
            # Cleanup
            await self.agent.cleanup()
        
        # Send completion status
        print("[DEBUG] Sending task completion status")
        status = TaskStatusUpdateEvent(
            context_id=context.context_id,  # type: ignore
            task_id=context.task_id,  # type: ignore
            status=TaskStatus(state=TaskState.completed),
            final=True,
        )
        await event_queue.enqueue_event(status)
        print("[DEBUG] OrchestratorExecutor.execute() finished")
    
    @override
    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        """Cancel the current task (not supported)."""
        print("[DEBUG] OrchestratorExecutor.cancel() called - not supported")
        raise Exception('cancel not supported')

