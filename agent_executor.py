"""Agent Executor for the Simple RAG Agent."""
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
from agent import SimpleRAGAgent


class SimpleRAGAgentExecutor(AgentExecutor):
    """Executor for the Simple RAG Agent."""
    
    def __init__(self):
        """Initialize the executor with the RAG agent."""
        print("[DEBUG] Initializing SimpleRAGAgentExecutor")
        self.agent = SimpleRAGAgent()
        # Initialize with sample documents if empty
        self.agent.initialize_with_sample_docs()
        print("[DEBUG] SimpleRAGAgentExecutor ready")
    
    @override
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Execute the RAG agent with the given context.
        
        Args:
            context: Request context containing the user query
            event_queue: Queue for sending events back to the client
        """
        print(f"[DEBUG] RAGAgentExecutor.execute() called")
        print(f"[DEBUG] Context ID: {context.context_id}")
        print(f"[DEBUG] Task ID: {context.task_id}")
        
        query = context.get_user_input()
        print(f"[DEBUG] User query: '{query}'")
        
        if not context.message:
            print("[DEBUG] ERROR: No message provided in context")
            raise Exception('No message provided')
        
        # Stream response from RAG agent
        print("[DEBUG] Starting to stream response from RAG agent")
        async for event in self.agent.stream_response(query):
            print(f"[DEBUG] Streaming chunk: done={event['done']}, content_length={len(event['content'])}")
            
            # Create artifact update event
            message = TaskArtifactUpdateEvent(
                context_id=context.context_id,  # type: ignore
                task_id=context.task_id,  # type: ignore
                artifact=new_text_artifact(
                    name='rag_result',
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
        print("[DEBUG] RAGAgentExecutor.execute() finished")
    
    @override
    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        """Cancel the current task (not supported)."""
        print("[DEBUG] RAGAgentExecutor.cancel() called - not supported")
        raise Exception('cancel not supported')

