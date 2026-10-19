# -*- mode: ruby -*-
# vi: set ft=ruby :
#
# Two-node K3s cluster on VirtualBox:
#   master  192.168.56.21  K3s server (control plane) + NFS server for PVs
#   agent   192.168.56.22  K3s agent (worker)
#
# bento/ubuntu-22.04 ships both amd64 and arm64 VirtualBox builds, so the
# same Vagrantfile works on Intel and Apple Silicon hosts.

MASTER_IP = "192.168.56.21"
AGENT_IP  = "192.168.56.22"
NFS_ROOT  = "/srv/nfs/k3s"

Vagrant.configure("2") do |config|
  config.vm.box = "bento/ubuntu-22.04"
  config.vm.box_check_update = false

  config.vm.provider "virtualbox" do |vb|
    vb.memory = 2048
    vb.cpus = 2
  end

  config.vm.define "master", primary: true do |master|
    master.vm.hostname = "master"
    master.vm.network "private_network", ip: MASTER_IP
    master.vm.provision "shell", path: "Scripts/k3s-master.sh",
      env: { "MASTER_IP" => MASTER_IP, "NFS_ROOT" => NFS_ROOT }
  end

  config.vm.define "agent" do |agent|
    agent.vm.hostname = "agent"
    agent.vm.network "private_network", ip: AGENT_IP
    agent.vm.provision "shell", path: "Scripts/k3s-agent.sh",
      env: { "MASTER_IP" => MASTER_IP, "AGENT_IP" => AGENT_IP }
  end
end
