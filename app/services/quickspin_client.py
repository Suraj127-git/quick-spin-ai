"""Async HTTP client for QuickSpin API integration."""

from typing import Any

import httpx

from app.core.config import Settings
from app.models.service import (
    ProvisionServiceRequest,
    Service,
    ServiceConfig,
    ServiceStatus,
    ServiceType,
)


class QuickSpinClient:
    """Async client for QuickSpin API operations."""

    def __init__(self, http_client: httpx.AsyncClient, settings: Settings) -> None:
        """
        Initialize QuickSpin API client.

        Args:
            http_client: Async HTTP client
            settings: Application settings
        """
        self.client = http_client
        self.base_url = settings.quickspin_api_url
        self.api_prefix = "/api/v1"

    def _get_headers(self, user_token: str) -> dict[str, str]:
        """
        Get HTTP headers with user authentication.

        Args:
            user_token: User JWT token

        Returns:
            Dictionary of HTTP headers
        """
        return {
            "Authorization": f"Bearer {user_token}",
            "Content-Type": "application/json",
        }

    async def provision_service(
        self,
        user_token: str,
        service_request: ProvisionServiceRequest,
    ) -> Service:
        """
        Provision a new managed service.

        Args:
            user_token: User JWT token
            service_request: Service provisioning request

        Returns:
            Provisioned Service instance

        Raises:
            httpx.HTTPError: If API request fails
        """
        response = await self.client.post(
            f"{self.base_url}{self.api_prefix}/services",
            headers=self._get_headers(user_token),
            json=service_request.model_dump(),
        )
        response.raise_for_status()

        data = response.json()
        return Service(**data["service"])

    async def get_service(self, user_token: str, service_id: str) -> Service:
        """
        Get service details by ID.

        Args:
            user_token: User JWT token
            service_id: Service unique identifier

        Returns:
            Service instance

        Raises:
            httpx.HTTPError: If API request fails
        """
        response = await self.client.get(
            f"{self.base_url}{self.api_prefix}/services/{service_id}",
            headers=self._get_headers(user_token),
        )
        response.raise_for_status()

        return Service(**response.json())

    async def list_services(
        self,
        user_token: str,
        service_type: ServiceType | None = None,
        status: ServiceStatus | None = None,
    ) -> list[Service]:
        """
        List user's managed services.

        Args:
            user_token: User JWT token
            service_type: Filter by service type
            status: Filter by service status

        Returns:
            List of Service instances

        Raises:
            httpx.HTTPError: If API request fails
        """
        params: dict[str, str] = {}
        if service_type:
            params["type"] = service_type.value
        if status:
            params["status"] = status.value

        response = await self.client.get(
            f"{self.base_url}{self.api_prefix}/services",
            headers=self._get_headers(user_token),
            params=params,
        )
        response.raise_for_status()

        services_data = response.json()
        return [Service(**service) for service in services_data["services"]]

    async def delete_service(self, user_token: str, service_id: str) -> dict[str, str]:
        """
        Delete a managed service.

        Args:
            user_token: User JWT token
            service_id: Service unique identifier

        Returns:
            Dictionary with deletion status message

        Raises:
            httpx.HTTPError: If API request fails
        """
        response = await self.client.delete(
            f"{self.base_url}{self.api_prefix}/services/{service_id}",
            headers=self._get_headers(user_token),
        )
        response.raise_for_status()

        return response.json()

    async def get_service_metrics(
        self,
        user_token: str,
        service_id: str,
    ) -> dict[str, Any]:
        """
        Get service metrics and resource usage.

        Args:
            user_token: User JWT token
            service_id: Service unique identifier

        Returns:
            Dictionary with metrics data

        Raises:
            httpx.HTTPError: If API request fails
        """
        response = await self.client.get(
            f"{self.base_url}{self.api_prefix}/services/{service_id}/metrics",
            headers=self._get_headers(user_token),
        )
        response.raise_for_status()

        return response.json()

    async def get_service_logs(
        self,
        user_token: str,
        service_id: str,
        lines: int = 100,
    ) -> list[str]:
        """
        Get recent service logs.

        Args:
            user_token: User JWT token
            service_id: Service unique identifier
            lines: Number of log lines to retrieve

        Returns:
            List of log lines

        Raises:
            httpx.HTTPError: If API request fails
        """
        response = await self.client.get(
            f"{self.base_url}{self.api_prefix}/services/{service_id}/logs",
            headers=self._get_headers(user_token),
            params={"lines": lines},
        )
        response.raise_for_status()

        return response.json()["logs"]

    async def get_billing_info(self, user_token: str) -> dict[str, Any]:
        """
        Get billing and usage information.

        Args:
            user_token: User JWT token

        Returns:
            Dictionary with billing data

        Raises:
            httpx.HTTPError: If API request fails
        """
        response = await self.client.get(
            f"{self.base_url}{self.api_prefix}/billing",
            headers=self._get_headers(user_token),
        )
        response.raise_for_status()

        return response.json()

    async def scale_service(
        self,
        user_token: str,
        service_id: str,
        config: ServiceConfig,
    ) -> Service:
        """
        Scale or update service configuration.

        Args:
            user_token: User JWT token
            service_id: Service unique identifier
            config: New service configuration

        Returns:
            Updated Service instance

        Raises:
            httpx.HTTPError: If API request fails
        """
        response = await self.client.patch(
            f"{self.base_url}{self.api_prefix}/services/{service_id}",
            headers=self._get_headers(user_token),
            json={"config": config.model_dump()},
        )
        response.raise_for_status()

        return Service(**response.json()["service"])
