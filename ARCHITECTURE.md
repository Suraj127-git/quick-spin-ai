# QuickSpin AI - Architecture Documentation

## Overview

QuickSpin AI is a Python-based intelligent assistant service that enhances the QuickSpin managed microservices platform with conversational AI capabilities. It uses LangChain/LangGraph for AI orchestration and Groq for ultra-fast LLM inference.

## System Architecture

```
┌───────────────────────────────────────────────────────────────────┐
│                         Client Layer                               │
│  ┌─────────────────┐          ┌─────────────────┐                │
│  │   Web Browser   │          │   CLI (Typer)   │                │
│  │   (HTTPS/REST)  │          │   (Rich UI)     │                │
│  └────────┬────────┘          └────────┬────────┘                │
└───────────┼─────────────────────────────┼─────────────────────────┘
            │                             │
            │         HTTP/REST           │
            ▼                             ▼
┌───────────────────────────────────────────────────────────────────┐
│                      API Layer (FastAPI)                           │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐             │
│  │   /chat     │  │ /recommend  │  │   /health    │             │
│  └─────────────┘  └─────────────┘  └──────────────┘             │
│                                                                    │
│  Dependencies: Security (JWT), Database, HTTP Client              │
└───────────────────────────┬───────────────────────────────────────┘
                            │
                            ▼
┌───────────────────────────────────────────────────────────────────┐
│                    Service Layer                                   │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │              AIEngineService                              │    │
│  │  - Intent Detection                                       │    │
│  │  - Context Retrieval                                      │    │
│  │  - Workflow Orchestration                                 │    │
│  │  - Response Generation                                    │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                    │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ QuickSpinClient │  │ VectorStoreServ │  │ KubernetesClient│  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└───────────────────────────┬───────────────────────────────────────┘
                            │
                            ▼
┌───────────────────────────────────────────────────────────────────┐
│                  Workflow Layer (LangGraph)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │  Provision   │  │  Diagnose    │  │  Optimize    │           │
│  │  Workflow    │  │  Workflow    │  │  Workflow    │           │
│  │              │  │              │  │              │           │
│  │ 1. Extract   │  │ 1. Gather    │  │ 1. Analyze   │           │
│  │ 2. Validate  │  │ 2. Analyze   │  │ 2. Calculate │           │
│  │ 3. Estimate  │  │ 3. Recommend │  │ 3. Recommend │           │
│  │ 4. Execute   │  │ 4. Execute   │  │              │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
└───────────────────────────┬───────────────────────────────────────┘
                            │
                            ▼
┌───────────────────────────────────────────────────────────────────┐
│                  Repository/Data Layer                             │
│  ┌──────────────────┐  ┌──────────────────┐                      │
│  │ ConversationRepo │  │  KnowledgeRepo   │                      │
│  │   (MongoDB)      │  │   (ChromaDB)     │                      │
│  │                  │  │                  │                      │
│  │ - Conversations  │  │ - Documentation  │                      │
│  │ - Messages       │  │ - Troubleshooting│                      │
│  │ - User Context   │  │ - Best Practices │                      │
│  └──────────────────┘  └──────────────────┘                      │
└───────────────────────────────────────────────────────────────────┘
            │                             │
            ▼                             ▼
     ┌───────────┐                 ┌───────────┐
     │  MongoDB  │                 │ ChromaDB  │
     └───────────┘                 └───────────┘
```

## Component Details

### 1. API Layer (FastAPI)

**Responsibilities**:
- HTTP request/response handling
- JWT authentication and authorization
- Input validation (Pydantic models)
- Dependency injection
- Error handling and logging
- Prometheus metrics

**Key Files**:
- `app/main.py`: Application entry point
- `app/routers/chat.py`: Chat endpoints
- `app/routers/recommendations.py`: Recommendation endpoints
- `app/routers/health.py`: Health checks

### 2. Service Layer

#### AIEngineService

**Responsibilities**:
- Intent detection from user messages
- Context retrieval from vector store
- Workflow selection and execution
- Response generation using LLM
- Conversation management

**Flow**:
```
User Message → Intent Detection → Context Retrieval → Workflow Execution → Response
```

#### QuickSpinClient

**Responsibilities**:
- Async HTTP client for QuickSpin API
- Service provisioning, deletion, scaling
- Metrics and logs retrieval
- Billing information access

**Integration**:
- Uses user JWT token for authentication
- Proxies requests to QuickSpin backend
- Handles retries and error mapping

#### VectorStoreService

**Responsibilities**:
- Semantic search over knowledge base
- Document embedding and indexing
- Knowledge base initialization

**Knowledge Categories**:
- Setup guides (Redis, RabbitMQ, PostgreSQL, etc.)
- Troubleshooting patterns
- Cost optimization strategies

#### KubernetesClient

**Responsibilities**:
- Pod status and health checks
- Log retrieval from containers
- Resource usage metrics
- Pod restart capabilities

### 3. Workflow Layer (LangGraph)

#### Provision Workflow

**Steps**:
1. **Extract Requirements**: Parse natural language to ServiceConfig
2. **Validate**: Check quotas and permissions
3. **Estimate Cost**: Calculate hourly/monthly costs
4. **Get Confirmation**: Present plan to user
5. **Execute**: Call QuickSpin API to provision service
6. **Generate Response**: Return connection info and status

**Technologies**:
- LangChain for prompt engineering
- Groq for fast LLM inference
- Vector store for configuration best practices

#### Diagnose Workflow

**Steps**:
1. **Gather Diagnostics**: Service metrics, logs, pod status
2. **Search Knowledge**: Find similar issues in vector store
3. **Analyze**: Use LLM to identify root cause
4. **Recommend Actions**: Suggest fixes with priority
5. **Execute (optional)**: Apply fixes with user confirmation

**Data Sources**:
- QuickSpin service metrics
- Kubernetes pod logs
- Historical troubleshooting patterns

#### Optimize Workflow

**Steps**:
1. **Fetch Services**: Get all user services and metrics
2. **Analyze Usage**: Identify underutilized resources
3. **Calculate Costs**: Current spend and breakdown
4. **Generate Recommendations**: Specific actions with savings
5. **Prioritize**: High/medium/low based on impact

**Optimization Strategies**:
- Idle resource cleanup (>7 days no activity)
- Resource rightsizing (<30% utilization)
- Tier downgrade opportunities
- Disable unused features (backups, HA)

### 4. Repository Layer

#### ConversationRepository

**Schema**:
```python
Conversation:
  - id: ObjectId
  - user_id: str
  - organization_id: str
  - title: str
  - created_at: datetime
  - updated_at: datetime
  - message_count: int

ConversationMessage:
  - id: ObjectId
  - conversation_id: str
  - role: user | assistant | system
  - content: str
  - timestamp: datetime
  - metadata: dict
```

**Operations**:
- Create/get/list/delete conversations
- Save/retrieve messages
- Query recent messages for context

#### KnowledgeRepository

**ChromaDB Collections**:
- `quickspin_knowledge`: Main knowledge base
- Documents with metadata (topic, category)
- Semantic search with cosine similarity

**Seeding**:
- Automatic on first startup
- Pre-populated with QuickSpin documentation
- Extensible for custom knowledge

## Data Flow

### Chat Message Processing

```
1. User sends message via API/CLI
   ↓
2. FastAPI validates JWT token
   ↓
3. Extract UserContext (user_id, org_id, tier)
   ↓
4. AIEngineService.process_message()
   ├─ Get/create conversation
   ├─ Save user message to MongoDB
   ├─ Detect intent (LLM)
   ├─ Retrieve context from ChromaDB
   ├─ Get conversation history
   ├─ Select workflow based on intent
   └─ Execute workflow
       ├─ Provision: Extract config → Estimate → Call API
       ├─ Diagnose: Gather data → Analyze → Recommend
       └─ Optimize: Fetch services → Analyze → Recommend
   ↓
5. Generate response using LLM
   ↓
6. Save assistant message to MongoDB
   ↓
7. Return ChatResponse with message, actions, metadata
```

### Cost Optimization Flow

```
1. User requests recommendations
   ↓
2. OptimizeWorkflow.execute()
   ├─ QuickSpinClient.list_services()
   ├─ For each service:
   │   ├─ Get metrics
   │   ├─ Calculate utilization
   │   └─ Identify optimization opportunity
   ├─ Calculate total costs
   ├─ Generate recommendations
   └─ Calculate potential savings
   ↓
3. Return RecommendationResponse
   ├─ List of Recommendation objects
   ├─ CostAnalysis summary
   └─ Total potential savings
```

## AI Components

### Intent Detection

Uses LLM to classify user intent:
- `provision_service`: Create new service
- `get_service_info`: Query service details
- `troubleshoot`: Fix issues
- `optimize_costs`: Reduce spending
- `get_connection_info`: Connection details
- `general_question`: General help

### Context Retrieval

Semantic search in ChromaDB:
- Query: User message
- Filter: Category (setup, common_issues, best_practices)
- Results: Top 2-3 most relevant documents
- Used to enhance LLM prompts

### Response Generation

LangChain prompt template:
```python
System: You are QuickSpin AI Assistant...
        Context: {knowledge_base_results}
        History: {recent_messages}
User: {user_message}
```

Groq LLM (Mixtral 8x7B):
- Ultra-fast inference (<1s)
- High quality responses
- Cost-effective ($0.10/1M tokens)

## Performance Characteristics

### Resource Footprint

- **Memory**: 200-256MB
- **CPU**: 0.1-0.2 cores idle, 0.5 cores peak
- **Storage**: 100MB (code) + 50MB (ChromaDB)

### Latency

- **Health check**: <10ms
- **Simple chat**: 500-800ms
- **Complex workflow**: 1-2s
- **Cost analysis**: 2-3s

### Scalability

- **Horizontal scaling**: Stateless design, scales with pods
- **Database**: MongoDB handles 1000s conversations/sec
- **Vector store**: ChromaDB in-memory for fast search
- **LLM**: Groq handles burst traffic

## Security

### Authentication

- JWT token validation (local or via auth service)
- Token contains: user_id, org_id, tier, roles
- Enforced at API layer (FastAPI dependency)

### Authorization

- Organization-scoped data access
- Conversation ownership verification
- Role-based permissions (admin, member, viewer)

### Data Isolation

- Conversations scoped by user_id
- MongoDB queries filtered by user
- No cross-organization data leakage

### Secrets Management

- Environment variables for API keys
- Kubernetes secrets in production
- No credentials in code or logs

## Monitoring

### Prometheus Metrics

Exposed at `/api/v1/metrics`:
- HTTP request duration
- Request count by endpoint
- Error rate
- Active conversations
- LLM inference time

### Logging

Structured logging with Python `logging`:
- Request/response logging
- Error stack traces
- Workflow execution steps
- LLM prompts and responses (debug mode)

### Health Checks

- `/api/v1/health`: Basic liveness
- `/api/v1/health/ready`: Database connectivity

## Future Enhancements

### Planned Features

1. **Streaming Responses**: SSE for real-time AI responses
2. **Multi-Service Operations**: Batch provisioning
3. **Proactive Alerts**: AI-driven anomaly detection
4. **Voice Interface**: Speech-to-text integration
5. **Custom Workflows**: User-defined automation

### Scalability Improvements

1. **Redis Caching**: Cache frequent queries
2. **Message Queue**: Async workflow execution
3. **Vector Store Sharding**: Scale knowledge base
4. **LLM Fine-tuning**: QuickSpin-specific model

### Integration Enhancements

1. **Slack Bot**: Conversational AI in Slack
2. **GitHub Actions**: CI/CD integration
3. **Grafana**: Metrics visualization
4. **Datadog**: APM and tracing
