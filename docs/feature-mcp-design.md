# Feature MCP: Code Map & Design (v3 - Polymorphic)

This document details the architecture for a polymorphic agent that can dynamically manage its own toolset at runtime.

## 1. File Manifest (v3)

### New Directories

-   `agent_server/`: Contains the FastAPI server for the agent.
-   `tool_server/`: Contains the FastAPI server for the tools.
-   `tests/`: Contains integration and unit tests.

### New Files

-   `agent_server/main.py`: The FastAPI application that exposes endpoints to control the agent.
-   `agent_server/requirements.txt`: Dependencies for the agent server.
-   `agent_server/Dockerfile`: To build the agent server container image.
-   `tool_server/main.py`: The FastAPI application for serving tools.
-   `tool_server/requirements.txt`: Dependencies for the tool server.
-   `tool_server/Dockerfile`: To build the tool server container image.
-   `docker-compose.yml`: Defines and orchestrates the services.
-   `.env`: Stores environment variables.
-   `tests/test_integration.py`: Initial integration test for the agent and tool servers.
-   `tests/test_tool_server.py`: Unit tests for individual tools.


### Modified Files

-   `run.py`: Refactored from the main agentic loop into a simple client for the `agent_server`. The original file has been backed up to `run.py.bak`.
-   `.gitignore`: Add `.env`, `__pycache__/`, `*.pyc`.

### Deleted Files

-   `tools.py`: Functionality will be migrated to `tool_server/main.py`.
-   `tools/` (directory): Manifests are no longer needed.

## 2. API Contracts & Schemas

### 2.1. Agent Server

-   **Endpoint:** `POST /agent/execute_task`
-   **Request Body:** `{"goal": "The user's objective..."}`
-   **Response:** `{"status": "completed", "final_answer": "..."}`

### 2.2. Tool Server

-   **Endpoint:** `POST /tools/{tool_name}` (e.g., `/tools/web_search`)
-   **Request/Response:** Standard contracts for each tool.

### 2.3. MCP Server (NEW Admin API)

This is the crucial new component. The MCP must expose an administrative API.

-   **Endpoint:** `POST /mcp/admin/toolsets`
-   **Purpose:** To dynamically update the list of active toolsets.
-   **Request Body:**
    ```json
    {
        "action": "ACTIVATE" | "DEACTIVATE",
        "toolset_ids": ["web_tools", "file_system_tools", "database_tools"]
    }
    ```

### 2.4. Agent's Internal `manage_toolsets` Tool (NEW)

This is a permanent, "meta-tool" that is always available to the agent. It is hardcoded into the agent's system prompt and is not part of the external tool server.

-   **Tool Name:** `manage_toolsets`
-   **Purpose:** Allows the model to change its own available tools.
-   **JSON Schema (for the model's reference):
    ```json
    {
        "name": "manage_toolsets",
        "description": "Activates or deactivates sets of tools to manage context and capabilities. Use this to acquire new tools for a task or to dismiss tools that are no longer needed.",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["ACTIVATE", "DEACTIVATE"],
                    "description": "The action to perform."
                },
                "toolset_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "A list of toolset identifiers to act upon (e.g., 'web_tools')."
                }
            },
            "required": ["action", "toolset_ids"]
        }
    }
    ```

## 3. Data Flow: Dynamic Tool Management

This sequence describes how the agent changes its own toolset.

1.  **Agent Reasoning:** The agent's model determines it needs a different set of tools. For example, its current prompt might be: "Okay, I have finished searching the web. I no longer need the web tools and now need the file system tools to save the results."
2.  **Model Generates Meta-Tool Call:** The model generates a JSON block for the internal `manage_toolsets` tool.
    ```json
    {
        "tool_name": "manage_toolsets",
        "parameters": {
            "action": "DEACTIVATE",
            "toolset_ids": ["web_tools"]
        }
    }
    // ... and another call to ACTIVATE file_system_tools
    ```
3.  **Agent Server Intercepts:** The Agent Server's main loop receives this tool call. It has a special `if` condition:
    ```python
    if tool_call['tool_name'] == 'manage_toolsets':
        # This is a meta-tool call, handle it internally.
        call_mcp_admin_api(tool_call['parameters'])
    else:
        # This is a standard tool call, send it to the MCP.
        call_mcp_execute_api(tool_call)
    ```
4.  **Agent Server -> MCP Admin API:** The agent server makes a `POST` request to `http://mcp-server:8080/mcp/admin/toolsets`, sending the parameters from the model's tool call.
5.  **MCP Server Reconfigures:** The MCP server receives the admin request. It dynamically updates its internal list of active tools. The next time the agent's model needs the tool list, the MCP will provide the newly configured set.
6.  **Agent Server Responds to Model:** The Agent Server confirms to the model that the toolsets have been updated, and the agent continues its reasoning loop with a new set of capabilities.

## 4. Containerization & Configuration (No Changes from v2)

### `agent_server/Dockerfile`

```Dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY agent_server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "agent_server.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

`tool_server/Dockerfile`

```Dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY tool_server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8001
CMD ["uvicorn", "tool_server.main:app", "--host", "0.0.0.0", "--port", "8001"]

`docker-compose.yml` (v3 Draft)

```yaml
version: '3.8'
services:
  agent-server:
    build:
      context: .
      dockerfile: agent_server/Dockerfile
    ports:
      - "8000:8000" # Expose agent API to the host
    env_file:
      - .env
    depends_on:
      - tool-server
      - mcp-server
    environment:
      - MCP_SERVER_URL=http://mcp-server:8080

  tool-server:
    build:
      context: .
      dockerfile: tool_server/Dockerfile
    ports:
      - "8001:8001"

  mcp-server:
    image: gcr.io/path/to/mcp/image:latest # Placeholder for the MCP server image
    ports:
      - "8080:8080"
    volumes:
      - ./mcp_config:/config # Mount a directory for MCP configuration files
    command: >
      mcp-server-binary
      --config /config/tool_registry.json
    # Note: The MCP server must expose the '/mcp/admin/toolsets' endpoint
    # for dynamic tool management.
```

## 5. Development and Testing Strategy

To ensure a robust and reliable refactoring process, we will adopt an incremental, test-driven development approach. This strategy will allow us to validate each component as it's built and integrated into the new microservice architecture.

### 5.1. Testing Framework

We will use `pytest` as the primary framework for our tests. Its powerful features, such as fixtures and clear assert statements, make it ideal for testing our FastAPI applications and business logic.

### 5.2. Test Organization

All tests will be placed in a dedicated `tests/` directory at the root of the project. This keeps the tests separate from the application code and makes them easy to discover and run.

### 5.3. Integration Testing

The first priority is to establish an integration test that verifies the core communication path of the new architecture. This initial test will:

1.  **Simulate a client request** to the `agent_server`'s `/agent/execute_task` endpoint.
2.  **Mock the `tool_server`'s response** to isolate the `agent_server`'s logic.
3.  **Assert** that the `agent_server` correctly processes a goal that requires a tool.
4.  **Verify** that the `agent_server` attempts to call the appropriate endpoint on the (mocked) `tool_server`.
5.  **Check** that the final response from the `agent_server` is structured correctly.

This end-to-end test (with a mocked tool server) will serve as a baseline to ensure the fundamental agent loop is functioning correctly before we build out the specific tools.

### 5.4. Unit Testing

As we migrate functionality from the original `tools.py` file into the new `tool_server`, we will create corresponding unit tests for each individual tool. For example, when implementing the `web_search` tool in the `tool_server`, we will create `tests/test_tool_server.py` with a specific test function that:

-   Calls the `/tools/web_search` endpoint directly.
-   Provides valid and invalid parameters.
-   Asserts that the tool returns the expected output or a correct error message.

This granular approach ensures that each tool's logic is sound and behaves as expected in isolation. By combining comprehensive unit tests with overarching integration tests, we can proceed with the refactoring confidently, knowing that each piece of the system is verified at every step.
