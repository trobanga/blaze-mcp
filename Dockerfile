FROM python:3.12-slim

WORKDIR /app

# Install uv for fast dependency management
RUN pip install --no-cache-dir uv

# Copy project files
COPY pyproject.toml .
COPY src/ src/

# Install dependencies
RUN uv pip install --system .

# Environment variables
ENV BLAZE_MCP_BLAZE_BASE_URL=http://blaze:8080/fhir
ENV BLAZE_MCP_TRANSPORT=sse
ENV BLAZE_MCP_HOST=0.0.0.0
ENV BLAZE_MCP_PORT=8000

# Expose SSE port
EXPOSE 8000

# Run the MCP server in SSE mode
ENTRYPOINT ["blaze-mcp", "--transport", "sse"]
