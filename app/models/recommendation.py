"""Cost optimization and recommendation models."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class RecommendationType(str, Enum):
    """Type of recommendation."""

    COST_OPTIMIZATION = "cost_optimization"
    PERFORMANCE_TUNING = "performance_tuning"
    SECURITY_IMPROVEMENT = "security_improvement"
    RESOURCE_RIGHTSIZING = "resource_rightsizing"
    IDLE_RESOURCE_CLEANUP = "idle_resource_cleanup"


class RecommendationPriority(str, Enum):
    """Recommendation priority level."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Recommendation(BaseModel):
    """Individual recommendation for optimization."""

    id: str = Field(..., description="Recommendation unique identifier")
    type: RecommendationType = Field(..., description="Type of recommendation")
    priority: RecommendationPriority = Field(..., description="Priority level")
    title: str = Field(..., description="Short recommendation title")
    description: str = Field(..., description="Detailed description")
    service_id: str | None = Field(
        default=None,
        description="Related service ID if applicable",
    )
    estimated_savings_monthly: float = Field(
        default=0.0,
        description="Estimated monthly cost savings in USD",
    )
    impact: str = Field(..., description="Expected impact of implementing this recommendation")
    actions: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Steps to implement recommendation",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata",
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "id": "rec_123abc",
                "type": "idle_resource_cleanup",
                "priority": "high",
                "title": "Delete 3 idle PostgreSQL instances",
                "description": "Found 3 PostgreSQL instances with no connections in last 7 days",
                "service_id": None,
                "estimated_savings_monthly": 12.0,
                "impact": "Reduce monthly bill by $12 with no impact on active workloads",
                "actions": [
                    {"action": "delete", "service_id": "postgres-test-1"},
                    {"action": "delete", "service_id": "postgres-test-2"},
                    {"action": "delete", "service_id": "postgres-test-3"},
                ],
                "metadata": {"last_activity_days_ago": 7},
            }
        }


class CostAnalysis(BaseModel):
    """Cost analysis summary."""

    total_monthly_cost: float = Field(..., description="Total monthly cost in USD")
    breakdown_by_service_type: dict[str, float] = Field(
        ...,
        description="Cost breakdown by service type",
    )
    top_expensive_services: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of most expensive services",
    )
    optimization_potential: float = Field(
        default=0.0,
        description="Potential monthly savings from all recommendations",
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "total_monthly_cost": 85.5,
                "breakdown_by_service_type": {
                    "redis": 12.0,
                    "postgresql": 45.0,
                    "elasticsearch": 28.5,
                },
                "top_expensive_services": [
                    {"service_id": "es-logs-prod", "cost": 28.5},
                    {"service_id": "postgres-main", "cost": 25.0},
                ],
                "optimization_potential": 20.0,
            }
        }


class RecommendationResponse(BaseModel):
    """Response containing recommendations."""

    recommendations: list[Recommendation] = Field(
        default_factory=list,
        description="List of recommendations",
    )
    cost_analysis: CostAnalysis | None = Field(
        default=None,
        description="Cost analysis summary",
    )
    total_potential_savings: float = Field(
        default=0.0,
        description="Total potential monthly savings",
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "recommendations": [],
                "cost_analysis": {"total_monthly_cost": 85.5},
                "total_potential_savings": 20.0,
            }
        }
