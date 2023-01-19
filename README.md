## Amazon EKS Anywhere (EKS-A) Conformance and Validation Framework

💥 Welcome to Amazon EKS Anywhere (EKS-A) Conformance and Validation Framework 💥

🎯 This repository is part of the Amazon EKS Anywhere (EKS-A) Conformance and Validation Framework, designed to address general validation and quality assurance of Partner and third-party solutions (add-ons) running on EKS-A on supported operating systems, hardware and virtualization platforms.

🎯 The EKS Anywhere conformance and validation framework provides an expandable and extensible approach to run conformance testing on different EKS deployment models such as EKS-A on VMware (VMC), EKS-A on Bare Metal, EKS-A on Snow and EKS on Rover (Outposts). It allows running Kubernetes conformance testing, Partner and OSS add-on deployment and validation on EKS-A environments and helps Partners validate their hardware (IHV) and software (ISV) solutions deployed on variety of EKS environments.

🎯 This repository is a GitOps repository powered by FluxCD and contains Partner and third-party solutions and functional tests for deployment in the supported deployment environments. Each deployment option is represented by the respective folder in this repository, where Partners and external contributors can submit a pull request. 

🎯 [GitOps](https://www.weave.works/technologies/gitops/) is leveraged as a decoupling mechanism between physical test environments and ISV solutions, enabling Partners to test their solutions without direct access to the respective labs and avoid potentially costly maintenance of the test environments. 

## Process Overview

Deployment of a third-party solution requires a PR for a FluxCD deployment submitted to this repository. 

🚀	The framework allows to submit your solution to a single location and deploy across all environments with the same configuration. In this case, create a new solution specific folder (e.g. `<orgname>` or `<orgname>/<productname>`) in the common folder [eks-anywhere-common/Addons/Partner](https://github.com/aws-samples/eks-anywhere-addons/tree/main/eks-anywhere-common/Addons/Partner) and submit your GitOps deployment (e.g. HelmRelease, manifests and/or other support package management resources) in that folder.

🚀	If your product and/or configuration must be distinct for each of the deployment options then create a new solution under the respective target. For example, if it is for EKS-A on Snow then the path is `eks-anywhere-snow/Addons/Partner`. 

🚀	You can deploy Helm via FluxCD HelmRelease custom resource. Here is a [Helm example](https:/github.com/aws-samples/eks-anywhere-addons/tree/main/eks-anywhere-common/Addons/Partner/Kubecost). In particular the example covers specification of [Helm repository](https://github.com/aws-samples/eks-anywhere-addons/blob/main/eks-anywhere-common/Addons/Partner/Kubecost/kubecost-source.yaml) and [Helm release](https://github.com/aws-samples/eks-anywhere-addons/blob/main/eks-anywhere-common/Addons/Partner/Kubecost/kubecost.yaml). 

🚀	Secrets management such as license key or credentials is implemented using the External Secrets add-on. You will need to share secrets with the AWS Partner team. The AWS Partner team will create those secrets in an AWS account and use External Secrets to bring them down to the target deployment cluster. After that, such secrets can be configured in your GitOps deployment folder and passed to the deployment using configuration values or if your helm deployment can use pre-created secrets, that option is also supported.  The sample folder also contains an example of leveraging a [secret](https://github.com/aws-samples/eks-anywhere-addons/blob/main/eks-anywhere-common/Addons/Partner/Kubecost/external-secret.yaml) with the deployment as well as an example of wiring that secret in your deployment [here](https://github.com/aws-samples/eks-anywhere-addons/blob/main/eks-anywhere-common/Addons/Partner/Kubecost/kubecost.yaml#L24) (line numbers may change in the link).

🚀	While validation that your solution deploys on the target deployment option is helpful, it does not provide the required level of quality assurance for functional verification, which is generally achieved with a test framework and automation normally included in the CI/CD cycle of the Partner product. We recommend that Partners wrap their functional test as a container and submit as a Kubernetes job along with their deployments to enable broader test coverage and better customer experience. The functional test job should be submitted under `eks-anywhere-common/testers` (runs on all platforms) or under your respective environment folder such as `eks-anywhere-snow/testers` (e.g. `eks-anywhere-snow/testers/<orgname>/<productname>`). Example [here](https://github.com/aws-samples/eks-anywhere-addons/tree/main/eks-anywhere-snow/Testers/Sample). 

## Contribution Flow

1.	Fork the repo. 
2.	Apply changes such as deployment and/or any documentation.
3.	Test them locally using FluxCD.
4.	Submit a PR to the main branch of this repository.

## Pre-requisite (Linux/MacOS)

This solution requires Flux CLI locally and Flux Controller on your Kubernetes cluster. Please follow the below steps for installing these pre-requisites :

🚀 Install Flux CLI:
```bash
    echo "----------------------------------------------------"
    echo "Downloading 'Flux' ..."
    curl -O "https://toolkit.Fluxcd.io/install.sh" --silent --location
    echo "Installing 'Flux' ..."
    chmod +x ./install.sh
    ./install.sh
    rm -rf ./install.sh
```

🚀 Install Flux Controller (assuming you have kubectl access to the target cluster):
```bash
flux install \
    --namespace=flux-system \
    --network-policy=false \
    --components=source-controller,helm-controller,kustomize-controller,notification-controller
```

## Local Testing (Linux/MacOS)

🚀 Add `GitRepository` for your fork:
```bash
flux create source git addons \
    --url=<forked repo from https://github.com/aws-samples/eks-anywhere-addons>\
    --branch=main # This should be replaced with your branch for testing your changes
```

🚀 Add Kustomization for your add-on:
```bash
# Example for Snowball Edge (replace --path with the target env as required)
flux create kustomization addons-snow-partner \
    --source=addons \
    --path="./eks-anywhere-snow/Addons/Partner" \
    --prune=true \
    --interval=5m 
```

## Validation

🚀 Validate by navigating to the target namespace and checking if all pods are running. As an example, Please see the kubernetes resources in botkube namespace as shown below:

```
❯ kga -n botkube
NAME                                   READY   STATUS    RESTARTS   AGE
pod/botkube-botkube-58c4579b44-87mbq   1/1     Running   0          7h55m

NAME                              READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/botkube-botkube   1/1     1            1           7h55m

NAME                                         DESIRED   CURRENT   READY   AGE
replicaset.apps/botkube-botkube-58c4579b44   1         1         1       7h55m
```

🚀 Troubleshooting: [FluxCD Troubleshooting](https://fluxcd.io/flux/cheatsheets/troubleshooting/)

## 🤝 Support & Feedback
Amazon EKS Anywhere (EKS-A) Conformance and Validation Framework is maintained by AWS Solution Architects and is not an AWS service. Support is provided on a best effort basis. If you have feedback, feature ideas, or wish to report bugs, please use the [Issues](https://github.com/aws-samples/eks-anywhere-addons/issues) section of this GitHub.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

## 🙌 Community
We welcome all individuals who are enthusiastic about Kubernetes to become a part of this open source conformance framework. Your contributions and participation are invaluable to the success of this project.

Built with  ❤️ at AWS.