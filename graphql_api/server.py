"""
GraphQL API Server
Flexible query interface with subscriptions
"""

from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL
import uvicorn
from .schema import schema

# Create FastAPI app
app = FastAPI(
    title="Qwen Messaging Agent GraphQL API",
    description="Flexible GraphQL interface for messaging agent",
    version="1.0.0"
)

# Create GraphQL router
graphql_app = GraphQLRouter(
    schema,
    subscription_protocols=[
        GRAPHQL_TRANSPORT_WS_PROTOCOL,
        GRAPHQL_WS_PROTOCOL,
    ],
)

# Mount GraphQL endpoint
app.include_router(graphql_app, prefix="/graphql")

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Qwen Messaging Agent GraphQL API",
        "graphql_endpoint": "/graphql",
        "graphql_playground": "/graphql (open in browser)",
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    """Health check."""
    return {"status": "healthy", "api_type": "graphql"}


if __name__ == "__main__":
    print("🚀 Starting GraphQL API Server")
    print("📊 GraphQL Playground: http://localhost:8001/graphql")
    print("📖 API Docs: http://localhost:8001/docs")
    print("\nExample Queries:")
    print("""
    query {
      conversations(limit: 5) {
        id
        state
        messageCount
      }
    }
    
    mutation {
      sendMessage(input: {message: "Hello"}) {
        response
        conversationId
      }
    }
    
    subscription {
      messageUpdates(conversationId: "conv_123") {
        content
        timestamp
      }
    }
    """)
    
    uvicorn.run(app, host="0.0.0.0", port=8001)
