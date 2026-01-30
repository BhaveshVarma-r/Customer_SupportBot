"""
Document loading and ChromaDB initialization for TechGear chatbot.
Loads product information and stores embeddings in ChromaDB.
"""

import os
from dotenv import load_dotenv
import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from langchain_core.documents import Document
from pathlib import Path
import logging

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
CHROMA_DB_PATH = Path(__file__).parent / "chroma_db"
KNOWLEDGE_BASE_PATH = Path(__file__).parent.parent / "data" / "product_info.txt"

# Ensure ChromaDB directory exists
CHROMA_DB_PATH.mkdir(parents=True, exist_ok=True)


def load_knowledge_base(file_path: str) -> str:
    """Load product information from text file."""
    logger.info(f"Loading knowledge base from {file_path}")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Knowledge base file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    logger.info(f"Loaded {len(content)} characters from knowledge base")
    return content


def split_documents(content: str, chunk_size: int = 1000, chunk_overlap: int = 100):
    """Split document into chunks for better retrieval and embedding."""
    logger.info(f"Splitting documents with chunk_size={chunk_size}, overlap={chunk_overlap}")
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""]
    )
    
    chunks = splitter.split_text(content)
    logger.info(f"Created {len(chunks)} chunks from knowledge base")
    
    return chunks


def get_or_create_chroma_client():
    """Initialize ChromaDB client with persistent storage."""
    logger.info(f"Initializing ChromaDB at {CHROMA_DB_PATH}")
    
    # Use the new ChromaDB API
    client = chromadb.PersistentClient(
        path=str(CHROMA_DB_PATH),
        settings=chromadb.Settings(
            anonymized_telemetry=False
        )
    )
    return client


def initialize_vector_store(force_reset: bool = False):
    """
    Initialize ChromaDB vector store with product information.
    
    Args:
        force_reset: If True, recreate the collection from scratch
    """
    logger.info("=" * 60)
    logger.info("Initializing TechGear ChatBot Vector Store")
    logger.info("=" * 60)
    
    try:
        # Initialize ChromaDB client
        client = get_or_create_chroma_client()
        
        # Get or delete existing collection
        collection_name = "techgear_products"
        
        if force_reset:
            logger.info(f"Force reset: Deleting existing collection '{collection_name}'")
            try:
                client.delete_collection(name=collection_name)
                logger.info(f"Collection '{collection_name}' deleted successfully")
            except Exception as e:
                logger.info(f"Collection didn't exist or couldn't be deleted: {e}")
        
        # Load and split knowledge base
        content = load_knowledge_base(str(KNOWLEDGE_BASE_PATH))
        chunks = split_documents(content)
        
        # Initialize embeddings
        logger.info("Initializing sentence-transformers embeddings...")
        embeddings_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Create documents list
        documents = []
        for i, chunk in enumerate(chunks):
            doc = Document(
                page_content=chunk,
                metadata={
                    "source": "product_info.txt",
                    "chunk_id": i,
                    "total_chunks": len(chunks)
                }
            )
            documents.append(doc)
        
        logger.info(f"Creating collection with {len(documents)} documents...")
        
        # Get or create collection
        collection = client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        # Add documents to collection
        doc_texts = [doc.page_content for doc in documents]
        doc_metadatas = [doc.metadata for doc in documents]
        doc_ids = [f"doc_{i}" for i in range(len(documents))]
        
        # Generate embeddings and add to ChromaDB
        logger.info("Generating embeddings and adding to ChromaDB...")
        
        # Process in batches to avoid rate limiting
        batch_size = 50
        for i in range(0, len(documents), batch_size):
            batch_end = min(i + batch_size, len(documents))
            batch_texts = doc_texts[i:batch_end]
            batch_metadatas = doc_metadatas[i:batch_end]
            batch_ids = doc_ids[i:batch_end]
            
            try:
                # Generate embeddings for batch using sentence-transformers
                batch_embeddings = embeddings_model.encode(batch_texts)
                
                # Add to collection
                collection.add(
                    documents=batch_texts,
                    metadatas=batch_metadatas,
                    ids=batch_ids,
                    embeddings=batch_embeddings.tolist()
                )
                logger.info(f"Added batch {i//batch_size + 1} ({batch_end}/{len(documents)} documents)")
            except Exception as e:
                logger.error(f"Error processing batch {i//batch_size + 1}: {e}")
                raise
        
        logger.info("=" * 60)
        logger.info("Vector store initialization completed successfully!")
        logger.info(f"Total documents in collection: {collection.count()}")
        logger.info("=" * 60)
        
        return client, collection
    
    except Exception as e:
        logger.error(f"Error during vector store initialization: {e}")
        raise


def get_vector_store():
    """Get existing ChromaDB vector store (assumes already initialized)."""
    logger.info("Getting existing ChromaDB vector store...")
    client = get_or_create_chroma_client()
    collection = client.get_collection(name="techgear_products")
    return client, collection


if __name__ == "__main__":
    # Initialize vector store
    initialize_vector_store(force_reset=True)
