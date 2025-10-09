from typing import List, Dict, Optional
from google.cloud import aiplatform_v1
from vertexai.language_models import TextEmbeddingModel
import os
import json
import structlog

logger = structlog.get_logger()


class RAGSystem:
    """RAG system using Vertex AI Vector Search and Text Embeddings."""

    def __init__(self, index_endpoint: str, project_id: Optional[str] = None):
        self.index_endpoint = index_endpoint
        self.client = aiplatform_v1.MatchServiceClient()
        self.project_id = project_id or os.getenv("PROJECT_ID")
        self.embedding_model = TextEmbeddingModel.from_pretrained("textembedding-gecko@003")

    def create_embedding(self, text: str) -> List[float]:
        """Create text embedding using Vertex AI."""
        try:
            embeddings = self.embedding_model.get_embeddings([text])
            return embeddings[0].values
        except Exception as e:
            logger.error("Failed to create embedding", error=str(e))
            raise

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search for relevant documents using query text."""
        try:
            # Create embedding for the query
            query_embedding = self.create_embedding(query)
            
            # Search vector index
            request = aiplatform_v1.FindNeighborsRequest(
                index_endpoint=self.index_endpoint,
                queries=[
                    aiplatform_v1.FindNeighborsRequest.Query(
                        datapoint=aiplatform_v1.IndexDatapoint(feature_vector=query_embedding),
                        neighbor_count=top_k,
                    )
                ],
            )
            response = self.client.find_neighbors(request)
            
            results: List[Dict] = []
            for neighbor in response.nearest_neighbors[0].neighbors:
                # Extract metadata from datapoint
                metadata = {}
                if neighbor.datapoint.restricts:
                    for restrict in neighbor.datapoint.restricts:
                        if restrict.allow_list:
                            metadata.update(restrict.allow_list)
                
                results.append({
                    "id": neighbor.datapoint.datapoint_id,
                    "distance": neighbor.distance,
                    "metadata": metadata,
                    "content": metadata.get("content", ""),
                    "source": metadata.get("source", ""),
                })
            
            logger.info("RAG search completed", query=query[:100], results_count=len(results))
            return results
            
        except Exception as e:
            logger.error("RAG search failed", error=str(e))
            return []

    def get_context(self, query: str, top_k: int = 3) -> str:
        """Get formatted context from search results."""
        results = self.search(query, top_k)
        if not results:
            return ""
        
        context_parts = []
        for i, result in enumerate(results, 1):
            content = result.get("content", "")
            source = result.get("source", "Unknown")
            context_parts.append(f"Document {i} (Source: {source}):\n{content}")
        
        return "\n\n".join(context_parts)


class RAGAgent:
    """Agent with RAG capabilities for enhanced responses."""

    def __init__(self, endpoint, rag_system: RAGSystem):
        self.endpoint = endpoint
        self.rag = rag_system

    def chat(self, user_message: str, conversation_history: List[Dict] = None) -> str:
        """Chat with RAG-enhanced responses."""
        try:
            # Search for relevant context
            relevant_docs = self.rag.search(user_message, top_k=3)
            
            # Build context from search results
            context = self.rag.get_context(user_message, top_k=3)
            
            # Create system message with context
            system_message = """You are a helpful assistant for a sports ticketing service. 
Use the provided context to answer questions accurately. If the context doesn't contain 
relevant information, use your general knowledge but indicate when you're not certain.

Context:
{context}""".format(context=context)
            
            # Build messages
            messages = [{"role": "system", "content": system_message}]
            if conversation_history:
                messages.extend(conversation_history)
            messages.append({"role": "user", "content": user_message})
            
            # Get response from model
            response = self.endpoint.predict(instances=[{"messages": messages}])
            return response.predictions[0]["response"]
            
        except Exception as e:
            logger.error("RAG agent chat failed", error=str(e))
            # Fallback to regular chat
            messages = [{"role": "user", "content": user_message}]
            response = self.endpoint.predict(instances=[{"messages": messages}])
            return response.predictions[0]["response"]


def create_sample_documents() -> List[Dict]:
    """Create sample documents for RAG system."""
    return [
        {
            "id": "team-info-1",
            "content": "The Lakers play at Crypto.com Arena in Los Angeles. Home games are typically on Tuesday, Thursday, and Sunday evenings.",
            "source": "team_info",
            "category": "venue"
        },
        {
            "id": "ticket-policy-1", 
            "content": "Tickets can be upgraded up to 2 hours before game time. Upgrades are subject to availability and price difference.",
            "source": "ticket_policy",
            "category": "upgrades"
        },
        {
            "id": "refund-policy-1",
            "content": "Refunds are available up to 24 hours before the event. After that, exchanges may be available for a fee.",
            "source": "refund_policy", 
            "category": "refunds"
        },
        {
            "id": "parking-info-1",
            "content": "Parking is available at the arena for $25-40 depending on the event. Valet parking is $60.",
            "source": "parking_info",
            "category": "parking"
        }
    ]
