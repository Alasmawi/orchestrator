#!/bin/bash
# Installs the K3s server (master node) and publishes its kubeconfig +
# join token into the Vagrant shared folder so the host and the agent
# node can both pick them up.
set -euo pipefail

# Every Vagrant box has the same 10.0.2.15 on its NAT adapter, so both
# the node IP and flannel's interface have to be pinned to the private
# network explicitly -- otherwise the two nodes claim the same address
# and pod-to-pod traffic between them never lands.
PRIVATE_IFACE="$(ip -o -4 addr show | awk -v ip="${MASTER_IP}" '$4 ~ "^"ip"/" {print $2; exit}')"
: "${PRIVATE_IFACE:?No interface holds ${MASTER_IP} -- is the private_network up?}"

curl -sfL https://get.k3s.io | \
    INSTALL_K3S_EXEC="server --node-ip=${MASTER_IP} --bind-address=${MASTER_IP} --tls-san=${MASTER_IP} --flannel-iface=${PRIVATE_IFACE} --node-external-ip=${MASTER_IP}" \
    sh -

until kubectl --kubeconfig /etc/rancher/k3s/k3s.yaml get nodes >/dev/null 2>&1; do
    sleep 2
done

mkdir -p /vagrant/.kube
cp /etc/rancher/k3s/k3s.yaml /vagrant/.kube/config
sed -i "s/127.0.0.1/${MASTER_IP}/" /vagrant/.kube/config
cp /var/lib/rancher/k3s/server/node-token /vagrant/.kube/node-token
chmod 644 /vagrant/.kube/config /vagrant/.kube/node-token
