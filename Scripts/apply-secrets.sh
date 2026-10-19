#!/bin/bash
# Creates/updates the three K8s Secrets from environment variables (sourced
# from .env by orchestrator.sh). The Secret objects are rendered in memory
# and piped straight to the API server, so no credential is ever written to a
# YAML file in the repo. Re-running it is safe (apply = create or update).
set -euo pipefail

: "${KUBECONFIG:?KUBECONFIG must be set}"
NAMESPACE="crud-master"

apply_secret() {
    local name="$1"; shift
    kubectl create secret generic "$name" --namespace "$NAMESPACE" "$@" \
        --dry-run=client -o yaml | kubectl apply -f -
}

apply_secret inventory-db-secret \
    --from-literal=POSTGRES_USER="${INVENTORY_DB_USER:?}" \
    --from-literal=POSTGRES_PASSWORD="${INVENTORY_DB_PASSWORD:?}" \
    --from-literal=POSTGRES_DB="${INVENTORY_DB_NAME:?}"

apply_secret billing-db-secret \
    --from-literal=POSTGRES_USER="${BILLING_DB_USER:?}" \
    --from-literal=POSTGRES_PASSWORD="${BILLING_DB_PASSWORD:?}" \
    --from-literal=POSTGRES_DB="${BILLING_DB_NAME:?}"

apply_secret rabbitmq-secret \
    --from-literal=RABBITMQ_USER="${RABBITMQ_USER:?}" \
    --from-literal=RABBITMQ_PASSWORD="${RABBITMQ_PASSWORD:?}"
