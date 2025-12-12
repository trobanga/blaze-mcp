"""Main MCP server for Blaze FHIR server."""

import argparse
import asyncio
import json
import logging
from typing import Any

from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.server.stdio import stdio_server
from mcp.types import GetPromptResult, Prompt, PromptArgument, PromptMessage
from mcp.types import Resource, TextContent, TextResourceContents, Tool

from .client import BlazeClient
from .config import settings
from .tools import get_all_tools, handle_tool_call

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_server() -> tuple[Server, BlazeClient]:
    """Create and configure the MCP server."""
    server = Server("blaze-mcp")
    client = BlazeClient()

    # Register tools
    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return get_all_tools()

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        return await handle_tool_call(client, name, arguments)

    # Register resources
    @server.list_resources()
    async def list_resources() -> list[Resource]:
        return [
            Resource(
                uri="blaze://capabilities",
                name="FHIR CapabilityStatement",
                description="The FHIR CapabilityStatement describing server capabilities",
                mimeType="application/fhir+json",
            ),
            Resource(
                uri="blaze://resource-types",
                name="Supported Resource Types",
                description="List of FHIR resource types supported by this server",
                mimeType="application/json",
            ),
            Resource(
                uri="blaze://totals",
                name="Resource Totals",
                description="Count of resources by type",
                mimeType="application/json",
            ),
        ]

    @server.read_resource()
    async def read_resource(uri: str) -> TextResourceContents:
        if uri == "blaze://capabilities":
            capabilities = await client.capabilities()
            return TextResourceContents(
                uri=uri,
                mimeType="application/fhir+json",
                text=json.dumps(capabilities, indent=2),
            )
        elif uri == "blaze://resource-types":
            capabilities = await client.capabilities()
            rest = capabilities.get("rest", [{}])[0]
            resources = rest.get("resource", [])
            types = [r.get("type") for r in resources if r.get("type")]
            return TextResourceContents(
                uri=uri,
                mimeType="application/json",
                text=json.dumps({"resourceTypes": sorted(types)}, indent=2),
            )
        elif uri == "blaze://totals":
            totals = await client.totals()
            params = totals.get("parameter", [])
            counts = {p.get("name"): p.get("valueUnsignedInt", 0) for p in params}
            return TextResourceContents(
                uri=uri,
                mimeType="application/json",
                text=json.dumps(counts, indent=2),
            )
        else:
            raise ValueError(f"Unknown resource URI: {uri}")

    # Register prompts
    @server.list_prompts()
    async def list_prompts() -> list[Prompt]:
        return [
            Prompt(
                name="patient_summary",
                description="Generate a clinical summary for a patient",
                arguments=[
                    PromptArgument(
                        name="patient_id",
                        description="The Patient resource ID",
                        required=True,
                    ),
                ],
            ),
            Prompt(
                name="cohort_query",
                description="Help build a query to find a cohort of patients",
                arguments=[
                    PromptArgument(
                        name="criteria",
                        description="Description of the patient criteria",
                        required=True,
                    ),
                ],
            ),
            Prompt(
                name="analyze_measure",
                description="Analyze and explain a MeasureReport result",
                arguments=[
                    PromptArgument(
                        name="measure_id",
                        description="The Measure resource ID",
                        required=True,
                    ),
                ],
            ),
            Prompt(
                name="fhir_query_help",
                description="Help construct a FHIR search query",
                arguments=[
                    PromptArgument(
                        name="resource_type",
                        description="The FHIR resource type to search",
                        required=True,
                    ),
                    PromptArgument(
                        name="goal",
                        description="What you're trying to find",
                        required=True,
                    ),
                ],
            ),
        ]

    @server.get_prompt()
    async def get_prompt(name: str, arguments: dict[str, str] | None) -> GetPromptResult:
        args = arguments or {}

        if name == "patient_summary":
            patient_id = args.get("patient_id", "")
            return GetPromptResult(
                description=f"Generate clinical summary for patient {patient_id}",
                messages=[
                    PromptMessage(
                        role="user",
                        content=TextContent(
                            type="text",
                            text=f"""Please generate a clinical summary for patient {patient_id}.

Use the patient_everything tool to retrieve all data for this patient, then create a structured summary including:

1. **Demographics**: Name, age, gender, contact information
2. **Active Conditions**: Current diagnoses and health issues
3. **Medications**: Current prescriptions and dosages
4. **Recent Encounters**: Last few visits and their purposes
5. **Key Observations**: Important vital signs and lab results
6. **Allergies**: Known allergies and intolerances
7. **Care Team**: Involved healthcare providers

Present the information in a clear, concise format suitable for clinical review.""",
                        ),
                    ),
                ],
            )
        elif name == "cohort_query":
            criteria = args.get("criteria", "")
            return GetPromptResult(
                description=f"Build query for: {criteria}",
                messages=[
                    PromptMessage(
                        role="user",
                        content=TextContent(
                            type="text",
                            text=f"""Help me build a FHIR search query to find patients matching these criteria:

{criteria}

Please:
1. Identify the relevant FHIR resource types needed
2. Determine the appropriate search parameters
3. Construct the search query step by step
4. Execute the search using the search_resources tool
5. Summarize the results

If the criteria would require CQL for complex logic, explain what would be needed.""",
                        ),
                    ),
                ],
            )
        elif name == "analyze_measure":
            measure_id = args.get("measure_id", "")
            return GetPromptResult(
                description=f"Analyze measure {measure_id}",
                messages=[
                    PromptMessage(
                        role="user",
                        content=TextContent(
                            type="text",
                            text=f"""Please analyze the quality measure {measure_id}.

1. First, use read_resource to get the Measure definition
2. Explain what this measure is evaluating
3. Use evaluate_measure to run the measure (you may need to ask for the period)
4. Interpret the MeasureReport results:
   - Population counts (initial, denominator, numerator, etc.)
   - Calculated rates/percentages
   - What the results mean clinically
5. Suggest potential areas for improvement if applicable""",
                        ),
                    ),
                ],
            )
        elif name == "fhir_query_help":
            resource_type = args.get("resource_type", "")
            goal = args.get("goal", "")
            return GetPromptResult(
                description=f"Help build {resource_type} query",
                messages=[
                    PromptMessage(
                        role="user",
                        content=TextContent(
                            type="text",
                            text=f"""Help me construct a FHIR search query for {resource_type} resources.

Goal: {goal}

Please:
1. Read the blaze://capabilities resource to see available search parameters for {resource_type}
2. Recommend which search parameters to use
3. Explain the syntax for each parameter
4. Build and execute the query using search_resources
5. Show example results and explain how to refine the query if needed""",
                        ),
                    ),
                ],
            )
        else:
            raise ValueError(f"Unknown prompt: {name}")

    logger.info(f"Blaze MCP server configured for {settings.blaze_base_url}")

    return server, client


async def run_stdio_server() -> None:
    """Run the MCP server with stdio transport."""
    server, client = create_server()

    try:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
            )
    finally:
        await client.close()


async def run_sse_server(host: str, port: int) -> None:
    """Run the MCP server with SSE transport."""
    from starlette.applications import Starlette
    from starlette.routing import Mount, Route

    import uvicorn

    server, client = create_server()
    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        async with sse.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await server.run(
                streams[0],
                streams[1],
                server.create_initialization_options(),
            )

    app = Starlette(
        debug=True,
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )

    logger.info(f"Starting SSE server on http://{host}:{port}")
    logger.info(f"  SSE endpoint: http://{host}:{port}/sse")
    logger.info(f"  Messages endpoint: http://{host}:{port}/messages/")

    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server_instance = uvicorn.Server(config)

    try:
        await server_instance.serve()
    finally:
        await client.close()


def main() -> None:
    """Entry point for the blaze-mcp command."""
    parser = argparse.ArgumentParser(description="Blaze MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default=settings.transport,
        help="Transport mode (default: stdio)",
    )
    parser.add_argument(
        "--host",
        default=settings.host,
        help="Host for SSE server (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=settings.port,
        help="Port for SSE server (default: 8000)",
    )
    args = parser.parse_args()

    if args.transport == "sse":
        asyncio.run(run_sse_server(args.host, args.port))
    else:
        asyncio.run(run_stdio_server())


if __name__ == "__main__":
    main()
