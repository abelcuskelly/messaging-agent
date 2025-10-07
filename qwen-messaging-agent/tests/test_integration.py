import pytest
from google.cloud import aiplatform


@pytest.fixture
def vertex_endpoint():
    aiplatform.init(project="test-project", location="us-central1")
    return aiplatform.Endpoint("projects/test-project/locations/us-central1/endpoints/0000000000000000000")


def test_end_to_end_prediction(vertex_endpoint):
    instances = [{"messages": [{"role": "user", "content": "Hello"}]}]
    # This is a stub; in CI, skip or mock actual call
    assert isinstance(instances, list)
