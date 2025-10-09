"""
Qdrant Vector Database Manager
Efficient storage and retrieval of ticket knowledge with semantic search
"""

import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import structlog
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, Filter, FieldCondition,
    MatchValue, Range, SearchRequest, UpdateStatus
)
from sentence_transformers import SentenceTransformer

logger = structlog.get_logger()


class QdrantVectorDB:
    """
    Vector database manager using Qdrant.
    Handles ticket knowledge storage and semantic search.
    """
    
    def __init__(
        self,
        host: str = None,
        port: int = None,
        collection_name: str = "ticket_knowledge",
        embedding_model: str = "all-MiniLM-L6-v2",
        vector_size: int = 384
    ):
        """
        Initialize Qdrant vector database.
        
        Args:
            host: Qdrant server host
            port: Qdrant server port
            collection_name: Name of the collection
            embedding_model: Sentence transformer model name
            vector_size: Dimension of embeddings
        """
        self.host = host or os.getenv("QDRANT_HOST", "localhost")
        self.port = port or int(os.getenv("QDRANT_PORT", 6333))
        self.collection_name = collection_name
        self.vector_size = vector_size
        
        # Initialize Qdrant client
        self.client = QdrantClient(host=self.host, port=self.port)
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer(embedding_model)
        
        # Create collection if it doesn't exist
        self._ensure_collection()
        
        logger.info("Qdrant vector DB initialized",
                   host=self.host,
                   port=self.port,
                   collection=collection_name)
    
    def _ensure_collection(self):
        """Create collection if it doesn't exist."""
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        if self.collection_name not in collection_names:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE
                )
            )
            logger.info("Collection created", name=self.collection_name)
        else:
            logger.info("Collection already exists", name=self.collection_name)
    
    def create_embedding(self, text: str) -> List[float]:
        """Create embedding for text."""
        embedding = self.embedding_model.encode(text)
        return embedding.tolist()
    
    def add_document(
        self,
        doc_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add a document to the vector database.
        
        Args:
            doc_id: Unique document identifier
            content: Document text content
            metadata: Additional metadata (category, source, price, etc.)
            
        Returns:
            True if successful
        """
        try:
            # Create embedding
            embedding = self.create_embedding(content)
            
            # Prepare payload
            payload = {
                "content": content,
                "created_at": datetime.utcnow().isoformat(),
                **(metadata or {})
            }
            
            # Create point
            point = PointStruct(
                id=hash(doc_id) & 0x7FFFFFFF,  # Convert to positive int
                vector=embedding,
                payload=payload
            )
            
            # Upsert point
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            logger.info("Document added",
                       doc_id=doc_id,
                       content_length=len(content))
            
            return True
            
        except Exception as e:
            logger.error("Failed to add document",
                        doc_id=doc_id,
                        error=str(e))
            return False
    
    def add_documents_batch(
        self,
        documents: List[Dict[str, Any]]
    ) -> int:
        """
        Add multiple documents in batch.
        
        Args:
            documents: List of dicts with 'id', 'content', and optional 'metadata'
            
        Returns:
            Number of documents successfully added
        """
        points = []
        
        for doc in documents:
            try:
                doc_id = doc.get("id")
                content = doc.get("content")
                metadata = doc.get("metadata", {})
                
                if not doc_id or not content:
                    continue
                
                # Create embedding
                embedding = self.create_embedding(content)
                
                # Prepare payload
                payload = {
                    "content": content,
                    "created_at": datetime.utcnow().isoformat(),
                    **metadata
                }
                
                # Create point
                point = PointStruct(
                    id=hash(doc_id) & 0x7FFFFFFF,
                    vector=embedding,
                    payload=payload
                )
                
                points.append(point)
                
            except Exception as e:
                logger.error("Failed to process document",
                           doc_id=doc.get("id"),
                           error=str(e))
        
        # Batch upsert
        if points:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            logger.info("Batch documents added", count=len(points))
        
        return len(points)
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        score_threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents.
        
        Args:
            query: Search query text
            top_k: Number of results to return
            filters: Optional metadata filters (e.g., category, price_range)
            score_threshold: Minimum similarity score
            
        Returns:
            List of matching documents with scores
        """
        try:
            # Create query embedding
            query_embedding = self.create_embedding(query)
            
            # Build filter if provided
            search_filter = None
            if filters:
                conditions = []
                for key, value in filters.items():
                    if isinstance(value, (list, tuple)):
                        # Range filter
                        conditions.append(
                            FieldCondition(
                                key=key,
                                range=Range(gte=value[0], lte=value[1])
                            )
                        )
                    else:
                        # Exact match
                        conditions.append(
                            FieldCondition(
                                key=key,
                                match=MatchValue(value=value)
                            )
                        )
                
                if conditions:
                    search_filter = Filter(must=conditions)
            
            # Search
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=top_k,
                query_filter=search_filter,
                score_threshold=score_threshold
            )
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "id": result.id,
                    "score": result.score,
                    "content": result.payload.get("content", ""),
                    "metadata": {
                        k: v for k, v in result.payload.items()
                        if k not in ["content", "created_at"]
                    },
                    "created_at": result.payload.get("created_at")
                })
            
            logger.info("Search completed",
                       query=query[:50],
                       results_count=len(formatted_results))
            
            return formatted_results
            
        except Exception as e:
            logger.error("Search failed", query=query, error=str(e))
            return []
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document by ID."""
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=[hash(doc_id) & 0x7FFFFFFF]
            )
            
            logger.info("Document deleted", doc_id=doc_id)
            return True
            
        except Exception as e:
            logger.error("Failed to delete document",
                        doc_id=doc_id,
                        error=str(e))
            return False
    
    def update_document(
        self,
        doc_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update a document's content or metadata."""
        try:
            point_id = hash(doc_id) & 0x7FFFFFFF
            
            # Get existing document
            existing = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[point_id]
            )
            
            if not existing:
                logger.warning("Document not found for update", doc_id=doc_id)
                return False
            
            # Update content if provided
            if content:
                embedding = self.create_embedding(content)
                payload = existing[0].payload
                payload["content"] = content
                payload["updated_at"] = datetime.utcnow().isoformat()
                
                if metadata:
                    payload.update(metadata)
                
                point = PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=payload
                )
                
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=[point]
                )
            
            logger.info("Document updated", doc_id=doc_id)
            return True
            
        except Exception as e:
            logger.error("Failed to update document",
                        doc_id=doc_id,
                        error=str(e))
            return False
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get collection information and statistics."""
        try:
            info = self.client.get_collection(self.collection_name)
            
            return {
                "name": self.collection_name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status.value,
                "config": {
                    "vector_size": self.vector_size,
                    "distance": "cosine"
                }
            }
            
        except Exception as e:
            logger.error("Failed to get collection info", error=str(e))
            return {}
    
    def clear_collection(self) -> bool:
        """Clear all documents from collection."""
        try:
            self.client.delete_collection(self.collection_name)
            self._ensure_collection()
            
            logger.warning("Collection cleared", name=self.collection_name)
            return True
            
        except Exception as e:
            logger.error("Failed to clear collection", error=str(e))
            return False


class TicketKnowledgeBase:
    """High-level interface for ticket knowledge management."""
    
    def __init__(self, vector_db: QdrantVectorDB):
        self.db = vector_db
    
    def add_ticket_pricing(
        self,
        game: str,
        date: str,
        venue: str,
        pricing: Dict[str, Any]
    ) -> bool:
        """Add ticket pricing information."""
        content = f"{game} on {date} at {venue}. "
        content += " ".join([
            f"{section}: ${price_range}"
            for section, price_range in pricing.items()
        ])
        
        metadata = {
            "category": "pricing",
            "game": game,
            "date": date,
            "venue": venue,
            "pricing": pricing
        }
        
        doc_id = f"pricing_{game}_{date}".replace(" ", "_")
        return self.db.add_document(doc_id, content, metadata)
    
    def add_policy(
        self,
        policy_type: str,
        title: str,
        description: str,
        rules: Dict[str, Any]
    ) -> bool:
        """Add policy information (refund, upgrade, etc.)."""
        content = f"{title}: {description}. "
        content += " ".join([
            f"{key}: {value}"
            for key, value in rules.items()
        ])
        
        metadata = {
            "category": "policy",
            "policy_type": policy_type,
            "title": title,
            "rules": rules
        }
        
        doc_id = f"policy_{policy_type}".replace(" ", "_")
        return self.db.add_document(doc_id, content, metadata)
    
    def add_venue_info(
        self,
        venue_name: str,
        address: str,
        capacity: int,
        sections: List[str],
        amenities: List[str]
    ) -> bool:
        """Add venue information."""
        content = f"{venue_name} located at {address}. "
        content += f"Capacity: {capacity}. "
        content += f"Sections: {', '.join(sections)}. "
        content += f"Amenities: {', '.join(amenities)}."
        
        metadata = {
            "category": "venue",
            "venue_name": venue_name,
            "address": address,
            "capacity": capacity,
            "sections": sections,
            "amenities": amenities
        }
        
        doc_id = f"venue_{venue_name}".replace(" ", "_")
        return self.db.add_document(doc_id, content, metadata)
    
    def search_pricing(
        self,
        query: str,
        game: Optional[str] = None,
        date_range: Optional[tuple] = None
    ) -> List[Dict[str, Any]]:
        """Search for pricing information."""
        filters = {"category": "pricing"}
        
        if game:
            filters["game"] = game
        
        if date_range:
            filters["date"] = date_range
        
        return self.db.search(query, top_k=5, filters=filters)
    
    def search_policies(
        self,
        query: str,
        policy_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search for policy information."""
        filters = {"category": "policy"}
        
        if policy_type:
            filters["policy_type"] = policy_type
        
        return self.db.search(query, top_k=3, filters=filters)
    
    def search_venues(self, query: str) -> List[Dict[str, Any]]:
        """Search for venue information."""
        filters = {"category": "venue"}
        return self.db.search(query, top_k=3, filters=filters)
    
    def load_from_knowledge_base(self, kb_file: str) -> int:
        """Load documents from knowledge base JSON file."""
        try:
            with open(kb_file, 'r') as f:
                documents = json.load(f)
            
            count = self.db.add_documents_batch(documents)
            logger.info("Knowledge base loaded",
                       file=kb_file,
                       documents=count)
            
            return count
            
        except Exception as e:
            logger.error("Failed to load knowledge base",
                        file=kb_file,
                        error=str(e))
            return 0


def create_sample_ticket_knowledge():
    """Create sample ticket knowledge for testing."""
    return [
        {
            "id": "pricing_lakers_warriors_2024_03_15",
            "content": "Lakers vs Warriors on March 15, 2024 at Crypto.com Arena. Lower bowl: $150-300, Upper bowl: $50-120, Courtside: $800-2000. Game time: 7:30 PM PST.",
            "metadata": {
                "category": "pricing",
                "game": "Lakers vs Warriors",
                "date": "2024-03-15",
                "venue": "Crypto.com Arena",
                "pricing": {
                    "lower_bowl": "150-300",
                    "upper_bowl": "50-120",
                    "courtside": "800-2000"
                }
            }
        },
        {
            "id": "policy_refund",
            "content": "Refund Policy: Full refunds available up to 48 hours before game time. Partial refunds (75%) available 24-48 hours before. No refunds within 24 hours of game time. Exchanges may be available for a $15 fee.",
            "metadata": {
                "category": "policy",
                "policy_type": "refund",
                "title": "Refund Policy",
                "rules": {
                    "full_refund_hours": 48,
                    "partial_refund_hours": 24,
                    "partial_refund_percentage": 75,
                    "exchange_fee": 15
                }
            }
        },
        {
            "id": "policy_upgrade",
            "content": "Seat Upgrade Policy: Upgrades available up to 2 hours before game time. Upgrade cost is the difference between current seat price and new seat price plus $25 processing fee. Upgrades subject to availability.",
            "metadata": {
                "category": "policy",
                "policy_type": "upgrade",
                "title": "Seat Upgrade Policy",
                "rules": {
                    "upgrade_deadline_hours": 2,
                    "processing_fee": 25
                }
            }
        },
        {
            "id": "venue_crypto_arena",
            "content": "Crypto.com Arena located at 1111 S Figueroa St, Los Angeles, CA 90015. Capacity: 19,068 for basketball. Sections: Lower bowl 101-130, Upper bowl 301-330, Club sections 200s, Courtside rows A-F. Amenities: Premium dining, VIP lounges, accessible seating, family restrooms.",
            "metadata": {
                "category": "venue",
                "venue_name": "Crypto.com Arena",
                "address": "1111 S Figueroa St, Los Angeles, CA 90015",
                "capacity": 19068,
                "sections": ["101-130", "301-330", "200s", "A-F"],
                "amenities": ["Premium dining", "VIP lounges", "Accessible seating"]
            }
        },
        {
            "id": "parking_crypto_arena",
            "content": "Crypto.com Arena parking: General parking $25-40, Premium parking $50-75, Valet parking $60-80. Parking opens 2 hours before game time. Limited street parking available nearby.",
            "metadata": {
                "category": "parking",
                "venue": "Crypto.com Arena",
                "pricing": {
                    "general": "25-40",
                    "premium": "50-75",
                    "valet": "60-80"
                }
            }
        },
        {
            "id": "team_stats_lakers_2024",
            "content": "Lakers 2023-24 season: 45-25 record, 3rd in Western Conference. LeBron James averaging 25.2 points, Anthony Davis 24.8 points. Home record: 28-8, Away record: 17-17. Playoff bound.",
            "metadata": {
                "category": "statistics",
                "team": "Lakers",
                "season": "2023-24",
                "record": "45-25",
                "conference_rank": 3
            }
        }
    ]


# Global vector DB instance
_vector_db: Optional[QdrantVectorDB] = None
_knowledge_base: Optional[TicketKnowledgeBase] = None


def get_vector_db() -> QdrantVectorDB:
    """Get or create global vector DB instance."""
    global _vector_db
    
    if _vector_db is None:
        _vector_db = QdrantVectorDB()
        logger.info("Vector DB instance created")
    
    return _vector_db


def get_ticket_knowledge_base() -> TicketKnowledgeBase:
    """Get or create global ticket knowledge base."""
    global _knowledge_base
    
    if _knowledge_base is None:
        vector_db = get_vector_db()
        _knowledge_base = TicketKnowledgeBase(vector_db)
        logger.info("Ticket knowledge base instance created")
    
    return _knowledge_base


if __name__ == "__main__":
    print("🗄️  Setting up Qdrant Vector Database...")
    
    # Initialize
    vector_db = get_vector_db()
    kb = get_ticket_knowledge_base()
    
    # Load sample data
    print("\n📚 Loading sample ticket knowledge...")
    sample_docs = create_sample_ticket_knowledge()
    count = vector_db.add_documents_batch(sample_docs)
    print(f"✅ Loaded {count} documents")
    
    # Get collection info
    info = vector_db.get_collection_info()
    print(f"\n📊 Collection Info:")
    print(f"   Name: {info['name']}")
    print(f"   Documents: {info['points_count']}")
    print(f"   Vector Size: {info['config']['vector_size']}")
    
    # Test search
    print("\n🔍 Testing semantic search...")
    test_queries = [
        "What are the ticket prices?",
        "What's the refund policy?",
        "Where is the arena located?",
        "How much does parking cost?"
    ]
    
    for query in test_queries:
        print(f"\n   Query: {query}")
        results = vector_db.search(query, top_k=2)
        for i, result in enumerate(results, 1):
            print(f"   {i}. Score: {result['score']:.3f}")
            print(f"      {result['content'][:80]}...")
    
    print("\n✅ Vector database setup complete!")
    print("\n💡 Your ticket knowledge is now searchable with semantic search!")
