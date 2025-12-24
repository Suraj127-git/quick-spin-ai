"""Diagnostic workflow for troubleshooting services."""

from typing import Any

from langchain.chains import LLMChain
from langchain.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

from app.services.kubernetes_client import KubernetesClient
from app.services.quickspin_client import QuickSpinClient
from app.services.vector_store import VectorStoreService


class DiagnoseWorkflow:
    """
    LangGraph workflow for service diagnostics.

    Workflow steps:
    1. Identify service and issue
    2. Gather service metrics and logs
    3. Search knowledge base for similar issues
    4. Analyze problem using LLM
    5. Suggest fixes
    6. Optionally execute fixes (with confirmation)
    """

    def __init__(
        self,
        llm: ChatGroq,
        quickspin_client: QuickSpinClient,
        kubernetes_client: KubernetesClient,
        vector_store: VectorStoreService,
    ) -> None:
        """
        Initialize diagnose workflow.

        Args:
            llm: LangChain LLM
            quickspin_client: QuickSpin API client
            kubernetes_client: Kubernetes client
            vector_store: Vector store service
        """
        self.llm = llm
        self.quickspin_client = quickspin_client
        self.k8s_client = kubernetes_client
        self.vector_store = vector_store

    async def _gather_diagnostics(
        self,
        service_id: str,
        user_token: str,
    ) -> dict[str, Any]:
        """
        Gather diagnostic information about a service.

        Args:
            service_id: Service unique identifier
            user_token: User JWT token

        Returns:
            Dictionary with diagnostic data
        """
        try:
            # Get service details
            service = await self.quickspin_client.get_service(user_token, service_id)

            # Get metrics
            metrics = await self.quickspin_client.get_service_metrics(user_token, service_id)

            # Get recent logs
            logs = await self.quickspin_client.get_service_logs(user_token, service_id, lines=50)

            return {
                "service": service.model_dump(),
                "metrics": metrics,
                "logs": logs,
                "status": "success",
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
            }

    async def _analyze_issue(
        self,
        diagnostics: dict[str, Any],
        user_message: str,
    ) -> dict[str, Any]:
        """
        Analyze issue using LLM and knowledge base.

        Args:
            diagnostics: Diagnostic data
            user_message: User's description of the issue

        Returns:
            Dictionary with analysis results
        """
        # Search for similar issues
        knowledge = await self.vector_store.search_knowledge(
            query=user_message,
            category="common_issues",
            n_results=2,
        )

        # Build context
        service = diagnostics.get("service", {})
        metrics = diagnostics.get("metrics", {})
        logs = diagnostics.get("logs", [])

        context = f"""
Service Type: {service.get('service_type')}
Status: {service.get('status')}
Metrics: {metrics}
Recent Logs (last 10 lines):
{chr(10).join(logs[-10:])}
"""

        knowledge_context = "\n\n".join([item["content"] for item in knowledge])

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are a QuickSpin service diagnostics expert. Analyze the service issue
                    and provide specific troubleshooting recommendations.

                    Service Information:
                    {context}

                    Knowledge Base (Similar Issues):
                    {knowledge}

                    Provide:
                    1. Root cause analysis
                    2. Impact assessment
                    3. Recommended actions (in priority order)
                    """,
                ),
                ("user", "{message}"),
            ]
        )

        chain = LLMChain(llm=self.llm, prompt=prompt)
        result = await chain.ainvoke(
            {
                "message": user_message,
                "context": context,
                "knowledge": knowledge_context,
            }
        )

        return {
            "analysis": result["text"].strip(),
            "service_type": service.get("service_type"),
        }

    async def execute(
        self,
        service_id: str,
        user_message: str,
        user_token: str,
    ) -> dict[str, Any]:
        """
        Execute diagnostic workflow.

        Args:
            service_id: Service to diagnose
            user_message: User's description of the issue
            user_token: User JWT token

        Returns:
            Dictionary with diagnostic results and recommendations
        """
        # Gather diagnostics
        diagnostics = await self._gather_diagnostics(service_id, user_token)

        if diagnostics["status"] == "error":
            return {
                "message": f"Failed to gather diagnostics: {diagnostics['error']}",
                "status": "error",
            }

        # Analyze issue
        analysis = await self._analyze_issue(diagnostics, user_message)

        # Generate response
        service = diagnostics["service"]
        response_message = f"""**Diagnostic Analysis for {service['name']}**

{analysis['analysis']}

**Current Service Status:**
- Status: {service['status']}
- Type: {service['service_type']}
- Tier: {service['tier']}

Would you like me to:
1. Show detailed logs
2. Restart the service
3. Scale resources
"""

        return {
            "message": response_message,
            "diagnostics": diagnostics,
            "analysis": analysis,
            "actions": [
                {"type": "show_logs", "service_id": service_id},
                {"type": "restart_service", "service_id": service_id},
                {"type": "scale_service", "service_id": service_id},
            ],
            "status": "success",
        }
