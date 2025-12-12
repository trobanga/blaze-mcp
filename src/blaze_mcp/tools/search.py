"""Search operations for FHIR resources."""

import json
from typing import Any

from mcp.types import TextContent, Tool

from ..client import BlazeClient
from ..config import settings

SEARCH_TOOLS = [
    Tool(
        name="search_resources",
        description="Search for FHIR resources of a given type with query parameters",
        inputSchema={
            "type": "object",
            "properties": {
                "resource_type": {
                    "type": "string",
                    "description": "FHIR resource type (e.g., Patient, Observation)",
                },
                "params": {
                    "type": "object",
                    "description": "Search parameters as key-value pairs",
                    "additionalProperties": {"type": "string"},
                },
                "count": {
                    "type": "integer",
                    "description": f"Max resources to return (default: {settings.default_page_size})",
                },
            },
            "required": ["resource_type"],
        },
    ),
    Tool(
        name="search_system",
        description="Search across all FHIR resource types",
        inputSchema={
            "type": "object",
            "properties": {
                "params": {
                    "type": "object",
                    "description": "Search parameters as key-value pairs",
                    "additionalProperties": {"type": "string"},
                },
                "count": {
                    "type": "integer",
                    "description": f"Max resources to return (default: {settings.default_page_size})",
                },
            },
        },
    ),
]


async def handle_search_tool(
    client: BlazeClient, name: str, arguments: dict[str, Any]
) -> list[TextContent] | None:
    """Handle search tool calls. Returns None if tool not handled."""
    try:
        count = arguments.get("count", settings.default_page_size)
        count = min(count, settings.max_page_size)

        if name == "search_resources":
            result = await client.search(
                arguments["resource_type"],
                arguments.get("params"),
                count,
            )
        elif name == "search_system":
            result = await client.search_system(
                arguments.get("params"),
                count,
            )
        else:
            return None

        # Summarize bundle response
        total = result.get("total", "unknown")
        entries = result.get("entry", [])

        summary = f"Found {total} total results, returning {len(entries)} entries.\n\n"
        summary += json.dumps(result, indent=2)

        return [TextContent(type="text", text=summary)]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {e!s}")]
