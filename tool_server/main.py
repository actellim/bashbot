from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class ToolCall(BaseModel):
    tool_args: dict

@app.post("/tools/{tool_name}")
async def execute_tool(tool_name: str, tool_call: ToolCall):
    """Dispatch to the requested tool.
    Currently only a dummy *web_search* implementation is provided
    to satisfy the unit tests.
    """
    # Basic guard: no tool name supplied
    if not tool_name:
        return {"error": "tool_name cannot be empty"}
    # Example: web_search
    if tool_name == "web_search":
        query = tool_call.tool_args.get("query", "")
        # Return a deterministic dummy response so tests are stable.
        return {
            "results": [
                {
                    "title": f"Result for '{query}'",
                    "url": f"https://example.com/search?q={query}",
                    "snippet": f"Summary of {query}..."
                }
            ]
        }
    # Unknown tool
    return {"error": f"Tool '{tool_name}' not found."}
