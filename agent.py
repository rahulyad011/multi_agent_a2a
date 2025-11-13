"""Simple RAG Agent using Chroma DB vector database."""
import os
from typing import Any, AsyncGenerator
from pathlib import Path

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer


class SimpleRAGAgent:
    """Simple RAG Agent that uses Chroma DB for document retrieval."""
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        """Initialize the RAG agent with Chroma DB.
        
        Args:
            persist_directory: Directory to persist Chroma DB data
        """
        print(f"[DEBUG] Initializing SimpleRAGAgent with persist_directory: {persist_directory}")
        
        # Initialize Chroma DB client
        self.client = chromadb.Client(Settings(
            persist_directory=persist_directory,
            is_persistent=True
        ))
        
        # Initialize sentence transformer for embeddings
        print("[DEBUG] Loading sentence transformer model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Get or create collection
        print("[DEBUG] Getting or creating Chroma collection 'documents'")
        self.collection = self.client.get_or_create_collection(
            name="documents",
            metadata={"description": "Document collection for RAG"}
        )
        
        print(f"[DEBUG] SimpleRAGAgent initialized. Collection size: {self.collection.count()}")
    
    def add_documents(self, documents: list[dict[str, str]]) -> None:
        """Add documents to the vector database.
        
        Args:
            documents: List of dicts with 'text' and 'metadata' keys
        """
        print(f"[DEBUG] Adding {len(documents)} documents to collection")
        
        texts = [doc['text'] for doc in documents]
        metadatas = [doc.get('metadata', {}) for doc in documents]
        ids = [f"doc_{i}" for i in range(len(documents))]
        
        # Generate embeddings
        print("[DEBUG] Generating embeddings for documents...")
        embeddings = self.embedding_model.encode(texts).tolist()
        
        # Add to collection
        self.collection.add(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        
        print(f"[DEBUG] Documents added successfully. New collection size: {self.collection.count()}")
    
    def query_documents(self, query: str, n_results: int = 3) -> list[dict[str, Any]]:
        """Query the vector database for relevant documents.
        
        Args:
            query: The query text
            n_results: Number of results to return
            
        Returns:
            List of relevant documents with metadata
        """
        print(f"[DEBUG] RAG Agent querying for: '{query}' (n_results={n_results})")
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query]).tolist()
        
        # Query the collection
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=n_results
        )
        
        print(f"[DEBUG] Found {len(results['documents'][0])} relevant documents")
        
        # Format results
        formatted_results = []
        if results['documents']:
            for i, doc in enumerate(results['documents'][0]):
                formatted_results.append({
                    'text': doc,
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                    'distance': results['distances'][0][i] if results['distances'] else None
                })
                print(f"[DEBUG] Document {i+1}: distance={results['distances'][0][i]:.4f}, text preview: {doc[:100]}...")
        
        return formatted_results
    
    async def stream_response(self, query: str) -> AsyncGenerator[dict[str, Any], None]:
        """Stream the response back to the client.
        
        Args:
            query: The user query
            
        Yields:
            Dict with 'content' and 'done' keys
        """
        print(f"[DEBUG] RAG Agent processing query: '{query}'")
        
        # Query relevant documents
        relevant_docs = self.query_documents(query, n_results=3)
        
        if not relevant_docs:
            print("[DEBUG] No relevant documents found")
            yield {'content': "I couldn't find any relevant information in my knowledge base for that query.", 'done': False}
            yield {'content': '', 'done': True}
            return
        
        # Build response from relevant documents
        print("[DEBUG] Building response from relevant documents")
        response = "Based on the documents in my knowledge base, here's what I found:\n\n"
        yield {'content': response, 'done': False}
        
        for i, doc in enumerate(relevant_docs, 1):
            doc_section = f"**Document {i}** (relevance: {1 - doc['distance']:.2f}):\n"
            yield {'content': doc_section, 'done': False}
            
            doc_text = f"{doc['text']}\n\n"
            yield {'content': doc_text, 'done': False}
        
        print("[DEBUG] Response streaming complete")
        yield {'content': '', 'done': True}
    
    def initialize_with_sample_docs(self) -> None:
        """Initialize the database with sample documents if empty."""
        if self.collection.count() > 0:
            print(f"[DEBUG] Collection already has {self.collection.count()} documents. Skipping initialization.")
            return
        
        print("[DEBUG] Initializing with sample documents...")
        sample_docs = [
            {
                'text': 'Python is a high-level, interpreted programming language known for its simplicity and readability. It supports multiple programming paradigms including procedural, object-oriented, and functional programming.',
                'metadata': {'topic': 'Python', 'category': 'Programming Languages'}
            },
            {
                'text': 'Machine learning is a subset of artificial intelligence that focuses on building systems that can learn from data. Common algorithms include linear regression, decision trees, and neural networks.',
                'metadata': {'topic': 'Machine Learning', 'category': 'AI'}
            },
            {
                'text': 'Vector databases store data as high-dimensional vectors, enabling efficient similarity search. They are commonly used in RAG (Retrieval Augmented Generation) systems to find relevant context for language models.',
                'metadata': {'topic': 'Vector Databases', 'category': 'Databases'}
            },
            {
                'text': 'The A2A (Agent-to-Agent) protocol enables communication between AI agents. It uses a JSON-RPC based messaging system to exchange tasks, messages, and artifacts between different agent systems.',
                'metadata': {'topic': 'A2A Protocol', 'category': 'Agent Communication'}
            },
            {
                'text': 'ChromaDB is an open-source embedding database designed for AI applications. It provides a simple API for storing and querying embeddings, making it ideal for building RAG systems.',
                'metadata': {'topic': 'ChromaDB', 'category': 'Databases'}
            }
        ]
        
        self.add_documents(sample_docs)
        print("[DEBUG] Sample documents initialized successfully")

