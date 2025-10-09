# Knowledge Base Setup Guide for Ticket Information

This guide will help you set up a knowledge base for your ticket information using the RAG (Retrieval Augmented Generation) system.

## Overview

The RAG system allows your messaging agent to access specific ticket information, pricing, policies, and statistics to provide accurate answers to customer questions.

## Step 1: Prepare Your Ticket Data

### Supported File Formats

1. **JSON Files** - Structured data like team info, pricing, policies
2. **CSV Files** - Tabular data like game schedules, pricing tables
3. **Text Files** - Unstructured information like policies, descriptions

### Example Data Structures

#### JSON Format
```json
{
  "teams": {
    "lakers": {
      "home_venue": "Crypto.com Arena",
      "city": "Los Angeles",
      "conference": "Western"
    }
  },
  "pricing": {
    "lower_bowl": {"min": 150, "max": 300},
    "upper_bowl": {"min": 50, "max": 120}
  },
  "policies": {
    "refund_hours": 48,
    "upgrade_hours": 2
  }
}
```

#### CSV Format
```csv
game,date,venue,lower_bowl_price,upper_bowl_price,courtside_price
Lakers vs Warriors,2024-03-15,Crypto.com Arena,150-300,50-120,800-2000
Lakers vs Celtics,2024-03-20,Crypto.com Arena,180-350,60-140,900-2200
```

#### Text Format
```
Lakers Ticket Information

Venue: Crypto.com Arena, Los Angeles, CA
Capacity: 19,068 for basketball

Pricing Structure:
- Lower Bowl: $150-300 (sections 101-130)
- Upper Bowl: $50-120 (sections 301-330)
- Courtside: $800-2000 (rows A-F)
```

## Step 2: Create Sample Data (Optional)

If you want to test the system first, create sample data:

```bash
python3 setup_knowledge_base.py --create-samples
```

This creates:
- `sample_ticket_data.json`
- `sample_ticket_data.csv`
- `sample_ticket_data.txt`

## Step 3: Process Your Ticket Data

### Basic Processing
```bash
# Process a JSON file
python3 setup_knowledge_base.py --process-file your_ticket_data.json --output knowledge_base.json

# Process a CSV file
python3 setup_knowledge_base.py --process-file your_ticket_data.csv --output knowledge_base.json

# Process a text file
python3 setup_knowledge_base.py --process-file your_ticket_data.txt --output knowledge_base.json
```

### With Embeddings (Recommended)
```bash
# Create embeddings for better search performance
python3 setup_knowledge_base.py --process-file your_ticket_data.json --create-embeddings --output knowledge_base.json
```

## Step 4: Set Up Vertex AI Vector Search

### Prerequisites
1. Google Cloud Project with Vertex AI enabled
2. Vector Search API enabled
3. Appropriate IAM permissions

### Create Vector Search Index

```python
from google.cloud import aiplatform_v1

def create_vector_index(project_id: str, location: str = "us-central1"):
    """Create a vector search index for your knowledge base."""
    
    client = aiplatform_v1.IndexServiceClient()
    
    # Define index configuration
    index = aiplatform_v1.Index(
        display_name="ticket-knowledge-base",
        description="Knowledge base for ticket information and pricing",
        metadata_schema_uri="gs://google-cloud-aiplatform/schema/matchingengine/metadata/nearest_neighbor_search_1.0.0.yaml",
        index_update_method=aiplatform_v1.Index.IndexUpdateMethod.BATCH_UPDATE,
    )
    
    # Create the index
    parent = f"projects/{project_id}/locations/{location}"
    operation = client.create_index(parent=parent, index=index)
    
    print("Creating index...")
    response = operation.result(timeout=300)
    print(f"Created index: {response.name}")
    
    return response.name
```

### Create Index Endpoint

```python
def create_index_endpoint(project_id: str, location: str = "us-central1"):
    """Create an index endpoint for serving the index."""
    
    client = aiplatform_v1.IndexEndpointServiceClient()
    
    index_endpoint = aiplatform_v1.IndexEndpoint(
        display_name="ticket-knowledge-endpoint",
        description="Endpoint for ticket knowledge base search",
    )
    
    parent = f"projects/{project_id}/locations/{location}"
    operation = client.create_index_endpoint(parent=parent, index_endpoint=index_endpoint)
    
    print("Creating index endpoint...")
    response = operation.result(timeout=300)
    print(f"Created endpoint: {response.name}")
    
    return response.name
```

## Step 5: Upload Documents to Vector Search

```python
def upload_documents_to_index(index_name: str, documents: List[Dict]):
    """Upload processed documents to the vector search index."""
    
    client = aiplatform_v1.IndexServiceClient()
    
    # Prepare datapoints
    datapoints = []
    for doc in documents:
        datapoint = aiplatform_v1.IndexDatapoint(
            datapoint_id=doc["id"],
            feature_vector=doc["embedding"],
            restricts=[
                aiplatform_v1.IndexDatapoint.Restriction(
                    namespace="content",
                    allow_list=[doc["content"]]
                ),
                aiplatform_v1.IndexDatapoint.Restriction(
                    namespace="source", 
                    allow_list=[doc["source"]]
                ),
                aiplatform_v1.IndexDatapoint.Restriction(
                    namespace="category",
                    allow_list=[doc["category"]]
                )
            ]
        )
        datapoints.append(datapoint)
    
    # Upload in batches
    batch_size = 100
    for i in range(0, len(datapoints), batch_size):
        batch = datapoints[i:i + batch_size]
        
        request = aiplatform_v1.UpsertDatapointsRequest(
            index=index_name,
            datapoints=batch
        )
        
        response = client.upsert_datapoints(request=request)
        print(f"Uploaded batch {i//batch_size + 1}: {len(batch)} documents")
```

## Step 6: Integrate with Your Messaging Agent

### Update Your Agent Code

```python
from agent.rag import RAGSystem, RAGAgent

# Initialize RAG system
rag_system = RAGSystem(
    index_endpoint="your-index-endpoint-id",
    project_id="your-project-id"
)

# Create RAG-enhanced agent
rag_agent = RAGAgent(endpoint=your_vertex_endpoint, rag_system=rag_system)

# Use in your chat function
def chat_with_rag(user_message: str, conversation_history: List[Dict] = None):
    return rag_agent.chat(user_message, conversation_history)
```

### Update Your API

```python
# In your FastAPI chat endpoint
@app.post("/chat")
async def chat_with_knowledge_base(request: ChatRequest):
    # Use RAG agent instead of regular agent
    response = rag_agent.chat(
        user_message=request.message,
        conversation_history=conversations.get(request.conversation_id, [])
    )
    
    return ChatResponse(response=response, conversation_id=request.conversation_id)
```

## Step 7: Test Your Knowledge Base

### Test Queries

Try these queries to test your knowledge base:

- "What are the ticket prices for Lakers games?"
- "What's the refund policy?"
- "Where do the Lakers play?"
- "What time do games start?"
- "How much does parking cost?"

### Monitor Performance

Check the logs to see:
- Which documents are being retrieved
- Search relevance scores
- Response quality

## Best Practices

### 1. Data Organization
- Use clear, descriptive content
- Include relevant keywords
- Organize by categories (pricing, policies, venue info)
- Keep documents focused and specific

### 2. Content Quality
- Use consistent formatting
- Include specific details (dates, prices, policies)
- Avoid ambiguous language
- Update regularly

### 3. Search Optimization
- Use relevant keywords in content
- Create embeddings for better semantic search
- Test different query variations
- Monitor search results quality

### 4. Maintenance
- Regularly update ticket information
- Add new games and pricing
- Remove outdated information
- Monitor customer questions for gaps

## Troubleshooting

### Common Issues

1. **No search results**: Check if documents are properly uploaded
2. **Irrelevant results**: Improve document content and keywords
3. **Slow responses**: Optimize embedding creation and search parameters
4. **Authentication errors**: Verify Google Cloud credentials and permissions

### Debug Commands

```bash
# Test document processing
python3 setup_knowledge_base.py --process-file your_data.json --output test.json

# Check embeddings
python3 -c "
from setup_knowledge_base import KnowledgeBaseBuilder
builder = KnowledgeBaseBuilder()
docs = builder.create_sample_ticket_data()
enhanced = builder.create_embeddings_for_documents(docs)
print(f'Created {len(enhanced)} documents with embeddings')
"
```

## Next Steps

1. **Start with sample data** to test the system
2. **Process your actual ticket data** using the provided tools
3. **Set up Vertex AI Vector Search** in your Google Cloud project
4. **Upload your documents** to the vector index
5. **Integrate with your messaging agent**
6. **Test and refine** based on customer interactions

Your knowledge base will help your messaging agent provide accurate, up-to-date information about tickets, pricing, policies, and more!
