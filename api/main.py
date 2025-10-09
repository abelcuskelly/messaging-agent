from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
from google.cloud import aiplatform
import os
import uuid


app = FastAPI()


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    response: str
    conversation_id: str


# In-memory conversation storage (use Redis/Firestore in production)
conversations: dict[str, list[dict[str, str]]] = {}

# Lazy-initialized Vertex AI Endpoint
_endpoint: aiplatform.Endpoint | None = None


def _endpoint_path() -> str:
    project_id = os.getenv("PROJECT_ID", "your-project-id")
    region = os.getenv("REGION", "us-central1")
    endpoint_id = os.getenv("ENDPOINT_ID", "your-endpoint-id")
    return f"projects/{project_id}/locations/{region}/endpoints/{endpoint_id}"


def _require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Simple header-based API key check. If API_KEY env is set, enforce it."""
    expected = os.getenv("API_KEY")
    if expected:
        if not x_api_key or x_api_key != expected:
            raise HTTPException(status_code=401, detail="Unauthorized")


@app.on_event("startup")
def startup_event():
    global _endpoint
    project_id = os.getenv("PROJECT_ID", "your-project-id")
    region = os.getenv("REGION", "us-central1")
    aiplatform.init(project=project_id, location=region)
    try:
        _endpoint = aiplatform.Endpoint(_endpoint_path())
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Failed to initialize Vertex AI endpoint: {exc}") from exc


@app.post("/chat", response_model=ChatResponse, dependencies=[Depends(_require_api_key)])
async def chat(request: ChatRequest):
    if _endpoint is None:
        raise HTTPException(status_code=500, detail="Endpoint not initialized")

    conv_id = request.conversation_id or str(uuid.uuid4())

    # Get or create conversation history
    if conv_id not in conversations:
        conversations[conv_id] = []

    # Add user message
    conversations[conv_id].append({"role": "user", "content": request.message})

    # Get prediction from Vertex AI
    prediction = _endpoint.predict(instances=[{"messages": conversations[conv_id]}])

    try:
        response_text = prediction.predictions[0]["response"]
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Invalid prediction payload: {exc}")

    # Add assistant response to history
    conversations[conv_id].append({"role": "assistant", "content": response_text})

    return ChatResponse(response=response_text, conversation_id=conv_id)


@app.get("/health")
async def health():
    return {"status": "healthy"}


