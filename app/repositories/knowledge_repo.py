"""Repository for ChromaDB vector store knowledge base."""

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import Settings


class KnowledgeRepository:
    """Repository for managing QuickSpin knowledge base in ChromaDB."""

    def __init__(self, settings: Settings) -> None:
        """
        Initialize knowledge repository with ChromaDB.

        Args:
            settings: Application settings
        """
        self.client = chromadb.Client(
            ChromaSettings(
                persist_directory=settings.chroma_persist_dir,
                anonymized_telemetry=False,
            )
        )
        self.collection = self.client.get_or_create_collection(
            name=settings.chroma_collection_name,
            metadata={"description": "QuickSpin documentation and knowledge base"},
        )

    async def add_documents(
        self,
        documents: list[str],
        metadatas: list[dict[str, str]] | None = None,
        ids: list[str] | None = None,
    ) -> None:
        """
        Add documents to the knowledge base.

        Args:
            documents: List of document texts
            metadatas: List of metadata dictionaries for each document
            ids: List of unique IDs for each document (auto-generated if None)
        """
        if ids is None:
            ids = [f"doc_{i}" for i in range(len(documents))]

        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
        )

    async def search(
        self,
        query: str,
        n_results: int = 5,
        where: dict[str, str] | None = None,
    ) -> dict[str, list[str | dict[str, str]]]:
        """
        Search for relevant documents using semantic similarity.

        Args:
            query: Search query
            n_results: Number of results to return
            where: Metadata filter conditions

        Returns:
            Dictionary with 'documents', 'metadatas', 'distances', and 'ids'
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where,
        )

        return {
            "documents": results["documents"][0] if results["documents"] else [],
            "metadatas": results["metadatas"][0] if results["metadatas"] else [],
            "distances": results["distances"][0] if results["distances"] else [],
            "ids": results["ids"][0] if results["ids"] else [],
        }

    async def delete_documents(self, ids: list[str]) -> None:
        """
        Delete documents from the knowledge base.

        Args:
            ids: List of document IDs to delete
        """
        self.collection.delete(ids=ids)

    async def count(self) -> int:
        """
        Get total number of documents in knowledge base.

        Returns:
            Document count
        """
        return self.collection.count()

    async def seed_knowledge_base(self) -> None:
        """Seed the knowledge base with QuickSpin documentation."""
        documents = [
            # Redis documentation
            """
            Redis Setup on QuickSpin:
            - Starter tier: 256MB RAM, 0.5 CPU cores, $0.008/hour
            - Pro tier: 1GB RAM, 1 CPU core, $0.03/hour
            - Enterprise tier: 4GB RAM, 2 CPU cores, $0.12/hour

            Connection: Use redis-py library with provided host and password
            Best practices: Set maxmemory-policy for cache eviction, enable persistence for durability
            """,
            # RabbitMQ documentation
            """
            RabbitMQ Setup on QuickSpin:
            - Starter tier: 512MB RAM, 0.5 CPU cores, $0.015/hour
            - Pro tier: 2GB RAM, 1 CPU core, $0.05/hour
            - Enterprise tier: 8GB RAM, 2 CPU cores, $0.18/hour

            Connection: Use pika (Python) or amqplib with AMQP protocol
            Best practices: Use separate vhosts for environments, implement dead-letter exchanges
            """,
            # PostgreSQL documentation
            """
            PostgreSQL Setup on QuickSpin:
            - Starter tier: 1GB RAM, 0.5 CPU cores, 10GB storage, $0.02/hour
            - Pro tier: 4GB RAM, 2 CPU cores, 50GB storage, $0.08/hour
            - Enterprise tier: 16GB RAM, 4 CPU cores, 200GB storage, $0.30/hour

            Connection: Use psycopg2 or asyncpg for async operations
            Best practices: Enable connection pooling, regular VACUUM, use indexes
            """,
            # Troubleshooting
            """
            Common RabbitMQ Issues:
            - Queue filling up: Check consumer health, scale consumers, increase prefetch count
            - Connection timeouts: Verify network policies, check authentication
            - Memory issues: Implement queue length limits, use lazy queues

            Common Redis Issues:
            - Memory full: Check maxmemory-policy, implement eviction, upgrade tier
            - Slow queries: Use SLOWLOG, optimize data structures, add indexes
            - Connection errors: Verify credentials, check network policies
            """,
            # Cost optimization
            """
            Cost Optimization Strategies:
            - Delete unused services (idle > 7 days)
            - Downgrade oversized instances (< 30% resource usage)
            - Enable backups only for production services
            - Use Starter tier for development/testing
            - Disable high availability for non-critical services
            """,
        ]

        metadatas = [
            {"topic": "redis", "category": "setup"},
            {"topic": "rabbitmq", "category": "setup"},
            {"topic": "postgresql", "category": "setup"},
            {"topic": "troubleshooting", "category": "common_issues"},
            {"topic": "cost_optimization", "category": "best_practices"},
        ]

        ids = [
            "redis_setup",
            "rabbitmq_setup",
            "postgresql_setup",
            "troubleshooting_common",
            "cost_optimization",
        ]

        await self.add_documents(documents=documents, metadatas=metadatas, ids=ids)
