"""Sample External API Agent - Demonstrates how to wrap a REST API endpoint."""
import json
from typing import Any, AsyncGenerator

import httpx


class ExternalAPIAgent:
    """Sample agent that wraps an external REST API endpoint.
    
    This demonstrates how to integrate any REST API with the orchestrator.
    The agent handles:
    - HTTP requests to external API
    - Input/output transformation
    - Error handling
    - Response streaming
    """
    
    def __init__(self, config: dict):
        """Initialize the external API agent.
        
        Args:
            config: Configuration dictionary with:
                - api_url: URL of the REST API endpoint
                - api_key: Optional API key for authentication
                - timeout: Request timeout in seconds
                - headers: Optional custom headers
        """
        print(f"[DEBUG] Initializing ExternalAPIAgent")
        
        self.api_url = config.get('api_url', 'http://localhost:8000/api/predict')
        self.api_key = config.get('api_key')
        self.timeout = config.get('timeout', 30.0)
        self.headers = config.get('headers', {})
        
        # Add API key to headers if provided
        if self.api_key:
            self.headers['Authorization'] = f'Bearer {self.api_key}'
        
        # Create HTTP client
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            headers=self.headers
        )
        
        print(f"[DEBUG] API URL: {self.api_url}")
        print(f"[DEBUG] Timeout: {self.timeout}s")
        print("[DEBUG] ExternalAPIAgent initialized")
    
    def _transform_input(self, query: str) -> dict:
        """Transform A2A query format to your API's expected format.
        
        This is where you adapt the input format to match your API.
        Common transformations:
        - Parse JSON strings
        - Convert text to structured data
        - Extract features from natural language
        
        Args:
            query: Input query from A2A protocol (string)
            
        Returns:
            Dictionary in format expected by your API
        """
        # Example: Try to parse as JSON first
        try:
            data = json.loads(query.strip())
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass
        
        # Example: Handle space-separated values
        if all(part.replace('.', '').replace('-', '').isdigit() for part in query.split()):
            values = [float(x) for x in query.split()]
            return {'features': values}
        
        # Default: Send as text query
        return {'query': query, 'text': query}
    
    def _transform_output(self, api_response: dict) -> str:
        """Transform your API's response format to A2A format.
        
        This is where you format the API response for display.
        
        Args:
            api_response: Response from your API
            
        Returns:
            Formatted string for A2A response
        """
        # Example: Format prediction response
        if 'prediction' in api_response:
            result = f"**Prediction:** {api_response['prediction']}\n"
            if 'confidence' in api_response:
                result += f"**Confidence:** {api_response['confidence']:.2%}\n"
            if 'probabilities' in api_response:
                result += "\n**Probabilities:**\n"
                for label, prob in api_response['probabilities'].items():
                    result += f"- {label}: {prob:.2%}\n"
            return result
        
        # Example: Format general response
        if 'result' in api_response:
            return f"**Result:** {api_response['result']}\n"
        
        # Default: Pretty print JSON
        return json.dumps(api_response, indent=2)
    
    async def call_api(self, query: str) -> dict:
        """Call the external REST API.
        
        Args:
            query: Input query string
            
        Returns:
            API response as dictionary
            
        Raises:
            httpx.HTTPError: If API call fails
        """
        # Transform input to API format
        api_input = self._transform_input(query)
        
        print(f"[DEBUG] Calling API: {self.api_url}")
        print(f"[DEBUG] API Input: {api_input}")
        
        try:
            # Make API call
            response = await self.client.post(
                self.api_url,
                json=api_input
            )
            response.raise_for_status()
            
            result = response.json()
            print(f"[DEBUG] API Response: {result}")
            
            return result
            
        except httpx.HTTPError as e:
            print(f"[DEBUG] API Error: {e}")
            raise
        except Exception as e:
            print(f"[DEBUG] Unexpected error: {e}")
            raise
    
    async def stream_response(self, query: str) -> AsyncGenerator[dict[str, Any], None]:
        """Stream the API response back to the client.
        
        This method is called by the A2A executor to get the response.
        It should yield chunks of content with 'content' and 'done' keys.
        
        Args:
            query: User query string
            
        Yields:
            Dict with 'content' (str) and 'done' (bool) keys
        """
        print(f"[DEBUG] ExternalAPIAgent processing query: '{query}'")
        
        try:
            # Call external API
            api_response = await self.call_api(query)
            
            # Transform output
            formatted_response = self._transform_output(api_response)
            
            # Stream response
            # You can split into multiple chunks for better UX
            yield {'content': formatted_response, 'done': False}
            yield {'content': '', 'done': True}
            
        except httpx.HTTPError as e:
            error_msg = (
                f"❌ **API Error**\n\n"
                f"Failed to call external API: {str(e)}\n\n"
                f"Please check:\n"
                f"- API URL is correct: {self.api_url}\n"
                f"- API is running and accessible\n"
                f"- Network connectivity\n"
            )
            yield {'content': error_msg, 'done': False}
            yield {'content': '', 'done': True}
            
        except Exception as e:
            error_msg = (
                f"❌ **Error**\n\n"
                f"Unexpected error: {str(e)}\n"
            )
            yield {'content': error_msg, 'done': False}
            yield {'content': '', 'done': True}
    
    async def cleanup(self):
        """Cleanup resources."""
        await self.client.aclose()

