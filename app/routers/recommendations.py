"""Cost optimization and recommendations endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from httpx import AsyncClient

from app.core.config import Settings, get_settings
from app.core.dependencies import get_groq_client, get_http_client
from app.core.security import UserContext, get_current_user
from app.models.recommendation import RecommendationResponse
from app.services.quickspin_client import QuickSpinClient
from app.workflows.optimize import OptimizeWorkflow
from groq import AsyncGroq
from langchain_groq import ChatGroq

router = APIRouter(prefix="/recommendations", tags=["recommendations"])
security = HTTPBearer()


@router.get("", response_model=RecommendationResponse)
async def get_recommendations(
    user: Annotated[UserContext, Depends(get_current_user)],
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    groq_client: Annotated[AsyncGroq, Depends(get_groq_client)],
    settings: Annotated[Settings, Depends(get_settings)],
    http_client: Annotated[AsyncClient, Depends(get_http_client)],
) -> RecommendationResponse:
    """
    Get cost optimization recommendations.

    Args:
        user: Current user context
        credentials: User JWT token credentials
        groq_client: Groq async client
        settings: Application settings
        http_client: HTTP client

    Returns:
        RecommendationResponse with recommendations and cost analysis

    Raises:
        HTTPException: If recommendation generation fails
    """
    try:
        # Initialize workflow
        llm = ChatGroq(
            groq_api_key=settings.groq_api_key,
            model_name=settings.groq_model,
        )
        quickspin_client = QuickSpinClient(http_client, settings)
        workflow = OptimizeWorkflow(llm=llm, quickspin_client=quickspin_client)

        # Execute optimization workflow
        result = await workflow.execute(user_token=credentials.credentials)

        return RecommendationResponse(**result)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate recommendations: {str(e)}",
        ) from e
