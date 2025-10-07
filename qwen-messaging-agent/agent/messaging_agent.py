from typing import List, Dict
from google.cloud import aiplatform


class MessagingAgent:
    """Simple stateful chat agent wrapping a Vertex AI Endpoint."""

    def __init__(self, endpoint: aiplatform.Endpoint):
        self.endpoint = endpoint
        self.conversation_history: List[Dict[str, str]] = []

    def chat(self, user_message: str) -> str:
        self.conversation_history.append({"role": "user", "content": user_message})
        prediction = self.endpoint.predict(
            instances=[{"messages": self.conversation_history}]
        )
        response = prediction.predictions[0]["response"]
        self.conversation_history.append({"role": "assistant", "content": response})
        return response

    def trim_history(self, max_messages: int = 50) -> None:
        if len(self.conversation_history) > max_messages:
            self.conversation_history = self.conversation_history[-max_messages:]


