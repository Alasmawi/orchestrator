#!/bin/bash
# Creates/updates every K8s Secret from environment variables (sourced
# from .env by orchestrator.sh) — no credentials ever live in a
# committed YAML file.
set -euo pipefail

: "${KUBECONFIG:?KUBECONFIG must be set}"
NAMESPACE="crud-master"

kubectl --kubeconfig "$KUBECONFIG" create secret generic inventory-db-secret \
    --namespace "$NAMESPACE" \
    --from-literal=POSTGRES_USER="${INVENTORY_DB_USER}" \
    --from-literal=POSTGRES_PASSWORD="${INVENTORY_DB_PASSWORD}" \
    --from-literal=POSTGRES_DB="${INVENTORY_DB_NAME}" \
    --dry-run=client -o yaml | kubectl --kubeconfig "$KUBECONFIG" apply -f -

kubectl --kubeconfig "$KUBECONFIG" create secret generic billing-db-secret \
    --namespace "$NAMESPACE" \
    --from-literal=POSTGRES_USER="${BILLING_DB_USER}" \
    --from-literal=POSTGRES_PASSWORD="${BILLING_DB_PASSWORD}" \
    --from-literal=POSTGRES_DB="${BILLING_DB_NAME}" \
    --dry-run=client -o yaml | kubectl --kubeconfig "$KUBECONFIG" apply -f -

kubectl --kubeconfig "$KUBECONFIG" create secret generic rabbitmq-secret \
    --namespace "$NAMESPACE" \
    --from-literal=RABBITMQ_USER="${RABBITMQ_USER}" \
    --from-literal=RABBITMQ_PASSWORD="${RABBITMQ_PASSWORD}" \
    --dry-run=client -o yaml | kubectl --kubeconfig "$KUBECONFIG" apply -f -
