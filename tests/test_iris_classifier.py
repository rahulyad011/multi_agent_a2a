"""Test script for Iris Classifier Agent via Orchestrator."""
import asyncio
import json
from uuid import uuid4

import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    Message,
    MessageSendParams,
    Part,
    Role,
    SendStreamingMessageRequest,
    TextPart,
)


async def test_iris_classifier_via_orchestrator():
    """Test Iris Classifier Agent through the Orchestrator."""
    
    orchestrator_url = "http://localhost:10003"
    
    print("=" * 60)
    print("Iris Classifier Agent - Orchestrator Test")
    print("=" * 60)
    print()
    
    # Test queries
    test_queries = [
        # JSON format
        '{"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}',
        '{"sepal_length": 7.0, "sepal_width": 3.2, "petal_length": 4.7, "petal_width": 1.4}',
        '{"sepal_length": 6.3, "sepal_width": 3.3, "petal_length": 6.0, "petal_width": 2.5}',
        # List format
        "[5.1, 3.5, 1.4, 0.2]",
        "[7.0, 3.2, 4.7, 1.4]",
        # Space-separated
        "5.1 3.5 1.4 0.2",
        "6.3 3.3 6.0 2.5",
    ]
    
    print(f"Connecting to orchestrator at {orchestrator_url}...")
    
    try:
        # Create HTTP client
        httpx_client = httpx.AsyncClient(timeout=60.0)
        
        # Fetch orchestrator agent card
        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url=orchestrator_url,
        )
        agent_card = await resolver.get_agent_card()
        
        print(f"✓ Connected to: {agent_card.name}")
        print(f"  Description: {agent_card.description}")
        print()
        
        # Create A2A client
        client = A2AClient(
            httpx_client=httpx_client,
            agent_card=agent_card
        )
        
        # Run test queries
        print("=" * 60)
        print("Running Test Queries")
        print("=" * 60)
        print()
        
        for i, query in enumerate(test_queries, 1):
            print(f"Test {i}/{len(test_queries)}: {query[:50]}...")
            print("-" * 60)
            
            try:
                # Create message
                message = Message(
                    role=Role.user,
                    parts=[Part(root=TextPart(text=query))],
                    message_id=uuid4().hex,
                )
                
                send_message_payload = MessageSendParams(
                    id=uuid4().hex,
                    message=message
                )
                
                streaming_request = SendStreamingMessageRequest(
                    id=uuid4().hex,
                    params=send_message_payload
                )
                
                # Stream response
                stream_response = client.send_message_streaming(streaming_request)
                
                full_response = ""
                async for chunk in stream_response:
                    try:
                        data = chunk.model_dump(mode='json', exclude_none=True)
                        if 'result' in data and 'artifact' in data['result']:
                            artifact = data['result']['artifact']
                            if 'parts' in artifact and artifact['parts']:
                                text = artifact['parts'][0].get('text', '')
                                if text:
                                    full_response += text
                                    print(text, end='', flush=True)
                    except Exception as e:
                        # Skip chunks that don't have the expected structure
                        continue
                
                print()
                print()
                
                # Check if response contains iris classification result
                if "Iris" in full_response or "setosa" in full_response.lower() or "versicolor" in full_response.lower() or "virginica" in full_response.lower():
                    print("✓ SUCCESS: Iris Classifier Agent responded correctly")
                elif "couldn't determine" in full_response.lower() or "no appropriate agent" in full_response.lower():
                    print("✗ FAILED: Orchestrator did not route to Iris Classifier Agent")
                else:
                    print("? UNKNOWN: Response received but unclear if from Iris Classifier")
                
            except Exception as e:
                print(f"✗ ERROR: {e}")
                import traceback
                traceback.print_exc()
            
            print()
            print("=" * 60)
            print()
        
        # Close client
        await httpx_client.aclose()
        
        print("Test completed!")
        
    except httpx.ConnectError:
        print(f"✗ ERROR: Could not connect to orchestrator at {orchestrator_url}")
        print("  Make sure the orchestrator is running:")
        print("    uv run python src/agents/orchestrator/main_host.py")
    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    print()
    print("⚠️  Make sure all agents are running before running this test!")
    print("   bash scripts/start_agents.sh")
    print()
    input("Press Enter to continue...")
    print()
    
    asyncio.run(test_iris_classifier_via_orchestrator())

