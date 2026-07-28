# -*- mode: ruby -*-
# vi: set ft=ruby :

MASTER_IP = "192.168.56.21"
AGENT_IP  = "192.168.56.22"

Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/jammy64"

  config.vm.provider "virtualbox" do |vb|
    vb.memory = 2048
    vb.cpus = 2
  end

  config.vm.define "master" do |master|
    master.vm.hostname = "master"
    master.vm.network "private_network", ip: MASTER_IP
    master.vm.provision "shell", path: "Scripts/k3s-master.sh", env: { "MASTER_IP" => MASTER_IP }
  end

  config.vm.define "agent" do |agent|
    agent.vm.hostname = "agent"
    agent.vm.network "private_network", ip: AGENT_IP
    agent.vm.provision "shell", path: "Scripts/k3s-agent.sh", env: { "MASTER_IP" => MASTER_IP }
  end
end
