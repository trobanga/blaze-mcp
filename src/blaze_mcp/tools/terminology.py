"""Terminology service operations."""

import json
from typing import Any

from mcp.types import TextContent, Tool

from ..client import BlazeClient

TERMINOLOGY_TOOLS = [
    Tool(
        name="validate_code",
        description="Validate a code against a code system",
        inputSchema={
            "type": "object",
            "properties": {
                "system": {
                    "type": "string",
                    "description": "The code system URL (e.g., http://loinc.org)",
                },
                "code": {
                    "type": "string",
                    "description": "The code to validate",
                },
                "display": {
                    "type": "string",
                    "description": "Optional display text to validate",
                },
            },
            "required": ["system", "code"],
        },
    ),
    Tool(
        name="expand_valueset",
        description="Expand a value set to list all contained codes",
        inputSchema={
            "type": "object",
            "properties": {
                "valueset_id": {
                    "type": "string",
                    "description": "The ValueSet resource ID",
                },
                "url": {
                    "type": "string",
                    "description": "The ValueSet canonical URL (alternative to ID)",
                },
                "filter": {
                    "type": "string",
                    "description": "Filter text to search within the value set",
                },
                "count": {
                    "type": "integer",
                    "description": "Maximum number of codes to return",
                },
            },
        },
    ),
    Tool(
        name="lookup_code",
        description="Look up detailed information about a code",
        inputSchema={
            "type": "object",
            "properties": {
                "system": {
                    "type": "string",
                    "description": "The code system URL",
                },
                "code": {
                    "type": "string",
                    "description": "The code to look up",
                },
            },
            "required": ["system", "code"],
        },
    ),
]


async def handle_terminology_tool(
    client: BlazeClient, name: str, arguments: dict[str, Any]
) -> list[TextContent] | None:
    """Handle terminology tool calls. Returns None if tool not handled."""
    try:
        if name == "validate_code":
            result = await client.validate_code(
                arguments["system"],
                arguments["code"],
                arguments.get("display"),
            )
        elif name == "expand_valueset":
            result = await client.expand_valueset(
                arguments.get("valueset_id"),
                arguments.get("url"),
                arguments.get("filter"),
                arguments.get("count"),
            )
        elif name == "lookup_code":
            result = await client.lookup_code(
                arguments["system"],
                arguments["code"],
            )
        else:
            return None

        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {e!s}")]
