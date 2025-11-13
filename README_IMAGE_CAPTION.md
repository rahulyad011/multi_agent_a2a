# Image Captioning Agent Addition

This document describes the Image Captioning Agent that was added to the orchestrator system.

## Overview

The Image Captioning Agent uses the **BLIP (Bootstrapping Language-Image Pre-training)** model to generate descriptive captions for images. It's connected to the orchestrator via the A2A protocol, just like the RAG agent.

## Architecture

```
User
  |
  v
Test Client (A2A Client)
  |
  | A2A Protocol
  v
Orchestrator Agent (Port 10003)
  |
  |--- A2A Protocol --> RAG Agent (Port 10002) --> ChromaDB
  |
  |--- A2A Protocol --> Image Caption Agent (Port 10004) --> BLIP Model
```

## Image Captioning Agent (Port 10004)

### Features
- Uses **Salesforce BLIP** model from HuggingFace Transformers
- Processes images in JPG, PNG, GIF, BMP, WEBP, TIFF formats
- Generates descriptive captions for images
- GPU-accelerated when available (falls back to CPU)
- Exposes A2A protocol interface

### Files
- `agent_image_caption.py` - Image captioning agent with BLIP model
- `image_caption_executor.py` - A2A executor wrapper
- `image_caption_main.py` - Server startup script

### Technical Details

**Model**: Salesforce/blip-image-captioning-base
- Lightweight and fast
- Good quality captions
- Works on CPU and GPU

**Input Format**:
```
caption: /path/to/image.jpg
/absolute/path/to/photo.png
describe image: ~/Pictures/sunset.jpg
```

**Output Format**:
```markdown
**Image Caption Analysis**

📷 Image: `image.jpg`

📝 Caption: a dog sitting on a couch

---
_Generated using BLIP image captioning model_
```

## Updated Orchestrator

The orchestrator now routes to **two specialized agents**:

### Routing Logic

```python
def should_route_to_image_caption(query):
    # Checks for:
    - Image-related keywords: 'caption', 'image', 'picture', 'photo'
    - Image file extensions: .jpg, .jpeg, .png, .gif, etc.
    - File path patterns: '/', '\', '~'
    
def should_route_to_rag(query):
    # Checks for:
    - Document keywords: 'what', 'explain', 'tell me about', etc.
    - NOT image-related queries
```

### A2A Communication

Both agents use the same A2A protocol:

1. **Agent Card Discovery**: Fetch agent capabilities
2. **Message Creation**: Create A2A message with query
3. **Streaming Request**: Send via `send_message_streaming()`
4. **Response Forwarding**: Stream results back to client

## Running the Full System

### Terminal 1: RAG Agent
```bash
uv run .
# Runs on port 10002
```

### Terminal 2: Image Caption Agent
```bash
uv run image_caption_main.py
# Runs on port 10004
```

### Terminal 3: Orchestrator
```bash
uv run orchestrator_main.py
# Runs on port 10003
# Connects to both RAG and Image Caption agents
```

### Terminal 4: Test Client
```bash
uv run test_client.py
# Connects to orchestrator
```

## Example Usage

### Document Search (Routes to RAG Agent)
```
> What is Python?

[DEBUG] Determining routing...
[DEBUG] ===== ROUTING TO RAG AGENT VIA A2A =====
[DEBUG] Fetching agent card from http://localhost:10002
[DEBUG] Sending streaming request to RAG Agent via A2A

Based on the documents in my knowledge base, here's what I found:

**Document 1** (relevance: 0.76):
Python is a high-level, interpreted programming language...
```

### Image Captioning (Routes to Image Caption Agent)
```
> caption: /Users/username/Pictures/dog.jpg

[DEBUG] Determining routing...
[DEBUG] ===== ROUTING TO IMAGE CAPTION AGENT VIA A2A =====
[DEBUG] Fetching agent card from http://localhost:10004
[DEBUG] Sending streaming request to Image Caption Agent via A2A

**Image Caption Analysis**

📷 Image: `dog.jpg`

📝 Caption: a dog sitting on a couch

---
_Generated using BLIP image captioning model_
```

### General Query (Handled by Orchestrator)
```
> What can you do?

[DEBUG] Handling query directly (no routing)

I'm an orchestrator agent. I can help you with:

**📚 Document Search** (via RAG Agent):
- Python programming
- Machine Learning
- Vector Databases
- A2A Protocol
- ChromaDB

**📷 Image Captioning** (via Image Caption Agent):
- Caption images by providing file paths
- Example: 'caption: /path/to/image.jpg'
```

## Debug Tracing

### Image Caption Agent Logs
```
[DEBUG] ImageCaptioningAgent processing query: 'caption: /path/to/image.jpg'
[DEBUG] Extracted image path: '/path/to/image.jpg'
[DEBUG] Calling caption_image()...
[DEBUG] Captioning image: /path/to/image.jpg
[DEBUG] Loading image...
[DEBUG] Image loaded: size=(800, 600), mode=RGB
[DEBUG] Processing image through BLIP...
[DEBUG] Generating caption...
[DEBUG] Generated caption: 'a dog sitting on a couch'
[DEBUG] Streaming response...
[DEBUG] Response streaming complete
```

### Orchestrator Routing Decision
```
[DEBUG] OrchestratorAgent processing query: 'caption: image.jpg'
[DEBUG] Determining routing...
[DEBUG] ===== ROUTING TO IMAGE CAPTION AGENT VIA A2A =====
[DEBUG] Initializing Image Caption agent A2A client...
[DEBUG] Fetching agent card from http://localhost:10004
[DEBUG] Agent card received: Image Captioning Agent
[DEBUG] Creating A2A message for Image Caption Agent
[DEBUG] Sending streaming request to Image Caption Agent via A2A
[DEBUG] Request ID: abc123...
[DEBUG] Receiving streaming response from Image Caption Agent
[DEBUG] Chunk 1: forwarding 28 chars
[DEBUG] Chunk 2: forwarding 23 chars
[DEBUG] ===== A2A CALL COMPLETE =====
```

## Dependencies Added

```toml
dependencies = [
    "transformers>=4.30.0",  # HuggingFace Transformers for BLIP
    "torch>=2.0.0",          # PyTorch for model inference
    "pillow>=10.0.0",        # Image processing
]
```

## Model Download

On first run, the BLIP model will be downloaded:
- Model: ~990MB
- Cache location: `~/.cache/huggingface/`
- This happens automatically on agent startup

## Performance

- **Model loading**: ~5-10 seconds on first start
- **Caption generation**: ~1-3 seconds per image (CPU)
- **Caption generation**: ~0.5-1 second per image (GPU)
- **Memory usage**: ~2GB (model + image)

## Supported Image Formats

- JPEG/JPG
- PNG
- GIF
- BMP
- WEBP
- TIFF

## Error Handling

The agent handles:
- Missing image files
- Invalid file formats
- Corrupted images
- Model loading errors

All errors are streamed back to the user via A2A protocol.

## Testing Tips

### Create a Test Image

```bash
# On macOS, you can capture a screenshot:
screencapture -x ~/Desktop/test_image.png

# Or use an existing image from your system:
ls ~/Pictures/*.jpg

# Then caption it:
> caption: /Users/your username/Desktop/test_image.png
```

### Test Different Image Types

```
> caption: ~/Pictures/vacation.jpg
> /Users/username/Desktop/screenshot.png
> describe image: /tmp/test.jpg
```

## Troubleshooting

### "Image file not found"
- Use absolute paths, not relative
- Expand `~` to full path if needed
- Check file permissions

### Model download issues
- Ensure internet connection
- Check firewall settings
- May need to set HuggingFace token for some models

### Out of memory
- Close other applications
- Use smaller images
- Consider using CPU if GPU memory is limited

### Slow performance
- First run downloads model (~1GB)
- CPU inference is slower than GPU
- Consider using a smaller model

## Extending the System

### Add More Models

You can easily swap the BLIP model:

```python
# In agent_image_caption.py
model_name = "Salesforce/blip-image-captioning-large"  # Larger model
model_name = "nlpconnect/vit-gpt2-image-captioning"   # Alternative
```

### Add More Agent Types

Following the same pattern:
1. Create agent file with A2A executor
2. Create server startup file
3. Update orchestrator routing logic
4. Add agent URL to orchestrator initialization

Example ideas:
- **Translation Agent**: Translate text between languages
- **Code Analysis Agent**: Analyze code snippets
- **Weather Agent**: Get weather information
- **Calculator Agent**: Perform calculations

## Security Notes

- Validate image paths before processing
- Sanitize user inputs
- Consider sandboxing image processing
- Monitor resource usage
- Implement rate limiting for production

## Conclusion

The Image Captioning Agent demonstrates:
1. **Multi-Agent Orchestration**: Multiple specialized agents
2. **A2A Protocol**: Standardized agent communication
3. **Extensibility**: Easy to add more agent types
4. **Traceability**: Debug logging throughout
5. **Real-world ML**: Integration with vision models

This creates a powerful multi-modal system where different AI capabilities can work together! 🚀

