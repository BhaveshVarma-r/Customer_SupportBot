# TechGear Chatbot - Quick Start Guide

## 🚀 5-Minute Setup

### Step 1: Get Your API Key
1. Go to [Google AI Studio](https://ai.google.dev)
2. Click "Get API Key"
3. Create a new API key (free tier available)
4. Copy the key

### Step 2: Configure the Application
```bash
# Navigate to backend folder
cd backend

# Create .env file
cp .env.example .env

# Edit .env and paste your API key
nano .env  # or use your favorite editor
# Replace: your_gemini_api_key_here with your actual key
```

### Step 3: Initialize the Vector Database
```bash
# From backend folder
python setup.py
```

This will:
- Load 300-500 product documents
- Generate embeddings (takes 2-3 minutes)
- Store in ChromaDB

### Step 4: Start the Server
```bash
# Still in backend folder
python main.py
```

You should see:
```
INFO:     Application startup complete
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 5: Open in Browser
- **Chat**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

---

## 💬 Test Queries

Try these sample queries:

### Product Questions
- "What is the price of SmartWatch Pro X?"
- "What features does the Power Bank Ultra have?"
- "Tell me about Wireless Earbuds Elite"

### Policies
- "What is your return policy?"
- "How long is the warranty?"
- "What payment methods do you accept?"

### Warranty & Support
- "Can I extend the warranty?"
- "How do I contact support?"
- "Can I swim with the SmartWatch?"

---

## 🎯 Key Features

✨ **Intelligent Classification** - Automatically categorizes questions
🔍 **Semantic Search** - Finds relevant products in knowledge base
🤖 **AI-Powered Answers** - Uses Google Gemini to generate responses
📱 **Beautiful UI** - Modern, responsive chat interface
📊 **Analytics** - Logs all interactions for insights
🔄 **Easy Updates** - Update knowledge base without retraining

---

## 📊 API Examples

### Send a Query
```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the price of SmartWatch Pro X?",
    "conversation_id": "user_123"
  }'
```

### Response
```json
{
  "conversation_id": "user_123",
  "query": "What is the price of SmartWatch Pro X?",
  "answer": "The SmartWatch Pro X costs ₹15,999...",
  "category": "products",
  "is_escalated": false,
  "retrieved_docs_count": 5,
  "sources": ["product_info.txt"],
  "timestamp": "2026-01-30T15:45:30.123456"
}
```

### Health Check
```bash
curl http://localhost:8000/api/health
```

---

## 🔧 Troubleshooting

### "API Key not valid"
- Copy your key from https://ai.google.dev
- Paste in `backend/.env`
- Restart the server

### "ChromaDB not found"
- Run `python backend/setup.py` first
- Wait for embeddings to complete (2-3 minutes)

### "Port 8000 already in use"
```bash
# Use a different port
python -m uvicorn main:app --port 8001
```

### "Connection refused"
- Make sure server is running: `python main.py`
- Check that you're using correct URL: `http://localhost:8000`

---

## 📚 Project Files

```
techgear_chatbot/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── workflow.py          # LangGraph orchestration
│   ├── rag_chain.py         # RAG implementation
│   ├── setup.py             # Initialize ChromaDB
│   ├── chroma_db/           # Vector database
│   ├── interactions.jsonl   # Query logs
│   └── requirements.txt      # Dependencies
├── frontend/
│   └── index.html           # Chat UI
├── data/
│   └── product_info.txt     # Knowledge base
├── README.md                # Full documentation
├── Design.md                # Architecture details
└── test_system.py           # Validation tests
```

---

## 🎓 Next Steps

### Customize the Knowledge Base
Edit `data/product_info.txt`:
- Add new products
- Update prices
- Add new policies
- Run `python backend/setup.py` to re-index

### Modify System Behavior
Edit `backend/workflow.py`:
- Change confidence thresholds
- Add new query categories
- Customize escalation logic

### Deploy to Production
See README.md for:
- Docker containerization
- Cloud deployment options
- Security best practices
- Performance optimization

---

## 💡 Tips & Tricks

### View Interaction Logs
```bash
# Recent queries
tail backend/interactions.jsonl

# Query breakdown
grep '"category":"products"' backend/interactions.jsonl | wc -l

# Find escalated queries
grep '"is_escalated":true' backend/interactions.jsonl
```

### Test RAG Chain Directly
```bash
cd backend
python rag_chain.py
```

### Restart Server (if needed)
```bash
# Kill the server (Ctrl+C in terminal)
# Restart:
python backend/main.py
```

---

## 📞 Support

- **API Docs**: http://localhost:8000/api/docs (Swagger UI)
- **Full Docs**: README.md in project root
- **Architecture**: Design.md in project root

---

## ⏱️ Typical Flow

1. **User Types Message** (in browser)
2. **FastAPI Receives** POST request
3. **Classifier Categorizes** the query
4. **Router Decides** how to handle it
5. **Retriever Searches** ChromaDB
6. **LLM Generates** answer with context
7. **Logger Records** interaction
8. **Response Sent** back to user

---

**Ready to chat? Open http://localhost:8000 and start asking!** 🎉

For detailed information, see [README.md](README.md) and [Design.md](Design.md)
