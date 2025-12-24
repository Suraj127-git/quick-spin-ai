"""QuickSpin service models."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ServiceType(str, Enum):
    """Supported QuickSpin service types."""

    REDIS = "redis"
    RABBITMQ = "rabbitmq"
    POSTGRESQL = "postgresql"
    MONGODB = "mongodb"
    MYSQL = "mysql"
    ELASTICSEARCH = "elasticsearch"


class ServiceTier(str, Enum):
    """QuickSpin service tier levels."""

    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class ServiceStatus(str, Enum):
    """Service provisioning status."""

    PENDING = "pending"
    PROVISIONING = "provisioning"
    RUNNING = "running"
    FAILED = "failed"
    STOPPED = "stopped"
    DELETING = "deleting"


class ServiceConfig(BaseModel):
    """Service configuration parameters."""

    service_type: ServiceType = Field(..., description="Type of service to provision")
    tier: ServiceTier = Field(default=ServiceTier.STARTER, description="Service tier")
    memory_mb: int = Field(default=256, description="Memory limit in MB", ge=128, le=16384)
    cpu_cores: float = Field(default=0.5, description="CPU cores allocation", ge=0.1, le=8.0)
    storage_gb: int = Field(default=1, description="Storage size in GB", ge=1, le=1000)
    replicas: int = Field(default=1, description="Number of replicas", ge=1, le=5)
    backup_enabled: bool = Field(default=False, description="Enable automated backups")
    high_availability: bool = Field(default=False, description="Enable HA configuration")
    custom_config: dict[str, Any] = Field(
        default_factory=dict,
        description="Service-specific configuration",
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "service_type": "redis",
                "tier": "starter",
                "memory_mb": 256,
                "cpu_cores": 0.5,
                "storage_gb": 1,
                "replicas": 1,
                "backup_enabled": False,
                "high_availability": False,
                "custom_config": {"maxmemory_policy": "allkeys-lru"},
            }
        }


class Service(BaseModel):
    """QuickSpin managed service instance."""

    id: str = Field(..., description="Service unique identifier")
    name: str = Field(..., description="Service name")
    service_type: ServiceType = Field(..., description="Service type")
    tier: ServiceTier = Field(..., description="Service tier")
    status: ServiceStatus = Field(..., description="Current status")
    organization_id: str = Field(..., description="Owner organization ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    config: ServiceConfig = Field(..., description="Service configuration")
    connection_info: dict[str, Any] = Field(
        default_factory=dict,
        description="Connection details and credentials",
    )
    metrics: dict[str, Any] = Field(default_factory=dict, description="Current metrics")
    estimated_cost_hourly: float = Field(
        default=0.0,
        description="Estimated hourly cost in USD",
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "id": "redis-dev-1a2b3c",
                "name": "dev-cache",
                "service_type": "redis",
                "tier": "starter",
                "status": "running",
                "organization_id": "org_456",
                "created_at": "2024-01-15T10:00:00Z",
                "updated_at": "2024-01-15T10:05:00Z",
                "config": {
                    "service_type": "redis",
                    "tier": "starter",
                    "memory_mb": 256,
                    "cpu_cores": 0.5,
                },
                "connection_info": {
                    "host": "redis-dev-1a2b3c.quickspin.io",
                    "port": 6379,
                },
                "metrics": {"memory_usage_mb": 45, "cpu_usage_percent": 12},
                "estimated_cost_hourly": 0.008,
            }
        }


class ProvisionServiceRequest(BaseModel):
    """Request to provision a new service."""

    name: str = Field(..., min_length=3, max_length=50, description="Service name")
    config: ServiceConfig = Field(..., description="Service configuration")

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "name": "dev-cache",
                "config": {
                    "service_type": "redis",
                    "tier": "starter",
                    "memory_mb": 256,
                    "cpu_cores": 0.5,
                },
            }
        }


class ProvisionServiceResponse(BaseModel):
    """Response from service provisioning."""

    service: Service = Field(..., description="Provisioned service details")
    message: str = Field(..., description="Human-readable status message")

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "service": {
                    "id": "redis-dev-1a2b3c",
                    "name": "dev-cache",
                    "status": "provisioning",
                },
                "message": "Redis instance is being provisioned. This may take 2-3 minutes.",
            }
        }
