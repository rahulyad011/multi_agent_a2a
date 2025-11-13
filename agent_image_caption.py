"""Simple Image Captioning Agent using transformers."""
import os
from typing import Any, AsyncGenerator
from pathlib import Path
from PIL import Image
import torch
from transformers import BlipProcessor, BlipForConditionalGeneration


class ImageCaptioningAgent:
    """Simple Image Captioning Agent that uses BLIP model."""
    
    def __init__(self, model_name: str = "Salesforce/blip-image-captioning-base"):
        """Initialize the image captioning agent.
        
        Args:
            model_name: HuggingFace model name for image captioning
        """
        print(f"[DEBUG] Initializing ImageCaptioningAgent with model: {model_name}")
        
        # Initialize BLIP model and processor
        print("[DEBUG] Loading BLIP model and processor...")
        self.processor = BlipProcessor.from_pretrained(model_name)
        self.model = BlipForConditionalGeneration.from_pretrained(model_name)
        
        # Move to GPU if available
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)
        print(f"[DEBUG] Model loaded on device: {self.device}")
        
        print("[DEBUG] ImageCaptioningAgent initialized successfully")
    
    def caption_image(self, image_path: str) -> str:
        """Generate a caption for the given image.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Generated caption text
        """
        print(f"[DEBUG] Captioning image: {image_path}")
        
        # Check if file exists
        if not os.path.exists(image_path):
            error_msg = f"Image file not found: {image_path}"
            print(f"[DEBUG] ERROR: {error_msg}")
            return error_msg
        
        try:
            # Load and process image
            print("[DEBUG] Loading image...")
            image = Image.open(image_path).convert('RGB')
            print(f"[DEBUG] Image loaded: size={image.size}, mode={image.mode}")
            
            # Process image
            print("[DEBUG] Processing image through BLIP...")
            inputs = self.processor(image, return_tensors="pt").to(self.device)
            
            # Generate caption
            print("[DEBUG] Generating caption...")
            output = self.model.generate(**inputs, max_length=50, num_beams=5)
            
            # Decode caption
            caption = self.processor.decode(output[0], skip_special_tokens=True)
            print(f"[DEBUG] Generated caption: '{caption}'")
            
            return caption
            
        except Exception as e:
            error_msg = f"Error processing image: {str(e)}"
            print(f"[DEBUG] ERROR: {error_msg}")
            import traceback
            traceback.print_exc()
            return error_msg
    
    async def stream_response(self, query: str) -> AsyncGenerator[dict[str, Any], None]:
        """Stream the caption response back to the client.
        
        Args:
            query: The user query containing image path
            
        Yields:
            Dict with 'content' and 'done' keys
        """
        print(f"[DEBUG] ImageCaptioningAgent processing query: '{query}'")
        
        # Extract image path from query
        # Expected format: "caption: /path/to/image.jpg" or just "/path/to/image.jpg"
        image_path = query.strip()
        
        # Remove common prefixes
        for prefix in ["caption:", "caption this:", "describe:", "what is in:"]:
            if image_path.lower().startswith(prefix):
                image_path = image_path[len(prefix):].strip()
                break
        
        print(f"[DEBUG] Extracted image path: '{image_path}'")
        
        # Check if path looks valid
        if not image_path:
            print("[DEBUG] No image path provided")
            yield {'content': "Please provide an image path. Example: 'caption: /path/to/image.jpg'", 'done': False}
            yield {'content': '', 'done': True}
            return
        
        # Generate caption
        print("[DEBUG] Calling caption_image()...")
        caption = self.caption_image(image_path)
        
        # Stream response
        print("[DEBUG] Streaming response...")
        
        # Add context to the response
        response_parts = [
            f"**Image Caption Analysis**\n\n",
            f"📷 Image: `{os.path.basename(image_path)}`\n\n",
            f"📝 Caption: {caption}\n\n",
            f"---\n",
            f"_Generated using BLIP image captioning model_"
        ]
        
        for part in response_parts:
            yield {'content': part, 'done': False}
        
        print("[DEBUG] Response streaming complete")
        yield {'content': '', 'done': True}

