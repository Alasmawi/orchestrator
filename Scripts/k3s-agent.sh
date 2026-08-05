#!/bin/bash
# Installs the K3s agent and joins it to the master using the token the
# master's provisioning script dropped into the shared /vagrant folder.
set -euo pipefail

until [ -f /vagrant/.kube/node-token ]; do
    sleep 2
done

TOKEN="$(cat /vagrant/.kube/node-token)"

# Same reason as on the master: without --node-ip the agent registers
# with its NAT address (10.0.2.15, identical on every Vagrant box) and
# the cluster ends up with two nodes claiming one IP.
PRIVATE_IFACE="$(ip -o -4 addr show | awk -v ip="${AGENT_IP}" '$4 ~ "^"ip"/" {print $2; exit}')"
: "${PRIVATE_IFACE:?No interface holds ${AGENT_IP} -- is the private_network up?}"

curl -sfL https://get.k3s.io | \
    K3S_URL="https://${MASTER_IP}:6443" \
    K3S_TOKEN="${TOKEN}" \
    INSTALL_K3S_EXEC="agent --node-ip=${AGENT_IP} --flannel-iface=${PRIVATE_IFACE}" \
    sh -
