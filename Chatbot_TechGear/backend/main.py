"""
FastAPI backend for TechGear customer support chatbot.
Provides REST endpoints for chat interactions.
"""

import logging
import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid
import json
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

# Import workflow
from workflow import process_query

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="TechGear Customer Support Chatbot API",
    description="RAG-based chatbot for TechGear Electronics customer support",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===================== Pydantic Models =====================

class ChatMessage(BaseModel):
    """Chat message model."""
    query: str = Field(..., description="Customer query or message")
    conversation_id: Optional[str] = Field(None, description="Optional conversation ID for tracking")


class ChatResponse(BaseModel):
    """Chat response model."""
    conversation_id: str = Field(..., description="Conversation ID")
    query: str = Field(..., description="Original query")
    answer: str = Field(..., description="Generated answer")
    category: str = Field(..., description="Query category (products/returns/warranty/support/general)")
    is_escalated: bool = Field(..., description="Whether query was escalated to human support")
    retrieved_docs_count: int = Field(..., description="Number of documents retrieved from knowledge base")
    sources: List[str] = Field(..., description="Source documents used for answer")
    timestamp: str = Field(..., description="Response timestamp")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    timestamp: str = Field(..., description="Timestamp")
    version: str = Field(..., description="API version")


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error message")
    detail: str = Field(..., description="Error details")
    conversation_id: Optional[str] = Field(None, description="Conversation ID if available")
    timestamp: str = Field(..., description="Timestamp")


# ===================== Endpoints =====================

@app.get("/", tags=["Frontend"], summary="Serve chatbot frontend")
async def serve_frontend():
    """Serve the frontend HTML."""
    frontend_path = Path(__file__).parent.parent / "frontend" / "index.html"
    
    if frontend_path.exists():
        return FileResponse(frontend_path)
    else:
        return JSONResponse(
            status_code=404,
            content={"error": "Frontend not found"}
        )


@app.post("/api/chat", response_model=ChatResponse, tags=["Chat"], summary="Send chat message")
async def chat(message: ChatMessage) -> ChatResponse:
    """
    Send a message to the chatbot and receive a response.
    
    The chatbot processes the query through a multi-stage workflow:
    1. **Classification**: Categorizes the query (products/returns/warranty/support/general)
    2. **Retrieval**: Retrieves relevant documents from knowledge base using ChromaDB
    3. **Generation**: Generates answer using RAG with Google Gemini
    4. **Routing**: Routes to appropriate handler or escalation if needed
    
    Query will be stored in interactions database for analytics.
    
    Args:
        message: Chat message containing query and optional conversation_id
    
    Returns:
        ChatResponse with answer and metadata
    
    Raises:
        HTTPException: If processing fails
    """
    try:
        logger.info(f"Received chat query: {message.query[:50]}...")
        
        # Validate query
        if not message.query or len(message.query.strip()) == 0:
            raise HTTPException(
                status_code=400,
                detail="Query cannot be empty"
            )
        
        if len(message.query) > 1000:
            raise HTTPException(
                status_code=400,
                detail="Query too long (max 1000 characters)"
            )
        
        # Generate conversation ID if not provided
        conversation_id = message.conversation_id or str(uuid.uuid4())[:12]
        
        logger.info(f"[{conversation_id}] Processing through workflow...")
        
        # Process query through workflow
        response = process_query(message.query, conversation_id)
        
        # Convert to response model
        chat_response = ChatResponse(
            conversation_id=response["conversation_id"],
            query=response["query"],
            answer=response["answer"],
            category=response["category"],
            is_escalated=response["is_escalated"],
            retrieved_docs_count=response["retrieved_docs_count"],
            sources=response["sources"],
            timestamp=response["timestamp"]
        )
        
        logger.info(f"[{conversation_id}] Response generated successfully")
        
        return chat_response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing chat: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )


@app.get("/api/health", response_model=HealthResponse, tags=["Health"], summary="Health check")
async def health_check() -> HealthResponse:
    """
    Health check endpoint.
    
    Returns:
        HealthResponse with service status
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="1.0.0"
    )


@app.get("/api/info", tags=["Info"], summary="Get API information")
async def get_info():
    """Get API information and available endpoints."""
    return {
        "name": "TechGear Customer Support Chatbot",
        "version": "1.0.0",
        "description": "RAG-based chatbot powered by LangChain, ChromaDB, and Google Gemini",
        "endpoints": {
            "chat": {
                "method": "POST",
                "path": "/api/chat",
                "description": "Send query and get answer"
            },
            "health": {
                "method": "GET",
                "path": "/api/health",
                "description": "Health check"
            },
            "docs": {
                "method": "GET",
                "path": "/api/docs",
                "description": "Interactive API documentation (Swagger UI)"
            },
            "redoc": {
                "method": "GET",
                "path": "/api/redoc",
                "description": "ReDoc API documentation"
            }
        },
        "query_categories": [
            "products",
            "returns",
            "warranty",
            "support",
            "general"
        ],
        "features": {
            "rag": "Retrieval-Augmented Generation from ChromaDB",
            "classification": "Automatic query classification",
            "escalation": "Intelligent escalation to human support",
            "tracking": "Conversation tracking and analytics"
        }
    }


# ===================== Error Handlers =====================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP Error",
            "detail": exc.detail,
            "timestamp": datetime.now().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": "An unexpected error occurred",
            "timestamp": datetime.now().isoformat()
        }
    )


# ===================== Startup & Shutdown =====================

@app.on_event("startup")
async def startup_event():
    """Execute on app startup."""
    logger.info("="*60)
    logger.info("TechGear Customer Support Chatbot Starting...")
    logger.info("="*60)
    logger.info("API Documentation available at:")
    logger.info("  - Swagger UI: http://localhost:8000/api/docs")
    logger.info("  - ReDoc: http://localhost:8000/api/redoc")
    logger.info("  - OpenAPI JSON: http://localhost:8000/api/openapi.json")
    logger.info("="*60)


@app.on_event("shutdown")
async def shutdown_event():
    """Execute on app shutdown."""
    logger.info("TechGear Customer Support Chatbot Shutting Down...")


if __name__ == "__main__":
    import uvicorn
    
    # Run the app
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
