"""Remote Agent Connection - manages communication with A2A agents."""
import traceback
from collections.abc import Callable

from a2a.client import Client, ClientFactory
from a2a.types import (
    AgentCard,
    Message,
    Task,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatusUpdateEvent,
)


TaskCallbackArg = Task | TaskStatusUpdateEvent | TaskArtifactUpdateEvent
TaskUpdateCallback = Callable[[TaskCallbackArg, AgentCard], Task]


class RemoteAgentConnection:
    """A class to manage connection to a remote A2A agent."""

    def __init__(self, client_factory: ClientFactory, agent_card: AgentCard):
        """Initialize remote agent connection.
        
        Args:
            client_factory: Factory to create A2A clients
            agent_card: The agent card for this remote agent
        """
        print(f"[DEBUG] Creating RemoteAgentConnection for: {agent_card.name}")
        self.agent_client: Client = client_factory.create(agent_card)
        self.card: AgentCard = agent_card
        self.pending_tasks = set()
        print(f"[DEBUG] RemoteAgentConnection ready for: {agent_card.name}")

    def get_agent(self) -> AgentCard:
        """Get the agent card for this connection."""
        return self.card

    async def send_message(self, message: Message) -> Task | Message | None:
        """Send a message to the remote agent and await response.
        
        Args:
            message: The message to send
            
        Returns:
            Task, Message, or None depending on agent response
        """
        print(f"[DEBUG] RemoteAgentConnection sending message to {self.card.name}")
        lastTask: Task | None = None
        
        try:
            async for event in self.agent_client.send_message(message):
                if isinstance(event, Message):
                    print(f"[DEBUG] Received Message from {self.card.name}")
                    return event
                
                if self.is_terminal_or_interrupted(event[0]):
                    print(f"[DEBUG] Received terminal/interrupted task from {self.card.name}")
                    return event[0]
                
                lastTask = event[0]
                
        except Exception as e:
            print(f'[DEBUG] ERROR: Exception in send_message to {self.card.name}')
            traceback.print_exc()
            raise e
        
        return lastTask

    def is_terminal_or_interrupted(self, task: Task) -> bool:
        """Check if task is in a terminal or interrupted state.
        
        Args:
            task: The task to check
            
        Returns:
            True if task is in terminal/interrupted state
        """
        return task.status.state in [
            TaskState.completed,
            TaskState.canceled,
            TaskState.failed,
            TaskState.input_required,
            TaskState.unknown,
        ]

