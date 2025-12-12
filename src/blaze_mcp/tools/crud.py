"""CRUD operations for FHIR resources."""

import json
from typing import Any

from mcp.types import TextContent, Tool

from ..client import BlazeClient

CRUD_TOOLS = [
    Tool(
        name="read_resource",
        description="Read a FHIR resource by type and ID",
        inputSchema={
            "type": "object",
            "properties": {
                "resource_type": {
                    "type": "string",
                    "description": "FHIR resource type (e.g., Patient, Observation)",
                },
                "resource_id": {
                    "type": "string",
                    "description": "Resource ID",
                },
            },
            "required": ["resource_type", "resource_id"],
        },
    ),
    Tool(
        name="vread_resource",
        description="Read a specific version of a FHIR resource",
        inputSchema={
            "type": "object",
            "properties": {
                "resource_type": {
                    "type": "string",
                    "description": "FHIR resource type",
                },
                "resource_id": {
                    "type": "string",
                    "description": "Resource ID",
                },
                "version_id": {
                    "type": "string",
                    "description": "Version ID",
                },
            },
            "required": ["resource_type", "resource_id", "version_id"],
        },
    ),
    Tool(
        name="create_resource",
        description="Create a new FHIR resource",
        inputSchema={
            "type": "object",
            "properties": {
                "resource_type": {
                    "type": "string",
                    "description": "FHIR resource type",
                },
                "resource": {
                    "type": "object",
                    "description": "The FHIR resource to create (JSON object)",
                },
            },
            "required": ["resource_type", "resource"],
        },
    ),
    Tool(
        name="update_resource",
        description="Update an existing FHIR resource",
        inputSchema={
            "type": "object",
            "properties": {
                "resource_type": {
                    "type": "string",
                    "description": "FHIR resource type",
                },
                "resource_id": {
                    "type": "string",
                    "description": "Resource ID",
                },
                "resource": {
                    "type": "object",
                    "description": "The updated FHIR resource (JSON object)",
                },
            },
            "required": ["resource_type", "resource_id", "resource"],
        },
    ),
    Tool(
        name="delete_resource",
        description="Delete a FHIR resource",
        inputSchema={
            "type": "object",
            "properties": {
                "resource_type": {
                    "type": "string",
                    "description": "FHIR resource type",
                },
                "resource_id": {
                    "type": "string",
                    "description": "Resource ID",
                },
            },
            "required": ["resource_type", "resource_id"],
        },
    ),
    Tool(
        name="get_history",
        description="Get the version history of a FHIR resource",
        inputSchema={
            "type": "object",
            "properties": {
                "resource_type": {
                    "type": "string",
                    "description": "FHIR resource type",
                },
                "resource_id": {
                    "type": "string",
                    "description": "Resource ID",
                },
                "count": {
                    "type": "integer",
                    "description": "Maximum number of versions to return",
                },
            },
            "required": ["resource_type", "resource_id"],
        },
    ),
    Tool(
        name="transaction",
        description="Execute a FHIR transaction bundle",
        inputSchema={
            "type": "object",
            "properties": {
                "bundle": {
                    "type": "object",
                    "description": "FHIR Bundle resource with type 'transaction' or 'batch'",
                },
            },
            "required": ["bundle"],
        },
    ),
]


async def handle_crud_tool(
    client: BlazeClient, name: str, arguments: dict[str, Any]
) -> list[TextContent] | None:
    """Handle CRUD tool calls. Returns None if tool not handled."""
    try:
        if name == "read_resource":
            result = await client.read(
                arguments["resource_type"],
                arguments["resource_id"],
            )
        elif name == "vread_resource":
            result = await client.vread(
                arguments["resource_type"],
                arguments["resource_id"],
                arguments["version_id"],
            )
        elif name == "create_resource":
            result = await client.create(
                arguments["resource_type"],
                arguments["resource"],
            )
        elif name == "update_resource":
            result = await client.update(
                arguments["resource_type"],
                arguments["resource_id"],
                arguments["resource"],
            )
        elif name == "delete_resource":
            deleted = await client.delete(
                arguments["resource_type"],
                arguments["resource_id"],
            )
            return [TextContent(type="text", text=f"Resource deleted: {deleted}")]
        elif name == "get_history":
            result = await client.history(
                arguments["resource_type"],
                arguments["resource_id"],
                arguments.get("count"),
            )
        elif name == "transaction":
            result = await client.transaction(arguments["bundle"])
        else:
            return None

        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {e!s}")]
