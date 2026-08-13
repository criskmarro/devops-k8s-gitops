# DevOps K8s GitOps

Cloud-native REST API fully containerized and deployed on a **Kubernetes cluster** using **GitOps principles via Argo CD**. Infrastructure defined as code with **Terraform** targeting AWS EKS. CI/CD automated with **GitHub Actions**.

> **Status:** Running locally on k3d. AWS EKS deployment ready — Terraform modules written and validated.

## Architecture

```
                         ┌──────────────────────────────────────────┐
                         │           Kubernetes Cluster              │
                         │                                           │
  GitHub ──CI/CD──►  Registry   Ingress ──► Namespace: app          │
    │                    │                    ├── Deployment (API)   │
    │  (GitOps)          │                    ├── Deployment (DB)    │
    └──────────────► Argo CD                  └── Services           │
                         │              Namespace: argocd            │
                         └──────────────────────────────────────────┘

  AWS Target Architecture (Terraform ready):
  ┌─────────────────────────────────────────┐
  │              AWS (us-east-1)            │
  │  ALB ──► EKS (private subnets)          │
  │  EKS ──► RDS PostgreSQL (private)       │
  │  VPC: public + private subnets + NAT    │
  └─────────────────────────────────────────┘
```

## Stack

| Layer | Technology |
|-------|-----------|
| **API** | Python 3.12 · FastAPI · SQLAlchemy |
| **Database** | PostgreSQL 16 |
| **Container** | Docker |
| **Orchestration** | Kubernetes · Kustomize |
| **GitOps** | Argo CD |
| **Infrastructure as Code** | Terraform 1.8 · AWS (VPC · EKS · RDS · ECR) |
| **CI/CD** | GitHub Actions |
| **Local cluster** | k3d |

## Project Structure

```
devops-k8s-gitops/
├── app/                        # FastAPI application
│   ├── main.py                 # Endpoints and app entrypoint
│   ├── models.py               # SQLAlchemy models
│   ├── database.py             # DB session and engine
│   ├── Dockerfile              # Production-ready image (non-root user)
│   └── requirements.txt
├── terraform/                  # Infrastructure as Code — AWS target
│   ├── main.tf                 # Root module
│   ├── variables.tf
│   ├── outputs.tf
│   ├── versions.tf             # Provider and version locks
│   └── modules/
│       ├── vpc/                # VPC, subnets, NAT Gateway, route tables
│       ├── eks/                # EKS cluster, node group, IAM roles
│       └── rds/                # RDS PostgreSQL, subnet group, security group
├── k8s/
│   ├── base/                   # Base Kubernetes manifests
│   │   ├── deployment.yaml     # API deployment with probes and resource limits
│   │   ├── postgres.yaml       # PostgreSQL deployment + service
│   │   ├── service.yaml        # ClusterIP service + Ingress
│   │   └── configmap.yaml
│   ├── overlays/
│   │   └── dev/                # Dev patches (1 replica, lower resource limits)
│   └── scripts/
│       └── setup-local.sh      # One-command local secret setup
├── gitops/
│   ├── apps/app.yaml           # Argo CD Application — auto-sync enabled
│   └── projects/project.yaml  # Argo CD AppProject
├── .github/workflows/
│   ├── ci.yml                  # Test → lint → build → push image
│   └── cd.yml                  # Update image tag → Argo CD detects → deploy
└── docker-compose.yml          # Alternative local dev setup
```

## Local Development

### Option A — Full Kubernetes stack with k3d (recommended)

```bash
# 1. Clone the repo
git clone https://github.com/criskmarro/devops-k8s-gitops.git
cd devops-k8s-gitops

# 2. Create k3d cluster with registry
k3d registry create registry.localhost --port 5000
k3d cluster create devops-gitops \
  --port "8080:80@loadbalancer" \
  --port "8443:443@loadbalancer" \
  --agents 2 \
  --registry-use k3d-registry.localhost:5000

# 3. Build and push image to local registry
docker build -t k3d-registry.localhost:5000/devops-k8s-gitops:latest ./app
docker push k3d-registry.localhost:5000/devops-k8s-gitops:latest

# 4. Install Argo CD
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# 5. Create secrets (never committed to Git)
bash k8s/scripts/setup-local.sh

# 6. Apply GitOps configuration
kubectl apply -f gitops/projects/project.yaml
kubectl apply -f gitops/apps/app.yaml

# 7. Access the API
kubectl port-forward svc/api -n app 8000:80
# → http://localhost:8000/health
# → http://localhost:8000/docs
```

### Option B — Docker Compose (quick start)

```bash
cp .env.example .env
docker compose up --build
# → http://localhost:8000/docs
```

## AWS Deployment (Terraform)

### Prerequisites
- AWS CLI configured (`aws configure`)
- Terraform >= 1.8
- kubectl

```bash
# 1. Create S3 bucket for remote state
aws s3 mb s3://criskmarro-tfstate --region us-east-1
aws s3api put-bucket-versioning \
  --bucket criskmarro-tfstate \
  --versioning-configuration Status=Enabled

# 2. Deploy infrastructure
cd terraform
terraform init
terraform plan -var-file="terraform.tfvars"
terraform apply -var-file="terraform.tfvars"

# 3. Configure kubectl
aws eks update-kubeconfig --region us-east-1 --name devops-k8s-gitops-dev

# 4. Install Argo CD and apply GitOps config
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl apply -f gitops/projects/project.yaml
kubectl apply -f gitops/apps/app.yaml
```

## CI/CD Flow

```
git push main
    │
    ▼
GitHub Actions CI
    ├── Run tests (pytest)
    ├── Lint (ruff)
    └── Build & push Docker image to registry
            │
            ▼
GitHub Actions CD
    └── Update image tag in k8s/base/deployment.yaml
            │
            ▼
Argo CD detects repo change (polling / webhook)
    └── Auto-sync → kubectl apply → Rolling update
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/items` | List all items |
| POST | `/items` | Create item |
| GET | `/items/{id}` | Get item by ID |

Interactive docs available at `/docs` (Swagger UI) and `/redoc`.

## Key Design Decisions

- **GitOps over push-based CD:** cluster state is always reconciled from Git. Any manual drift is automatically corrected by Argo CD.
- **Kustomize base/overlays pattern:** environment-specific config without duplicating manifests.
- **Secrets never in Git:** managed via `kubectl create secret` locally; AWS Secrets Manager in production.
- **Terraform modules by concern:** vpc / eks / rds are independent, reusable, and separately testable.
- **Non-root container user:** Dockerfile creates a dedicated system user for security.
- **Health probes on all deployments:** liveness and readiness probes prevent traffic to unhealthy pods.

## Author

**Cristian Marro** · [github.com/criskmarro](https://github.com/criskmarro) · [linkedin.com/in/criskmarro](#)