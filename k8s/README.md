# Kubernetes Manifests + Helm Charts

This directory contains two equivalent deployment approaches for the Oil Price Pipeline:

| Approach | Location | Best for |
|----------|----------|----------|
| Raw manifests | `manifests/` | Understanding what each resource does, one-off deploys |
| Helm chart | `helm/oil-pipeline/` | Repeatable installs, environment overrides, portfolio demo |

Both produce identical deployments — the Helm chart is simply the parameterized version of the raw manifests.

---

## Architecture

```
                          ┌─────────────────────────────────────────┐
                          │          Namespace: oil-pipeline          │
                          │                                           │
  kubectl port-forward    │  ┌─────────────┐   ClusterIP :80         │
  localhost:8080 ─────────┼─▶│ API Service │                         │
                          │  └──────┬──────┘                         │
                          │         │                                 │
                          │  ┌──────▼──────┐   ┌──────────────────┐  │
                          │  │  API Pods   │──▶│ Lakehouse PVC    │  │
                          │  │   (x2)      │   │  (ReadOnly)      │  │
                          │  └──────┬──────┘   └────────┬─────────┘  │
                          │         │                    │            │
                          │  ┌──────▼──────┐   ┌────────┴─────────┐  │
                          │  │  PG Service │   │ Lakehouse Job    │  │
                          │  │  ClusterIP  │   │  (run-once)      │  │
                          │  └──────┬──────┘   └────────┬─────────┘  │
                          │         │                    │            │
                          │  ┌──────▼──────┐            │            │
                          │  │  PG Pod     │◀───────────┘            │
                          │  └──────┬──────┘ (read warehouse)        │
                          │         │                                 │
                          │  ┌──────▼──────┐   ┌──────────────────┐  │
                          │  │  PG PVC     │   │ Ingestor Job     │  │
                          │  │   (5 Gi)    │   │  (run-once)      │  │
                          │  └─────────────┘   └────────┬─────────┘  │
                          │                             │             │
                          │                   (writes fact data)      │
                          └─────────────────────────────────────────┘
```

---

## Prerequisites

- `kubectl` configured against a cluster (minikube, kind, or cloud)
- Helm 3.x installed (`helm version`)
- Docker images built and pushed (or loaded locally):
  - `arash/oil-ingestor:latest`
  - `arash/oil-lakehouse:latest`
  - `arash/oil-api:latest`
- For local clusters (minikube/kind), load images with:
  ```bash
  # minikube
  minikube image load arash/oil-api:latest

  # kind
  kind load docker-image arash/oil-api:latest
  ```

---

## Quick Start — Raw Manifests

Apply resources in dependency order:

```bash
# 1. Namespace (must exist before everything else)
kubectl apply -f k8s/manifests/namespace.yaml

# 2. Configuration and secrets
kubectl apply -f k8s/manifests/configmap.yaml
kubectl apply -f k8s/manifests/secret.yaml

# 3. Persistent storage
kubectl apply -f k8s/manifests/postgres-pvc.yaml
kubectl apply -f k8s/manifests/lakehouse-pvc.yaml

# 4. PostgreSQL — deploy and wait for readiness
kubectl apply -f k8s/manifests/postgres-deployment.yaml
kubectl apply -f k8s/manifests/postgres-service.yaml
kubectl rollout status deployment/oil-pipeline-postgres -n oil-pipeline

# 5. Apply database schema (first run only)
#    Option A: exec into the pod and run psql
kubectl exec -n oil-pipeline deployment/oil-pipeline-postgres -- \
  psql -U arash -d oil_warehouse -c "SELECT 1"
#    Then apply your init scripts from database/init/ in order (00 through 09).

# 6. Run the ingestor (fetches Yahoo Finance data -> PostgreSQL)
kubectl apply -f k8s/manifests/ingestor-job.yaml
kubectl wait --for=condition=complete job/oil-pipeline-ingestor \
  -n oil-pipeline --timeout=600s
kubectl logs job/oil-pipeline-ingestor -n oil-pipeline

# 7. Run the lakehouse (PostgreSQL -> Parquet medallion layers)
kubectl apply -f k8s/manifests/lakehouse-job.yaml
kubectl wait --for=condition=complete job/oil-pipeline-lakehouse \
  -n oil-pipeline --timeout=300s

# 8. Deploy the API
kubectl apply -f k8s/manifests/api-deployment.yaml
kubectl apply -f k8s/manifests/api-service.yaml
kubectl rollout status deployment/oil-pipeline-api -n oil-pipeline

# 9. Check everything is running
kubectl get all -n oil-pipeline

# 10. Access the API
kubectl port-forward svc/oil-pipeline-api -n oil-pipeline 8080:80
# Then open: http://localhost:8080/docs
```

---

## Quick Start — Helm

```bash
# Install (first time)
helm install oil-pipeline k8s/helm/oil-pipeline \
  --namespace oil-pipeline \
  --create-namespace

# Check status
helm status oil-pipeline -n oil-pipeline
kubectl get all -n oil-pipeline

# Access the API
kubectl port-forward svc/oil-pipeline-oil-pipeline-api \
  -n oil-pipeline 8080:80
# Open: http://localhost:8080/docs

# Upgrade (after changing values or templates)
helm upgrade oil-pipeline k8s/helm/oil-pipeline \
  --namespace oil-pipeline

# Override values at install time
helm install oil-pipeline k8s/helm/oil-pipeline \
  --namespace oil-pipeline \
  --create-namespace \
  --set api.replicaCount=3 \
  --set postgres.credentials.password=my-secure-password \
  --set ingestor.mode=backfill

# Run the built-in connectivity test
helm test oil-pipeline -n oil-pipeline

# Uninstall (removes all resources but NOT the PVCs by default)
helm uninstall oil-pipeline -n oil-pipeline
```

---

## Configuration Reference

| Key | Default | Description |
|-----|---------|-------------|
| `namespace` | `oil-pipeline` | Kubernetes namespace for all resources |
| `global.imagePullPolicy` | `IfNotPresent` | Image pull policy for all containers |
| `postgres.image.tag` | `16-alpine` | PostgreSQL image tag |
| `postgres.storage.size` | `5Gi` | PVC size for PostgreSQL data |
| `postgres.resources.requests.cpu` | `250m` | CPU request for PostgreSQL |
| `postgres.resources.limits.memory` | `512Mi` | Memory limit for PostgreSQL |
| `postgres.credentials.database` | `oil_warehouse` | PostgreSQL database name |
| `postgres.credentials.username` | `arash` | PostgreSQL username |
| `postgres.credentials.password` | `warehouse_dev_2026` | PostgreSQL password (override in prod!) |
| `ingestor.enabled` | `true` | Whether to deploy the ingestor Job |
| `ingestor.mode` | `incremental` | Ingestor command (`backfill` or `incremental`) |
| `ingestor.backoffLimit` | `3` | Max Job retries before failure |
| `lakehouse.enabled` | `true` | Whether to deploy the lakehouse Job |
| `lakehouse.storage.size` | `2Gi` | PVC size for Parquet files |
| `api.replicaCount` | `2` | Number of API pod replicas |
| `api.service.type` | `ClusterIP` | Kubernetes service type for the API |
| `api.autoscaling.enabled` | `false` | Enable HPA for API pods |
| `config.logLevel` | `INFO` | Log level for all services |
| `config.dataDir` | `/app/data` | Lakehouse Parquet root inside the pod |
| `config.lakehouseBasePath` | `/opt/lakehouse` | API's lakehouse base path |

---

## Validating Without a Cluster

```bash
# Render Helm templates without installing
helm template oil-pipeline k8s/helm/oil-pipeline \
  --namespace oil-pipeline

# Lint the Helm chart for errors
helm lint k8s/helm/oil-pipeline

# Dry-run raw manifests against a real cluster (no changes applied)
kubectl apply -f k8s/manifests/ -n oil-pipeline --dry-run=client

# Render and pipe directly to dry-run
helm template oil-pipeline k8s/helm/oil-pipeline \
  --namespace oil-pipeline | kubectl apply --dry-run=client -f -
```

---

## Key Differences from Docker Compose

| Concept | Docker Compose | Kubernetes |
|---------|---------------|------------|
| Service discovery | Service name as hostname | ClusterIP Service + DNS |
| Run-once jobs | No native concept (exits naturally) | `kind: Job` with `restartPolicy: Never` |
| Startup ordering | `depends_on: condition: service_healthy` | Init containers with `pg_isready` loop |
| Persistent storage | Named volumes | PersistentVolumeClaim |
| Shared volumes | Direct volume mount | ReadWriteOnce PVC (one writer at a time) |
| Secrets | Plain env vars in compose file | `kind: Secret` (base64, or external) |
| Config | Env vars in compose file | `kind: ConfigMap` |
| Scaling | `--scale api=3` | `replicas: N` in Deployment spec |
| Health checks | `healthcheck:` block | `livenessProbe` + `readinessProbe` |
| Zero-downtime deploys | Not built-in | `RollingUpdate` strategy |

---

## Production Considerations

The following changes would be made before running this in production:

1. **PostgreSQL as a StatefulSet** — or better, use a managed service (AWS RDS, Cloud SQL, Azure Database for PostgreSQL). A Deployment with a single RWO PVC works but loses the automatic pod identity and ordered rollout that StatefulSet provides.

2. **Secrets management** — replace the base64 `Secret` with [Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets), [External Secrets Operator](https://external-secrets.io/), or HashiCorp Vault. Never commit plaintext credentials.

3. **Ingress + TLS** — add an `Ingress` resource (nginx-ingress or Traefik) and a `Certificate` (cert-manager + Let's Encrypt) instead of exposing via `LoadBalancer` or `port-forward`.

4. **Horizontal Pod Autoscaler** — set `api.autoscaling.enabled: true` and tune `targetCPUUtilization` based on load testing. The API is stateless and scales horizontally.

5. **Database schema migrations** — replace the manual init-script approach with a migration tool (Alembic for Python, Flyway, or Liquibase) run as an init container or pre-deploy Job, so schema changes are tracked and reversible.

6. **Container registry** — push images to a private registry (ECR, GCR, Artifact Registry) and update `image.repository` accordingly. Add `imagePullSecrets` to pod specs.

7. **Resource tuning** — the CPU/memory requests and limits are conservative estimates. Profile actual usage under load and right-size accordingly to avoid OOMKilled pods or throttling.

8. **Network Policies** — restrict traffic between pods using `NetworkPolicy` resources (e.g., only the API pod should reach PostgreSQL; the ingestor and lakehouse should not be reachable inbound).

9. **PodDisruptionBudget** — add a PDB for the API deployment to ensure at least one replica stays up during node maintenance.

---

## Cleanup

```bash
# Helm: remove the release (PVCs are NOT deleted by default)
helm uninstall oil-pipeline -n oil-pipeline

# Also delete PVCs if you want a full wipe
kubectl delete pvc postgres-data lakehouse-data -n oil-pipeline

# Delete the namespace (removes everything inside it)
kubectl delete namespace oil-pipeline

# Raw manifests: delete all resources
kubectl delete -f k8s/manifests/ --ignore-not-found
kubectl delete namespace oil-pipeline
```
