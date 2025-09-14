# Feature: MCP Integration Plan (v2)

## 1. Project Goal

The primary goal is to refactor the agent into a professional microservice architecture and to **empower the agent to dynamically manage its own toolset at runtime**, creating a truly polymorphic and context-aware system.

## 2. High-Level Architecture

We will adopt a three-server model, orchestrated by Docker Compose:

1.  **Agent Server:** A FastAPI server that exposes an API for controlling the agent. It will also house the logic for the agent's internal, meta-tools.

2.  **Tool Server:** A FastAPI server that exposes our standard Python tools (e.g., `web_search`) via a REST API.

3.  **MCP Server:** The central hub for tools. Crucially, the MCP server must expose **an administrative API** to allow for the dynamic addition and removal of toolsets during the agent's operation. The agent will call this API to reconfigure its own capabilities on the fly.

4.  **External Ollama Model:** Runs on the host machine, accessible via a `OLLAMA_URL` environment variable.

## 3. Key Changes & Requirements

### 3.1. Agent Server Implementation

-   [ ] Create `agent_server/` directory and FastAPI application.
-   [ ] Refactor `run_agent.py` logic to be callable by the server.
-   [ ] **Implement internal tool-management logic** (see section 3.3).
-   [ ] Containerize the Agent Server.

### 3.2. Tool Server Implementation

-   [ ] Create `tool_server/` directory and FastAPI application.
-   [ ] Create API endpoints for all external tools.
-   [ ] Containerize the Tool Server.

### 3.3. Dynamic Tool Management (Polymorphism)

-   [ ] **MCP Admin API:** The chosen or configured MCP server MUST provide endpoints to dynamically update its active tool configuration (e.g., `POST /admin/toolsets/activate`, `POST /admin/toolsets/deactivate`).
-   [ ] **Internal `manage_toolsets` Tool:** The agent will be given a permanent, built-in "meta-tool" whose description is always in context. This tool is **not** in the tool server.
    -   *Example Schema:* `manage_toolsets(action: Literal['add', 'remove'], toolset_id: str)`
-   [ ] **Agent Logic Update:** The agent's core loop must be updated to recognize a call to `manage_toolsets`. Instead of sending it to the MCP as a standard tool call, the agent will intercept it and make a direct administrative API call to the MCP server to reconfigure the toolset.

### 3.4. Docker Compose & Environment

-   [ ] Create `docker-compose.yml` to define and link `agent-server`, `tool-server`, and `mcp-server`.
-   [ ] Create a `.env` file for secrets and configuration.

## 4. Development Plan

1.  Structure the project: create `agent_server/` and `tool_server/` directories.
2.  Design the API contracts for the Tool Server, Agent Server, and critically, the **MCP Admin API**.
3.  Design the schema for the internal `manage_toolsets` meta-tool.
4.  Build the `tool_server` and `agent_server` with basic endpoints.
5.  Create Dockerfiles and a `docker-compose.yml` to run the services.
6.  Implement the `manage_toolsets` logic within the agent server.
