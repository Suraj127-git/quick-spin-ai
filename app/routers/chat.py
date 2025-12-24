"""Chat endpoints for conversational AI."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from groq import AsyncGroq
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import Settings, get_settings
from app.core.dependencies import get_database, get_groq_client, get_http_client
from app.core.security import UserContext, get_current_user
from app.models.conversation import ChatRequest, ChatResponse, Conversation
from app.repositories.conversation_repo import ConversationRepository
from app.services.ai_engine import AIEngineService
from app.services.quickspin_client import QuickSpinClient
from app.services.vector_store import VectorStoreService

router = APIRouter(prefix="/chat", tags=["chat"])
security = HTTPBearer()


async def get_ai_engine(
    groq_client: Annotated[AsyncGroq, Depends(get_groq_client)],
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    http_client: Annotated[AsyncClient, Depends(get_http_client)],
) -> AIEngineService:
    """
    Get AI engine service instance.

    Args:
        groq_client: Groq async client
        settings: Application settings
        db: MongoDB database
        http_client: HTTP client

    Returns:
        AIEngineService instance
    """
    vector_store = VectorStoreService(settings)
    quickspin_client = QuickSpinClient(http_client, settings)
    conversation_repo = ConversationRepository(db)

    return AIEngineService(
        groq_client=groq_client,
        settings=settings,
        vector_store=vector_store,
        quickspin_client=quickspin_client,
        conversation_repo=conversation_repo,
    )


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    user: Annotated[UserContext, Depends(get_current_user)],
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    ai_engine: Annotated[AIEngineService, Depends(get_ai_engine)],
) -> ChatResponse:
    """
    Process chat message and generate AI response.

    Args:
        request: Chat request with user message
        user: Current user context
        credentials: User JWT token credentials
        ai_engine: AI engine service

    Returns:
        ChatResponse with AI-generated reply

    Raises:
        HTTPException: If processing fails
    """
    try:
        response = await ai_engine.process_message(
            request=request,
            user=user,
            user_token=credentials.credentials,
        )
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process message: {str(e)}",
        ) from e


@router.get("/conversations", response_model=list[Conversation])
async def list_conversations(
    user: Annotated[UserContext, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    limit: int = 50,
    skip: int = 0,
) -> list[Conversation]:
    """
    List user conversations.

    Args:
        user: Current user context
        db: MongoDB database
        limit: Maximum number of conversations
        skip: Number of conversations to skip

    Returns:
        List of Conversation instances
    """
    repo = ConversationRepository(db)
    conversations = await repo.list_conversations(
        user_id=user.user_id,
        limit=limit,
        skip=skip,
    )
    return conversations


@router.get("/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(
    conversation_id: str,
    user: Annotated[UserContext, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
) -> Conversation:
    """
    Get conversation by ID.

    Args:
        conversation_id: Conversation ID
        user: Current user context
        db: MongoDB database

    Returns:
        Conversation instance

    Raises:
        HTTPException: If conversation not found
    """
    repo = ConversationRepository(db)
    conversation = await repo.get_conversation(conversation_id)

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Verify ownership
    if conversation.user_id != user.user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    return conversation


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    user: Annotated[UserContext, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
) -> dict[str, str]:
    """
    Delete a conversation.

    Args:
        conversation_id: Conversation ID
        user: Current user context
        db: MongoDB database

    Returns:
        Dictionary with deletion status

    Raises:
        HTTPException: If conversation not found or access denied
    """
    repo = ConversationRepository(db)
    conversation = await repo.get_conversation(conversation_id)

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Verify ownership
    if conversation.user_id != user.user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    success = await repo.delete_conversation(conversation_id)

    if success:
        return {"status": "deleted", "conversation_id": conversation_id}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete conversation")
