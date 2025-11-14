"""Simple OCI GenAI LLM configuration utility."""
import oci
from langchain_oci import ChatOCIGenAI


def configure_llm_chat(config, model_id="cohere.command-r-plus", service_endpoint="", compartment_id="", max_tokens=2000):
    """
    Configure OCI GenAI Chat LLM.
    
    Args:
        config: OCI config object (from oci.config.from_file() or similar)
        model_id: OCI model ID (e.g., "cohere.command-r-plus")
        service_endpoint: OCI GenAI service endpoint URL
        compartment_id: OCI compartment ID
        max_tokens: Maximum tokens for responses
        
    Returns:
        ChatOCIGenAI instance
    """
    generative_ai_inference_client = oci.generative_ai_inference.GenerativeAiInferenceClient(config)
    
    llm = ChatOCIGenAI(
        model_id=model_id,
        service_endpoint=service_endpoint,
        compartment_id=compartment_id,
        client=generative_ai_inference_client,
        model_kwargs={"max_tokens": max_tokens}
    )
    
    return llm

