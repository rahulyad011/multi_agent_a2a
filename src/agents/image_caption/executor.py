"""Agent Executor for the Image Captioning Agent."""
from typing import override
import base64
import io

from PIL import Image
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import (
    DataPart,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
)
from a2a.utils import new_text_artifact
from src.agents.image_caption.agent import ImageCaptioningAgent


class ImageCaptioningAgentExecutor(AgentExecutor):
    """Executor for the Image Captioning Agent."""
    
    def __init__(self):
        """Initialize the executor with the image captioning agent."""
        print("[DEBUG] Initializing ImageCaptioningAgentExecutor")
        self.agent = ImageCaptioningAgent()
        print("[DEBUG] ImageCaptioningAgentExecutor ready")
    
    @override
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Execute the image captioning agent with the given context.
        
        Args:
            context: Request context containing the user query
            event_queue: Queue for sending events back to the client
        """
        print(f"[DEBUG] ImageCaptionExecutor.execute() called")
        print(f"[DEBUG] Context ID: {context.context_id}")
        print(f"[DEBUG] Task ID: {context.task_id}")
        
        query = context.get_user_input()
        print(f"[DEBUG] User query: '{query}'")
        
        if not context.message:
            print("[DEBUG] ERROR: No message provided in context")
            raise Exception('No message provided')
        
        # Extract image from message parts if available
        image = None
        if context.message and context.message.parts:
            print(f"[DEBUG] Checking {len(context.message.parts)} message parts for image data")
            for i, part in enumerate(context.message.parts):
                try:
                    # Handle Part object with root attribute
                    if hasattr(part, 'root'):
                        part_root = part.root
                        print(f"[DEBUG] Part {i}: has root, type={type(part_root).__name__}")
                    else:
                        part_root = part
                        print(f"[DEBUG] Part {i}: no root, type={type(part_root).__name__}")
                    
                    # Check if this is a DataPart with image data
                    if isinstance(part_root, DataPart):
                        print(f"[DEBUG] Part {i} is DataPart, data type={type(part_root.data).__name__}")
                        if part_root.data:
                            data_obj = part_root.data
                            
                            # Handle dictionary format: {"mime_type": "image/png", "data": base64_string}
                            if isinstance(data_obj, dict):
                                print(f"[DEBUG] DataPart.data is dict, keys={list(data_obj.keys())}")
                                base64_data = data_obj.get('data')
                                mime_type = data_obj.get('mime_type', 'image/png')
                                if base64_data:
                                    print(f"[DEBUG] Decoding base64 image data (length: {len(base64_data)})")
                                    image_bytes = base64.b64decode(base64_data)
                                    image = Image.open(io.BytesIO(image_bytes))
                                    print(f"[DEBUG] Successfully extracted image from DataPart (dict format), size={image.size}")
                                    break  # Found image, no need to check other parts
                            
                            # Handle string format (data URI)
                            elif isinstance(data_obj, str) and data_obj.startswith('data:image'):
                                print(f"[DEBUG] DataPart.data is data URI")
                                # Extract base64 part from data URI
                                base64_data = data_obj.split(',')[1]
                                image_bytes = base64.b64decode(base64_data)
                                image = Image.open(io.BytesIO(image_bytes))
                                print(f"[DEBUG] Successfully extracted image from DataPart (data URI), size={image.size}")
                                break  # Found image, no need to check other parts
                            else:
                                print(f"[DEBUG] DataPart.data is not dict or data URI, type={type(data_obj).__name__}")
                    else:
                        print(f"[DEBUG] Part {i} is not DataPart, type={type(part_root).__name__}")
                    
                    # Fallback: Check for image data in various formats
                    image_data = None
                    
                    # Check if part_root has image attribute
                    if hasattr(part_root, 'image'):
                        image_data = part_root.image
                    # Check if part_root has data attribute
                    elif hasattr(part_root, 'data'):
                        image_data = part_root.data
                    # Check if part_root is a dict with image/data key
                    elif isinstance(part_root, dict):
                        image_data = part_root.get('image') or part_root.get('data')
                    # Check if part itself is a dict
                    elif isinstance(part, dict):
                        image_data = part.get('image') or part.get('data')
                    
                    if image_data:
                        # Image data might be base64 encoded string
                        if isinstance(image_data, str):
                            # Check if it's a data URI
                            if image_data.startswith('data:image'):
                                # Extract base64 part from data URI
                                base64_data = image_data.split(',')[1]
                                image_bytes = base64.b64decode(base64_data)
                            else:
                                # Assume it's base64 encoded
                                image_bytes = base64.b64decode(image_data)
                            image = Image.open(io.BytesIO(image_bytes))
                            print("[DEBUG] Extracted image from message part (base64)")
                            break  # Found image, no need to check other parts
                        elif isinstance(image_data, bytes):
                            image = Image.open(io.BytesIO(image_data))
                            print("[DEBUG] Extracted image bytes from message part")
                            break  # Found image, no need to check other parts
                        
                except Exception as e:
                    print(f"[DEBUG] Warning: Could not extract image from part: {e}")
                    import traceback
                    traceback.print_exc()
                    # Continue to next part
                    continue
        
        # Log image extraction result
        if image:
            print(f"[DEBUG] Image successfully extracted: size={image.size}, mode={image.mode}")
        else:
            print("[DEBUG] No image found in message parts - will try to extract from query text")
        
        # Stream response from image captioning agent
        print("[DEBUG] Starting to stream response from image captioning agent")
        async for event in self.agent.stream_response(query, image=image):
            print(f"[DEBUG] Streaming chunk: done={event['done']}, content_length={len(event['content'])}")
            
            # Create artifact update event
            message = TaskArtifactUpdateEvent(
                context_id=context.context_id,  # type: ignore
                task_id=context.task_id,  # type: ignore
                artifact=new_text_artifact(
                    name='image_caption_result',
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
        print("[DEBUG] ImageCaptionExecutor.execute() finished")
    
    @override
    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        """Cancel the current task (not supported)."""
        print("[DEBUG] ImageCaptionExecutor.cancel() called - not supported")
        raise Exception('cancel not supported')

