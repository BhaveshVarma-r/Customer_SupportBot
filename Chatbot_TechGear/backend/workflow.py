"""
LangGraph-based workflow for customer support chatbot.
Implements multi-node workflow with classification, RAG answering, and escalation.
"""

import json
import logging
import os
from dotenv import load_dotenv
from typing import Dict, Any, List, Literal
from datetime import datetime
from pathlib import Path
import google.generativeai as genai
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field
from rag_chain import initialize_rag_chain

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

# Database path for storing interactions
DB_PATH = Path(__file__).parent / "interactions.jsonl"


class QueryClassification(BaseModel):
    """Schema for query classification."""
    category: Literal["products", "returns", "warranty", "support", "general"] = Field(
        description="Category of the customer query"
    )
    confidence: float = Field(
        description="Confidence score (0-1) for the classification",
        ge=0,
        le=1
    )
    reasoning: str = Field(
        description="Brief reasoning for the classification"
    )


class ChatbotState:
    """State object for LangGraph workflow."""
    
    def __init__(self):
        self.query = ""
        self.classification = None
        self.retrieved_docs = []
        self.answer = ""
        self.escalation_reason = ""
        self.is_escalated = False
        self.conversation_id = ""
        self.metadata = {}


class QueryClassifier:
    """Classify customer queries into categories."""
    
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
        
        model_name = os.getenv("GEMINI_MODEL", "gemini-pro")
        self.model = genai.GenerativeModel(model_name)
        self.parser = JsonOutputParser(pydantic_object=QueryClassification)
    
    def classify(self, query: str) -> Dict[str, Any]:
        """
        Classify customer query.
        
        Args:
            query: Customer query
        
        Returns:
            Classification result with category and confidence
        """
        logger.info(f"Classifying query: {query[:50]}...")
        
        prompt_text = f"""You are a query classification expert for TechGear Electronics customer support.

Classify the following customer query into one of these categories:
1. "products" - Questions about product features, specs, pricing, availability
2. "returns" - Questions about return policy, refunds, exchange
3. "warranty" - Questions about warranty coverage, warranty terms, extended warranty
4. "support" - Technical issues, troubleshooting, service requests
5. "general" - Greetings, feedback, general inquiries, information requests

Query: {query}

Provide your classification in JSON format with:
- category: one of the above categories
- confidence: how confident you are (0-1)
- reasoning: brief explanation

JSON Response:"""
        
        try:
            response = self.model.generate_content(prompt_text)
            
            # Parse JSON from response
            response_text = response.text
            
            # Try to extract JSON from response
            import json
            # Find JSON in response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                result = json.loads(json_str)
                
                # Validate keys
                if 'category' in result and 'confidence' in result:
                    logger.info(f"Classification: {result['category']} (confidence: {result['confidence']})")
                    return {
                        "category": result.get('category', 'general'),
                        "confidence": float(result.get('confidence', 0.5)),
                        "reasoning": result.get('reasoning', 'Classified')
                    }
            
            # Default response
            return {
                "category": "general",
                "confidence": 0.5,
                "reasoning": "Could not parse classification response"
            }
        
        except Exception as e:
            logger.error(f"Classification error: {e}")
            return {
                "category": "general",
                "confidence": 0.5,
                "reasoning": "Error in classification, defaulting to general"
            }


class RAGResponder:
    """Generate answers using RAG."""
    
    def __init__(self):
        self.rag_chain = initialize_rag_chain()
    
    def respond(self, query: str) -> Dict[str, Any]:
        """
        Generate RAG-based response.
        
        Args:
            query: Customer query
        
        Returns:
            RAG response with answer and sources
        """
        logger.info(f"Generating RAG response for: {query[:50]}...")
        
        try:
            result = self.rag_chain.answer_query(query)
            return result
        
        except Exception as e:
            logger.error(f"RAG response error: {e}")
            return {
                "query": query,
                "answer": f"I apologize, but I encountered an error retrieving information. Please contact our support team at support@techgear.com or call 1800-TECHGEAR.",
                "retrieved_docs_count": 0,
                "sources": []
            }


class EscalationHandler:
    """Handle query escalation to human support."""
    
    @staticmethod
    def escalate(query: str, reason: str) -> Dict[str, Any]:
        """
        Escalate query to human support.
        
        Args:
            query: Original customer query
            reason: Reason for escalation
        
        Returns:
            Escalation response
        """
        logger.warning(f"Escalating query: {query[:50]}... Reason: {reason}")
        
        return {
            "query": query,
            "answer": f"""I appreciate your query, but I need to escalate this to our specialist team for better assistance.

Reason: {reason}

Our support team will contact you shortly:
📧 Email: support@techgear.com
📞 Phone: 1800-TECHGEAR (1800-832-4432)
⏰ Hours: Monday-Saturday, 9:00 AM - 6:00 PM IST

Reference ID: {datetime.now().strftime('%Y%m%d%H%M%S%f')}""",
            "is_escalated": True,
            "escalation_reason": reason
        }


class InteractionLogger:
    """Log interactions to database for analytics."""
    
    @staticmethod
    def log_interaction(interaction_data: Dict[str, Any]):
        """Log interaction to file."""
        try:
            with open(DB_PATH, 'a') as f:
                f.write(json.dumps(interaction_data) + "\n")
            logger.info(f"Interaction logged: {interaction_data.get('query', '')[:50]}...")
        except Exception as e:
            logger.error(f"Error logging interaction: {e}")


def create_workflow_graph():
    """
    Create LangGraph workflow graph.
    
    Workflow:
    1. Classifier Node: Categorize incoming query
    2. Router: Route to appropriate handler based on classification
    3. RAG Responder Node: Generate answer for standard queries
    4. Escalation Node: Handle complex/unhandled queries
    5. Logger Node: Log interaction
    """
    
    graph = StateGraph(dict)
    
    # Initialize components
    classifier = QueryClassifier()
    rag_responder = RAGResponder()
    escalation_handler = EscalationHandler()
    logger_component = InteractionLogger()
    
    # Node 1: Classifier
    def classify_node(state: dict) -> dict:
        """Classify incoming query."""
        query = state.get("query", "")
        conversation_id = state.get("conversation_id", "")
        
        logger.info(f"[{conversation_id}] Entering Classifier Node")
        
        classification = classifier.classify(query)
        
        state["classification"] = classification
        state["timestamp"] = datetime.now().isoformat()
        
        logger.info(f"[{conversation_id}] Classified as: {classification['category']}")
        
        return state
    
    # Node 2: RAG Responder (for products, support, warranty queries)
    def rag_responder_node(state: dict) -> dict:
        """Generate answer using RAG."""
        query = state.get("query", "")
        conversation_id = state.get("conversation_id", "")
        
        logger.info(f"[{conversation_id}] Entering RAG Responder Node")
        
        rag_response = rag_responder.respond(query)
        
        state["answer"] = rag_response.get("answer", "")
        state["retrieved_docs_count"] = rag_response.get("retrieved_docs_count", 0)
        state["sources"] = rag_response.get("sources", [])
        state["is_escalated"] = False
        
        logger.info(f"[{conversation_id}] Generated RAG response")
        
        return state
    
    # Node 3: Escalation Handler
    def escalation_node(state: dict) -> dict:
        """Escalate query to human support."""
        query = state.get("query", "")
        classification = state.get("classification", {})
        conversation_id = state.get("conversation_id", "")
        
        logger.info(f"[{conversation_id}] Entering Escalation Node")
        
        reason = f"Query about {classification.get('category', 'general')} requires specialist review."
        
        escalation_response = escalation_handler.escalate(query, reason)
        
        state["answer"] = escalation_response.get("answer", "")
        state["is_escalated"] = escalation_response.get("is_escalated", True)
        state["escalation_reason"] = escalation_response.get("escalation_reason", "")
        
        logger.info(f"[{conversation_id}] Query escalated")
        
        return state
    
    # Node 4: Logger
    def logger_node(state: dict) -> dict:
        """Log interaction to database."""
        conversation_id = state.get("conversation_id", "")
        
        logger.info(f"[{conversation_id}] Logging interaction")
        
        interaction_data = {
            "conversation_id": conversation_id,
            "query": state.get("query", ""),
            "category": state.get("classification", {}).get("category", "unknown"),
            "answer": state.get("answer", ""),
            "is_escalated": state.get("is_escalated", False),
            "retrieved_docs_count": state.get("retrieved_docs_count", 0),
            "timestamp": state.get("timestamp", datetime.now().isoformat()),
            "sources": state.get("sources", [])
        }
        
        logger_component.log_interaction(interaction_data)
        
        return state
    
    # Conditional routing function
    def route_based_on_classification(state: dict) -> str:
        """Route based on query classification."""
        classification = state.get("classification", {})
        category = classification.get("category", "general")
        confidence = classification.get("confidence", 0)
        
        # Low confidence queries go to escalation
        if confidence < 0.5:
            return "escalation"
        
        # Route based on category
        if category in ["products", "warranty", "support"]:
            return "rag_responder"
        elif category == "returns":
            return "rag_responder"  # RAG has return policy info
        else:
            return "rag_responder"  # Try RAG first, escalate if needed
    
    # Add nodes
    graph.add_node("classifier", classify_node)
    graph.add_node("rag_responder", rag_responder_node)
    graph.add_node("escalation", escalation_node)
    graph.add_node("logger", logger_node)
    
    # Add edges
    graph.set_entry_point("classifier")
    graph.add_conditional_edges(
        "classifier",
        route_based_on_classification,
        {
            "rag_responder": "rag_responder",
            "escalation": "escalation"
        }
    )
    
    # Both responder and escalation go to logger, then END
    graph.add_edge("rag_responder", "logger")
    graph.add_edge("escalation", "logger")
    graph.add_edge("logger", END)
    
    logger.info("LangGraph workflow created successfully")
    
    return graph.compile()


# Global workflow instance
_workflow = None


def get_workflow():
    """Get or create workflow instance."""
    global _workflow
    if _workflow is None:
        _workflow = create_workflow_graph()
    return _workflow


def process_query(query: str, conversation_id: str = None) -> Dict[str, Any]:
    """
    Process customer query through workflow.
    
    Args:
        query: Customer query
        conversation_id: Optional conversation ID for tracking
    
    Returns:
        Final response from workflow
    """
    import uuid
    
    if conversation_id is None:
        conversation_id = str(uuid.uuid4())[:8]
    
    logger.info(f"[{conversation_id}] Processing query: {query}")
    
    # Initialize state
    initial_state = {
        "query": query,
        "conversation_id": conversation_id,
        "classification": None,
        "answer": "",
        "is_escalated": False,
        "retrieved_docs_count": 0,
        "sources": [],
        "metadata": {}
    }
    
    # Process through workflow
    workflow = get_workflow()
    final_state = workflow.invoke(initial_state)
    
    # Prepare output
    response = {
        "conversation_id": conversation_id,
        "query": query,
        "answer": final_state.get("answer", ""),
        "category": final_state.get("classification", {}).get("category", "unknown"),
        "is_escalated": final_state.get("is_escalated", False),
        "retrieved_docs_count": final_state.get("retrieved_docs_count", 0),
        "sources": final_state.get("sources", []),
        "timestamp": final_state.get("timestamp", datetime.now().isoformat())
    }
    
    logger.info(f"[{conversation_id}] Query processed successfully")
    
    return response


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test workflow
    test_queries = [
        "What is the warranty on SmartWatch Pro X?",
        "Can I return my earbuds after 10 days?",
        "My smartwatch won't turn on, help!",
        "What are your business hours?",
        "Hello, I'd like to know about your products"
    ]
    
    for query in test_queries:
        print("\n" + "="*60)
        print(f"Query: {query}")
        print("="*60)
        
        response = process_query(query)
        
        print(f"Answer: {response['answer']}")
        print(f"Category: {response['category']}")
        print(f"Escalated: {response['is_escalated']}")
        print(f"Sources: {response['sources']}")
