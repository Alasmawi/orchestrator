#!/bin/bash
# Installs the K3s agent and joins it to the master using the token the
# master's provisioning script dropped into the shared /vagrant folder.
set -euo pipefail

until [ -f /vagrant/.kube/node-token ]; do
    sleep 2
done

TOKEN="$(cat /vagrant/.kube/node-token)"

curl -sfL https://get.k3s.io | \
    K3S_URL="https://${MASTER_IP}:6443" \
    K3S_TOKEN="${TOKEN}" \
    sh -
