"""Agent Executor for the Iris Classifier Agent."""
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
from src.agents.iris_classifier.agent import IrisClassifierAgent
from src.utils.config_loader import ConfigLoader


class IrisClassifierAgentExecutor(AgentExecutor):
    """Executor for the Iris Classifier Agent."""
    
    def __init__(self, config: dict | None = None):
        """Initialize the executor with the Iris Classifier agent.
        
        Args:
            config: Optional configuration dictionary. If None, loads from config file.
        """
        print("[DEBUG] Initializing IrisClassifierAgentExecutor")
        
        # Load configuration
        if config is None:
            config_loader = ConfigLoader()
            try:
                agent_config = config_loader.load_agent_config("iris_classifier")
                config = agent_config.agent_config
            except Exception as e:
                print(f"[DEBUG] Warning: Could not load config, using defaults: {e}")
                config = {}
        
        # Initialize agent with config
        model_path = config.get("model_path", "./models/iris_rf_model.pkl")
        n_estimators = config.get("n_estimators", 100)
        random_state = config.get("random_state", 42)
        
        self.agent = IrisClassifierAgent(
            model_path=model_path,
            n_estimators=n_estimators,
            random_state=random_state,
        )
        
        print("[DEBUG] IrisClassifierAgentExecutor ready")
    
    @override
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Execute the Iris Classifier agent with the given context.
        
        Args:
            context: Request context containing the user query
            event_queue: Queue for sending events back to the client
        """
        print(f"[DEBUG] IrisClassifierExecutor.execute() called")
        print(f"[DEBUG] Context ID: {context.context_id}")
        print(f"[DEBUG] Task ID: {context.task_id}")
        
        query = context.get_user_input()
        print(f"[DEBUG] User query: '{query}'")
        
        if not context.message:
            print("[DEBUG] ERROR: No message provided in context")
            raise Exception('No message provided')
        
        # Stream response from agent
        print("[DEBUG] Starting to stream response from Iris Classifier agent")
        async for event in self.agent.stream_response(query):
            print(f"[DEBUG] Streaming chunk: done={event['done']}, content_length={len(event['content'])}")
            
            # Create artifact update event
            message = TaskArtifactUpdateEvent(
                context_id=context.context_id,  # type: ignore
                task_id=context.task_id,  # type: ignore
                artifact=new_text_artifact(
                    name='iris_classification_result',
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
        print("[DEBUG] IrisClassifierExecutor.execute() finished")
    
    @override
    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        """Cancel the current task (not supported)."""
        print("[DEBUG] IrisClassifierExecutor.cancel() called - not supported")
        raise Exception('cancel not supported')

