#!/bin/bash
# Provisions the agent node: installs the NFS client (needed by kubelet to
# mount the database PVs) and joins K3s using the token the master dropped
# into the shared /vagrant folder.
set -euo pipefail

: "${MASTER_IP:?}" "${AGENT_IP:?}"

export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq nfs-common >/dev/null

until [ -f /vagrant/.kube/node-token ]; do
    sleep 2
done
TOKEN="$(cat /vagrant/.kube/node-token)"

# Same reason as on the master: keep flannel off the shared NAT interface.
IFACE="$(ip -o -4 addr show | awk -v ip="${AGENT_IP}" '$4 ~ "^"ip"/" {print $2}')"

curl -sfL https://get.k3s.io | \
    K3S_URL="https://${MASTER_IP}:6443" \
    K3S_TOKEN="${TOKEN}" \
    INSTALL_K3S_EXEC="agent --node-ip=${AGENT_IP} --flannel-iface=${IFACE}" \
    sh -
