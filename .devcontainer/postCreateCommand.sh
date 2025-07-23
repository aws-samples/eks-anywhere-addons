#!/usr/bin/env bash

# Step 1 setup autocomplete for kubectl and alias k
mkdir $HOME/.kube
echo "source <(kubectl completion bash)" >> $HOME/.bashrc
echo "alias k=kubectl" >> $HOME/.bashrc
echo "complete -F __start_kubectl k" >> $HOME/.bashrc

# Step 2 - Installs Flux on your local machine.
echo "----------------------------------------------------"
echo "Downloading 'Flux' ..."
curl -O "https://toolkit.Fluxcd.io/install.sh" --silent --location
echo "Installing 'Flux' ..."
chmod +x ./install.sh
./install.sh
rm -rf ./install.sh

export PATH=$HOME/.fluxcd/bin:$PATH

echo "Flux has been installed and PATH is updated for this session."

# Step 3 Setup Minikube
minikube start

# Step 4 - Installs Flux Controller on your Kubernetes Cluster.
flux install \
    --namespace=flux-system \
    --network-policy=false \
    --components=source-controller,helm-controller,kustomize-controller,notification-controller