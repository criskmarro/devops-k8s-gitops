# DevOps K8s GitOps

Cloud-native REST API deployed on **AWS EKS** using **Terraform** for infrastructure, **Kubernetes + Kustomize** for workloads, and **Argo CD** for GitOps-based continuous delivery.

## Architecture

```
                         ┌─────────────────────────────────────────┐
                         │              AWS (us-east-1)             │
                         │                                          │
  GitHub ──CI/CD──►  ECR │   ALB ──► EKS Cluster                  │
    │                    │              ├── Namespace: app          │
    │  (GitOps)          │              │     ├── Deployment (API)  │
    └──────────────► Argo CD            │     └── Service           │
                         │              └── Namespace: argocd       │
                         │                                          │
                         │   EKS ──private──► RDS PostgreSQL        │
                         │                                          │
                         │   VPC: public subnets + private subnets  │
                         └─────────────────────────────────────────┘
```

## Stack

| Layer | Technology |
|-------|-----------|
| **API** | Python 3.12 · FastAPI · SQLAlchemy |
| **Database** | PostgreSQL 16 (AWS RDS) |
| **Container** | Docker · AWS ECR |
| **Orchestration** | Kubernetes 1.30 · AWS EKS |
| **Config management** | Kustomize |
| **GitOps** | Argo CD |
| **Infrastructure** | Terraform 1.8 · AWS (VPC · EKS · RDS · ECR) |
| **CI/CD** | GitHub Actions |

## Project Structure

```
devops-k8s-gitops/
├── app/                    # FastAPI application
│   ├── main.py             # Routes and app entrypoint
│   ├── models.py           # SQLAlchemy models
│   ├── database.py         # DB session and connection
│   ├── Dockerfile          # Production-ready image
│   └── requirements.txt
├── terraform/              # Infrastructure as Code
│   ├── main.tf             # Root module — calls submodules
│   ├── variables.tf
│   ├── outputs.tf
│   ├── versions.tf         # Provider and Terraform version locks
│   └── modules/
│       ├── vpc/            # VPC, subnets, NAT Gateway, route tables
│       ├── eks/            # EKS cluster, node group, IAM roles
│       └── rds/            # RDS PostgreSQL, subnet group, security group
├── k8s/
│   ├── base/               # Base Kubernetes manifests
│   │   ├── deployment.yaml
│   │   ├── service.yaml    # ClusterIP + ALB Ingress
│   │   └── configmap.yaml
│   └── overlays/
│       └── dev/            # Dev environment patches (1 replica, lower limits)
├── gitops/
│   ├── apps/app.yaml       # Argo CD Application definition
│   └── projects/project.yaml
├── .github/workflows/
│   ├── ci.yml              # Test → lint → build → push to ECR
│   └── cd.yml              # Update image tag → Argo CD auto-sync
└── docker-compose.yml      # Local development environment
```

## Local Development

```bash
# Clone the repo
git clone https://github.com/criskmarro/devops-k8s-gitops.git
cd devops-k8s-gitops

# Copy and configure environment variables
cp .env.example .env

# Start the full stack locally
docker compose up --build

# API available at http://localhost:8000
# Docs at http://localhost:8000/docs
```

## Infrastructure Deployment

### Prerequisites
- AWS CLI configured (`aws configure`)
- Terraform >= 1.8
- kubectl

### 1. Create S3 bucket for Terraform state
```bash
aws s3 mb s3://criskmarro-tfstate --region us-east-1
```

### 2. Deploy infrastructure
```bash
cd terraform
terraform init
terraform plan -var="db_password=yourpassword"
terraform apply -var="db_password=yourpassword"
```

### 3. Configure kubectl for EKS
```bash
aws eks update-kubeconfig --region us-east-1 --name devops-k8s-gitops-dev
kubectl get nodes
```

### 4. Install Argo CD
```bash
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
    └── Build & push image to ECR
            │
            ▼
GitHub Actions CD
    └── Update image tag in k8s/base/deployment.yaml
            │
            ▼
Argo CD detects repo change
    └── Auto-sync → kubectl apply → Rolling update in EKS
```

## Key Design Decisions

- **GitOps over push-based CD:** the cluster state is always reconciled from Git, not from imperative kubectl commands. Any drift is automatically corrected by Argo CD.
- **Kustomize overlays** allow environment-specific config (replicas, resource limits) without duplicating base manifests.
- **Private subnets for EKS nodes and RDS** — only the ALB lives in public subnets.
- **Terraform modules** are separated by concern (vpc / eks / rds) to allow independent changes and reuse.

## Author

**Cristian Marro** · [github.com/criskmarro](https://github.com/criskmarro) · [linkedin.com/in/criskmarro](#)
