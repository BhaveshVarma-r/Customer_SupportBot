"""
RAG (Retrieval Augmented Generation) chain implementation.
Uses ChromaDB retriever and Google Gemini model for answer generation.
"""

import logging
import os
from dotenv import load_dotenv
from typing import List, Dict, Any
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
import chromadb
from pathlib import Path
import json
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

CHROMA_DB_PATH = Path(__file__).parent / "chroma_db"


class ChromaRetriever:
    """Custom retriever using ChromaDB for semantic search."""
    
    def __init__(self, collection, embeddings, k: int = 5):
        self.collection = collection
        self.embeddings = embeddings
        self.k = k
    
    def retrieve(self, query: str) -> List[Document]:
        """Retrieve top-k relevant documents from ChromaDB."""
        try:
            # Generate embedding for query
            query_embedding = self.embeddings.encode(query).tolist()
            
            # Query ChromaDB collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=self.k,
                include=["documents", "metadatas", "distances"]
            )
            
            # Convert results to Document objects
            documents = []
            if results and results["documents"]:
                for i, doc_text in enumerate(results["documents"][0]):
                    metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                    distance = results["distances"][0][i] if results["distances"] else 0
                    
                    metadata["distance"] = float(distance)
                    
                    doc = Document(
                        page_content=doc_text,
                        metadata=metadata
                    )
                    documents.append(doc)
            
            logger.info(f"Retrieved {len(documents)} documents for query: {query[:50]}...")
            return documents
        
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return []


class RAGChain:
    """RAG chain implementation using ChromaDB and Gemini."""
    
    def __init__(self, collection, model_name: str = None):
        """
        Initialize RAG chain.
        
        Args:
            collection: ChromaDB collection
            model_name: Google Gemini model name (uses env var or default)
        """
        self.collection = collection
        
        # Get model name from environment variable or use provided/default
        if model_name is None:
            model_name = os.getenv("GEMINI_MODEL", "gemini-pro")
        
        self.model_name = model_name
        
        # Initialize embeddings and LLM via google.generativeai
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.warning("GOOGLE_API_KEY not set. Using google.generativeai defaults.")
        else:
            genai.configure(api_key=api_key)
        
        self.embeddings_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.model = genai.GenerativeModel(model_name)
        
        # Initialize retriever
        self.retriever = ChromaRetriever(collection, self.embeddings_model, k=5)
        
        # System prompt for RAG
        self.system_prompt = """You are a helpful customer support chatbot for TechGear Electronics. 
You have access to a comprehensive product knowledge base including:
- Product specifications and features
- Pricing and warranty information
- Return and refund policies
- Shipping and delivery details
- Payment methods and discounts
- Customer support contact information
- FAQs and troubleshooting guides

Use the provided context to answer customer queries accurately and helpfully.
If the answer is not in the context, say so honestly and provide the support contact information.
Always be professional, courteous, and aim to resolve customer issues."""
        
        logger.info(f"RAG Chain initialized with model: {model_name}")
    
    def format_docs(self, docs: List[Document]) -> str:
        """Format retrieved documents for context."""
        if not docs:
            return "No relevant information found in knowledge base."
        
        formatted = "\n\n---\n\n".join(
            f"Source: {doc.metadata.get('source', 'unknown')}\n{doc.page_content}"
            for doc in docs
        )
        return formatted
    
    def generate_answer(self, query: str, retrieved_docs: List[Document]) -> Dict[str, Any]:
        """
        Generate answer using LLM with retrieved context.
        
        Args:
            query: User query
            retrieved_docs: Documents retrieved from ChromaDB
        
        Returns:
            Dictionary with answer and metadata
        """
        try:
            # Format context
            context = self.format_docs(retrieved_docs)
            
            # Build prompt
            full_prompt = f"""{self.system_prompt}

Based on the following context, answer the customer query.

Context:
{context}

Customer Query: {query}

Provide a helpful, accurate, and concise response."""
            
            # Generate response using genai
            response = self.model.generate_content(full_prompt)
            answer = response.text if response and response.text else "Unable to generate response"
            
            return {
                "query": query,
                "answer": answer,
                "retrieved_docs_count": len(retrieved_docs),
                "sources": [doc.metadata.get("source", "unknown") for doc in retrieved_docs]
            }
        
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return {
                "query": query,
                "answer": f"I encountered an error processing your query: {str(e)}. Please contact support@techgear.com",
                "retrieved_docs_count": 0,
                "sources": []
            }
    
    def answer_query(self, query: str) -> Dict[str, Any]:
        """
        Complete RAG pipeline: retrieve and generate answer.
        
        Args:
            query: User query
        
        Returns:
            Answer with metadata
        """
        logger.info(f"Processing query: {query}")
        
        # Retrieve relevant documents
        retrieved_docs = self.retriever.retrieve(query)
        
        # Generate answer
        result = self.generate_answer(query, retrieved_docs)
        result["timestamp"] = datetime.now().isoformat()
        
        return result


def initialize_rag_chain():
    """Initialize and return RAG chain."""
    logger.info("Initializing RAG Chain...")
    
    # Get ChromaDB client and collection
    client = chromadb.PersistentClient(
        path=str(CHROMA_DB_PATH),
        settings=chromadb.Settings(
            anonymized_telemetry=False
        )
    )
    
    collection = client.get_collection(name="techgear_products")
    
    # Create and return RAG chain
    rag_chain = RAGChain(collection)
    
    return rag_chain


if __name__ == "__main__":
    # Test RAG chain
    logging.basicConfig(level=logging.INFO)
    
    rag_chain = initialize_rag_chain()
    
    # Test queries
    test_queries = [
        "What is the price of SmartWatch Pro X?",
        "What are the return policies?",
        "Can I swim with the SmartWatch Pro X?",
        "How long does the Wireless Earbuds Elite battery last?",
        "What payment methods do you accept?"
    ]
    
    for query in test_queries:
        print("\n" + "="*60)
        print(f"Query: {query}")
        print("="*60)
        
        result = rag_chain.answer_query(query)
        
        print(f"Answer: {result['answer']}")
        print(f"Sources: {result['sources']}")
        print(f"Retrieved docs: {result['retrieved_docs_count']}")

