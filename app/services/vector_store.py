"""ChromaDB vector store service for semantic search."""

from app.core.config import Settings
from app.repositories.knowledge_repo import KnowledgeRepository


class VectorStoreService:
    """Service for semantic search over QuickSpin knowledge base."""

    def __init__(self, settings: Settings) -> None:
        """
        Initialize vector store service.

        Args:
            settings: Application settings
        """
        self.repo = KnowledgeRepository(settings)

    async def search_knowledge(
        self,
        query: str,
        category: str | None = None,
        n_results: int = 3,
    ) -> list[dict[str, str]]:
        """
        Search knowledge base for relevant information.

        Args:
            query: Search query
            category: Optional category filter
            n_results: Number of results to return

        Returns:
            List of relevant documents with metadata
        """
        where = {"category": category} if category else None
        results = await self.repo.search(query, n_results=n_results, where=where)

        # Combine documents with their metadata
        knowledge_items = []
        for i, doc in enumerate(results["documents"]):
            knowledge_items.append(
                {
                    "content": doc,
                    "metadata": results["metadatas"][i],
                    "relevance": 1 - results["distances"][i],  # Convert distance to similarity
                }
            )

        return knowledge_items

    async def add_knowledge(
        self,
        documents: list[str],
        metadatas: list[dict[str, str]],
    ) -> None:
        """
        Add new documents to knowledge base.

        Args:
            documents: List of document texts
            metadatas: List of metadata for each document
        """
        await self.repo.add_documents(documents=documents, metadatas=metadatas)

    async def initialize_knowledge_base(self) -> None:
        """Initialize knowledge base with QuickSpin documentation."""
        count = await self.repo.count()
        if count == 0:
            await self.repo.seed_knowledge_base()
