#!/bin/bash
# create | start | stop | destroy the K3s cluster and (on create) the
# crud-master workloads on it.
set -euo pipefail
cd "$(dirname "$0")"

usage() {
    echo "Usage: $0 {create|start|stop|destroy}"
    exit 1
}

[ $# -eq 1 ] || usage

if [ -f .env ]; then
    set -a
    # shellcheck disable=SC1091
    source .env
    set +a
fi

deploy_workloads() {
    export KUBECONFIG="$(pwd)/.kube/config"
    kubectl wait --for=condition=Ready node --all --timeout=180s

    kubectl apply -f Manifests/00-namespace.yaml
    ./Scripts/apply-secrets.sh

    kubectl apply -f Manifests/inventory-db.yaml
    kubectl apply -f Manifests/billing-db.yaml
    kubectl apply -f Manifests/rabbit-queue.yaml

    : "${DOCKERHUB_USERNAME:?DOCKERHUB_USERNAME must be set in .env (images must be pushed first, see README)}"
    for manifest in inventory-app billing-app api-gateway-app; do
        sed "s|__DOCKERHUB_USERNAME__|${DOCKERHUB_USERNAME}|g" "Manifests/${manifest}.yaml" | kubectl apply -f -
    done

    kubectl apply -f Manifests/inventory-app-hpa.yaml
    kubectl apply -f Manifests/api-gateway-app-hpa.yaml
}

case "$1" in
    create)
        vagrant up
        deploy_workloads
        echo "cluster created"
        ;;
    start)
        vagrant up
        echo "cluster started"
        ;;
    stop)
        vagrant halt
        echo "cluster stopped"
        ;;
    destroy)
        vagrant destroy -f
        rm -rf .kube
        echo "cluster destroyed"
        ;;
    *)
        usage
        ;;
esac
