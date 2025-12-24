# QuickSpin AI Service - Kubernetes Manifests

Kubernetes deployment configuration for the QuickSpin AI intelligent service.

---

## Overview

The QuickSpin AI service provides intelligent capabilities including:
- AI-powered chat assistance
- Service provisioning recommendations
- Automated diagnostics and optimization
- LangChain-based workflow orchestration
- Vector store (ChromaDB) for knowledge management

---

## Files

| File | Description |
|------|-------------|
| `namespace.yaml` | quickspin-ai namespace definition |
| `deployment.yaml` | Main AI service deployment (2 replicas) |
| `service.yaml` | ClusterIP service for internal access |
| `ingress.yaml` | NGINX Ingress for external access |
| `pvc.yaml` | PersistentVolumeClaim for ChromaDB vector store (10Gi) |
| `hpa.yaml` | HorizontalPodAutoscaler (2-6 replicas, 70% CPU, 80% memory) |
| `certificate.yaml` | cert-manager TLS certificate |
| `secrets.yaml.example` | Secret template (actual secrets from GitLab CI/CD) |

---

## Deployment

### Prerequisites

1. **GitLab CI/CD variables configured:**
   - See [GITLAB_VARIABLES_SETUP.md](../GITLAB_VARIABLES_SETUP.md#ai-service-variables)
   - Required: GROQ_API_KEY, MONGODB_URI, JWT_SECRET_KEY, etc.

2. **GitLab Container Registry access:**
   - Image pull secret `gitlab-registry` must exist in namespace

3. **Service account:**
   - Uses `quickspin-operator` service account (from backend) for K8s access
   - Ensure RBAC is configured (see [k8s/rbac](../../quick-spin-backend/k8s/rbac/README.md))

### Manual Deployment

```bash
# 1. Create namespace
kubectl apply -f k8s/namespace.yaml

# 2. Create image pull secret
kubectl create secret docker-registry gitlab-registry \
  --docker-server=registry.gitlab.com \
  --docker-username=<deploy-token-username> \
  --docker-password=<deploy-token-password> \
  -n quickspin-ai

# 3. Create secrets (from GitLab variables)
kubectl create secret generic quickspin-ai-secrets \
  --from-literal=QUICKSPIN_API_URL="https://api.quickspin.cloud" \
  --from-literal=QUICKSPIN_AUTH_URL="https://auth.quickspin.cloud" \
  --from-literal=GROQ_API_KEY="gsk_your_key" \
  --from-literal=MONGODB_URI="mongodb://user:pass@host:port/quickspin_ai" \
  --from-literal=JWT_SECRET_KEY="$(openssl rand -base64 32)" \
  --from-literal=K8S_IN_CLUSTER="true" \
  -n quickspin-ai

# 4. Create PersistentVolumeClaim for ChromaDB
kubectl apply -f k8s/pvc.yaml

# 5. Deploy the service
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# 6. Deploy ingress and certificate
kubectl apply -f k8s/certificate.yaml
kubectl apply -f k8s/ingress.yaml

# 7. Deploy HPA (optional but recommended)
kubectl apply -f k8s/hpa.yaml
```

### CI/CD Deployment

The GitLab CI/CD pipeline automatically handles deployment:

- **Staging:** Automatic deployment on `develop` branch push
- **Production:** Manual deployment on `main/master` branch (requires approval)

See [.gitlab-ci.yml](../.gitlab-ci.yml) for pipeline configuration.

---

## Resource Requirements

### Per Pod
- **CPU Request:** 500m (0.5 cores)
- **CPU Limit:** 2000m (2 cores)
- **Memory Request:** 1Gi
- **Memory Limit:** 2Gi
- **Storage:** 10Gi (shared ChromaDB volume)

### Cluster-Wide (Production)
- **Min:** 2 replicas = 1 CPU, 2Gi memory, 10Gi storage
- **Max:** 6 replicas (with HPA) = 3 CPUs, 6Gi memory, 10Gi storage

---

## Health Checks

### Liveness Probe
```yaml
httpGet:
  path: /api/v1/health
  port: 8000
initialDelaySeconds: 30
periodSeconds: 10
```

### Readiness Probe
```yaml
httpGet:
  path: /api/v1/health
  port: 8000
initialDelaySeconds: 10
periodSeconds: 5
```

---

## Autoscaling

The HPA scales based on:
- **CPU:** 70% average utilization
- **Memory:** 80% average utilization

Scale-down behavior:
- Wait 5 minutes before scaling down
- Reduce by max 50% per minute

Scale-up behavior:
- Scale up immediately
- Increase by max 100% per 30 seconds OR 2 pods per 30 seconds

---

## Environment Variables

### From Secrets
- `QUICKSPIN_API_URL` - Backend API endpoint
- `QUICKSPIN_AUTH_URL` - Auth service endpoint
- `GROQ_API_KEY` - Groq AI API key
- `MONGODB_URI` - MongoDB connection string
- `JWT_SECRET_KEY` - JWT signing key
- `K8S_IN_CLUSTER` - Kubernetes in-cluster mode

### Hardcoded in Deployment
- `APP_ENV=production`
- `LOG_LEVEL=INFO`
- `API_PREFIX=/api/v1`
- `GROQ_MODEL=mixtral-8x7b-32768`
- `CHROMA_PERSIST_DIR=/data/chroma`
- `CHROMA_COLLECTION_NAME=quickspin_knowledge`

---

## Storage

### ChromaDB Vector Store
- **PVC Name:** `quickspin-ai-chroma-pvc`
- **Size:** 10Gi
- **Access Mode:** ReadWriteOnce
- **Storage Class:** `local-path` (K3s default)
- **Mount Path:** `/data/chroma` (inside container)

**Note:** This volume persists vector embeddings and knowledge base data. Do not delete unless you want to reset the AI's knowledge.

---

## Networking

### Service
- **Type:** ClusterIP (internal only)
- **Port:** 8000
- **Session Affinity:** ClientIP (3-hour timeout)

### Ingress
- **Host:** `ai.quickspin.cloud`
- **TLS:** Enabled (Let's Encrypt)
- **Rate Limit:** 100 requests/minute
- **Timeouts:** 300 seconds (read/send)
- **Max Body Size:** 10MB

---

## Monitoring

### Prometheus Metrics
The AI service exposes Prometheus metrics via:
```
http://quickspin-ai:8000/metrics
```

Key metrics:
- HTTP request duration
- HTTP request count
- AI inference latency
- Vector store operations

### Health Endpoint
```bash
curl https://ai.quickspin.cloud/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "mongodb": "connected",
  "vector_store": "ready"
}
```

---

## Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl get pods -n quickspin-ai

# View pod logs
kubectl logs -n quickspin-ai deployment/quickspin-ai

# Describe pod for events
kubectl describe pod -n quickspin-ai <pod-name>

# Common issues:
# - ImagePullBackOff: Check gitlab-registry secret
# - CrashLoopBackOff: Check logs for errors
# - Pending: Check PVC is bound
```

### ChromaDB Volume Issues

```bash
# Check PVC status
kubectl get pvc -n quickspin-ai

# Should show "Bound" status
# If "Pending", check storage class availability

# View PVC details
kubectl describe pvc quickspin-ai-chroma-pvc -n quickspin-ai
```

### AI Service Not Responding

```bash
# Check health endpoint
kubectl exec -it deployment/quickspin-ai -n quickspin-ai -- curl localhost:8000/api/v1/health

# Check MongoDB connection
kubectl exec -it deployment/quickspin-ai -n quickspin-ai -- env | grep MONGODB

# Check Groq API key
kubectl exec -it deployment/quickspin-ai -n quickspin-ai -- env | grep GROQ
```

### Rolling Back Deployment

```bash
# View deployment history
kubectl rollout history deployment/quickspin-ai -n quickspin-ai

# Rollback to previous version
kubectl rollout undo deployment/quickspin-ai -n quickspin-ai

# Rollback to specific revision
kubectl rollout undo deployment/quickspin-ai -n quickspin-ai --to-revision=2
```

---

## Scaling

### Manual Scaling

```bash
# Scale to specific replica count
kubectl scale deployment/quickspin-ai --replicas=4 -n quickspin-ai

# Verify scaling
kubectl get deployment quickspin-ai -n quickspin-ai
```

### Autoscaling Status

```bash
# Check HPA status
kubectl get hpa -n quickspin-ai

# View HPA details
kubectl describe hpa quickspin-ai-hpa -n quickspin-ai

# Disable autoscaling (temporarily)
kubectl delete hpa quickspin-ai-hpa -n quickspin-ai
```

---

## Security

### Service Account
Uses `quickspin-operator` service account with permissions to:
- Manage deployments and services
- Access Kubernetes API for service provisioning
- Create/delete resources in tenant namespaces

### Network Policies
The AI service can communicate with:
- QuickSpin backend API
- MongoDB database
- Kubernetes API server
- External Groq AI API (for inference)

### Secrets
All sensitive data stored in Kubernetes secrets:
- Never committed to Git
- Managed via GitLab CI/CD variables
- Encrypted at rest in etcd

---

## Updates and Maintenance

### Updating the Deployment

```bash
# Update image
kubectl set image deployment/quickspin-ai quickspin-ai=registry.gitlab.com/quick-spin/quick-spin-ai:v1.2.3 -n quickspin-ai

# Watch rollout progress
kubectl rollout status deployment/quickspin-ai -n quickspin-ai

# Verify new version
kubectl get pods -n quickspin-ai -o wide
```

### Updating Secrets

```bash
# Update secrets
kubectl create secret generic quickspin-ai-secrets \
  --from-literal=GROQ_API_KEY="new_key" \
  ... (other variables) \
  -n quickspin-ai \
  --dry-run=client -o yaml | kubectl apply -f -

# Restart deployment to pick up new secrets
kubectl rollout restart deployment/quickspin-ai -n quickspin-ai
```

---

## References

- [QuickSpin AI Architecture](../ARCHITECTURE.md)
- [GitLab CI/CD Pipeline](../.gitlab-ci.yml)
- [GitLab Variables Setup](../GITLAB_VARIABLES_SETUP.md#ai-service-variables)
- [RBAC Configuration](../../quick-spin-backend/k8s/rbac/README.md)

---

**Last Updated:** 2025-12-24
**Kubernetes Version:** v1.24+ (K3s v1.33.6)
**AI Service Version:** 0.1.0
