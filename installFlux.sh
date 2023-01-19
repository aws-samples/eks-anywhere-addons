
# Step 1 - Installs Flux on your local machine.
echo "----------------------------------------------------"
echo "Downloading 'Flux' ..."
curl -O "https://toolkit.Fluxcd.io/install.sh" --silent --location
echo "Installing 'Flux' ..."
chmod +x ./install.sh
./install.sh
rm -rf ./install.sh

# Step 2 - Installs Flux Controller on your Kubernetes Cluster.
flux install \
    --namespace=flux-system \
    --network-policy=false \
    --components=source-controller,helm-controller,kustomize-controller,notification-controller