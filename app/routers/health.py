"""Health check endpoint."""

from typing import Any

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.dependencies import get_database

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    """
    Health check endpoint.

    Returns:
        Dictionary with status
    """
    return {"status": "healthy", "service": "quickspin-ai"}


@router.get("/health/ready")
async def readiness_check(
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> dict[str, Any]:
    """
    Readiness check endpoint.

    Args:
        db: MongoDB database

    Returns:
        Dictionary with readiness status
    """
    # Check MongoDB connection
    try:
        await db.command("ping")
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "ready" if db_status == "connected" else "not_ready",
        "checks": {
            "database": db_status,
        },
    }
