"""FastAPI dependency injection utilities."""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from groq import AsyncGroq
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import Settings, get_settings


async def get_mongodb_client(
    settings: Annotated[Settings, Depends(get_settings)],
) -> AsyncGenerator[AsyncIOMotorClient, None]:
    """
    Get MongoDB async client.

    Args:
        settings: Application settings

    Yields:
        AsyncIOMotorClient instance
    """
    client = AsyncIOMotorClient(str(settings.mongodb_uri))
    try:
        yield client
    finally:
        client.close()


async def get_database(
    client: Annotated[AsyncIOMotorClient, Depends(get_mongodb_client)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AsyncIOMotorDatabase:
    """
    Get MongoDB database instance.

    Args:
        client: MongoDB client
        settings: Application settings

    Returns:
        AsyncIOMotorDatabase instance
    """
    return client[settings.mongodb_database]


async def get_groq_client(
    settings: Annotated[Settings, Depends(get_settings)],
) -> AsyncGroq:
    """
    Get Groq async client for LLM inference.

    Args:
        settings: Application settings

    Returns:
        AsyncGroq client instance
    """
    return AsyncGroq(api_key=settings.groq_api_key)


async def get_http_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Get async HTTP client for external API calls.

    Yields:
        AsyncClient instance
    """
    async with AsyncClient(timeout=30.0) as client:
        yield client
