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
    
    def process_image(self, image: Image.Image, question: str | None = None) -> str:
        """Process an image and generate a caption or answer a question.
        
        Args:
            image: PIL Image object
            question: Optional question about the image. If None, generates a caption.
            
        Returns:
            Generated caption or answer text
        """
        try:
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            print(f"[DEBUG] Processing image: size={image.size}, mode={image.mode}")
            
            # Process image
            print("[DEBUG] Processing image through BLIP...")
            if question:
                # For question-answering, use the processor with text prompt
                inputs = self.processor(image, question, return_tensors="pt").to(self.device)
                print(f"[DEBUG] Answering question: '{question}'")
            else:
                # For captioning, just process the image
                inputs = self.processor(image, return_tensors="pt").to(self.device)
                print("[DEBUG] Generating caption...")
            
            # Generate response
            output = self.model.generate(**inputs, max_length=100, num_beams=5)
            
            # Decode response
            result = self.processor.decode(output[0], skip_special_tokens=True)
            print(f"[DEBUG] Generated response: '{result}'")
            
            return result
            
        except Exception as e:
            error_msg = f"Error processing image: {str(e)}"
            print(f"[DEBUG] ERROR: {error_msg}")
            import traceback
            traceback.print_exc()
            return error_msg
    
    def caption_image(self, image_path: str) -> str:
        """Generate a caption for the given image file path.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Generated caption text
        """
        print(f"[DEBUG] Captioning image from path: {image_path}")
        
        # Check if file exists
        if not os.path.exists(image_path):
            error_msg = f"Image file not found: {image_path}"
            print(f"[DEBUG] ERROR: {error_msg}")
            return error_msg
        
        try:
            # Load image
            print("[DEBUG] Loading image...")
            image = Image.open(image_path)
            return self.process_image(image)
            
        except Exception as e:
            error_msg = f"Error loading image: {str(e)}"
            print(f"[DEBUG] ERROR: {error_msg}")
            import traceback
            traceback.print_exc()
            return error_msg
    
    async def stream_response(self, query: str, image: Image.Image | None = None) -> AsyncGenerator[dict[str, Any], None]:
        """Stream the caption or answer response back to the client.
        
        Args:
            query: The user query (can contain image path or question)
            image: Optional PIL Image object (if image was uploaded)
            
        Yields:
            Dict with 'content' and 'done' keys
        """
        print(f"[DEBUG] ImageCaptioningAgent processing query: '{query}'")
        
        # If image is provided directly, use it
        if image is not None:
            print("[DEBUG] Using provided image object")
            # Extract question from query if it's not just a path
            question = None
            query_lower = query.lower().strip()
            
            # Check if query is a question (not a file path)
            question_keywords = ['what', 'where', 'who', 'when', 'why', 'how', 'describe', 'tell me', 'explain']
            if any(keyword in query_lower for keyword in question_keywords) and not os.path.exists(query):
                question = query.strip()
                print(f"[DEBUG] Detected question: '{question}'")
            
            # Process image with question (or generate caption if no question)
            result = self.process_image(image, question)
            
            # Stream response
            print("[DEBUG] Streaming response...")
            if question:
                response_parts = [
                    f"**Image Question Answering**\n\n",
                    f"❓ Question: {question}\n\n",
                    f"💬 Answer: {result}\n\n",
                    f"---\n",
                    f"_Generated using BLIP vision-language model_"
                ]
            else:
                response_parts = [
                    f"**Image Caption Analysis**\n\n",
                    f"📝 Caption: {result}\n\n",
                    f"---\n",
                    f"_Generated using BLIP image captioning model_"
                ]
            
            for part in response_parts:
                yield {'content': part, 'done': False}
            
            print("[DEBUG] Response streaming complete")
            yield {'content': '', 'done': True}
            return
        
        # Otherwise, try to extract image path from query
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
            yield {'content': "Please provide an image path or upload an image. Example: 'caption: /path/to/image.jpg'", 'done': False}
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

