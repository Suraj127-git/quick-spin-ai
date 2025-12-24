# QuickSpin AI Service - CI/CD Setup Guide

Complete guide for setting up GitLab CI/CD for the QuickSpin AI intelligent service.

---

## Overview

The QuickSpin AI service is now fully integrated into the GitLab CI/CD pipeline with:
- ✅ **Automated testing** (pytest, ruff, mypy)
- ✅ **Security scanning** (Trivy, dependency scanning, secret detection)
- ✅ **Automated deployments** (staging on `develop`, production on `main` with manual approval)
- ✅ **Complete Kubernetes manifests** (deployment, service, ingress, HPA, PVC for ChromaDB)
- ✅ **Discord notifications**

---

## Quick Start

### 1. Configure GitLab CI/CD Variables

Go to GitLab: **Settings → CI/CD → Variables** and add:

| Variable | Value | Protected | Masked |
|----------|-------|-----------|--------|
| `QUICKSPIN_API_URL` | `https://api-staging.quickspin.cloud` | ❌ No | ❌ No |
| `QUICKSPIN_API_URL_PROD` | `https://api.quickspin.cloud` | ✅ Yes | ❌ No |
| `QUICKSPIN_AUTH_URL` | `https://auth-staging.quickspin.cloud` | ❌ No | ❌ No |
| `QUICKSPIN_AUTH_URL_PROD` | `https://auth.quickspin.cloud` | ✅ Yes | ❌ No |
| `GROQ_API_KEY` | `gsk_...` (from Groq console) | ✅ Yes | ✅ Yes |
| `GROQ_API_KEY_PROD` | `gsk_...` (production key) | ✅ Yes | ✅ Yes |
| `MONGODB_URI` | `mongodb://user:pass@host:port/quickspin_ai` | ✅ Yes | ✅ Yes |
| `MONGODB_URI_PROD` | `mongodb://user:pass@host:port/quickspin_ai` | ✅ Yes | ✅ Yes |
| `JWT_SECRET_KEY` | `openssl rand -base64 32` | ✅ Yes | ✅ Yes |
| `JWT_SECRET_KEY_PROD` | `openssl rand -base64 32` | ✅ Yes | ✅ Yes |
| `KUBECONFIG_CONTENT` | See [RBAC setup](../quick-spin-backend/k8s/rbac/README.md) | File | ✅ Yes |
| `DISCORD_WEBHOOK_URL` | Discord webhook (optional) | ❌ No | ❌ No |

**See:** [GITLAB_VARIABLES_SETUP.md](../GITLAB_VARIABLES_SETUP.md#ai-service-variables) for detailed instructions.

### 2. Set Up Kubernetes Namespace

```bash
# Create namespace
kubectl apply -f k8s/namespace.yaml

# Create image pull secret
kubectl create secret docker-registry gitlab-registry \
  --docker-server=registry.gitlab.com \
  --docker-username=<deploy-token-username> \
  --docker-password=<deploy-token-password> \
  -n quickspin-ai

# Verify
kubectl get namespace quickspin-ai
kubectl get secret gitlab-registry -n quickspin-ai
```

### 3. Deploy Initial Resources

```bash
# Create PersistentVolumeClaim for ChromaDB
kubectl apply -f k8s/pvc.yaml

# Create certificate (requires cert-manager)
kubectl apply -f k8s/certificate.yaml

# Verify PVC is bound
kubectl get pvc -n quickspin-ai
```

### 4. Test Pipeline

```bash
# Create feature branch
git checkout -b test/ai-cicd

# Make a small change
echo "# CI/CD Test" >> README.md
git add README.md
git commit -m "test: Trigger AI service CI/CD pipeline"
git push origin test/ai-cicd

# Watch pipeline in GitLab
# Go to: CI/CD → Pipelines
```

### 5. Deploy to Staging

```bash
# Merge to develop branch
git checkout develop
git merge test/ai-cicd
git push origin develop

# GitLab automatically:
# 1. Runs tests
# 2. Scans for security issues
# 3. Builds Docker image
# 4. Deploys to staging namespace
```

### 6. Deploy to Production

```bash
# Merge to main branch
git checkout main
git merge develop
git push origin main

# In GitLab:
# 1. Pipeline runs automatically
# 2. Production deployment job waits for manual approval
# 3. Click "deploy:production" job → Run
# 4. Monitor deployment in New Relic (if configured)
```

---

## Pipeline Stages

### 1. Test Stage
- **Unit Tests:** `pytest tests/ -v --cov=app`
- **Linting:** `ruff check app/`
- **Type Checking:** `mypy app/ --strict`
- **Coverage:** Generates coverage report, uploads to GitLab

### 2. Security Stage
- **Container Scanning:** Trivy scans Docker image for vulnerabilities
- **Dependency Scanning:** Safety + pip-audit check Python dependencies
- **Secret Detection:** Scans codebase for accidentally committed secrets

### 3. Build Stage
- **Docker Build:** Multi-stage build with UV package manager
- **Registry Push:** Pushes to GitLab Container Registry
- **Tags:** `latest`, `$CI_COMMIT_SHORT_SHA`

### 4. Deploy-Staging Stage
- **Trigger:** Automatic on `develop` branch push
- **Creates Secrets:** From GitLab CI/CD variables
- **Updates Deployment:** Sets image to new SHA
- **Waits for Rollout:** Ensures all pods are healthy
- **Environment:** `ai-staging` (https://ai-staging.quickspin.cloud)

### 5. Deploy-Production Stage
- **Trigger:** Manual approval on `main` branch
- **Creates Secrets:** Production variants (`_PROD` suffix)
- **Updates Deployment:** Zero-downtime rolling update
- **Health Checks:** Verifies all pods pass readiness checks
- **Environment:** `ai-production` (https://ai.quickspin.cloud)

### 6. Notify Stage
- **Discord Notification:** Sends build status to Discord webhook
- **Always Runs:** Triggers on both success and failure

---

## Kubernetes Architecture

### Deployment
- **Replicas:** 2 (minimum)
- **Image:** `registry.gitlab.com/quick-spin/quick-spin-ai:latest`
- **Resources:**
  - Request: 500m CPU, 1Gi memory
  - Limit: 2 CPU, 2Gi memory
- **Service Account:** `quickspin-operator` (from backend, for K8s API access)
- **Volume:** ChromaDB PersistentVolume mounted at `/data/chroma`

### Service
- **Type:** ClusterIP (internal only)
- **Port:** 8000
- **Session Affinity:** ClientIP (3-hour timeout)

### Ingress
- **Host:** `ai.quickspin.cloud`
- **TLS:** Let's Encrypt (cert-manager)
- **Rate Limit:** 100 requests/minute
- **Timeout:** 300 seconds (for long AI operations)

### HPA (Autoscaling)
- **Min Replicas:** 2
- **Max Replicas:** 6
- **Metrics:**
  - CPU: 70% utilization
  - Memory: 80% utilization
- **Behavior:** Fast scale-up, gradual scale-down

### PersistentVolume
- **Name:** `quickspin-ai-chroma-pvc`
- **Size:** 10Gi
- **Purpose:** ChromaDB vector store persistence
- **Storage Class:** `local-path` (K3s default)

---

## Environment Variables

### Application Config (Hardcoded)
```yaml
APP_ENV: production
LOG_LEVEL: INFO
API_PREFIX: /api/v1
HOST: 0.0.0.0
PORT: 8000
WORKERS: 2
GROQ_MODEL: mixtral-8x7b-32768
CHROMA_PERSIST_DIR: /data/chroma
CHROMA_COLLECTION_NAME: quickspin_knowledge
MONGODB_DATABASE: quickspin_ai
JWT_ALGORITHM: HS256
```

### Secrets (From GitLab CI/CD)
```yaml
QUICKSPIN_API_URL: QuickSpin backend API endpoint
QUICKSPIN_AUTH_URL: QuickSpin auth service endpoint
GROQ_API_KEY: Groq AI API key for inference
MONGODB_URI: MongoDB connection string
JWT_SECRET_KEY: JWT token signing key
K8S_IN_CLUSTER: "true"
```

---

## Monitoring & Health Checks

### Health Endpoint
```bash
# Check health
curl https://ai.quickspin.cloud/api/v1/health

# Expected response:
{
  "status": "healthy",
  "version": "0.1.0",
  "mongodb": "connected",
  "vector_store": "ready"
}
```

### Liveness Probe
- **Path:** `/api/v1/health`
- **Initial Delay:** 30s
- **Period:** 10s
- **Timeout:** 5s
- **Failure Threshold:** 3

### Readiness Probe
- **Path:** `/api/v1/health`
- **Initial Delay:** 10s
- **Period:** 5s
- **Timeout:** 3s
- **Failure Threshold:** 3

### Prometheus Metrics
```bash
# Metrics endpoint
curl https://ai.quickspin.cloud/metrics
```

---

## Troubleshooting

### Pipeline Fails at Test Stage

```bash
# Run tests locally
cd quick-spin-ai
uv sync --all-extras
uv run pytest tests/ -v

# Fix failing tests, then commit
git add .
git commit -m "fix: Fix failing tests"
git push
```

### Container Scanning Finds Vulnerabilities

```yaml
# Create .trivyignore file to suppress false positives
cat > .trivyignore <<EOF
CVE-2023-XXXXX  # False positive - not applicable
EOF

git add .trivyignore
git commit -m "security: Add Trivy ignore list"
```

### Deployment Fails - ImagePullBackOff

```bash
# Check if gitlab-registry secret exists
kubectl get secret gitlab-registry -n quickspin-ai

# If missing, create it:
kubectl create secret docker-registry gitlab-registry \
  --docker-server=registry.gitlab.com \
  --docker-username=<token-username> \
  --docker-password=<token-password> \
  -n quickspin-ai
```

### Pods Crash - MongoDB Connection Failed

```bash
# Check if secret has correct MONGODB_URI
kubectl get secret quickspin-ai-secrets -n quickspin-ai -o yaml

# Verify MongoDB is accessible from cluster
kubectl run -it --rm debug --image=mongo:7 --restart=Never -- mongosh "$MONGODB_URI"

# Update secret if needed (via GitLab CI/CD variables)
# Then redeploy
```

### ChromaDB Volume Issues

```bash
# Check PVC status
kubectl get pvc quickspin-ai-chroma-pvc -n quickspin-ai

# If "Pending", check storage class
kubectl get storageclass

# Describe PVC for details
kubectl describe pvc quickspin-ai-chroma-pvc -n quickspin-ai
```

### Rollback Deployment

```bash
# View deployment history
kubectl rollout history deployment/quickspin-ai -n quickspin-ai

# Rollback to previous version
kubectl rollout undo deployment/quickspin-ai -n quickspin-ai

# Check rollout status
kubectl rollout status deployment/quickspin-ai -n quickspin-ai
```

---

## Development Workflow

### Feature Development

```bash
# 1. Create feature branch
git checkout -b feature/new-ai-capability

# 2. Make changes
# ... code changes ...

# 3. Test locally
uv run pytest tests/
uv run ruff check app/
uv run mypy app/

# 4. Commit and push
git add .
git commit -m "feat: Add new AI capability"
git push origin feature/new-ai-capability

# 5. Create merge request
# Go to GitLab → Merge Requests → New merge request
# Set target branch: develop

# 6. Pipeline runs automatically on MR
# Fix any issues, push updates

# 7. Merge to develop after approval
# Automatic deployment to staging

# 8. Test in staging
curl https://ai-staging.quickspin.cloud/api/v1/health

# 9. Merge to main for production
# Requires manual approval in pipeline
```

### Hotfix Workflow

```bash
# 1. Create hotfix branch from main
git checkout main
git pull
git checkout -b hotfix/critical-bug

# 2. Fix the bug
# ... code changes ...

# 3. Test thoroughly
uv run pytest tests/ -v

# 4. Commit and push
git add .
git commit -m "fix: Critical bug in AI inference"
git push origin hotfix/critical-bug

# 5. Create MR to main
# Pipeline runs

# 6. After approval, merge to main
# Manually trigger production deployment

# 7. Backport to develop
git checkout develop
git merge hotfix/critical-bug
git push origin develop
```

---

## Security Best Practices

### ✅ Do

- ✅ Store all secrets in GitLab CI/CD variables (protected + masked)
- ✅ Use different secrets for staging vs production
- ✅ Rotate secrets every 90 days
- ✅ Keep dependencies updated (run `uv lock --upgrade` regularly)
- ✅ Review security scan reports before deploying
- ✅ Use RBAC with least-privilege service account
- ✅ Enable network policies for pod isolation

### ❌ Don't

- ❌ Don't commit secrets to Git
- ❌ Don't use production secrets in staging
- ❌ Don't skip security scans
- ❌ Don't deploy without testing
- ❌ Don't ignore dependency vulnerabilities
- ❌ Don't share Groq API keys publicly

---

## Cost Optimization

### Groq API Usage
- Monitor API usage in Groq dashboard
- Set up alerts for high usage
- Cache AI responses when possible
- Use appropriate model for task (mixtral-8x7b for balance)

### Kubernetes Resources
- HPA scales down to 2 replicas during low traffic
- Right-sized resource requests (500m CPU, 1Gi memory)
- ChromaDB volume reused across restarts

### CI/CD Minutes
- Tests run only on relevant branches (main, develop, MRs)
- Docker layer caching reduces build times
- Security scans run in parallel with tests

---

## Performance Tuning

### Application
```yaml
# Increase workers for higher throughput
env:
  - name: WORKERS
    value: "4"  # Up from 2

# Increase resources
resources:
  requests:
    cpu: 1000m    # Up from 500m
    memory: 2Gi   # Up from 1Gi
  limits:
    cpu: 4000m    # Up from 2000m
    memory: 4Gi   # Up from 2Gi
```

### HPA
```yaml
# Scale more aggressively
spec:
  minReplicas: 3  # Up from 2
  maxReplicas: 10 # Up from 6
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          averageUtilization: 60  # Down from 70
```

### Database
- Use MongoDB with replica set for HA
- Add indexes on frequently queried fields
- Monitor slow queries

---

## Integration with Other Services

### QuickSpin Backend
- AI service calls backend API: `$QUICKSPIN_API_URL`
- Uses JWT tokens from `$QUICKSPIN_AUTH_URL`
- Service account has K8s API access for provisioning

### MongoDB
- Stores conversation history
- Stores AI recommendations
- Used by LangChain for state management

### ChromaDB
- Vector store for RAG (Retrieval-Augmented Generation)
- Persisted to PVC
- Stores QuickSpin knowledge base embeddings

### Groq AI
- LLM inference via Groq API
- Model: mixtral-8x7b-32768
- API key from GitLab secrets

---

## Next Steps

### After Initial Deployment

1. **Monitor Performance**
   - Check New Relic dashboards (if configured)
   - Monitor Groq API usage
   - Review pod resource utilization

2. **Set Up Alerts**
   - High error rate
   - Pod crashes
   - API quota limits

3. **Optimize Knowledge Base**
   - Add more embeddings to ChromaDB
   - Fine-tune RAG retrieval
   - Update system prompts

4. **Enable Advanced Features**
   - Multi-model support (add GPT-4, Claude)
   - Streaming responses
   - Conversation memory optimization

---

## References

- [Main CI/CD Implementation Plan](../CICD_IMPLEMENTATION_PLAN.md)
- [GitLab Variables Setup](../GITLAB_VARIABLES_SETUP.md#ai-service-variables)
- [Kubernetes Manifests README](k8s/README.md)
- [RBAC Configuration](../quick-spin-backend/k8s/rbac/README.md)
- [Rollback Procedures](../ROLLBACK_PROCEDURES.md)
- [Troubleshooting Guide](../CICD_TROUBLESHOOTING.md)

---

**Project:** QuickSpin AI Service
**Version:** 0.1.0
**Python:** 3.12+
**Last Updated:** 2025-12-24
