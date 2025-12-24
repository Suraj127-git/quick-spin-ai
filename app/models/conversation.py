"""Conversation and message models."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Message role enumeration."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ConversationMessage(BaseModel):
    """Individual message in a conversation."""

    id: str | None = Field(default=None, alias="_id")
    conversation_id: str = Field(..., description="Parent conversation ID")
    role: MessageRole = Field(..., description="Message sender role")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        """Pydantic model configuration."""

        populate_by_name = True
        json_schema_extra = {
            "example": {
                "conversation_id": "conv_123abc",
                "role": "user",
                "content": "I need a Redis instance for caching",
                "timestamp": "2024-01-15T10:30:00Z",
                "metadata": {"intent": "provision_service"},
            }
        }


class Conversation(BaseModel):
    """Conversation session model."""

    id: str | None = Field(default=None, alias="_id")
    user_id: str = Field(..., description="User who owns this conversation")
    organization_id: str = Field(..., description="Organization context")
    title: str = Field(default="New Conversation", description="Conversation title")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    message_count: int = Field(default=0, description="Total messages in conversation")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata like tags, context",
    )

    class Config:
        """Pydantic model configuration."""

        populate_by_name = True
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
                "organization_id": "org_456",
                "title": "Redis Setup Discussion",
                "created_at": "2024-01-15T10:00:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
                "message_count": 5,
                "metadata": {"tags": ["redis", "caching"]},
            }
        }


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""

    message: str = Field(..., min_length=1, max_length=4000, description="User message")
    conversation_id: str | None = Field(
        default=None,
        description="Existing conversation ID or None for new conversation",
    )
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context for AI processing",
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "message": "How do I connect to my Redis instance?",
                "conversation_id": "conv_123abc",
                "context": {"service_id": "redis-dev-1a2b3c"},
            }
        }


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""

    conversation_id: str = Field(..., description="Conversation ID")
    message: str = Field(..., description="AI assistant response")
    intent: str | None = Field(default=None, description="Detected user intent")
    actions: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Suggested or performed actions",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional response metadata",
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "conversation_id": "conv_123abc",
                "message": "Here's how to connect to redis-dev-1a2b3c...",
                "intent": "get_connection_info",
                "actions": [
                    {
                        "type": "code_snippet",
                        "language": "python",
                        "code": "redis.Redis(host='...', port=6379)",
                    }
                ],
                "metadata": {"confidence": 0.95},
            }
        }
