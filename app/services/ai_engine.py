"""AI engine service orchestrating LangChain and LangGraph."""

from typing import Any

from groq import AsyncGroq
from langchain.chains import LLMChain
from langchain.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

from app.core.config import Settings
from app.core.security import UserContext
from app.models.conversation import ChatRequest, ChatResponse
from app.repositories.conversation_repo import ConversationRepository
from app.services.quickspin_client import QuickSpinClient
from app.services.vector_store import VectorStoreService
from app.workflows.provision import ProvisionWorkflow


class AIEngineService:
    """
    Core AI engine orchestrating conversations and workflows.

    This service coordinates:
    - Intent detection and classification
    - Context retrieval from vector store
    - LangGraph workflow execution
    - Response generation
    """

    def __init__(
        self,
        groq_client: AsyncGroq,
        settings: Settings,
        vector_store: VectorStoreService,
        quickspin_client: QuickSpinClient,
        conversation_repo: ConversationRepository,
    ) -> None:
        """
        Initialize AI engine.

        Args:
            groq_client: Groq async client
            settings: Application settings
            vector_store: Vector store service
            quickspin_client: QuickSpin API client
            conversation_repo: Conversation repository
        """
        self.groq_client = groq_client
        self.settings = settings
        self.vector_store = vector_store
        self.quickspin_client = quickspin_client
        self.conversation_repo = conversation_repo

        # Initialize LangChain LLM
        self.llm = ChatGroq(
            groq_api_key=settings.groq_api_key,
            model_name=settings.groq_model,
            temperature=0.7,
        )

        # Initialize workflows
        self.provision_workflow = ProvisionWorkflow(
            llm=self.llm,
            quickspin_client=quickspin_client,
            vector_store=vector_store,
        )

    async def _detect_intent(self, message: str) -> dict[str, Any]:
        """
        Detect user intent from message.

        Args:
            message: User message

        Returns:
            Dictionary with intent and extracted parameters
        """
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are an intent classifier for QuickSpin, a managed microservices platform.
                    Analyze the user message and classify it into one of these intents:
                    - provision_service: User wants to create a new service
                    - get_service_info: User wants information about a service
                    - troubleshoot: User has a problem with a service
                    - optimize_costs: User wants to reduce costs
                    - get_connection_info: User needs connection details
                    - general_question: General question about QuickSpin

                    Return JSON with 'intent' and 'entities' (extracted service types, names, etc).
                    """,
                ),
                ("user", "{message}"),
            ]
        )

        chain = LLMChain(llm=self.llm, prompt=prompt)
        result = await chain.ainvoke({"message": message})

        # Parse LLM response (simplified - in production use structured output)
        response_text = result["text"].strip()

        # Simple intent detection based on keywords
        intent = "general_question"
        entities: dict[str, str] = {}

        message_lower = message.lower()
        if any(
            word in message_lower
            for word in ["create", "provision", "need", "want", "set up", "setup"]
        ):
            intent = "provision_service"
            # Extract service type
            for service_type in ["redis", "rabbitmq", "postgresql", "mongodb", "elasticsearch"]:
                if service_type in message_lower:
                    entities["service_type"] = service_type
                    break

        elif any(word in message_lower for word in ["connect", "connection", "credentials"]):
            intent = "get_connection_info"

        elif any(word in message_lower for word in ["problem", "issue", "error", "broken", "not working"]):
            intent = "troubleshoot"

        elif any(word in message_lower for word in ["cost", "bill", "expensive", "save money"]):
            intent = "optimize_costs"

        return {"intent": intent, "entities": entities, "confidence": 0.85}

    async def _retrieve_context(self, message: str, intent: str) -> list[dict[str, str]]:
        """
        Retrieve relevant context from knowledge base.

        Args:
            message: User message
            intent: Detected intent

        Returns:
            List of relevant knowledge base entries
        """
        # Map intent to category
        category_map = {
            "provision_service": "setup",
            "troubleshoot": "common_issues",
            "optimize_costs": "best_practices",
        }

        category = category_map.get(intent)
        return await self.vector_store.search_knowledge(
            query=message,
            category=category,
            n_results=2,
        )

    async def _generate_response(
        self,
        message: str,
        intent: str,
        context: list[dict[str, str]],
        conversation_history: list[dict[str, str]],
    ) -> str:
        """
        Generate AI response using LLM.

        Args:
            message: User message
            intent: Detected intent
            context: Retrieved knowledge base context
            conversation_history: Recent conversation messages

        Returns:
            Generated response text
        """
        # Build context string
        context_str = "\n\n".join([item["content"] for item in context])

        # Build conversation history
        history_str = "\n".join(
            [f"{msg['role']}: {msg['content']}" for msg in conversation_history[-5:]]
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are QuickSpin AI Assistant, helping developers manage their microservices.

                    Context from knowledge base:
                    {context}

                    Recent conversation:
                    {history}

                    Be concise, helpful, and technical. Provide specific commands, code snippets,
                    and configuration examples when relevant. If you suggest actions, explain the impact.
                    """,
                ),
                ("user", "{message}"),
            ]
        )

        chain = LLMChain(llm=self.llm, prompt=prompt)
        result = await chain.ainvoke(
            {
                "message": message,
                "context": context_str,
                "history": history_str,
            }
        )

        return result["text"].strip()

    async def process_message(
        self,
        request: ChatRequest,
        user: UserContext,
        user_token: str,
    ) -> ChatResponse:
        """
        Process user message and generate response.

        Args:
            request: Chat request
            user: User context
            user_token: User JWT token

        Returns:
            ChatResponse with AI-generated reply
        """
        # Get or create conversation
        if request.conversation_id:
            conversation = await self.conversation_repo.get_conversation(
                request.conversation_id
            )
            if not conversation:
                conversation = await self.conversation_repo.create_conversation(
                    user_id=user.user_id,
                    organization_id=user.organization_id,
                )
        else:
            conversation = await self.conversation_repo.create_conversation(
                user_id=user.user_id,
                organization_id=user.organization_id,
            )

        # Save user message
        await self.conversation_repo.save_message(
            conversation_id=str(conversation.id),
            role="user",
            content=request.message,
            metadata=request.context,
        )

        # Detect intent
        intent_result = await self._detect_intent(request.message)
        intent = intent_result["intent"]

        # Retrieve context
        context = await self._retrieve_context(request.message, intent)

        # Get conversation history
        recent_messages = await self.conversation_repo.get_recent_messages(
            conversation_id=str(conversation.id),
            count=10,
        )
        conversation_history = [
            {"role": msg.role.value, "content": msg.content} for msg in recent_messages
        ]

        # Execute workflow based on intent
        actions: list[dict[str, Any]] = []
        if intent == "provision_service":
            # Use provision workflow
            workflow_result = await self.provision_workflow.execute(
                message=request.message,
                entities=intent_result["entities"],
                user_token=user_token,
            )
            response_text = workflow_result["message"]
            actions = workflow_result.get("actions", [])
        else:
            # Generate standard response
            response_text = await self._generate_response(
                message=request.message,
                intent=intent,
                context=context,
                conversation_history=conversation_history,
            )

        # Save assistant message
        await self.conversation_repo.save_message(
            conversation_id=str(conversation.id),
            role="assistant",
            content=response_text,
            metadata={"intent": intent},
        )

        return ChatResponse(
            conversation_id=str(conversation.id),
            message=response_text,
            intent=intent,
            actions=actions,
            metadata={"confidence": intent_result["confidence"]},
        )
