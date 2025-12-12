"""Administrative operations for Blaze server."""

import json
from typing import Any

from mcp.types import TextContent, Tool

from ..client import BlazeClient
from ..config import settings


def get_admin_tools() -> list[Tool]:
    """Get admin tools if enabled."""
    if not settings.admin_tools_enabled:
        return []

    return [
        Tool(
            name="get_totals",
            description="Get resource counts by type (fast O(1) operation)",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="run_compaction",
            description="Trigger database compaction",
            inputSchema={
                "type": "object",
                "properties": {
                    "column_family": {
                        "type": "string",
                        "description": "Specific column family to compact (optional)",
                    },
                },
            },
        ),
        Tool(
            name="run_reindex",
            description="Trigger re-indexing of search parameters",
            inputSchema={
                "type": "object",
                "properties": {
                    "resource_type": {
                        "type": "string",
                        "description": "Resource type to re-index (optional, all if not specified)",
                    },
                    "search_param": {
                        "type": "string",
                        "description": "Specific search parameter to re-index (optional)",
                    },
                },
            },
        ),
    ]


async def handle_admin_tool(
    client: BlazeClient, name: str, arguments: dict[str, Any]
) -> list[TextContent] | None:
    """Handle admin tool calls. Returns None if tool not handled."""
    if not settings.admin_tools_enabled:
        return None

    try:
        if name == "get_totals":
            result = await client.totals()
            # Format nicely
            params = result.get("parameter", [])
            summary = "Resource totals:\n"
            for param in params:
                name_part = param.get("name", "")
                value = param.get("valueUnsignedInt", 0)
                summary += f"  {name_part}: {value}\n"
            return [TextContent(type="text", text=summary)]

        elif name == "run_compaction":
            result = await client.compact(arguments.get("column_family"))
            return [
                TextContent(
                    type="text",
                    text=f"Compaction triggered: {json.dumps(result, indent=2)}",
                )
            ]

        elif name == "run_reindex":
            result = await client.reindex(
                arguments.get("resource_type"),
                arguments.get("search_param"),
            )
            return [
                TextContent(
                    type="text",
                    text=f"Re-index triggered: {json.dumps(result, indent=2)}",
                )
            ]

        else:
            return None

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {e!s}")]
