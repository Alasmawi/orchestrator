#!/bin/bash
# Creates, starts, stops and destroys the K3s cluster (2 Vagrant VMs) and
# deploys the crud-master microservices onto it.
#
#   ./orchestrator.sh create   build the VMs, install K3s, deploy everything
#   ./orchestrator.sh start    boot a stopped cluster
#   ./orchestrator.sh stop     shut the VMs down (data is kept)
#   ./orchestrator.sh deploy   (re)apply secrets + manifests on a running cluster
#   ./orchestrator.sh status   show nodes, workloads, HPAs and volumes
#   ./orchestrator.sh destroy  delete the VMs and the local kubeconfig
set -euo pipefail
cd "$(dirname "$0")"

NAMESPACE="crud-master"
export KUBECONFIG="$(pwd)/.kube/config"

usage() {
    sed -n '5,10s/^#  //p' "$0"
    exit 1
}

log() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
die() { printf '\033[1;31merror:\033[0m %s\n' "$*" >&2; exit 1; }

require() {
    for cmd in "$@"; do
        command -v "$cmd" >/dev/null 2>&1 || die "'$cmd' is required but not installed (see README > Prerequisites)"
    done
}

load_env() {
    [ -f .env ] || die ".env not found: run 'cp .env.example .env' and fill it in"
    set -a
    # shellcheck disable=SC1091
    source .env
    set +a
    local missing=()
    for var in INVENTORY_DB_NAME INVENTORY_DB_USER INVENTORY_DB_PASSWORD \
               BILLING_DB_NAME BILLING_DB_USER BILLING_DB_PASSWORD \
               RABBITMQ_USER RABBITMQ_PASSWORD DOCKERHUB_USERNAME; do
        [ -n "${!var:-}" ] || missing+=("$var")
    done
    [ ${#missing[@]} -eq 0 ] || die "missing values in .env: ${missing[*]}"
    IMAGE_TAG="${IMAGE_TAG:-latest}"
}

wait_for_nodes() {
    log "waiting for both nodes to be Ready"
    local i
    for i in $(seq 1 90); do
        [ "$(kubectl get nodes --no-headers 2>/dev/null | wc -l | tr -d ' ')" -ge 2 ] && break
        sleep 2
    done
    kubectl wait --for=condition=Ready node --all --timeout=180s
}

# App manifests reference __DOCKERHUB_USERNAME__/<app>:__IMAGE_TAG__ so no
# account name is hard-coded; everything else is applied as-is.
render() {
    sed -e "s|__DOCKERHUB_USERNAME__|${DOCKERHUB_USERNAME}|g" \
        -e "s|__IMAGE_TAG__|${IMAGE_TAG}|g" "$1"
}

deploy_workloads() {
    wait_for_nodes

    log "namespace, storage and secrets"
    kubectl apply -f Manifests/namespace.yaml
    kubectl apply -f Manifests/storage.yaml
    ./Scripts/apply-secrets.sh

    log "databases and message queue"
    kubectl apply -f Manifests/inventory-db.yaml
    kubectl apply -f Manifests/billing-db.yaml
    kubectl apply -f Manifests/rabbit-queue.yaml

    log "applications"
    for manifest in inventory-app billing-app api-gateway-app; do
        render "Manifests/${manifest}.yaml" | kubectl apply -f -
    done

    log "autoscalers"
    kubectl apply -f Manifests/inventory-app-hpa.yaml
    kubectl apply -f Manifests/api-gateway-app-hpa.yaml

    log "waiting for every workload to become ready"
    kubectl -n "$NAMESPACE" rollout status statefulset/inventory-db --timeout=300s
    kubectl -n "$NAMESPACE" rollout status statefulset/billing-db --timeout=300s
    kubectl -n "$NAMESPACE" rollout status deployment/rabbit-queue --timeout=300s
    kubectl -n "$NAMESPACE" rollout status deployment/inventory-app --timeout=300s
    kubectl -n "$NAMESPACE" rollout status statefulset/billing-app --timeout=300s
    kubectl -n "$NAMESPACE" rollout status deployment/api-gateway-app --timeout=300s
}

show_status() {
    kubectl get nodes -o wide
    echo
    kubectl -n "$NAMESPACE" get statefulsets,deployments,hpa,pods,svc,ingress -o wide
    echo
    kubectl -n "$NAMESPACE" get pvc
}

[ $# -eq 1 ] || usage

case "$1" in
    create)
        require vagrant VBoxManage kubectl
        load_env
        vagrant up
        deploy_workloads
        echo "cluster created"
        ;;
    start)
        require vagrant
        vagrant up
        echo "cluster started"
        ;;
    stop)
        require vagrant
        vagrant halt
        echo "cluster stopped"
        ;;
    deploy)
        require kubectl
        load_env
        deploy_workloads
        echo "workloads deployed"
        ;;
    status)
        require kubectl
        show_status
        ;;
    destroy)
        require vagrant
        vagrant destroy -f
        rm -rf .kube
        echo "cluster destroyed"
        ;;
    *)
        usage
        ;;
esac
