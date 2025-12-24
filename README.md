# QuickSpin AI

Intelligent AI service for QuickSpin managed microservices platform. Provides conversational service management, intelligent resource optimization, and automated troubleshooting.

## Overview

QuickSpin AI enhances the developer experience by providing:

- **Conversational Service Management**: Provision and manage microservices through natural language
- **Intelligent Recommendations**: Get AI-powered suggestions for service configuration and scaling
- **Automated Troubleshooting**: Diagnose and resolve issues with AI-powered diagnostics
- **Cost Optimization**: Monitor usage and identify opportunities to reduce costs
- **Interactive Assistance**: Learn QuickSpin features through conversational AI

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      QuickSpin AI Service                    │
├─────────────────────────────────────────────────────────────┤
│  FastAPI API          │         Typer CLI                   │
├─────────────────────────────────────────────────────────────┤
│                    AI Engine (LangChain)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Provision   │  │  Diagnose    │  │  Optimize    │      │
│  │  Workflow    │  │  Workflow    │  │  Workflow    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
├─────────────────────────────────────────────────────────────┤
│  Vector Store    │  QuickSpin API  │  Kubernetes API       │
│  (ChromaDB)      │  Client         │  Client               │
└─────────────────────────────────────────────────────────────┘
         │                  │                    │
         ▼                  ▼                    ▼
    Knowledge Base    QuickSpin Services    K8s Cluster
```

## Technical Stack

- **Backend**: FastAPI with async/await
- **AI**: LangChain, LangGraph, Groq API
- **Vector Store**: ChromaDB for semantic search
- **Database**: MongoDB (Motor) for conversation history
- **CLI**: Typer with Rich terminal UI
- **Deployment**: Docker, Kubernetes

## Quick Start

### Prerequisites

- Python 3.12+
- MongoDB (local or remote)
- Groq API key
- QuickSpin account with JWT token

### Installation

```bash
# Clone the repository
cd quick-spin-ai

# Install dependencies with uv
make install

# Or using uv directly
uv sync --all-extras

# Copy environment template
cp .env.example .env

# Edit .env with your configuration
# - Add your GROQ_API_KEY
# - Set MONGODB_URI
# - Add JWT_SECRET_KEY
```

### Running Locally

```bash
# Start development server
make run

# Or using uv
uv run python -m app.main

# API will be available at http://localhost:8000
# Docs at http://localhost:8000/api/v1/docs
```

### Using Docker Compose

```bash
# Build and start services
make docker-up

# View logs
make docker-logs

# Stop services
make docker-down
```

## Usage

### API Usage

#### Chat Endpoint

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I need a Redis instance for caching with 256MB RAM"
  }'
```

#### Get Recommendations

```bash
curl -X GET http://localhost:8000/api/v1/recommendations \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### CLI Usage

#### Interactive Chat Mode

```bash
# Start interactive chat
make run-cli TOKEN=your_jwt_token

# Or using uv
uv run python -m app.cli chat --token your_jwt_token
```

Example conversation:
```
You: I need a Redis instance for caching
QuickSpin AI: I'll create a Redis instance with the following configuration:

Configuration:
- Tier: Starter
- Memory: 256MB
- CPU: 0.5 cores

Estimated Cost:
- Hourly: $0.008
- Monthly: $5.76

To provision this service, confirm and I'll proceed with creation.
```

#### Get Cost Recommendations

```bash
uv run python -m app.cli recommend --token your_jwt_token
```

## Development

### Project Structure

```
quick-spin-ai/
├── app/
│   ├── core/              # Configuration, dependencies, security
│   ├── models/            # Pydantic models
│   ├── repositories/      # Data access layer (MongoDB, ChromaDB)
│   ├── services/          # Business logic services
│   ├── workflows/         # LangGraph workflows
│   ├── routers/           # FastAPI endpoints
│   ├── main.py           # FastAPI application
│   └── cli.py            # Typer CLI
├── tests/                # Test suite
├── Dockerfile            # Multi-stage Docker build
├── docker-compose.yml    # Development environment
├── pyproject.toml        # Dependencies and configuration
└── Makefile             # Development commands
```

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test file
uv run pytest tests/test_health.py -v
```

### Code Quality

```bash
# Format code
make format

# Run linters
make lint

# Type checking with mypy
uv run mypy app/
```

## Configuration

### Environment Variables

See [.env.example](.env.example) for all configuration options.

Key variables:
- `GROQ_API_KEY`: Groq API key for LLM inference
- `MONGODB_URI`: MongoDB connection string
- `JWT_SECRET_KEY`: Secret for JWT validation
- `QUICKSPIN_API_URL`: QuickSpin API endpoint
- `CHROMA_PERSIST_DIR`: ChromaDB persistence directory

### Knowledge Base

The AI uses ChromaDB for semantic search over QuickSpin documentation. On first startup, the knowledge base is automatically seeded with:

- Service setup guides (Redis, RabbitMQ, PostgreSQL, etc.)
- Common troubleshooting solutions
- Cost optimization best practices

Add custom knowledge in [`app/repositories/knowledge_repo.py`](app/repositories/knowledge_repo.py:99).

## Deployment

### Docker

```bash
# Build image
docker build -t quickspin-ai:latest .

# Run container
docker run -d \
  -p 8000:8000 \
  -e GROQ_API_KEY=your_key \
  -e MONGODB_URI=mongodb://mongo:27017 \
  quickspin-ai:latest
```

### Kubernetes

Example deployment:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: quickspin-ai
spec:
  replicas: 2
  selector:
    matchLabels:
      app: quickspin-ai
  template:
    metadata:
      labels:
        app: quickspin-ai
    spec:
      containers:
      - name: quickspin-ai
        image: quickspin-ai:latest
        ports:
        - containerPort: 8000
        env:
        - name: GROQ_API_KEY
          valueFrom:
            secretKeyRef:
              name: quickspin-ai-secrets
              key: groq-api-key
        - name: MONGODB_URI
          value: mongodb://mongo-service:27017/quickspin_ai
        resources:
          requests:
            memory: "256Mi"
            cpu: "200m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

## Features in Detail

### 1. Service Provisioning

The AI understands natural language requests and maps them to QuickSpin service configurations:

**User**: "I need a production-ready PostgreSQL database with high availability"

**AI**: Provisions PostgreSQL with Pro tier, HA enabled, and appropriate resources.

### 2. Troubleshooting

Diagnoses issues by analyzing:
- Service status and metrics
- Kubernetes pod logs
- Historical patterns from knowledge base

**User**: "My RabbitMQ queue is filling up"

**AI**: Analyzes metrics, checks consumer status, suggests scaling or configuration changes.

### 3. Cost Optimization

Identifies optimization opportunities:
- Idle services to delete
- Oversized instances to downgrade
- Unused features to disable

Provides actionable recommendations with estimated monthly savings.

### 4. Conversation History

All conversations are persisted in MongoDB, allowing:
- Context-aware responses
- Conversation resumption
- Usage analytics

## API Endpoints

- `GET /`: Service information
- `GET /api/v1/health`: Health check
- `GET /api/v1/health/ready`: Readiness check
- `POST /api/v1/chat`: Send chat message
- `GET /api/v1/chat/conversations`: List conversations
- `GET /api/v1/chat/conversations/{id}`: Get conversation
- `DELETE /api/v1/chat/conversations/{id}`: Delete conversation
- `GET /api/v1/recommendations`: Get cost optimization recommendations
- `GET /api/v1/metrics`: Prometheus metrics

## Performance

Target resource footprint:
- **Memory**: < 256MB
- **CPU**: < 0.2 cores
- **Startup**: < 5 seconds

Achieved through:
- Groq for ultra-fast inference (no local LLM)
- Lightweight ChromaDB for vector search
- Efficient async I/O with FastAPI
- Minimal dependencies

## Security

- JWT token validation with QuickSpin auth service
- Organization-scoped access control
- Conversation data isolation per user
- No credential storage (proxies to QuickSpin API)

## Contributing

```bash
# Install development dependencies
make dev

# Run tests before committing
make test

# Format code
make format

# Run linters
make lint
```

## License

Proprietary - QuickSpin Platform

## Support

For issues or questions:
- GitHub Issues: [quickspin-ai/issues](https://github.com/quickspin/quickspin-ai/issues)
- Documentation: [docs.quickspin.io](https://docs.quickspin.io)
- Email: support@quickspin.io

---

**QuickSpin AI** - Making microservices management delightful 🚀
