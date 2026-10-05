# 🚑 Emergency Ambulance Dispatcher

Educational simulator combining **Claude + MCP + Priority Queue + Min Heap + Graph + A***.

## Run

1. Python 3.10+
2. `python -m venv .venv`
3. Windows: `.venv\\Scripts\\activate`
4. `pip install -r requirements.txt`
5. `uvicorn backend.main:app --reload`
6. Open `http://127.0.0.1:8000`

## MCP

The MCP server is in `mcp_server/server.py`. The current official MCP Python SDK uses `MCPServer` and supports development with `mcp dev`; see the official SDK documentation.

Run locally with:

`uv run mcp dev mcp_server/server.py`

## Demo

Create a critical accident at Gandhipuram → dispatch → block a road → dispatch another emergency to demonstrate dynamic rerouting.

## Claude

The project separates dispatcher logic from MCP tools so Claude can call the tools through an MCP-compatible host. Add your Anthropic API key/model configuration when you are ready to connect Claude. The included web simulator works without an API key.

> This is a simulation for academic use. It does not contact real emergency services, real hospitals, real ambulance GPS, or live traffic systems.
