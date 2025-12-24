# QuickSpin AI - Quick Start Guide

Get up and running with QuickSpin AI in 5 minutes.

## Prerequisites

- Python 3.12 or higher
- MongoDB (local or Docker)
- Groq API key ([get one here](https://console.groq.com))
- QuickSpin account with JWT token

## Installation

### Option 1: Automated Setup (Recommended)

```bash
cd quick-spin-ai
chmod +x setup.sh
./setup.sh
```

The script will:
- Check Python version
- Install uv (if needed)
- Install dependencies
- Create `.env` file
- Set up data directories

### Option 2: Manual Setup

```bash
# Install uv (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync --all-extras

# Create environment file
cp .env.example .env

# Edit .env with your configuration
nano .env
```

## Configuration

Edit `.env` and add:

```bash
# Required
GROQ_API_KEY=gsk_your_groq_api_key_here
JWT_SECRET_KEY=your_random_secret_key_here

# MongoDB (use Docker Compose or your own)
MONGODB_URI=mongodb://localhost:27017/quickspin_ai

# Optional - defaults provided
QUICKSPIN_API_URL=https://api.quickspin.io
GROQ_MODEL=mixtral-8x7b-32768
```

## Running with Docker Compose (Easiest)

```bash
# Start all services (API + MongoDB)
docker-compose up -d

# View logs
docker-compose logs -f quickspin-ai

# Stop services
docker-compose down
```

API will be available at `http://localhost:8000`

## Running Locally

```bash
# Start MongoDB (if not using Docker)
mongod --dbpath ./data/mongodb

# In another terminal, start the API
make run
# Or: uv run python -m app.main
```

## Verify Installation

```bash
# Check health
curl http://localhost:8000/api/v1/health

# Expected response:
# {"status":"healthy","service":"quickspin-ai"}
```

## First Steps

### 1. API Documentation

Visit `http://localhost:8000/api/v1/docs` for interactive API documentation.

### 2. Test Chat Endpoint

```bash
export TOKEN="your_quickspin_jwt_token"

curl -X POST http://localhost:8000/api/v1/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is QuickSpin?"
  }'
```

### 3. Use CLI

```bash
# Interactive chat mode
uv run python -m app.cli chat --token $TOKEN

# Get cost recommendations
uv run python -m app.cli recommend --token $TOKEN
```

## Example Conversations

### Provisioning a Service

```
You: I need a Redis instance for caching with 512MB RAM

AI: I'll create a Redis instance with the following configuration:

Configuration:
- Tier: Pro
- Memory: 512MB
- CPU: 1 cores

Estimated Cost:
- Hourly: $0.03
- Monthly: $21.60

To provision this service, confirm and I'll proceed with creation.
```

### Getting Connection Info

```
You: How do I connect to my Redis instance redis-dev-abc123?

AI: Here's how to connect to redis-dev-abc123:

Python:
import redis
r = redis.Redis(
    host='redis-dev-abc123.quickspin.io',
    port=6379,
    password='your_password_here'
)

Your connection string and credentials are available in the QuickSpin dashboard.
```

### Cost Optimization

```
You: How can I reduce my bill?

AI: I analyzed your services and found 3 optimization opportunities:

1. [HIGH] Delete 2 idle PostgreSQL instances
   - Services: postgres-test-1, postgres-test-2
   - Last activity: 8 days ago
   - Potential savings: $15.00/month

2. [MEDIUM] Downgrade underutilized Elasticsearch cluster
   - Service: es-logs-dev
   - Current utilization: 25%
   - Potential savings: $8.00/month

Total potential savings: $23.00/month
```

## Troubleshooting

### MongoDB Connection Error

```bash
# Make sure MongoDB is running
docker-compose up -d mongodb

# Or start local MongoDB
mongod --dbpath ./data/mongodb
```

### Groq API Error

- Verify your `GROQ_API_KEY` in `.env`
- Check quota at [console.groq.com](https://console.groq.com)

### Import Errors

```bash
# Reinstall dependencies
uv sync --all-extras --force
```

### Port Already in Use

```bash
# Change port in .env
PORT=8001

# Or kill process on port 8000
lsof -ti:8000 | xargs kill -9
```

## Development Workflow

```bash
# Install dev dependencies
make dev

# Run tests
make test

# Format code
make format

# Run linters
make lint

# View all commands
make help
```

## Next Steps

- Read [README.md](README.md) for detailed features
- See [ARCHITECTURE.md](ARCHITECTURE.md) for system design
- Check [CONTRIBUTING.md](CONTRIBUTING.md) for contributing guidelines

## Getting Help

- API Docs: `http://localhost:8000/api/v1/docs`
- Issues: [GitHub Issues](https://github.com/quickspin/quickspin-ai/issues)
- Email: support@quickspin.io

---

Happy building! 🚀
