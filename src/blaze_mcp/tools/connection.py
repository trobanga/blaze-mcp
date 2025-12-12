"""Connection management tools for dynamic Blaze URL configuration."""

from typing import Any

from mcp.types import TextContent, Tool

from ..client import BlazeClient

CONNECTION_TOOLS = [
    Tool(
        name="set_blaze_url",
        description="Set the Blaze FHIR server URL for subsequent operations. Use this when connecting to a different Blaze instance.",
        inputSchema={
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The Blaze FHIR server base URL (e.g., http://192.168.1.100:8080/fhir)",
                },
            },
            "required": ["url"],
        },
    ),
    Tool(
        name="get_blaze_url",
        description="Get the currently configured Blaze FHIR server URL",
        inputSchema={
            "type": "object",
            "properties": {},
        },
    ),
    Tool(
        name="test_connection",
        description="Test the connection to the Blaze server by fetching its CapabilityStatement",
        inputSchema={
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "Optional: test a specific URL without changing the default",
                },
            },
        },
    ),
]


async def handle_connection_tool(
    client: BlazeClient, name: str, arguments: dict[str, Any]
) -> list[TextContent] | None:
    """Handle connection management tool calls."""
    if name == "set_blaze_url":
        url = arguments["url"].rstrip("/")
        if not url.startswith(("http://", "https://")):
            return [TextContent(type="text", text=f"Error: URL must start with http:// or https://")]

        old_url = client.base_url
        client.set_base_url(url)
        return [
            TextContent(
                type="text",
                text=f"Blaze URL updated:\n  Previous: {old_url}\n  Current:  {url}",
            )
        ]

    elif name == "get_blaze_url":
        return [
            TextContent(
                type="text",
                text=f"Current Blaze URL: {client.base_url}",
            )
        ]

    elif name == "test_connection":
        test_url = arguments.get("url")
        if test_url:
            test_url = test_url.rstrip("/")

        try:
            # Temporarily use the test URL if provided
            if test_url:
                old_url = client.base_url
                client.set_base_url(test_url)

            capabilities = await client.capabilities()

            # Restore original URL if we were just testing
            if test_url:
                client.set_base_url(old_url)

            software = capabilities.get("software", {})
            name_str = software.get("name", "Unknown")
            version = software.get("version", "Unknown")
            fhir_version = capabilities.get("fhirVersion", "Unknown")

            target = test_url or client.base_url
            return [
                TextContent(
                    type="text",
                    text=f"Connection successful to {target}\n"
                    f"  Server: {name_str} {version}\n"
                    f"  FHIR Version: {fhir_version}",
                )
            ]
        except Exception as e:
            target = test_url or client.base_url
            return [
                TextContent(
                    type="text",
                    text=f"Connection failed to {target}\n  Error: {e!s}",
                )
            ]

    return None
