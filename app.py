"""Streamlit app for testing the Multi-Agent Orchestrator system."""
import asyncio
import base64
import io
from typing import Any, Optional
from uuid import uuid4

import httpx
import streamlit as st
from PIL import Image
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    DataPart,
    Message,
    MessageSendParams,
    Part,
    Role,
    SendStreamingMessageRequest,
    TextPart,
)


# Helper function to run async code in Streamlit
def run_async(coro):
    """Run an async coroutine in a way that works with Streamlit.
    
    This function properly manages the event loop to avoid
    "Event loop is closed" errors in Streamlit. It uses the
    persistent event loop stored in session state to ensure
    all async operations use the same loop.
    
    Args:
        coro: The coroutine to run
        
    Returns:
        The result of the coroutine
    """
    # Use the persistent event loop from session state
    if 'event_loop' in st.session_state:
        loop = st.session_state.event_loop
    else:
        # Fallback: get or create a loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        st.session_state.event_loop = loop
    
    # Make sure this loop is set as the current event loop
    asyncio.set_event_loop(loop)
    
    # Run the coroutine and return the result
    return loop.run_until_complete(coro)


# Page configuration
st.set_page_config(
    page_title="Multi-Agent A2A Demo",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .agent-card {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f0f2f6;
        margin: 1rem 0;
    }
    .status-connected {
        color: #28a745;
        font-weight: bold;
    }
    .status-disconnected {
        color: #dc3545;
        font-weight: bold;
    }
    .example-query {
        background-color: #e7f3ff;
        padding: 0.5rem;
        border-radius: 0.3rem;
        margin: 0.3rem 0;
        cursor: pointer;
    }
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    </style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    # Initialize event loop FIRST, before anything else
    if 'event_loop' not in st.session_state:
        # Create and store a persistent event loop for the session
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        st.session_state.event_loop = loop
    
    # Make sure the stored loop is set as current
    asyncio.set_event_loop(st.session_state.event_loop)
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'connected' not in st.session_state:
        st.session_state.connected = False
    if 'agent_card' not in st.session_state:
        st.session_state.agent_card = None
    if 'client' not in st.session_state:
        st.session_state.client = None
    if 'httpx_client' not in st.session_state:
        st.session_state.httpx_client = None
    if 'show_debug' not in st.session_state:
        st.session_state.show_debug = False
    if 'uploaded_image' not in st.session_state:
        st.session_state.uploaded_image = None
    if 'uploader_key' not in st.session_state:
        st.session_state.uploader_key = 0


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
        if st.session_state.show_debug:
            st.error(f"Error extracting text: {e}")
    return ''


async def connect_to_orchestrator(orchestrator_url: str) -> tuple[bool, Optional[str]]:
    """Connect to the orchestrator agent.
    
    Args:
        orchestrator_url: URL of the orchestrator agent
        
    Returns:
        Tuple of (success, error_message)
    """
    try:
        # Create httpx client
        httpx_client = httpx.AsyncClient(timeout=60.0)
        st.session_state.httpx_client = httpx_client
        
        # Fetch the orchestrator agent card
        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url=orchestrator_url,
        )
        agent_card = await resolver.get_agent_card()
        st.session_state.agent_card = agent_card
        
        # Create the A2A client
        client = A2AClient(
            httpx_client=httpx_client,
            agent_card=agent_card
        )
        st.session_state.client = client
        st.session_state.connected = True
        
        return True, None
        
    except httpx.ConnectError:
        return False, f"Could not connect to orchestrator at {orchestrator_url}"
    except Exception as e:
        return False, f"Failed to initialize client: {str(e)}"


async def send_query(query: str, image: Image.Image | None = None) -> str:
    """Send a query to the orchestrator and return the response.
    
    Args:
        query: User query text
        image: Optional PIL Image object to send with the query
        
    Returns:
        Response text from the agent
    """
    if not st.session_state.client:
        return "Error: Not connected to orchestrator"
    
    try:
        # Build message parts using proper A2A types
        parts = [Part(root=TextPart(text=query))]
        
        # Add image if provided
        if image is not None:
            # Convert image to base64
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            image_bytes = buffer.getvalue()
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            
            # DataPart.data expects a dictionary with mime_type and data
            data_dict = {
                "mime_type": "image/png",
                "data": image_base64
            }
            
            # Add image part using DataPart
            parts.append(Part(root=DataPart(data=data_dict)))
        
        # Create message payload using proper A2A types
        message = Message(
            role=Role.user,
            parts=parts,
            message_id=uuid4().hex,
        )
        
        send_message_payload = MessageSendParams(
            id=uuid4().hex,
            message=message
        )
        
        # Create streaming request
        streaming_request = SendStreamingMessageRequest(
            id=uuid4().hex,
            params=send_message_payload
        )
        
        # Stream response
        stream_response = st.session_state.client.send_message_streaming(streaming_request)
        
        full_response = ""
        async for chunk in stream_response:
            text = get_response_text(chunk)
            if text:
                full_response += text
                await asyncio.sleep(0.01)  # Small delay
        
        return full_response
        
    except Exception as e:
        return f"Error: {str(e)}"


def render_sidebar():
    """Render the sidebar with connection and settings."""
    with st.sidebar:
        st.markdown("### ⚙️ Connection Settings")
        
        # Orchestrator URL input
        orchestrator_url = st.text_input(
            "Orchestrator URL",
            value="http://localhost:10003",
            help="URL of the orchestrator agent"
        )
        
        # Connect button
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🔌 Connect", use_container_width=True):
                with st.spinner("Connecting..."):
                    success, error = run_async(connect_to_orchestrator(orchestrator_url))
                    if success:
                        st.success("✅ Connected!")
                        st.rerun()
                    else:
                        st.error(f"❌ {error}")
        
        with col2:
            if st.button("🔄 Reset", use_container_width=True):
                # Close httpx client if exists
                if st.session_state.httpx_client:
                    try:
                        run_async(st.session_state.httpx_client.aclose())
                    except Exception as e:
                        if st.session_state.show_debug:
                            st.warning(f"Error closing httpx client: {e}")
                
                # Reset all state except event_loop (keep it persistent)
                st.session_state.messages = []
                st.session_state.connected = False
                st.session_state.agent_card = None
                st.session_state.client = None
                st.session_state.httpx_client = None
                # Note: We keep event_loop alive for reuse
                st.rerun()
        
        # Connection status
        st.markdown("---")
        st.markdown("### 📊 Status")
        if st.session_state.connected:
            st.markdown('<p class="status-connected">🟢 Connected</p>', unsafe_allow_html=True)
            if st.session_state.agent_card:
                st.markdown(f"**Agent:** {st.session_state.agent_card.name}")
                with st.expander("ℹ️ Agent Details"):
                    st.markdown(f"**Description:** {st.session_state.agent_card.description}")
        else:
            st.markdown('<p class="status-disconnected">🔴 Disconnected</p>', unsafe_allow_html=True)
            st.info("👆 Connect to the orchestrator to start chatting")
        
        # Debug mode toggle
        st.markdown("---")
        st.session_state.show_debug = st.checkbox("🐛 Debug Mode", value=st.session_state.show_debug)
        
        # Example queries
        st.markdown("---")
        st.markdown("### 📚 Example Queries")
        
        st.markdown("**Document Search:**")
        doc_examples = [
            "What is Python?",
            "Tell me about machine learning",
            "Explain the A2A protocol",
            "What is ChromaDB?"
        ]
        for example in doc_examples:
            if st.button(f"📄 {example}", key=f"doc_{example}", use_container_width=True):
                st.session_state.example_query = example
        
        st.markdown("**Image Analysis:**")
        img_examples = [
            "What is in this image?",
            "Describe this image",
            "Caption this image"
        ]
        for example in img_examples:
            if st.button(f"📷 {example}", key=f"img_{example}", use_container_width=True):
                st.session_state.example_query = example
        
        # Instructions
        st.markdown("---")
        st.markdown("### 📖 Instructions")
        with st.expander("How to use"):
            st.markdown("""
            1. **Start the agents**:
               ```bash
               bash scripts/start_agents.sh
               ```
            
            2. **Connect** to the orchestrator using the button above
            
            3. **Type your query** or click example queries
            
            4. **View responses** in the chat interface
            
            **For image analysis**:
            - Upload an image using the uploader above
            - Ask questions like "What is in this image?" or "Describe this image"
            - Or provide a file path: `caption: /path/to/image.jpg`
            """)


def render_main_content():
    """Render the main chat interface."""
    st.markdown('<p class="main-header">🤖 Multi-Agent A2A Demo</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Interactive testing interface for the Agent-to-Agent protocol</p>', unsafe_allow_html=True)
    
    # Display architecture overview
    with st.expander("🏗️ System Architecture", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **🎯 Orchestrator Agent**
            - Port: 10003
            - Routes queries to specialized agents
            - Handles A2A protocol communication
            """)
        
        with col2:
            st.markdown("""
            **📚 RAG Agent**
            - Port: 10002
            - Document search using ChromaDB
            - Vector similarity search
            """)
        
        with col3:
            st.markdown("""
            **📷 Image Caption Agent**
            - Port: 10004
            - BLIP model for image analysis
            - Generates descriptive captions
            """)
    
    st.markdown("---")
    
    # Chat interface
    if not st.session_state.connected:
        st.warning("⚠️ Please connect to the orchestrator in the sidebar to start chatting")
        return
    
    # Display chat messages
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                if "image" in message:
                    st.image(message["image"], caption="Uploaded Image", use_container_width=True)
                st.markdown(message["content"])
    
    # Image upload section - right above chat input
    uploaded_file = st.file_uploader(
        "📷 Upload Image (Optional)",
        type=['png', 'jpg', 'jpeg', 'gif', 'webp'],
        help="Upload an image to ask questions about it",
        key=f"image_uploader_{st.session_state.uploader_key}"
    )
    
    if uploaded_file is not None:
        # Store image in session state
        image = Image.open(uploaded_file)
        st.session_state.uploaded_image = image
        # Show preview in a compact way
        col1, col2 = st.columns([3, 1])
        with col1:
            st.image(image, caption="📷 Image ready - ask a question about it!", use_container_width=True)
        with col2:
            if st.button("❌ Clear", use_container_width=True):
                st.session_state.uploaded_image = None
                st.session_state.uploader_key += 1
                st.rerun()
    else:
        st.session_state.uploaded_image = None
    
    # Chat input - right below image uploader
    query = st.chat_input("Type your message here... (or ask about the uploaded image)")
    
    # Check if example query was clicked
    if 'example_query' in st.session_state and st.session_state.example_query:
        query = st.session_state.example_query
        st.session_state.example_query = None
    
    if query:
        # Get uploaded image if available
        image = st.session_state.get('uploaded_image', None)
        
        # Add user message to chat
        message_content = {"role": "user", "content": query}
        if image:
            message_content["image"] = image
        st.session_state.messages.append(message_content)
        
        # Display user message
        with st.chat_message("user"):
            if image:
                st.image(image, caption="Uploaded Image", use_container_width=True)
            st.markdown(query)
        
        # Get and display assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = run_async(send_query(query, image=image))
                st.markdown(response)
        
        # Add assistant response to chat
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Clear uploaded image after use by incrementing uploader key
        if image:
            st.session_state.uploaded_image = None
            st.session_state.uploader_key += 1  # This will reset the file uploader
        
        # Rerun to update chat
        st.rerun()


def main():
    """Main application entry point."""
    initialize_session_state()
    render_sidebar()
    render_main_content()


if __name__ == "__main__":
    main()

