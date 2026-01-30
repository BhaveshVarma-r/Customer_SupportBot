# TechGear Customer Support Chatbot - Architecture & Workflow Design

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (HTML/CSS/JS)                       │
│                    - Interactive Chat Interface                      │
│                    - Message Display & Input                         │
│                    - Real-time Status Updates                        │
└─────────────────────────────────────┬───────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND SERVER                          │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ POST /api/chat → Process Query through Workflow              │  │
│  │ GET /api/health → Health Check                               │  │
│  │ GET /api/docs → Swagger Documentation                        │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────┬───────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    LANGGRAPH WORKFLOW ORCHESTRATOR                   │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ NODE 1: CLASSIFIER                                           │  │
│  │ ─────────────────────────────────────────────────────────── │  │
│  │ • Uses Gemini-Pro LLM                                        │  │
│  │ • Categorizes query into: products/returns/warranty/support │  │
│  │ • Computes confidence score (0-1)                           │  │
│  │ Output: {category, confidence, reasoning}                   │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                            │                                        │
│                            ▼                                        │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ NODE 2: CONDITIONAL ROUTER                                  │  │
│  │ ─────────────────────────────────────────────────────────── │  │
│  │ • Routes based on classification confidence                 │  │
│  │ • Low confidence (< 0.5) → Escalate                         │  │
│  │ • Standard queries → RAG Responder                          │  │
│  │ • Complex queries → Escalation Handler                      │  │
│  └──────────────────────────────────────────────────────────────┘  │
│            │                                    │                   │
│            ▼                                    ▼                   │
│  ┌─────────────────────────┐    ┌──────────────────────────────┐  │
│  │ NODE 3A: RAG RESPONDER  │    │ NODE 3B: ESCALATION HANDLER  │  │
│  │ ──────────────────────  │    │ ─────────────────────────────│  │
│  │ • Retrieves context     │    │ • Generates escalation msg   │  │
│  │ • Generates answer      │    │ • Provides support channels  │  │
│  │ • Returns sources       │    │ • Creates reference ID       │  │
│  └─────────────────────────┘    └──────────────────────────────┘  │
│            │                                    │                   │
│            └────────────────┬───────────────────┘                   │
│                             ▼                                        │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ NODE 4: INTERACTION LOGGER                                  │  │
│  │ ────────────────────────────────────────────────────────── │  │
│  │ • Logs to interactions.jsonl for analytics                  │  │
│  │ • Records: query, answer, category, escalation status       │  │
│  │ • Timestamp and conversation tracking                       │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                             │                                        │
│                             ▼                                        │
│                    Returns Final Response                            │
│                                                                       │
└─────────────────────────────────────┬───────────────────────────────┘
                                      │
                     ┌────────────────┼────────────────┐
                     ▼                ▼                ▼
         ┌────────────────┐  ┌──────────────┐  ┌────────────────┐
         │   ChromaDB     │  │   Gemini     │  │   JSON Files   │
         │   Vector DB    │  │   LLM API    │  │   Database     │
         └────────────────┘  └──────────────┘  └────────────────┘
```

## Data Flow in Detail

### 1. Query Classification (Node 1)
```
Query Input
    │
    ├─→ Classifier Node
    │   ├─→ Generate embedding from query
    │   ├─→ Send to Gemini-Pro LLM
    │   └─→ Parse JSON response
    │
    └─→ Output: {
            "category": "products" | "returns" | "warranty" | "support" | "general",
            "confidence": 0.95,
            "reasoning": "Query about product features and pricing"
        }
```

### 2. Conditional Routing
```
Classification Result
    │
    ├─→ Confidence Score Check
    │   ├─→ confidence < 0.5 → Escalation Node
    │   └─→ confidence ≥ 0.5 → RAG Responder Node
    │
    └─→ Based on Category
        ├─→ "products" → RAG Responder
        ├─→ "returns" → RAG Responder
        ├─→ "warranty" → RAG Responder
        ├─→ "support" → RAG Responder
        └─→ "general" → RAG Responder
```

### 3. RAG Retrieval & Answer Generation (Node 3A)

```
Query
    │
    ├─→ Chromadb Retriever
    │   ├─→ Generate query embedding using GoogleGenerativeAIEmbeddings
    │   ├─→ Search in vector store (cosine similarity)
    │   ├─→ Retrieve top 5 most relevant documents/chunks
    │   └─→ Return {documents[], metadata[], distances[]}
    │
    ├─→ Format Retrieved Context
    │   └─→ Combine all chunks with source metadata
    │
    ├─→ Build Prompt
    │   ├─→ System prompt: Define chatbot role & knowledge
    │   ├─→ Context: Retrieved documents
    │   └─→ Query: Original customer question
    │
    ├─→ LLM Generation (Gemini-Pro)
    │   ├─→ Send prompt to LLM
    │   ├─→ Stream/receive response
    │   └─→ Parse output
    │
    └─→ Output: {
            "query": "...",
            "answer": "...",
            "retrieved_docs_count": 5,
            "sources": ["product_info.txt", ...]
        }
```

### 4. Escalation Path (Node 3B)
```
Low Confidence Query
    │
    └─→ Escalation Handler
        ├─→ Generate escalation reason
        ├─→ Create support contact message
        ├─→ Generate reference ID (timestamp-based)
        │
        └─→ Output: {
                "answer": "Escalation message with support channels",
                "is_escalated": true,
                "escalation_reason": "...",
                "reference_id": "202601301545..."
            }
```

### 5. Logging & Analytics (Node 4)
```
Processed Response
    │
    └─→ Logger Node
        ├─→ Extract interaction data:
        │   ├─→ conversation_id
        │   ├─→ query
        │   ├─→ category
        │   ├─→ answer
        │   ├─→ is_escalated
        │   ├─→ retrieved_docs_count
        │   └─→ timestamp
        │
        └─→ Append to interactions.jsonl
            └─→ Line: {"conversation_id": "...", "query": "...", ...}
```

## Vector Store Architecture (ChromaDB)

```
Knowledge Base (product_info.txt)
    │
    ├─→ Document Chunking (TextSplitter)
    │   ├─→ Chunk Size: 1000 characters
    │   ├─→ Overlap: 100 characters
    │   └─→ Total Chunks: ~500+ documents
    │
    ├─→ Embedding Generation
    │   ├─→ Model: GoogleGenerativeAIEmbeddings
    │   ├─→ Embedding Dim: 768
    │   └─→ Batch Processing: 50 docs at a time
    │
    └─→ ChromaDB Storage
        ├─→ Collection: "techgear_products"
        ├─→ Distance Metric: Cosine Similarity
        ├─→ Persistence: /chroma_db/
        │   ├─→ chroma.sqlite3
        │   └─→ parquet files
        │
        └─→ Each Document Stored With:
            ├─→ page_content (text)
            ├─→ metadata:
            │   ├─→ source: "product_info.txt"
            │   ├─→ chunk_id: index
            │   └─→ total_chunks: total count
            └─→ embedding (768-dim vector)
```

## FastAPI Endpoints

### POST /api/chat
```
Request:
{
  "query": "What is the price of SmartWatch Pro X?",
  "conversation_id": "optional_id"
}

Response (200 OK):
{
  "conversation_id": "conv_abc123",
  "query": "What is the price of SmartWatch Pro X?",
  "answer": "The SmartWatch Pro X costs ₹15,999...",
  "category": "products",
  "is_escalated": false,
  "retrieved_docs_count": 5,
  "sources": ["product_info.txt", ...],
  "timestamp": "2026-01-30T15:45:30.123456"
}

Response (400 Bad Request):
{
  "error": "HTTP Error",
  "detail": "Query cannot be empty",
  "timestamp": "2026-01-30T15:45:30.123456"
}
```

### GET /api/health
```
Response (200 OK):
{
  "status": "healthy",
  "timestamp": "2026-01-30T15:45:30.123456",
  "version": "1.0.0"
}
```

### GET /api/docs
- Interactive Swagger UI with all endpoints
- Try-it-out feature for testing
- Request/response schemas

## Workflow State Transitions

```
START
  │
  ├─→ receive_query
  │   │   query: str
  │   │   conversation_id: str
  │   └─→ state['query'] = query
  │
  ├─→ [NODE 1] classify_node
  │   │   Classify query into categories
  │   │   state['classification'] = {...}
  │   │   state['timestamp'] = now()
  │   │
  │   └─→ [ROUTER] route_based_on_classification
  │       ├─→ confidence < 0.5 → escalation
  │       └─→ confidence ≥ 0.5 → rag_responder
  │
  ├─→ [NODE 2A] rag_responder_node (OR)
  │   │   [NODE 2B] escalation_node
  │   │
  │   │   • Generate answer
  │   │   • Set state['answer']
  │   │   • Set state['is_escalated']
  │   │
  │   └─→ Both paths converge
  │
  └─→ [NODE 3] logger_node
      │   Log interaction to database
      │
      └─→ [NODE 4] return_response
          │
          └─→ END
```

## Query Processing Example

```
User Input: "Can I return my SmartWatch after 15 days?"

Step 1: Classification
  → Query Embedding
  → Gemini Analysis
  → Output: {category: "returns", confidence: 0.98}

Step 2: Router Decision
  → Confidence 0.98 ≥ 0.5 ✓
  → Route to RAG Responder

Step 3: RAG Retrieval
  → Query embedding in ChromaDB
  → Retrieved chunks:
     • "Return Policy: 7-day no-questions-asked..."
     • "Warranty: 1 year standard..."
     • "Product: SmartWatch Pro X..."
  → Total retrieved: 5 chunks

Step 4: Answer Generation
  → Combine context with query
  → Send to Gemini-Pro
  → Response: "I'm sorry, our return policy allows returns within 7 days only. 
               After 15 days, your SmartWatch may not be eligible for return. 
               However, you might be eligible for warranty service if there's a defect."

Step 5: Logging
  → {conversation_id, query, category: "returns", answer, 
     is_escalated: false, retrieved_docs_count: 5, timestamp}

Step 6: Response to Frontend
  → Send response with metadata to user
```

## Error Handling

```
Error Scenarios:

1. Empty Query
   → Status: 400 Bad Request
   → Message: "Query cannot be empty"

2. Query Too Long (>1000 chars)
   → Status: 400 Bad Request
   → Message: "Query too long (max 1000 characters)"

3. ChromaDB Connection Error
   → Route to Escalation
   → Message with support contact info

4. LLM API Error
   → Graceful fallback
   → Escalation to human support

5. Unknown Error
   → Status: 500 Internal Server Error
   → Generic error message
   → Log error details for debugging
```

## Performance Considerations

1. **ChromaDB Indexing**: Cosine similarity for fast semantic search
2. **Batch Processing**: Process embeddings in batches of 50
3. **LangGraph Optimization**: Async execution where possible
4. **Response Caching**: Consider caching for frequent queries
5. **Rate Limiting**: Implement if needed for production

## Security Considerations

1. **Input Validation**: Reject very long queries
2. **CORS**: Allow frontend domain(s)
3. **Error Messages**: Don't expose sensitive info
4. **Logging**: Store PII-sensitive data securely
5. **API Keys**: Use environment variables for Gemini API key

## Future Enhancements

1. Multi-turn conversation context
2. User feedback mechanism for improving answers
3. Query recommendation engine
4. Conversation analytics dashboard
5. Custom knowledge base update interface
6. Multi-language support
7. Document versioning
8. A/B testing for different response strategies
