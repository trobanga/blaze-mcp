"""Configuration for Blaze MCP server."""

from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    blaze_base_url: str = "http://localhost:8080/fhir"
    blaze_timeout: float = 30.0
    admin_tools_enabled: bool = True
    default_page_size: int = 20
    max_page_size: int = 100

    # Transport configuration
    transport: Literal["stdio", "sse"] = "stdio"
    host: str = "0.0.0.0"
    port: int = 8000

    model_config = {"env_prefix": "BLAZE_MCP_"}


settings = Settings()
