#!/bin/bash
# Provisions the master node:
#   1. an NFS server exporting the directories that back the database PVs,
#      so a database pod can be rescheduled on either node and keep its data;
#   2. the K3s server (control plane), pinned to the private network;
#   3. publishes kubeconfig + join token into the shared /vagrant folder for
#      the host (kubectl) and the agent node.
set -euo pipefail

: "${MASTER_IP:?}" "${NFS_ROOT:?}"

# --- NFS -------------------------------------------------------------------
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq nfs-kernel-server >/dev/null

mkdir -p "${NFS_ROOT}/inventory-db" "${NFS_ROOT}/billing-db"
mkdir -p /etc/exports.d
# no_root_squash: the postgres entrypoint starts as root to chown its data dir.
echo "${NFS_ROOT} 192.168.56.0/24(rw,sync,no_subtree_check,no_root_squash)" > /etc/exports.d/k3s.exports
exportfs -ra
systemctl enable --now nfs-server >/dev/null

# --- K3s server ------------------------------------------------------------
# VirtualBox gives every VM the same NAT address (10.0.2.15) on its first NIC;
# flannel must use the host-only NIC or cross-node pod traffic breaks.
IFACE="$(ip -o -4 addr show | awk -v ip="${MASTER_IP}" '$4 ~ "^"ip"/" {print $2}')"

curl -sfL https://get.k3s.io | \
    INSTALL_K3S_EXEC="server --node-ip=${MASTER_IP} --advertise-address=${MASTER_IP} --tls-san=${MASTER_IP} --flannel-iface=${IFACE} --write-kubeconfig-mode=644" \
    sh -

until k3s kubectl get nodes >/dev/null 2>&1; do
    sleep 2
done

mkdir -p /vagrant/.kube
sed "s/127.0.0.1/${MASTER_IP}/" /etc/rancher/k3s/k3s.yaml > /vagrant/.kube/config
cp /var/lib/rancher/k3s/server/node-token /vagrant/.kube/node-token
chmod 600 /vagrant/.kube/config /vagrant/.kube/node-token
