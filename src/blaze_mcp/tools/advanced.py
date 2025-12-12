"""Advanced query operations (patient-everything, measures, GraphQL)."""

import json
from typing import Any

from mcp.types import TextContent, Tool

from ..client import BlazeClient

ADVANCED_TOOLS = [
    Tool(
        name="patient_everything",
        description="Get all resources in a patient's compartment ($everything)",
        inputSchema={
            "type": "object",
            "properties": {
                "patient_id": {
                    "type": "string",
                    "description": "The Patient resource ID",
                },
                "start": {
                    "type": "string",
                    "description": "Start date filter (YYYY-MM-DD)",
                },
                "end": {
                    "type": "string",
                    "description": "End date filter (YYYY-MM-DD)",
                },
                "count": {
                    "type": "integer",
                    "description": "Maximum number of resources to return",
                },
            },
            "required": ["patient_id"],
        },
    ),
    Tool(
        name="evaluate_measure",
        description="Evaluate a quality measure against patient data",
        inputSchema={
            "type": "object",
            "properties": {
                "measure_id": {
                    "type": "string",
                    "description": "The Measure resource ID",
                },
                "period_start": {
                    "type": "string",
                    "description": "Measurement period start (YYYY-MM-DD)",
                },
                "period_end": {
                    "type": "string",
                    "description": "Measurement period end (YYYY-MM-DD)",
                },
                "subject": {
                    "type": "string",
                    "description": "Subject reference (e.g., Patient/123 or Group/456)",
                },
            },
            "required": ["measure_id", "period_start", "period_end"],
        },
    ),
    Tool(
        name="graphql_query",
        description="Execute a GraphQL query against the FHIR server",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The GraphQL query string",
                },
                "variables": {
                    "type": "object",
                    "description": "GraphQL variables (optional)",
                },
            },
            "required": ["query"],
        },
    ),
]


async def handle_advanced_tool(
    client: BlazeClient, name: str, arguments: dict[str, Any]
) -> list[TextContent] | None:
    """Handle advanced tool calls. Returns None if tool not handled."""
    try:
        if name == "patient_everything":
            result = await client.patient_everything(
                arguments["patient_id"],
                arguments.get("start"),
                arguments.get("end"),
                arguments.get("count"),
            )
            # Summarize the bundle
            entries = result.get("entry", [])
            resource_types: dict[str, int] = {}
            for entry in entries:
                res = entry.get("resource", {})
                rt = res.get("resourceType", "Unknown")
                resource_types[rt] = resource_types.get(rt, 0) + 1

            summary = f"Patient {arguments['patient_id']} has {len(entries)} resources:\n"
            for rt, count in sorted(resource_types.items()):
                summary += f"  - {rt}: {count}\n"
            summary += "\n" + json.dumps(result, indent=2)
            return [TextContent(type="text", text=summary)]

        elif name == "evaluate_measure":
            result = await client.evaluate_measure(
                arguments["measure_id"],
                arguments["period_start"],
                arguments["period_end"],
                arguments.get("subject"),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "graphql_query":
            result = await client.graphql(
                arguments["query"],
                arguments.get("variables"),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        else:
            return None

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {e!s}")]
