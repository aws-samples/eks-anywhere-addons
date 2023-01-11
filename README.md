## Amazon EKS Anywhere Partner Add-ons

This repository is part of the Amazon EKS Anywhere (EKS-A) Conformance and Validation Framework, designed to address general validation and quality assurance of Partner and third-party solutions (add-ons) running on EKS-A on supported operating systems, hardware and virtualization platforms.

The EKS Anywhere conformance and validation framework provides an expandable and extensible approach to run conformance testing on different EKS deployment models such as EKS-A on VMware (VMC), EKS-A on Bare Metal, EKS-A on Snow and EKS on Rover (Outposts). It allows running Kubernetes conformance testing, Partner and OSS add-on deployment and validation on EKS-A environments and helps Partners validate their hardware and software solutions deployed on variety of EKS environments.

This repository is a GitOps repository powered by FluxCD and contains Partner and third-party solutions and functional tests for deployment in the supported deployment environments. Each deployment option is represented by the respective folder in this repository, where Partners and external contributors can submit a pull request. 

GitOps is leveraged as a decoupling mechanism between physical test environments and ISV solutions, enabling Partners to test their solutions without direct access to the respective labs and avoid potentially costly maintenance of the test environments. 

## Process Overview

Deployment of a third-party solution requires a PR for a FluxCD deployment submitted to this repository. 

-	The framework allows to submit your solution to a single location and deploy across all environments with the same configuration. In this case, create a new solution specific folder (e.g. `<orgname>` or `<orgname>-<productname>`) in the common folder [eks-anywhere-common/Addons/Partner](https://github.com/aws-samples/eks-anywhere-addons/tree/main/eks-anywhere-common/Addons/Partner) and submit your GitOps deployment (e.g. HelmRelease, manifests and/or other support package management resources) in that folder.

-	If your product and/or configuration must be distinct for each of the deployment options then create a new solution under the respective target. For example, if it is for EKS-A on Snow then the path is `eks-anywhere-snow/Addons/Partner`. 

-	You can deploy Helm via FluxCD HelmRelease custom resource. Here is a [Helm example](https:/github.com/aws-samples/eks-anywhere-addons/tree/main/eks-anywhere-common/Addons/Partner/Kubecost). In particular the example covers specification of [Helm repository](https://github.com/aws-samples/eks-anywhere-addons/blob/main/eks-anywhere-common/Addons/Partner/Kubecost/kubecost-source.yaml) and [Helm release](https://github.com/aws-samples/eks-anywhere-addons/blob/main/eks-anywhere-common/Addons/Partner/Kubecost/kubecost.yaml). 

-	Secrets management such as license key or credentials is implemented using the External Secrets add-on. You will need to share secrets with the AWS Partner team. The AWS Partner team will create those secrets in an AWS account and use External Secrets to bring them down to the target deployment cluster. After that, such secrets can be configured in your GitOps deployment folder and passed to the deployment using configuration values or if your helm deployment can use pre-created secrets, that option is also supported.  The sample folder also contains an example of leveraging a [secret](https://github.com/aws-samples/eks-anywhere-addons/blob/main/eks-anywhere-common/Addons/Partner/Kubecost/external-secret.yaml) with the deployment as well as an example of wiring that secret in your deployment [here](https://github.com/aws-samples/eks-anywhere-addons/blob/main/eks-anywhere-common/Addons/Partner/Kubecost/kubecost.yaml#L24) (line numbers may change in the link).

-	While validation that your solution deploys on the target deployment option is helpful, it does not provide the required level of quality assurance for functional verification, which is generally achieved with a test framework and automation normally included in the CI/CD cycle of the Partner product. We recommend that Partners wrap their functional test as a container and submit as a Kubernetes job along with their deployments to enable broader test coverage and better customer experience. The functional test job should be submitted under `eks-anywhere-common/testers` (runs on all platforms) or under your respective environment folder such as `eks-anywhere-snow/testers` (e.g. `eks-anywhere-snow/testers/<orgname>-<productname>`). Example [here](https://github.com/aws-samples/eks-anywhere-addons/tree/main/eks-anywhere-snow/Testers/Sample). 

## Contribution Flow

1.	Fork the repo. 
2.	Apply changes such as deployment and/or any documentation.
3.	Test them locally using FluxCD.
4.	Submit a PR to the main branch of this repository.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file..

