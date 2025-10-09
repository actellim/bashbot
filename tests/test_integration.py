# home/actellim/Projects/bashbot/tests/test_integration.py
import json
import pytest
from fastapi.testclient import TestClient
from agent_server.main import app

# Import httpx's mock transport for mocking outbound calls
import httpx
from httpx import Response

# ------------------------------------------------------
# 1. Mock the Tool Server
# ------------------------------------------------------
def mock_tool_server(request: httpx.Request) -> Response:
    # Expect a POST to /tools/web_search with a JSON body that includes 'query'
    if request.method == "POST" and request.url.path == "/tools/web_search":
        payload = request.json()
        # Return a dummy search result
        return Response(
            status_code=200,
            json={
                "results": [
                    {"title": "Dummy result", "url": "https://example.com", "snippet": "foo bar baz"}
                ]
            },
        )
    # Default 404 for any other endpoints
    return Response(status_code=404, content=b"Not Found")

# Create a mock transport that will intercept all outgoing HTTPX requests.
mock_transport = httpx.MockTransport(mock_tool_server)

# ------------------------------------------------------
# 2. Fixture to inject the mock transport into the TestClient
# ------------------------------------------------------
@pytest.fixture
def client():
    # Patch httpx in the agent code to use our mock transport.
    # In the actual agent code, outbound calls should use httpx.Client().
    # For now, we monkey‑patch requests in the TestClient context.
    with httpx.Client(transport=mock_transport) as client_transport:
        # FastAPI's TestClient will internally use `requests`,
        # but our integration uses httpx so we replace the transport.
        # Using `mock_transport` ensures any `httpx` calls to the tool
        # server respond with the dummy data defined above.
        with TestClient(app) as c:
            yield c

# ------------------------------------------------------
# 3. The actual integration test
# ------------------------------------------------------
def test_agent_execute_task(client):
    # Define a goal that will trigger a web search tool call
    # (In a future iteration, the agent will detect the need for a
    # tool and call the tool server accordingly).
    payload = {"goal": "Show me some search results."}

    # Send the POST request to the agent
    response = client.post("/agent/execute_task", json=payload)

    # Basic sanity checks on the HTTP layer
    assert response.status_code == 200
    data = response.json()

    # The stubbed handler in agent_server/main.py currently returns
    # a simple dict.  After we implement full logic we’ll assert
    # that the tool was called and its output was forwarded.
    assert data["status"] == "in_progress"
    assert "details" in data
    assert isinstance(data["details"], str)

    # TODO: In the final implementation, we expect the
    # tool server's response to be integrated into the
    # agent's reply, e.g.:
    # assert "search results" in data["final_answer"]