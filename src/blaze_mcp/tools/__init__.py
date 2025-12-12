"""MCP tools for Blaze FHIR operations."""

from typing import Any

from mcp.types import TextContent, Tool

from ..client import BlazeClient
from .admin import get_admin_tools, handle_admin_tool
from .advanced import ADVANCED_TOOLS, handle_advanced_tool
from .connection import CONNECTION_TOOLS, handle_connection_tool
from .crud import CRUD_TOOLS, handle_crud_tool
from .search import SEARCH_TOOLS, handle_search_tool
from .terminology import TERMINOLOGY_TOOLS, handle_terminology_tool


def get_all_tools() -> list[Tool]:
    """Get all available tools."""
    return [
        *CONNECTION_TOOLS,
        *CRUD_TOOLS,
        *SEARCH_TOOLS,
        *TERMINOLOGY_TOOLS,
        *ADVANCED_TOOLS,
        *get_admin_tools(),
    ]


async def handle_tool_call(
    client: BlazeClient, name: str, arguments: dict[str, Any]
) -> list[TextContent]:
    """Route tool calls to appropriate handlers."""
    handlers = [
        handle_connection_tool,
        handle_crud_tool,
        handle_search_tool,
        handle_terminology_tool,
        handle_advanced_tool,
        handle_admin_tool,
    ]

    for handler in handlers:
        result = await handler(client, name, arguments)
        if result is not None:
            return result

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


__all__ = ["get_all_tools", "handle_tool_call"]
