"""Tests for the Blaze FHIR client."""

import pytest
from pytest_httpx import HTTPXMock

from blaze_mcp.client import BlazeClient


@pytest.fixture
def client() -> BlazeClient:
    return BlazeClient(base_url="http://test:8080/fhir")


@pytest.mark.asyncio
async def test_read_resource(client: BlazeClient, httpx_mock: HTTPXMock) -> None:
    """Test reading a FHIR resource."""
    httpx_mock.add_response(
        url="http://test:8080/fhir/Patient/123",
        json={"resourceType": "Patient", "id": "123", "name": [{"family": "Test"}]},
    )

    result = await client.read("Patient", "123")

    assert result["resourceType"] == "Patient"
    assert result["id"] == "123"

    await client.close()


@pytest.mark.asyncio
async def test_search_resources(client: BlazeClient, httpx_mock: HTTPXMock) -> None:
    """Test searching for FHIR resources."""
    httpx_mock.add_response(
        url="http://test:8080/fhir/Patient?family=Test&_count=10",
        json={
            "resourceType": "Bundle",
            "type": "searchset",
            "total": 1,
            "entry": [{"resource": {"resourceType": "Patient", "id": "123"}}],
        },
    )

    result = await client.search("Patient", {"family": "Test"}, count=10)

    assert result["resourceType"] == "Bundle"
    assert result["total"] == 1
    assert len(result["entry"]) == 1

    await client.close()


@pytest.mark.asyncio
async def test_create_resource(client: BlazeClient, httpx_mock: HTTPXMock) -> None:
    """Test creating a FHIR resource."""
    httpx_mock.add_response(
        url="http://test:8080/fhir/Patient",
        method="POST",
        json={"resourceType": "Patient", "id": "456", "name": [{"family": "New"}]},
        status_code=201,
    )

    result = await client.create("Patient", {"resourceType": "Patient", "name": [{"family": "New"}]})

    assert result["id"] == "456"

    await client.close()


@pytest.mark.asyncio
async def test_capabilities(client: BlazeClient, httpx_mock: HTTPXMock) -> None:
    """Test getting CapabilityStatement."""
    httpx_mock.add_response(
        url="http://test:8080/fhir/metadata",
        json={
            "resourceType": "CapabilityStatement",
            "status": "active",
            "fhirVersion": "4.0.1",
        },
    )

    result = await client.capabilities()

    assert result["resourceType"] == "CapabilityStatement"
    assert result["fhirVersion"] == "4.0.1"

    await client.close()


@pytest.mark.asyncio
async def test_patient_everything(client: BlazeClient, httpx_mock: HTTPXMock) -> None:
    """Test patient $everything operation."""
    httpx_mock.add_response(
        url="http://test:8080/fhir/Patient/123/$everything",
        json={
            "resourceType": "Bundle",
            "type": "searchset",
            "entry": [
                {"resource": {"resourceType": "Patient", "id": "123"}},
                {"resource": {"resourceType": "Observation", "id": "obs1"}},
            ],
        },
    )

    result = await client.patient_everything("123")

    assert len(result["entry"]) == 2

    await client.close()
