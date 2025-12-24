"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.config import get_settings
from app.routers import chat, health, recommendations
from app.services.vector_store import VectorStoreService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.

    Handles startup and shutdown events.

    Args:
        app: FastAPI application instance

    Yields:
        None
    """
    # Startup
    settings = get_settings()
    logger.info(f"Starting QuickSpin AI Service in {settings.app_env} mode")

    # Initialize vector store knowledge base
    vector_store = VectorStoreService(settings)
    await vector_store.initialize_knowledge_base()
    logger.info("Vector store initialized with knowledge base")

    yield

    # Shutdown
    logger.info("Shutting down QuickSpin AI Service")


def create_application() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        Configured FastAPI application instance
    """
    settings = get_settings()

    app = FastAPI(
        title="QuickSpin AI",
        description="Intelligent AI service for QuickSpin managed microservices platform",
        version="0.1.0",
        docs_url=f"{settings.api_prefix}/docs",
        redoc_url=f"{settings.api_prefix}/redoc",
        openapi_url=f"{settings.api_prefix}/openapi.json",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.is_development else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health.router, prefix=settings.api_prefix)
    app.include_router(chat.router, prefix=settings.api_prefix)
    app.include_router(recommendations.router, prefix=settings.api_prefix)

    # Prometheus metrics
    Instrumentator().instrument(app).expose(app, endpoint=f"{settings.api_prefix}/metrics")

    logger.info("FastAPI application configured")

    return app


# Create application instance
app = create_application()


@app.get("/")
async def root() -> dict[str, str]:
    """
    Root endpoint.

    Returns:
        Welcome message
    """
    return {
        "service": "QuickSpin AI",
        "version": "0.1.0",
        "docs": f"{get_settings().api_prefix}/docs",
    }


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.is_development,
        log_level=settings.log_level.lower(),
    )
