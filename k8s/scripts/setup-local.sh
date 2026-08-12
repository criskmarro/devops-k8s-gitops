#!/bin/bash
# Setup para entorno local con k3d
# Crea recursos que no deben estar en Git (secrets)

set -e

echo "==> Creando namespace..."
kubectl create namespace app --dry-run=client -o yaml | kubectl apply -f -

echo "==> Creando secrets..."
kubectl create secret generic app-secrets -n app \
  --from-literal=database-url="postgresql://postgres:postgres@postgres:5432/appdb" \
  --from-literal=db-password="postgres" \
  --dry-run=client -o yaml | kubectl apply -f -

echo "==> Listo. Argo CD sincronizará el resto automáticamente."
