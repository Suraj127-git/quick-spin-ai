"""Repository for conversation and message persistence."""

from datetime import datetime
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.conversation import Conversation, ConversationMessage


class ConversationRepository:
    """Repository for managing conversations and messages in MongoDB."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        """
        Initialize conversation repository.

        Args:
            db: MongoDB database instance
        """
        self.conversations = db.conversations
        self.messages = db.messages

    async def create_conversation(
        self,
        user_id: str,
        organization_id: str,
        title: str = "New Conversation",
        metadata: dict[str, Any] | None = None,
    ) -> Conversation:
        """
        Create a new conversation.

        Args:
            user_id: User who owns the conversation
            organization_id: Organization context
            title: Conversation title
            metadata: Additional metadata

        Returns:
            Created Conversation instance
        """
        conversation_data = {
            "user_id": user_id,
            "organization_id": organization_id,
            "title": title,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "message_count": 0,
            "metadata": metadata or {},
        }

        result = await self.conversations.insert_one(conversation_data)
        conversation_data["_id"] = str(result.inserted_id)

        return Conversation(**conversation_data)

    async def get_conversation(self, conversation_id: str) -> Conversation | None:
        """
        Get conversation by ID.

        Args:
            conversation_id: Conversation ID

        Returns:
            Conversation instance or None if not found
        """
        data = await self.conversations.find_one({"_id": ObjectId(conversation_id)})
        if data:
            data["_id"] = str(data["_id"])
            return Conversation(**data)
        return None

    async def list_conversations(
        self,
        user_id: str,
        limit: int = 50,
        skip: int = 0,
    ) -> list[Conversation]:
        """
        List conversations for a user.

        Args:
            user_id: User ID
            limit: Maximum number of results
            skip: Number of results to skip

        Returns:
            List of Conversation instances
        """
        cursor = (
            self.conversations.find({"user_id": user_id})
            .sort("updated_at", -1)
            .skip(skip)
            .limit(limit)
        )

        conversations = []
        async for data in cursor:
            data["_id"] = str(data["_id"])
            conversations.append(Conversation(**data))

        return conversations

    async def update_conversation(
        self,
        conversation_id: str,
        title: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """
        Update conversation metadata.

        Args:
            conversation_id: Conversation ID
            title: New title
            metadata: Updated metadata

        Returns:
            True if updated successfully
        """
        update_data: dict[str, Any] = {"updated_at": datetime.utcnow()}

        if title is not None:
            update_data["title"] = title
        if metadata is not None:
            update_data["metadata"] = metadata

        result = await self.conversations.update_one(
            {"_id": ObjectId(conversation_id)},
            {"$set": update_data},
        )

        return result.modified_count > 0

    async def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete conversation and all associated messages.

        Args:
            conversation_id: Conversation ID

        Returns:
            True if deleted successfully
        """
        # Delete all messages
        await self.messages.delete_many({"conversation_id": conversation_id})

        # Delete conversation
        result = await self.conversations.delete_one({"_id": ObjectId(conversation_id)})

        return result.deleted_count > 0

    async def save_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> ConversationMessage:
        """
        Save a message to a conversation.

        Args:
            conversation_id: Conversation ID
            role: Message role (user/assistant/system)
            content: Message content
            metadata: Additional metadata

        Returns:
            Created ConversationMessage instance
        """
        message_data = {
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow(),
            "metadata": metadata or {},
        }

        result = await self.messages.insert_one(message_data)
        message_data["_id"] = str(result.inserted_id)

        # Increment message count and update conversation timestamp
        await self.conversations.update_one(
            {"_id": ObjectId(conversation_id)},
            {
                "$inc": {"message_count": 1},
                "$set": {"updated_at": datetime.utcnow()},
            },
        )

        return ConversationMessage(**message_data)

    async def get_messages(
        self,
        conversation_id: str,
        limit: int = 100,
        skip: int = 0,
    ) -> list[ConversationMessage]:
        """
        Get messages for a conversation.

        Args:
            conversation_id: Conversation ID
            limit: Maximum number of messages
            skip: Number of messages to skip

        Returns:
            List of ConversationMessage instances
        """
        cursor = (
            self.messages.find({"conversation_id": conversation_id})
            .sort("timestamp", 1)
            .skip(skip)
            .limit(limit)
        )

        messages = []
        async for data in cursor:
            data["_id"] = str(data["_id"])
            messages.append(ConversationMessage(**data))

        return messages

    async def get_recent_messages(
        self,
        conversation_id: str,
        count: int = 10,
    ) -> list[ConversationMessage]:
        """
        Get most recent messages from a conversation.

        Args:
            conversation_id: Conversation ID
            count: Number of recent messages to retrieve

        Returns:
            List of recent ConversationMessage instances
        """
        cursor = (
            self.messages.find({"conversation_id": conversation_id})
            .sort("timestamp", -1)
            .limit(count)
        )

        messages = []
        async for data in cursor:
            data["_id"] = str(data["_id"])
            messages.append(ConversationMessage(**data))

        # Reverse to get chronological order
        return list(reversed(messages))
