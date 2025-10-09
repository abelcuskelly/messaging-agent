# Qdrant Vector Database Setup Guide

Complete guide for setting up and using Qdrant vector database for ticket knowledge.

## Why Qdrant?

- ✅ **Open-source** and self-hostable
- ✅ **High performance** with HNSW indexing (millisecond search)
- ✅ **Easy Python SDK** with async support
- ✅ **Metadata filtering** for complex queries
- ✅ **Production-ready** with clustering and replication
- ✅ **Docker deployment** for easy setup
- ✅ **Cloud option** available (Qdrant Cloud)

## Installation Options

### Option 1: Docker (Recommended)

```bash
# Using Docker Compose (easiest)
docker compose -f docker-compose.qdrant.yml up -d

# Or using Docker directly
docker run -d \
  --name qwen-qdrant \
  -p 6333:6333 \
  -p 6334:6334 \
  -v $(pwd)/qdrant_storage:/qdrant/storage \
  qdrant/qdrant:latest

# Verify it's running
curl http://localhost:6333/health
```

### Option 2: Qdrant Cloud (Managed)

```bash
# Sign up at https://cloud.qdrant.io
# Get your cluster URL and API key
# Set environment variables:
export QDRANT_HOST=your-cluster.qdrant.io
export QDRANT_PORT=6333
export QDRANT_API_KEY=your-api-key
```

### Option 3: Local Binary

```bash
# Download from https://github.com/qdrant/qdrant/releases
wget https://github.com/qdrant/qdrant/releases/latest/download/qdrant-x86_64-unknown-linux-gnu.tar.gz
tar -xzf qdrant-x86_64-unknown-linux-gnu.tar.gz
./qdrant
```

## Quick Start

### 1. Install Python Dependencies

```bash
pip install qdrant-client sentence-transformers
```

### 2. Initialize Vector Database

```python
from vector_db.qdrant_manager import get_vector_db, get_ticket_knowledge_base

# Initialize
vector_db = get_vector_db()
kb = get_ticket_knowledge_base()

# Check connection
info = vector_db.get_collection_info()
print(f"Collection: {info['name']}")
print(f"Documents: {info['points_count']}")
```

### 3. Load Your Ticket Knowledge

```python
# Option A: Load from JSON file
kb.load_from_knowledge_base("knowledge_base.json")

# Option B: Add individual documents
kb.add_ticket_pricing(
    game="Lakers vs Warriors",
    date="2024-03-15",
    venue="Crypto.com Arena",
    pricing={
        "lower_bowl": "150-300",
        "upper_bowl": "50-120",
        "courtside": "800-2000"
    }
)

kb.add_policy(
    policy_type="refund",
    title="Refund Policy",
    description="Full refunds available up to 48 hours before game",
    rules={
        "full_refund_hours": 48,
        "partial_refund_hours": 24,
        "exchange_fee": 15
    }
)

kb.add_venue_info(
    venue_name="Crypto.com Arena",
    address="1111 S Figueroa St, Los Angeles, CA",
    capacity=19068,
    sections=["101-130", "301-330", "200s"],
    amenities=["Premium dining", "VIP lounges"]
)
```

### 4. Search Your Knowledge

```python
# Semantic search
results = vector_db.search("What are the ticket prices?", top_k=3)

for result in results:
    print(f"Score: {result['score']:.3f}")
    print(f"Content: {result['content']}")
    print(f"Metadata: {result['metadata']}")

# Filtered search
results = kb.search_pricing(
    query="Lakers tickets",
    game="Lakers vs Warriors",
    date_range=("2024-03-01", "2024-03-31")
)

# Policy search
refund_info = kb.search_policies("refund policy", policy_type="refund")

# Venue search
venue_info = kb.search_venues("parking at arena")
```

## Data Structure

### Document Format

```json
{
  "id": "unique_document_id",
  "content": "Full text content for semantic search",
  "metadata": {
    "category": "pricing|policy|venue|statistics",
    "game": "Lakers vs Warriors",
    "date": "2024-03-15",
    "venue": "Crypto.com Arena",
    "pricing": {
      "lower_bowl": "150-300",
      "upper_bowl": "50-120"
    }
  }
}
```

### Categories

- **pricing**: Ticket prices, seat categories, dynamic pricing
- **policy**: Refund, upgrade, exchange policies
- **venue**: Arena information, seating charts, amenities
- **statistics**: Team stats, player info, records
- **parking**: Parking rates and locations
- **concessions**: Food and beverage pricing

## Integration with RAG

```python
from vector_db.qdrant_manager import get_vector_db
from agent.rag import RAGAgent

# Initialize vector DB
vector_db = get_vector_db()

# Use in RAG agent
class QdrantRAGAgent:
    def __init__(self, endpoint, vector_db):
        self.endpoint = endpoint
        self.vector_db = vector_db
    
    def chat(self, user_message: str) -> str:
        # Search knowledge base
        relevant_docs = self.vector_db.search(user_message, top_k=3)
        
        # Build context
        context = "\n\n".join([
            f"Source: {doc['content']}"
            for doc in relevant_docs
        ])
        
        # Create prompt with context
        system_message = f"""You are a helpful ticketing assistant.
Use this information to answer the question:

{context}

If the information isn't in the context, use your general knowledge."""
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
        
        # Get response
        response = self.endpoint.predict(instances=[{"messages": messages}])
        return response.predictions[0]["response"]
```

## Advanced Features

### Metadata Filtering

```python
# Search with filters
results = vector_db.search(
    query="ticket prices",
    top_k=5,
    filters={
        "category": "pricing",
        "date": ("2024-03-01", "2024-03-31"),  # Date range
        "venue": "Crypto.com Arena"
    },
    score_threshold=0.7  # Minimum similarity
)
```

### Batch Operations

```python
# Batch add documents
documents = [
    {
        "id": "doc_1",
        "content": "Content 1",
        "metadata": {"category": "pricing"}
    },
    {
        "id": "doc_2",
        "content": "Content 2",
        "metadata": {"category": "policy"}
    }
]

count = vector_db.add_documents_batch(documents)
print(f"Added {count} documents")
```

### Update Documents

```python
# Update document content
vector_db.update_document(
    doc_id="pricing_lakers_warriors",
    content="Updated pricing information...",
    metadata={"updated": True}
)
```

## Performance Optimization

### 1. Embedding Model Selection

```python
# Faster, smaller model (default)
vector_db = QdrantVectorDB(embedding_model="all-MiniLM-L6-v2", vector_size=384)

# More accurate, larger model
vector_db = QdrantVectorDB(embedding_model="all-mpnet-base-v2", vector_size=768)

# Multilingual support
vector_db = QdrantVectorDB(embedding_model="paraphrase-multilingual-MiniLM-L12-v2", vector_size=384)
```

### 2. Indexing Configuration

```python
# For production, configure HNSW parameters
from qdrant_client.models import HnswConfigDiff

client.update_collection(
    collection_name="ticket_knowledge",
    hnsw_config=HnswConfigDiff(
        m=16,  # Number of edges per node
        ef_construct=100,  # Size of dynamic candidate list
    )
)
```

### 3. Caching

```python
# Cache embeddings
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_embedding(text: str) -> List[float]:
    return vector_db.create_embedding(text)
```

## Monitoring

### Collection Statistics

```python
info = vector_db.get_collection_info()
print(f"Documents: {info['points_count']}")
print(f"Vectors: {info['vectors_count']}")
print(f"Status: {info['status']}")
```

### Search Performance

```python
import time

start = time.time()
results = vector_db.search("ticket prices", top_k=10)
duration = (time.time() - start) * 1000

print(f"Search completed in {duration:.2f}ms")
print(f"Results: {len(results)}")
```

## Production Deployment

### 1. High Availability Setup

```yaml
# docker-compose-ha.yml
version: '3.8'
services:
  qdrant-1:
    image: qdrant/qdrant:latest
    ports: ["6333:6333"]
    volumes: ["./qdrant_1:/qdrant/storage"]
  
  qdrant-2:
    image: qdrant/qdrant:latest
    ports: ["6335:6333"]
    volumes: ["./qdrant_2:/qdrant/storage"]
```

### 2. Backup Strategy

```bash
# Backup Qdrant data
docker exec qwen-qdrant tar -czf /tmp/backup.tar.gz /qdrant/storage
docker cp qwen-qdrant:/tmp/backup.tar.gz ./backups/qdrant-$(date +%Y%m%d).tar.gz

# Restore from backup
docker cp ./backups/qdrant-20240315.tar.gz qwen-qdrant:/tmp/backup.tar.gz
docker exec qwen-qdrant tar -xzf /tmp/backup.tar.gz -C /
```

### 3. Monitoring

```python
# Add to your monitoring dashboard
from vector_db.qdrant_manager import get_vector_db

vector_db = get_vector_db()
info = vector_db.get_collection_info()

metrics = {
    "vector_db_documents": info["points_count"],
    "vector_db_status": info["status"],
    "vector_db_size_mb": info.get("size_mb", 0)
}
```

## Troubleshooting

### Connection Issues

```python
# Test connection
from qdrant_client import QdrantClient

client = QdrantClient(host="localhost", port=6333)
try:
    client.get_collections()
    print("✅ Connected to Qdrant")
except Exception as e:
    print(f"❌ Connection failed: {e}")
```

### Performance Issues

```bash
# Check Qdrant logs
docker logs qwen-qdrant

# Monitor resource usage
docker stats qwen-qdrant
```

### Data Issues

```python
# Verify document count
info = vector_db.get_collection_info()
print(f"Documents in DB: {info['points_count']}")

# Test search
results = vector_db.search("test query", top_k=1)
print(f"Search working: {len(results) > 0}")
```

## Best Practices

1. **Organize by Category**: Use metadata categories for efficient filtering
2. **Consistent Format**: Keep document structure uniform
3. **Regular Updates**: Update pricing and policies frequently
4. **Backup Regularly**: Schedule daily backups
5. **Monitor Performance**: Track search latency and accuracy
6. **Cache Embeddings**: Cache frequently used embeddings
7. **Batch Operations**: Use batch insert for large datasets
8. **Version Control**: Track knowledge base changes

## Next Steps

1. **Start Qdrant**: `docker compose -f docker-compose.qdrant.yml up -d`
2. **Load Data**: `python3 vector_db/qdrant_manager.py`
3. **Test Search**: Run sample queries
4. **Integrate with RAG**: Connect to your messaging agent
5. **Monitor**: Add to your dashboards

Your vector database is now ready to power intelligent, context-aware responses! 🚀
