## VMware CSI Driver Pre-Requisites

In order to sucessfully install the VMware CSI Driver, the following items must be completed first: 
1. Creation of the `ClusterSecretStore` Kubernetes resource detailed in the eks-anywhere-addons/README.md file 

2. Creation of config secrets in AWS Secrets Manager that External secrets will reference in the 
vsphere-external-secrets.yaml file.

# Creation of the Config Secrets 

Two Secrets must be created, csi-vsphere.conf referenced by the 
vsphere-csi-controller in the vsphere-csi-driver.yaml file, and 
vsphere.conf that is referenced in the vsphere-cloud-controller.yaml file

Both secrets are multi-line configs, so the "Plaintext" secret type must be used. 

In csi-vsphere.conf, the secret will contain Global configuration data and Virtual Center specific information in the following format:

```
[Global]
insecure-flag = "true"
port = "443"

[VirtualCenter "<Your Vcenter IP Address>"]
cluster-id = "<Your Cluster ID"
user = "<Your Vcenter Username>"
password = "<Your Vcenter Password>"
datacenters = "<Your Datacenter(s)>"
```

In vsphere.conf the same information is required, YAML formatted:

```
global:
  port: 443
  insecureFlag: true

vcenter:
  <Your VCenter Name>:
      server: <Your Vcenter IP Address>
      user: <Your Vcenter Username>
      password: <Your Vcenter Password>
      datacenters:
      - <Your Datacenter(s)>
```

