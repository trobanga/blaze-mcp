"""FHIR client for communicating with Blaze server."""

from typing import Any
from urllib.parse import urlencode

import httpx

from .config import settings


class BlazeClient:
    """HTTP client for Blaze FHIR server.

    Supports dynamic URL switching for multiple Blaze instances.
    """

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float | None = None,
    ) -> None:
        self._base_url = base_url or settings.blaze_base_url
        self.timeout = timeout or settings.blaze_timeout
        self._clients: dict[str, httpx.AsyncClient] = {}

    @property
    def base_url(self) -> str:
        """Get current base URL."""
        return self._base_url

    def set_base_url(self, url: str) -> None:
        """Set the default base URL for subsequent requests."""
        self._base_url = url.rstrip("/")

    async def _get_client(self, base_url: str | None = None) -> httpx.AsyncClient:
        """Get or create HTTP client for the given base URL."""
        url = base_url or self._base_url

        if url not in self._clients:
            self._clients[url] = httpx.AsyncClient(
                base_url=url,
                timeout=self.timeout,
                headers={
                    "Accept": "application/fhir+json",
                    "Content-Type": "application/fhir+json",
                },
            )
        return self._clients[url]

    async def close(self) -> None:
        """Close all HTTP clients."""
        for client in self._clients.values():
            await client.aclose()
        self._clients.clear()

    def _build_url(self, path: str, params: dict[str, Any] | None = None) -> str:
        url = path
        if params:
            filtered = {k: v for k, v in params.items() if v is not None}
            if filtered:
                url = f"{path}?{urlencode(filtered, doseq=True)}"
        return url

    async def read(self, resource_type: str, resource_id: str) -> dict[str, Any]:
        """Read a specific resource by type and ID."""
        client = await self._get_client()
        response = await client.get(f"/{resource_type}/{resource_id}")
        response.raise_for_status()
        return response.json()

    async def vread(
        self, resource_type: str, resource_id: str, version_id: str
    ) -> dict[str, Any]:
        """Read a specific version of a resource."""
        client = await self._get_client()
        response = await client.get(
            f"/{resource_type}/{resource_id}/_history/{version_id}"
        )
        response.raise_for_status()
        return response.json()

    async def search(
        self,
        resource_type: str,
        params: dict[str, Any] | None = None,
        count: int | None = None,
    ) -> dict[str, Any]:
        """Search for resources of a given type."""
        client = await self._get_client()
        search_params = dict(params or {})
        if count:
            search_params["_count"] = count
        url = self._build_url(f"/{resource_type}", search_params)
        response = await client.get(url)
        response.raise_for_status()
        return response.json()

    async def search_system(
        self,
        params: dict[str, Any] | None = None,
        count: int | None = None,
    ) -> dict[str, Any]:
        """Search across all resource types."""
        client = await self._get_client()
        search_params = dict(params or {})
        if count:
            search_params["_count"] = count
        url = self._build_url("/", search_params)
        response = await client.get(url)
        response.raise_for_status()
        return response.json()

    async def create(self, resource_type: str, resource: dict[str, Any]) -> dict[str, Any]:
        """Create a new resource."""
        client = await self._get_client()
        response = await client.post(f"/{resource_type}", json=resource)
        response.raise_for_status()
        return response.json()

    async def update(
        self, resource_type: str, resource_id: str, resource: dict[str, Any]
    ) -> dict[str, Any]:
        """Update an existing resource."""
        client = await self._get_client()
        response = await client.put(f"/{resource_type}/{resource_id}", json=resource)
        response.raise_for_status()
        return response.json()

    async def delete(self, resource_type: str, resource_id: str) -> bool:
        """Delete a resource."""
        client = await self._get_client()
        response = await client.delete(f"/{resource_type}/{resource_id}")
        response.raise_for_status()
        return response.status_code == 204

    async def history(
        self,
        resource_type: str,
        resource_id: str,
        count: int | None = None,
    ) -> dict[str, Any]:
        """Get the history of a resource."""
        client = await self._get_client()
        params = {"_count": count} if count else None
        url = self._build_url(f"/{resource_type}/{resource_id}/_history", params)
        response = await client.get(url)
        response.raise_for_status()
        return response.json()

    async def history_type(
        self,
        resource_type: str,
        count: int | None = None,
    ) -> dict[str, Any]:
        """Get the history of a resource type."""
        client = await self._get_client()
        params = {"_count": count} if count else None
        url = self._build_url(f"/{resource_type}/_history", params)
        response = await client.get(url)
        response.raise_for_status()
        return response.json()

    async def transaction(self, bundle: dict[str, Any]) -> dict[str, Any]:
        """Execute a transaction bundle."""
        client = await self._get_client()
        response = await client.post("/", json=bundle)
        response.raise_for_status()
        return response.json()

    async def capabilities(self) -> dict[str, Any]:
        """Get the CapabilityStatement (metadata)."""
        client = await self._get_client()
        response = await client.get("/metadata")
        response.raise_for_status()
        return response.json()

    async def patient_everything(
        self,
        patient_id: str,
        start: str | None = None,
        end: str | None = None,
        count: int | None = None,
    ) -> dict[str, Any]:
        """Get all resources in a patient's compartment."""
        client = await self._get_client()
        params: dict[str, Any] = {}
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        if count:
            params["_count"] = count
        url = self._build_url(f"/Patient/{patient_id}/$everything", params or None)
        response = await client.get(url)
        response.raise_for_status()
        return response.json()

    async def evaluate_measure(
        self,
        measure_id: str,
        period_start: str,
        period_end: str,
        subject: str | None = None,
    ) -> dict[str, Any]:
        """Evaluate a measure."""
        client = await self._get_client()
        params: dict[str, Any] = {
            "periodStart": period_start,
            "periodEnd": period_end,
        }
        if subject:
            params["subject"] = subject
        url = self._build_url(f"/Measure/{measure_id}/$evaluate-measure", params)
        response = await client.get(url)
        response.raise_for_status()
        return response.json()

    async def graphql(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute a GraphQL query."""
        client = await self._get_client()
        body: dict[str, Any] = {"query": query}
        if variables:
            body["variables"] = variables
        response = await client.post("/$graphql", json=body)
        response.raise_for_status()
        return response.json()

    async def validate_code(
        self,
        system: str,
        code: str,
        display: str | None = None,
    ) -> dict[str, Any]:
        """Validate a code against a code system."""
        client = await self._get_client()
        params: dict[str, Any] = {"system": system, "code": code}
        if display:
            params["display"] = display
        url = self._build_url("/CodeSystem/$validate-code", params)
        response = await client.get(url)
        response.raise_for_status()
        return response.json()

    async def expand_valueset(
        self,
        valueset_id: str | None = None,
        url: str | None = None,
        filter_text: str | None = None,
        count: int | None = None,
    ) -> dict[str, Any]:
        """Expand a value set."""
        client = await self._get_client()
        params: dict[str, Any] = {}
        if url:
            params["url"] = url
        if filter_text:
            params["filter"] = filter_text
        if count:
            params["count"] = count

        if valueset_id:
            endpoint = f"/ValueSet/{valueset_id}/$expand"
        else:
            endpoint = "/ValueSet/$expand"

        request_url = self._build_url(endpoint, params or None)
        response = await client.get(request_url)
        response.raise_for_status()
        return response.json()

    async def lookup_code(
        self,
        system: str,
        code: str,
    ) -> dict[str, Any]:
        """Look up details for a code."""
        client = await self._get_client()
        params = {"system": system, "code": code}
        url = self._build_url("/CodeSystem/$lookup", params)
        response = await client.get(url)
        response.raise_for_status()
        return response.json()

    async def totals(self) -> dict[str, Any]:
        """Get resource counts by type."""
        client = await self._get_client()
        response = await client.get("/$totals")
        response.raise_for_status()
        return response.json()

    async def compact(self, column_family: str | None = None) -> dict[str, Any]:
        """Trigger database compaction."""
        client = await self._get_client()
        params = {"column-family": column_family} if column_family else None
        url = self._build_url("/$compact", params)
        response = await client.post(url)
        response.raise_for_status()
        return response.json()

    async def reindex(
        self,
        resource_type: str | None = None,
        search_param: str | None = None,
    ) -> dict[str, Any]:
        """Trigger re-indexing."""
        client = await self._get_client()
        params: dict[str, Any] = {}
        if resource_type:
            params["type"] = resource_type
        if search_param:
            params["search-param"] = search_param
        url = self._build_url("/$re-index", params or None)
        response = await client.post(url)
        response.raise_for_status()
        return response.json()
