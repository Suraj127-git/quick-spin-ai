"""Provisioning workflow using LangGraph."""

from typing import Any

from langchain.chains import LLMChain
from langchain.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

from app.models.service import ProvisionServiceRequest, ServiceConfig, ServiceTier, ServiceType
from app.services.quickspin_client import QuickSpinClient
from app.services.vector_store import VectorStoreService


class ProvisionWorkflow:
    """
    LangGraph workflow for service provisioning.

    Workflow steps:
    1. Extract service requirements from natural language
    2. Map to ServiceConfig
    3. Estimate costs
    4. Get user confirmation
    5. Call QuickSpin API
    6. Generate response with connection info
    """

    def __init__(
        self,
        llm: ChatGroq,
        quickspin_client: QuickSpinClient,
        vector_store: VectorStoreService,
    ) -> None:
        """
        Initialize provision workflow.

        Args:
            llm: LangChain LLM
            quickspin_client: QuickSpin API client
            vector_store: Vector store service
        """
        self.llm = llm
        self.quickspin_client = quickspin_client
        self.vector_store = vector_store

    async def _extract_requirements(
        self,
        message: str,
        entities: dict[str, str],
    ) -> ServiceConfig:
        """
        Extract service requirements from user message.

        Args:
            message: User message
            entities: Extracted entities

        Returns:
            ServiceConfig instance
        """
        # Get relevant documentation
        knowledge = await self.vector_store.search_knowledge(
            query=message,
            category="setup",
            n_results=1,
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """Extract service configuration from user request.

                    Context:
                    {context}

                    Return a configuration matching these defaults if not specified:
                    - Tier: starter (unless user says "production" or "high availability")
                    - Memory: 256MB for Redis, 512MB for RabbitMQ, 1GB for databases
                    - CPU: 0.5 cores
                    - Storage: 1GB (databases only)
                    - Replicas: 1
                    """,
                ),
                ("user", "{message}"),
            ]
        )

        # Determine service type
        service_type = ServiceType(entities.get("service_type", "redis"))

        # Simple rule-based config (in production, use LLM structured output)
        tier = ServiceTier.STARTER
        memory_mb = 256 if service_type == ServiceType.REDIS else 512
        cpu_cores = 0.5
        storage_gb = 1 if service_type in [ServiceType.POSTGRESQL, ServiceType.MONGODB] else 1

        # Check for tier indicators in message
        if any(word in message.lower() for word in ["production", "high availability", "ha"]):
            tier = ServiceTier.PRO
            memory_mb *= 4
            cpu_cores = 1.0

        return ServiceConfig(
            service_type=service_type,
            tier=tier,
            memory_mb=memory_mb,
            cpu_cores=cpu_cores,
            storage_gb=storage_gb,
        )

    def _estimate_cost(self, config: ServiceConfig) -> float:
        """
        Estimate hourly cost based on configuration.

        Args:
            config: Service configuration

        Returns:
            Estimated hourly cost in USD
        """
        # Cost calculation (simplified)
        base_costs = {
            ServiceTier.STARTER: 0.01,
            ServiceTier.PRO: 0.04,
            ServiceTier.ENTERPRISE: 0.15,
        }

        return base_costs.get(config.tier, 0.01)

    async def execute(
        self,
        message: str,
        entities: dict[str, str],
        user_token: str,
    ) -> dict[str, Any]:
        """
        Execute provision workflow.

        Args:
            message: User message
            entities: Extracted entities
            user_token: User JWT token

        Returns:
            Dictionary with workflow result
        """
        # Extract requirements
        config = await self._extract_requirements(message, entities)

        # Estimate cost
        hourly_cost = self._estimate_cost(config)
        monthly_cost = hourly_cost * 24 * 30

        # Generate service name
        service_type = config.service_type.value
        service_name = f"{service_type}-{config.tier.value}"

        # Create response suggesting provisioning
        response_message = f"""I'll create a {service_type.title()} instance with the following configuration:

**Configuration:**
- Tier: {config.tier.value.title()}
- Memory: {config.memory_mb}MB
- CPU: {config.cpu_cores} cores
- Storage: {config.storage_gb}GB

**Estimated Cost:**
- Hourly: ${hourly_cost:.3f}
- Monthly: ${monthly_cost:.2f}

To provision this service, confirm and I'll proceed with creation."""

        return {
            "message": response_message,
            "actions": [
                {
                    "type": "provision_service",
                    "service_name": service_name,
                    "config": config.model_dump(),
                    "estimated_cost_hourly": hourly_cost,
                    "status": "pending_confirmation",
                }
            ],
        }

    async def provision_service(
        self,
        service_name: str,
        config: ServiceConfig,
        user_token: str,
    ) -> dict[str, Any]:
        """
        Actually provision the service via QuickSpin API.

        Args:
            service_name: Name for the service
            config: Service configuration
            user_token: User JWT token

        Returns:
            Dictionary with provisioning result
        """
        try:
            request = ProvisionServiceRequest(name=service_name, config=config)
            service = await self.quickspin_client.provision_service(user_token, request)

            return {
                "message": f"""✓ Successfully provisioned {service.service_type.value} instance!

**Service Details:**
- ID: {service.id}
- Name: {service.name}
- Status: {service.status.value}

Your service is being set up. It will be ready in 2-3 minutes.
I'll notify you once it's running.""",
                "service": service.model_dump(),
                "status": "success",
            }
        except Exception as e:
            return {
                "message": f"Failed to provision service: {str(e)}",
                "status": "error",
                "error": str(e),
            }
