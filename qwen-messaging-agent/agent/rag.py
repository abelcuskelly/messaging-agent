from typing import List, Dict
from google.cloud import aiplatform_v1


class RAGSystem:
    """RAG using Vertex AI Vector Search MatchService."""

    def __init__(self, index_endpoint: str):
        self.index_endpoint = index_endpoint
        self.client = aiplatform_v1.MatchServiceClient()

    def search(self, embedding: List[float], top_k: int = 5) -> List[Dict]:
        request = aiplatform_v1.FindNeighborsRequest(
            index_endpoint=self.index_endpoint,
            queries=[
                aiplatform_v1.FindNeighborsRequest.Query(
                    datapoint=aiplatform_v1.IndexDatapoint(feature_vector=embedding),
                    neighbor_count=top_k,
                )
            ],
        )
        response = self.client.find_neighbors(request)
        results: List[Dict] = []
        for neighbor in response.nearest_neighbors[0].neighbors:
            results.append(
                {
                    "id": neighbor.datapoint.datapoint_id,
                    "distance": neighbor.distance,
                }
            )
        return results


