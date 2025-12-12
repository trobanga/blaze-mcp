# Blaze MCP Server

An [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) server that enables AI assistants like Claude to interact with [Blaze FHIR Server](https://github.com/samply/blaze) through natural language.

## Overview

This server exposes Blaze's FHIR capabilities to AI agents, allowing them to:

- Search and retrieve patient data
- Execute CQL-based quality measures
- Validate terminology codes
- Manage FHIR resources
- Query multiple Blaze instances dynamically

## Quick Start

### Installation

```bash
pip install -e .
```

### Run with Claude Code

Add to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "blaze": {
      "command": "blaze-mcp"
    }
  }
}
```

Then ask Claude: *"Connect to Blaze at http://localhost:8080/fhir and search for patients"*

## Features

### Tools

| Category | Tools | Description |
|----------|-------|-------------|
| **Connection** | `set_blaze_url`, `get_blaze_url`, `test_connection` | Switch between Blaze instances at runtime |
| **CRUD** | `read_resource`, `create_resource`, `update_resource`, `delete_resource` | Basic FHIR operations |
| **Search** | `search_resources`, `search_system` | Query resources with FHIR search parameters |
| **History** | `get_history`, `vread_resource` | Access resource versions |
| **Patient** | `patient_everything` | Retrieve complete patient compartment |
| **Measures** | `evaluate_measure` | Run CQL-based quality measures |
| **GraphQL** | `graphql_query` | Flexible queries via GraphQL |
| **Terminology** | `validate_code`, `expand_valueset`, `lookup_code` | Code system operations |
| **Transactions** | `transaction` | Execute FHIR bundles |
| **Admin** | `get_totals`, `run_compaction`, `run_reindex` | Server administration |

### Resources

| URI | Description |
|-----|-------------|
| `blaze://capabilities` | FHIR CapabilityStatement |
| `blaze://resource-types` | List of supported resource types |
| `blaze://totals` | Resource counts by type |

### Prompts

| Name | Description |
|------|-------------|
| `patient_summary` | Generate a clinical summary for a patient |
| `cohort_query` | Build FHIR/CQL queries for patient cohorts |
| `analyze_measure` | Interpret quality measure results |
| `fhir_query_help` | Guidance for constructing FHIR searches |

## Configuration

All settings can be configured via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `BLAZE_MCP_BLAZE_BASE_URL` | `http://localhost:8080/fhir` | Default Blaze URL |
| `BLAZE_MCP_BLAZE_TIMEOUT` | `30.0` | Request timeout (seconds) |
| `BLAZE_MCP_ADMIN_TOOLS_ENABLED` | `true` | Enable admin tools |
| `BLAZE_MCP_DEFAULT_PAGE_SIZE` | `20` | Default search page size |
| `BLAZE_MCP_MAX_PAGE_SIZE` | `100` | Maximum search page size |
| `BLAZE_MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `sse` |
| `BLAZE_MCP_HOST` | `0.0.0.0` | SSE server host |
| `BLAZE_MCP_PORT` | `8000` | SSE server port |

## Usage

### With Claude Desktop

Add to your config file:
- Linux: `~/.config/claude/claude_desktop_config.json`
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "blaze": {
      "command": "blaze-mcp",
      "env": {
        "BLAZE_MCP_BLAZE_BASE_URL": "http://localhost:8080/fhir"
      }
    }
  }
}
```

### With Claude Code

```json
{
  "mcpServers": {
    "blaze": {
      "command": "blaze-mcp"
    }
  }
}
```

### Dynamic URL (Multiple Blaze Instances)

The Blaze URL can be changed at runtime - no restart needed:

```
User: "Connect to the production Blaze at https://blaze.hospital.org/fhir"
Claude: [uses set_blaze_url tool]
        "Connected to https://blaze.hospital.org/fhir"

User: "How many patients are there?"
Claude: [uses get_totals tool]
        "There are 50,432 patients..."

User: "Now check the staging server at http://staging:8080/fhir"
Claude: [uses set_blaze_url tool]
        ...
```

### SSE Transport (Network Mode)

Run as an HTTP service for containerized or remote deployments:

```bash
blaze-mcp --transport sse --port 8000
```

Endpoints:
- `http://localhost:8000/sse` - SSE connection
- `http://localhost:8000/messages/` - Message endpoint

### Docker

```bash
docker build -t blaze-mcp .

docker run -d \
  -p 8000:8000 \
  -e BLAZE_MCP_BLAZE_BASE_URL=http://blaze:8080/fhir \
  blaze-mcp
```

### Docker Compose

```yaml
services:
  blaze:
    image: samply/blaze:latest
    ports:
      - "8080:8080"
    volumes:
      - blaze-data:/app/data

  blaze-mcp:
    build: .
    ports:
      - "8000:8000"
    environment:
      BLAZE_MCP_BLAZE_BASE_URL: http://blaze:8080/fhir
    depends_on:
      - blaze

volumes:
  blaze-data:
```

## Example Conversations

Once configured, you can interact naturally:

```
"Connect to Blaze at http://192.168.1.50:8080/fhir"

"Search for all patients with diabetes"

"Get the complete medical record for patient 12345"

"Find observations for patient 12345 from the last year"

"Validate the LOINC code 8480-6"

"How many resources are in the database?"

"Evaluate the diabetes-screening measure for 2024"

"Create a new Patient resource with name John Doe"
```

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Type checking
mypy src/

# Linting
ruff check src/
ruff format src/
```

## Architecture

```
┌─────────────────┐                     ┌─────────────────┐
│   AI Assistant  │  ←── MCP Protocol ──│   blaze-mcp     │
│   (Claude)      │      (stdio/SSE)    │                 │
└─────────────────┘                     └────────┬────────┘
                                                 │
                                                 │ HTTP/FHIR
                                                 ▼
                                        ┌─────────────────┐
                                        │     Blaze       │
                                        │  FHIR Server    │
                                        └─────────────────┘
```

## License

Apache 2.0

## Links

- [Blaze FHIR Server](https://github.com/samply/blaze)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [FHIR R4 Specification](https://hl7.org/fhir/R4/)
