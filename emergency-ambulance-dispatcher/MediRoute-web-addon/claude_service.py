
import json
import os
import tempfile
from typing import Any, Optional

import anthropic

from backend.services import data_service as ds
from backend.services import dispatcher
from backend.algorithms.astar import astar

MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5")

SYSTEM_PROMPT = """
You are MediRoute, an educational emergency ambulance dispatch simulator.
Never claim that a real ambulance, hospital, emergency service, or person has been contacted.
Use the MediRoute tools to inspect simulated ambulances, hospitals, traffic, routes, and emergencies.
When the user describes an emergency, extract the location, emergency type, severity (1-5),
and required facility when possible. If important information is missing, ask a concise
clarifying question unless the available information is sufficient for a simulation.
For a dispatch request, use the program's tools rather than inventing ambulance, route,
traffic, or hospital data.
Explain the result clearly and identify that it is simulated.
"""

def _tools():
    return [
        {
            "name": "get_available_ambulances",
            "description": "Return currently available simulated ambulances.",
            "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "name": "get_emergencies",
            "description": "Return simulated emergencies currently known to MediRoute.",
            "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "name": "get_hospitals",
            "description": "Return simulated hospital capacity and facilities.",
            "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "name": "get_traffic_conditions",
            "description": "Return simulated traffic-weighted road data.",
            "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "name": "calculate_route",
            "description": "Calculate a traffic-weighted route in the simulated road graph.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "start": {"type": "string"},
                    "goal": {"type": "string"},
                },
                "required": ["start", "goal"],
                "additionalProperties": False,
            },
        },
        {
            "name": "create_emergency",
            "description": "Create and prioritize a simulated emergency. Severity must be 1-5.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"},
                    "emergency_type": {"type": "string"},
                    "severity": {"type": "integer", "minimum": 1, "maximum": 5},
                    "required_facility": {"type": "string"},
                },
                "required": ["location", "emergency_type", "severity"],
                "additionalProperties": False,
            },
        },
        {
            "name": "dispatch_ambulance",
            "description": "Dispatch the best available simulated ambulance for an emergency.",
            "input_schema": {
                "type": "object",
                "properties": {"emergency_id": {"type": "string"}},
                "required": ["emergency_id"],
                "additionalProperties": False,
            },
        },
        {
            "name": "block_road",
            "description": "Block a simulated road so routing can demonstrate rerouting.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "from_node": {"type": "string"},
                    "to_node": {"type": "string"},
                },
                "required": ["from_node", "to_node"],
                "additionalProperties": False,
            },
        },
        {
            "name": "open_road",
            "description": "Reopen a previously blocked simulated road.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "from_node": {"type": "string"},
                    "to_node": {"type": "string"},
                },
                "required": ["from_node", "to_node"],
                "additionalProperties": False,
            },
        },
    ]


def _call_tool(name: str, args: dict[str, Any]) -> Any:
    if name == "get_available_ambulances":
        return ds.available_ambulances()
    if name == "get_emergencies":
        return dispatcher.emergencies
    if name == "get_hospitals":
        return ds.hospitals
    if name == "get_traffic_conditions":
        return ds.roads
    if name == "calculate_route":
        return astar(ds.roads, args["start"], args["goal"]) or {"error": "No route available"}
    if name == "create_emergency":
        return dispatcher.create_emergency(
            args["location"],
            args["emergency_type"],
            args["severity"],
            args.get("required_facility", ""),
        )
    if name == "dispatch_ambulance":
        return dispatcher.dispatch(args["emergency_id"])
    if name == "block_road":
        return {"ok": ds.update_road(args["from_node"], args["to_node"], "blocked")}
    if name == "open_road":
        return {"ok": ds.update_road(args["from_node"], args["to_node"], "open")}
    raise ValueError(f"Unknown tool: {name}")


def _extract_text(content) -> str:
    parts = []
    for block in content:
        if getattr(block, "type", None) == "text":
            parts.append(block.text)
    return "\n".join(parts).strip()


async def analyze_with_claude(message: str, upload: Optional[Any] = None) -> dict:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return {
            "ok": False,
            "error": "ANTHROPIC_API_KEY is not configured. Add it to your .env file.",
        }

    client = anthropic.Anthropic(api_key=api_key)

    user_content = []
    if message:
        user_content.append({"type": "text", "text": message})

    # PDF upload: send as base64 document content. This keeps the first version
    # self-contained; Anthropic also provides a Files API for larger documents.
    if upload is not None:
        filename = upload.filename or "document"
        data = await upload.read()
        if len(data) > 32 * 1024 * 1024:
            return {"ok": False, "error": "Document is larger than 32 MB."}

        content_type = upload.content_type or ""
        if content_type == "application/pdf" or filename.lower().endswith(".pdf"):
            import base64
            user_content.append({
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": base64.b64encode(data).decode("ascii"),
                },
                "title": filename,
            })
            user_content.append({
                "type": "text",
                "text": "Analyze the uploaded document as part of this simulated emergency request.",
            })
        else:
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError:
                return {
                    "ok": False,
                    "error": "For this first version, upload a PDF or UTF-8 text file.",
                }
            user_content.append({
                "type": "text",
                "text": f"Uploaded document ({filename}):\n\n{text[:200000]}",
            })

    if not user_content:
        return {"ok": False, "error": "No message or document supplied."}

    messages = [{"role": "user", "content": user_content}]

    # Agent/tool loop: Claude chooses a MediRoute tool, our server executes it,
    # then Claude receives the result and continues until it produces a final answer.
    for _ in range(8):
        response = client.messages.create(
            model=MODEL,
            max_tokens=1800,
            system=SYSTEM_PROMPT,
            tools=_tools(),
            messages=messages,
        )

        if response.stop_reason != "tool_use":
            return {
                "ok": True,
                "answer": _extract_text(response.content),
                "model": MODEL,
            }

        messages.append({"role": "assistant", "content": response.content})

        results = []
        for block in response.content:
            if getattr(block, "type", None) != "tool_use":
                continue
            try:
                result = _call_tool(block.name, block.input)
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result, default=str),
                })
            except Exception as exc:
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "is_error": True,
                    "content": str(exc),
                })

        messages.append({"role": "user", "content": results})

    return {
        "ok": False,
        "error": "Claude reached the tool-call safety limit before producing a final answer.",
    }
