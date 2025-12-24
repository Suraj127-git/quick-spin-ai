"""Cost optimization workflow."""

from typing import Any

from langchain.chains import LLMChain
from langchain.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

from app.models.recommendation import (
    CostAnalysis,
    Recommendation,
    RecommendationPriority,
    RecommendationType,
)
from app.services.quickspin_client import QuickSpinClient


class OptimizeWorkflow:
    """
    LangGraph workflow for cost optimization.

    Workflow steps:
    1. Fetch all user services
    2. Analyze usage patterns and metrics
    3. Identify optimization opportunities
    4. Generate recommendations
    5. Calculate potential savings
    """

    def __init__(
        self,
        llm: ChatGroq,
        quickspin_client: QuickSpinClient,
    ) -> None:
        """
        Initialize optimize workflow.

        Args:
            llm: LangChain LLM
            quickspin_client: QuickSpin API client
        """
        self.llm = llm
        self.quickspin_client = quickspin_client

    async def _analyze_usage(
        self,
        services: list[dict[str, Any]],
    ) -> list[Recommendation]:
        """
        Analyze service usage and identify optimization opportunities.

        Args:
            services: List of user services

        Returns:
            List of Recommendation instances
        """
        recommendations = []

        for service in services:
            service_id = service["id"]
            metrics = service.get("metrics", {})

            # Check for idle services (no activity in last 7 days)
            # In production, this would check actual metrics
            if service["status"] == "running":
                memory_usage = metrics.get("memory_usage_mb", 0)
                memory_limit = service["config"]["memory_mb"]

                # Low utilization check
                if memory_limit > 0 and memory_usage / memory_limit < 0.3:
                    monthly_cost = service["estimated_cost_hourly"] * 24 * 30
                    potential_savings = monthly_cost * 0.5  # Downgrade could save 50%

                    recommendations.append(
                        Recommendation(
                            id=f"rec_{service_id}_rightsizing",
                            type=RecommendationType.RESOURCE_RIGHTSIZING,
                            priority=RecommendationPriority.MEDIUM,
                            title=f"Downgrade underutilized {service['service_type']} instance",
                            description=f"Service {service['name']} is using only {(memory_usage/memory_limit)*100:.1f}% of allocated memory",
                            service_id=service_id,
                            estimated_savings_monthly=potential_savings,
                            impact="Reduce resource allocation to match actual usage",
                            actions=[
                                {
                                    "action": "downgrade_tier",
                                    "service_id": service_id,
                                    "from_tier": service["tier"],
                                    "to_tier": "starter",
                                }
                            ],
                            metadata={"current_utilization": memory_usage / memory_limit},
                        )
                    )

        return recommendations

    async def execute(
        self,
        user_token: str,
    ) -> dict[str, Any]:
        """
        Execute cost optimization workflow.

        Args:
            user_token: User JWT token

        Returns:
            Dictionary with recommendations and cost analysis
        """
        # Fetch all services
        services = await self.quickspin_client.list_services(user_token)
        services_data = [service.model_dump() for service in services]

        # Calculate current costs
        total_monthly_cost = sum(
            service["estimated_cost_hourly"] * 24 * 30 for service in services_data
        )

        # Breakdown by service type
        breakdown: dict[str, float] = {}
        for service in services_data:
            service_type = service["service_type"]
            cost = service["estimated_cost_hourly"] * 24 * 30
            breakdown[service_type] = breakdown.get(service_type, 0) + cost

        # Top expensive services
        sorted_services = sorted(
            services_data,
            key=lambda s: s["estimated_cost_hourly"],
            reverse=True,
        )
        top_expensive = [
            {
                "service_id": s["id"],
                "service_name": s["name"],
                "service_type": s["service_type"],
                "cost": s["estimated_cost_hourly"] * 24 * 30,
            }
            for s in sorted_services[:5]
        ]

        # Generate recommendations
        recommendations = await self._analyze_usage(services_data)

        # Calculate optimization potential
        optimization_potential = sum(rec.estimated_savings_monthly for rec in recommendations)

        cost_analysis = CostAnalysis(
            total_monthly_cost=total_monthly_cost,
            breakdown_by_service_type=breakdown,
            top_expensive_services=top_expensive,
            optimization_potential=optimization_potential,
        )

        return {
            "recommendations": recommendations,
            "cost_analysis": cost_analysis,
            "total_potential_savings": optimization_potential,
        }
