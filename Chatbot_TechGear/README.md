# TechGear Customer Support Chatbot

## 🎯 Overview

A production-ready **RAG (Retrieval-Augmented Generation) chatbot** for TechGear Electronics customer support. Built with **LangChain**, **ChromaDB**, **LangGraph**, and **Google's Gemini AI model**, this system answers customer queries intelligently using a comprehensive product knowledge base.

### Key Features

✨ **Intelligent Query Classification** - Automatically categorizes customer queries into products, returns, warranty, support, and general categories

🔍 **Semantic Search Retrieval** - Uses ChromaDB with embeddings to find the most relevant product information

🤖 **Advanced Answer Generation** - Leverages Google Gemini Pro LLM to generate contextual, accurate answers

🔄 **Multi-Stage Workflow** - LangGraph orchestration with classification, routing, response generation, and escalation

📊 **Conversation Tracking** - Logs all interactions for analytics and improvement

🚀 **REST API** - FastAPI backend with Swagger documentation

💬 **Interactive Frontend** - Beautiful, responsive chat interface

📱 **Mobile Friendly** - Works seamlessly on all devices

## 📋 Project Structure

```
techgear_chatbot/
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── workflow.py             # LangGraph workflow orchestration
│   ├── rag_chain.py            # RAG chain implementation
│   ├── setup.py                # ChromaDB initialization
│   ├── chroma_db/              # Vector database storage
│   ├── interactions.jsonl      # Interaction logs
│   └── requirements.txt         # Python dependencies
├── frontend/
│   └── index.html              # Chat UI
├── data/
│   └── product_info.txt        # Knowledge base (300-500 entries)
├── Design.md                   # System architecture & workflow
└── README.md                   # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Google Gemini API Key
- pip (Python package manager)

### Installation

1. **Clone or navigate to project**
```bash
cd /home/labuser/Python_Projects/techgear_chatbot
```

2. **Set up virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
cd backend
pip install -r requirements.txt
```

4. **Configure Gemini API Key**
```bash
export GOOGLE_API_KEY="your_gemini_api_key_here"
```

Or create a `.env` file in `backend/` folder:
```
GOOGLE_API_KEY=your_gemini_api_key_here
```

5. **Initialize ChromaDB with knowledge base**
```bash
python setup.py
```

This will:
- Load product information from `data/product_info.txt`
- Split documents into optimal chunks
- Generate embeddings using Google's embedding model
- Store vectors in ChromaDB

### Running the Application

1. **Start the FastAPI server**
```bash
python main.py
```

The server will start at `http://localhost:8000`

2. **Access the chatbot**
- Open browser to `http://localhost:8000`
- Or use API directly at `http://localhost:8000/api/docs` (Swagger UI)

3. **Test the API**
```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the price of SmartWatch Pro X?"}'
```

## 🏗️ System Architecture

### Components

1. **Frontend (HTML/CSS/JS)**
   - Interactive chat interface
   - Real-time message updates
   - Status indicators
   - Responsive design

2. **FastAPI Backend**
   - REST API endpoints
   - Request validation
   - Error handling
   - CORS support
   - Swagger documentation

3. **LangGraph Workflow**
   - **Node 1: Classifier** - Categorizes queries using Gemini LLM
   - **Node 2: Router** - Routes to appropriate handler
   - **Node 3A: RAG Responder** - Generates answers using retrieved context
   - **Node 3B: Escalation Handler** - Routes to human support if needed
   - **Node 4: Logger** - Logs interactions for analytics

4. **ChromaDB Vector Store**
   - Stores embeddings of all knowledge base documents
   - Fast semantic search using cosine similarity
   - Persistent storage with DuckDB

5. **Google Gemini LLM**
   - Query classification
   - Answer generation
   - Embedding generation

### Data Flow

```
User Query (Frontend)
  ↓
POST /api/chat (FastAPI)
  ↓
Classifier Node (LLM)
  ↓
Router (Conditional)
  ├→ RAG Responder
  │  ├→ ChromaDB Search
  │  ├→ Gemini LLM
  │  └→ Answer Generation
  └→ Escalation Handler
     └→ Support Contact Info
  ↓
Logger Node (Analytics)
  ↓
Response to Frontend
  ↓
Display in Chat UI
```

See `Design.md` for detailed architecture diagrams and data flow.

## 📚 Knowledge Base

The knowledge base (`data/product_info.txt`) contains 300-500 entries covering:

### Products
- **SmartWatch Category**
  - SmartWatch Pro X (₹15,999)
  - SmartWatch Pro Max (₹22,999)
  - SmartWatch Essential (₹7,999)
  - SmartWatch Kids Edition (₹4,999)
  - SmartWatch Fitness Pro (₹12,999)

- **Wireless Earbuds Category**
  - Wireless Earbuds Elite (₹4,999)
  - Wireless Earbuds Premium Pro (₹8,999)
  - Wireless Earbuds Budget (₹1,999)
  - Wireless Earbuds Sports Elite (₹6,999)
  - Wireless Earbuds Gaming Pro (₹7,999)

- **Power Banks Category**
  - Power Bank Ultra 20000mAh (₹2,499)
  - Power Bank Ultra Max 30000mAh (₹3,999)
  - Power Bank Lite 10000mAh (₹1,299)
  - Power Bank Solar 25000mAh (₹3,499)
  - Power Bank Wireless 15000mAh (₹2,999)
  - Power Bank Professional 40000mAh (₹5,999)

### Policies & Information
- Return Policy (7-day no-questions-asked)
- Warranty Terms (1-3 years)
- Shipping & Delivery
- Payment Methods
- Customer Support Contact
- FAQs & Troubleshooting

### Product Details
- Specifications
- Features
- Pricing
- Warranty coverage
- Compatibility
- Comparisons

## 🔌 API Endpoints

### Chat Endpoint
```http
POST /api/chat
Content-Type: application/json

{
  "query": "What is the price of SmartWatch Pro X?",
  "conversation_id": "optional_id"
}
```

**Response (200 OK)**
```json
{
  "conversation_id": "conv_abc123",
  "query": "What is the price of SmartWatch Pro X?",
  "answer": "The SmartWatch Pro X costs ₹15,999 and features...",
  "category": "products",
  "is_escalated": false,
  "retrieved_docs_count": 5,
  "sources": ["product_info.txt"],
  "timestamp": "2026-01-30T15:45:30.123456"
}
```

### Health Check
```http
GET /api/health
```

### API Documentation
- **Swagger UI**: `http://localhost:8000/api/docs`
- **ReDoc**: `http://localhost:8000/api/redoc`
- **OpenAPI JSON**: `http://localhost:8000/api/openapi.json`

## 💬 Example Conversations

### Example 1: Product Inquiry
```
User: "What products do you offer?"
Bot: "TechGear Electronics offers a comprehensive range of tech products..."
Category: products | Escalated: No | Sources: 5
```

### Example 2: Warranty Question
```
User: "What is the warranty on SmartWatch Pro X?"
Bot: "The SmartWatch Pro X comes with 1 year standard warranty covering..."
Category: warranty | Escalated: No | Sources: 3
```

### Example 3: Return Policy
```
User: "Can I return my earbuds after 10 days?"
Bot: "Unfortunately, our return policy allows returns within 7 days only..."
Category: returns | Escalated: No | Sources: 4
```

### Example 4: Technical Support
```
User: "My smartwatch won't turn on"
Bot: "I've escalated your issue to our specialist support team..."
Category: support | Escalated: Yes | Sources: 0
```

## 🔧 Configuration

### Environment Variables
```bash
# .env file in backend/
GOOGLE_API_KEY=your_api_key_here
CHROMA_DB_PATH=/path/to/chroma_db  # Optional
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

### Tuning Parameters

In `backend/setup.py`:
```python
chunk_size=1000        # Document chunk size
chunk_overlap=100      # Chunk overlap for context
```

In `backend/rag_chain.py`:
```python
k=5                    # Number of retrieved documents
temperature=0.7        # LLM creativity (0-1)
```

In `backend/workflow.py`:
```python
confidence_threshold=0.5  # For routing decisions
```

## 📊 Logging & Analytics

### Interaction Logs
All interactions are logged to `backend/interactions.jsonl`:
```json
{
  "conversation_id": "conv_abc123",
  "query": "What is the price?",
  "category": "products",
  "answer": "The price is...",
  "is_escalated": false,
  "retrieved_docs_count": 5,
  "timestamp": "2026-01-30T15:45:30.123456",
  "sources": ["product_info.txt"]
}
```

### Analyzing Logs
```bash
# Count queries by category
grep -o '"category":"[^"]*' backend/interactions.jsonl | cut -d'"' -f4 | sort | uniq -c

# Find escalated queries
grep '"is_escalated":true' backend/interactions.jsonl
```

## 🧪 Testing

### Manual Testing
```bash
# Test through Swagger UI
curl http://localhost:8000/api/docs

# Test through cURL
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "Tell me about Power Banks"}'
```

### Test Queries
```python
test_queries = [
    "What products do you offer?",
    "What is the return policy?",
    "How long is the warranty?",
    "Can I swim with SmartWatch Pro X?",
    "My earbuds won't pair",
    "What payment methods do you accept?",
    "Tell me about the Power Bank Solar",
]
```

## 🚀 Production Deployment

### Deploy on Cloud
1. **Docker** - Containerize the application
2. **Railway/Render** - Easy deployment platforms
3. **AWS/GCP/Azure** - Full cloud infrastructure
4. **Heroku** - Simple platform-as-a-service

### Performance Optimization
- Enable caching for frequent queries
- Use async/await for concurrent requests
- Implement rate limiting
- Monitor API response times
- Add database connection pooling

### Security Hardening
- Add API key authentication
- Implement request signing
- Use HTTPS/TLS
- Regular security audits
- Sanitize user inputs

## 📈 Future Enhancements

- [ ] Multi-turn conversation context
- [ ] User feedback rating system
- [ ] Query recommendation engine
- [ ] Admin dashboard for analytics
- [ ] Custom knowledge base updates
- [ ] Multi-language support
- [ ] Document versioning
- [ ] A/B testing framework
- [ ] Sentiment analysis
- [ ] User preference learning

## 🤝 Contributing

To improve the chatbot:

1. **Update Knowledge Base**
   - Edit `data/product_info.txt`
   - Re-run `python setup.py`

2. **Improve Prompts**
   - Edit system prompts in `rag_chain.py`
   - Adjust `temperature` and retrieval settings

3. **Extend Workflow**
   - Add new nodes in `workflow.py`
   - Modify routing logic

4. **Fix Issues**
   - Check error logs in console
   - Review `interactions.jsonl` for patterns
   - Test with various query types

## 📞 Support

For issues or questions:
- 📧 support@techgear.com
- 📱 1800-TECHGEAR
- 🌐 Visit website for more help

## 📄 License

This project is provided as-is for TechGear Electronics.

## 🎓 Learning Resources

### Technologies Used
- [LangChain Documentation](https://python.langchain.com/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Google Gemini API](https://ai.google.dev/)

### Concepts
- **RAG (Retrieval-Augmented Generation)** - Combining retrieval and generation for better answers
- **Vector Embeddings** - Semantic representation of text
- **Semantic Search** - Finding relevant documents using meaning
- **LLM Orchestration** - Coordinating multiple AI components
- **Workflow Automation** - Using graphs for complex processes

## ✅ Checklist for Deployment

- [ ] Set GOOGLE_API_KEY environment variable
- [ ] Run `python setup.py` to initialize ChromaDB
- [ ] Test API endpoints with sample queries
- [ ] Review logs for any errors
- [ ] Configure frontend URL if backend is on different server
- [ ] Set up monitoring/alerting
- [ ] Configure CORS for production domain
- [ ] Enable HTTPS/TLS
- [ ] Set up database backups
- [ ] Document any customizations

---

**Built with ❤️ for TechGear Electronics Customer Support**

*Last Updated: January 30, 2026*
