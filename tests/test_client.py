"""Test client to interact with the Orchestrator Agent."""
import asyncio
from typing import Any
from uuid import uuid4

import httpx

from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    MessageSendParams,
    SendStreamingMessageRequest,
)


def print_welcome_message() -> None:
    """Print welcome message."""
    print("=" * 70)
    print("Welcome to the Multi-Agent Orchestrator Demo!")
    print("=" * 70)
    print("\nThis demo shows A2A protocol in action:")
    print("1. You interact with the Orchestrator Agent (port 10003)")
    print("2. The Orchestrator routes to specialized agents via A2A:")
    print("   • RAG Agent (port 10002) - Document search")
    print("   • Image Caption Agent (port 10004) - Image analysis")
    print("\n📚 Document Search Queries:")
    print("  - 'What is Python?'")
    print("  - 'Tell me about machine learning'")
    print("  - 'Explain the A2A protocol'")
    print("  - 'What is ChromaDB?'")
    print("\n📷 Image Captioning Queries:")
    print("  - 'caption: /absolute/path/to/your/image.jpg'")
    print("  - '/Users/username/Pictures/photo.png'")
    print("  - 'describe image: ~/Downloads/sunset.jpg'")
    print("\nℹ️  General:")
    print("  - 'What can you do?'")
    print("\nType 'exit' to quit.\n")
    print("=" * 70)


def get_user_query() -> str:
    """Get user input."""
    return input('\n> ')


async def interact_with_orchestrator(client: A2AClient) -> None:
    """Interact with the orchestrator agent.
    
    Args:
        client: The A2A client connected to orchestrator
    """
    while True:
        user_input = get_user_query()
        if user_input.lower() == 'exit':
            print('\nGoodbye!')
            break
        
        if not user_input.strip():
            continue
        
        print("\n[CLIENT DEBUG] Sending query to Orchestrator Agent...")
        
        # Create message payload
        send_message_payload: dict[str, Any] = {
            'message': {
                'role': 'user',
                'parts': [{'type': 'text', 'text': user_input}],
                'messageId': uuid4().hex,
            },
        }
        
        try:
            # Create streaming request
            streaming_request = SendStreamingMessageRequest(
                id=uuid4().hex,
                params=MessageSendParams(**send_message_payload)
            )
            
            print("[CLIENT DEBUG] Receiving streaming response...")
            
            # Stream response
            stream_response = client.send_message_streaming(streaming_request)
            
            print("\n--- Response ---")
            chunk_count = 0
            async for chunk in stream_response:
                chunk_count += 1
                text = get_response_text(chunk)
                if text:
                    print(text, end='', flush=True)
                await asyncio.sleep(0.01)  # Small delay for better output
            
            print(f"\n[CLIENT DEBUG] Received {chunk_count} chunks")
            print("--- End Response ---")
            
        except Exception as e:
            print(f'\n[ERROR] An error occurred: {e}')
            import traceback
            traceback.print_exc()


def get_response_text(chunk) -> str:
    """Extract text from response chunk.
    
    Args:
        chunk: Response chunk from A2A client
        
    Returns:
        Extracted text content
    """
    try:
        data = chunk.model_dump(mode='json', exclude_none=True)
        if 'result' in data and 'artifact' in data['result']:
            artifact = data['result']['artifact']
            if 'parts' in artifact and artifact['parts']:
                return artifact['parts'][0].get('text', '')
    except Exception as e:
        print(f"[CLIENT DEBUG] Error extracting text: {e}")
    return ''


async def main() -> None:
    """Main entry point."""
    print_welcome_message()
    
    orchestrator_url = 'http://localhost:10003'
    
    print(f"[CLIENT DEBUG] Connecting to Orchestrator at {orchestrator_url}")
    
    async with httpx.AsyncClient(timeout=60.0) as httpx_client:
        try:
            # Fetch the orchestrator agent card
            print("[CLIENT DEBUG] Fetching agent card...")
            resolver = A2ACardResolver(
                httpx_client=httpx_client,
                base_url=orchestrator_url,
            )
            agent_card = await resolver.get_agent_card()
            print(f"[CLIENT DEBUG] Connected to: {agent_card.name}")
            print(f"[CLIENT DEBUG] Description: {agent_card.description}")
            
            # Create the A2A client
            client = A2AClient(
                httpx_client=httpx_client, agent_card=agent_card
            )
            
            # Start interaction loop
            await interact_with_orchestrator(client)
            
        except httpx.ConnectError:
            print(f"\n[ERROR] Could not connect to orchestrator at {orchestrator_url}")
            print("Make sure the orchestrator is running:")
            print("  uv run orchestrator_main.py")
        except Exception as e:
            print(f"\n[ERROR] Failed to initialize client: {e}")
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(main())

