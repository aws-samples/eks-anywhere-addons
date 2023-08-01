## Amazon EKS Anywhere (EKS-A) Conformance and Validation Framework

💥 Welcome to Amazon EKS Anywhere (EKS-A) Conformance and Validation Framework 💥

🎯 This repository is part of the Amazon EKS Anywhere (EKS-A) Conformance and Validation Framework, designed to address general validation and quality assurance of Partner and third-party solutions (add-ons) running on EKS-A on supported operating systems, hardware and virtualization platforms.

🎯 The EKS Anywhere conformance and validation framework provides an expandable and extensible approach to run conformance testing on different EKS deployment models such as EKS-A on VMware (VMC), EKS-A on Bare Metal, EKS-A on Snow , EKS-A on Nutanix and Local clusters for Amazon EKS on AWS Outposts. It allows running Kubernetes conformance testing, Partner and OSS add-on deployment and validation on EKS-A environments and helps Partners validate their hardware (IHV) and software (ISV) solutions deployed on variety of EKS environments.

🎯 This repository is a GitOps repository powered by FluxCD and contains Partner and third-party solutions and functional tests for deployment in the supported deployment environments. Each deployment option is represented by the respective folder in this repository, where Partners and external contributors can submit a pull request. 

🎯 [GitOps](https://www.weave.works/technologies/gitops/) is leveraged as a decoupling mechanism between physical test environments and ISV solutions, enabling Partners to test their solutions without direct access to the respective labs and avoid potentially costly maintenance of the test environments. 

## 🏃‍♀️Getting Started

Deployment of a third-party solution requires a PR for a FluxCD deployment submitted to this repository. 

🚀	The framework allows to submit your solution to a single location and deploy across all environments with the same configuration. In this case, create a new solution specific folder (e.g. `<orgname>` or `<orgname>/<productname>`) in the common folder [eks-anywhere-common/Addons/Partner](https://github.com/aws-samples/eks-anywhere-addons/tree/main/eks-anywhere-common/Addons/Partner) and submit your GitOps deployment (e.g. HelmRelease, manifests and/or other support package management resources) in that folder.

🚀	If your product and/or configuration must be distinct for each of the deployment options then create a new solution under the respective target. For example, if it is for EKS-A on Snow then the path is `eks-anywhere-snow/Addons/Partner`. 

🚀 For kubernetes namespace resource for your product, please add labels as shown below for reporting purposes:

```
apiVersion: v1
kind: Namespace
metadata:
    name: kubecost
    labels:
        aws.conformance.vendor: kubecost
        aws.conformance.vendor-solution: cost-analyzer
```

🚀	You can deploy Helm via FluxCD HelmRelease custom resource. Here is a [Helm example](https:/github.com/aws-samples/eks-anywhere-addons/tree/main/eks-anywhere-common/Addons/Partner/Kubecost). In particular the example covers specification of [Helm repository](https://github.com/aws-samples/eks-anywhere-addons/blob/main/eks-anywhere-common/Addons/Partner/Kubecost/kubecost-source.yaml) and [Helm release](https://github.com/aws-samples/eks-anywhere-addons/blob/main/eks-anywhere-common/Addons/Partner/Kubecost/kubecost.yaml). 

🚀	Secrets management such as license key or credentials is implemented using the External Secrets add-on. You will need to share secrets with the AWS Partner team. The AWS Partner team will create those secrets in an AWS account and use External Secrets to bring them down to the target deployment cluster. After that, such secrets can be configured in your GitOps deployment folder and passed to the deployment using configuration values or if your helm deployment can use pre-created secrets, that option is also supported.  The sample folder also contains an example of leveraging a [secret](https://github.com/aws-samples/eks-anywhere-addons/blob/main/eks-anywhere-common/Addons/Partner/Kubecost/external-secret.yaml) with the deployment as well as an example of wiring that secret in your deployment [here](https://github.com/aws-samples/eks-anywhere-addons/blob/main/eks-anywhere-common/Addons/Partner/Kubecost/kubecost.yaml#L24) (line numbers may change in the link).

🚀	Though deployment and validation of your solution on the target deployment option is helpful, it does not provide the required level of quality assurance for functional verification, which is generally achieved with a test framework and automation normally included in the CI/CD cycle of the Partner product.

## Functional Job Requirements

1. Functional test should base its test cases on the specifications of the ISV product under test
2. Functional test should validate the functionality of the ISV product and describe what the ISV product does
3. Healthchecks, service endpoints checks or any other technical checks do not represent sufficient coverage required for the functional test
4. Functional test should be wrapped as a container, container image should be published on ECR, and/or provide evidence of successful recent vulnerability scan
5. Functional test must be implemented as a Kubernetes Job and any non-zero exit status of the job execution will be considered a failure
6. Functional test must be repeatable. That means that if the job has executed before successfully and no changes were applied, we expect to run it continuously and mark the product as failure if the test job starts producing failures even if previous executions against the same environment were successful
7. Functional test should not require elevated security permissions, such as cluster roles, privileged mode, non-ephemeral storage
8. Functional test should be submitted under `eks-anywhere-common/testers` (runs on all platforms) or under your respective environment folder such as `eks-anywhere-snow/testers` (e.g. `eks-anywhere-snow/testers/<orgname>/<productname>`)

Refer the example [here](https://github.com/aws-samples/eks-anywhere-addons/tree/main/eks-anywhere-common/Testers/Hashicorp/Vault/kvJob.yaml) for functional test job.


## Contribution Flow

1.	Fork the repo. 
2.	Apply changes such as deployment and/or any documentation.
3.	Test them locally using FluxCD.
4.	Submit a PR to the main branch of this repository.

## Pre-requisite (Linux/MacOS)

This solution requires Flux CLI locally and Flux Controller on your Kubernetes cluster. Flux requires access to a source repository via api and access to the kubernetes cluster you want to use for testing. Please follow the below steps for installing these pre-requisites.

If you do not already have access to a running kubernetes cluster you can consider setting up an [EKS Anywhere local cluster](https://anywhere.eks.amazonaws.com/docs/getting-started/local-environment/) on docker provider or a local [k3s](https://k3s.io/) cluster or you may choose a hosted service such as [AWS EKS](https://aws.amazon.com/eks/).

Flux integrates into your running cluster and needs the kubeconfig file of the cluster for testing. Flux will look in the default location, i.e. *~/.kube/config*. 

Before setting up Flux make sure your configuration file points to your cluster. You can use the following command for example to verify that a suitable kubeconfig file can be found and the cluster can be accessed. If no configuration is found you will get an error message indicating that *"http://localhost:8080/version"* cannot be accessed. Do not be confused by the port number. The port number for accessing the kubernetes cluster is part of the configuration file and the reported port in the error message is a default port.

```bash
kubectl get ns
```

You can use the following to ensure the flux installation finds the cluster you want to use for testing.

```bash
export KUBECONFIG=$PATH_TO_kubeconfig.yaml
```

Once you have a kubernetes cluster running and the configuration file is properly setup you are ready to install flux.

```bash
git clone https://github.com/aws-samples/eks-anywhere-addons.git
cd eks-anywhere-addons
chmod +x installFlux.sh
./installFlux.sh
```
**Note:** In order to commit back to the project you need to create a fork in GitHub of the *eks-anywhere-addons* repository into your own project. After the fork is created clone the source code from your fork. To keep the projects connected, you can add the AWS project as an upstream by adding he below to your .git/config file.

```
[remote "upstream"]
    url = git@github.com:aws-samples/eks-anywhere-addons.git
    fetch = +refs/heads/*:refs/remotes/upstream/*
```

## Local Testing (Linux/MacOS)

🚀 First, lets create a plaintext secret in AWS Secrets Manager for your secrets (credentials, license keys, API keys, etc.) using instructions in [create an AWS Secrets Manager secret](https://docs.aws.amazon.com/secretsmanager/latest/userguide/create_secret.html) in `us-west-2` region.

Next, install [external-secrets](https://github.com/external-secrets/external-secrets) on your cluster using the below helm installation of external-secrets to sync secrets between AWS Secrets manager and EKSA Cluster:

```bash
helm repo add external-secrets https://charts.external-secrets.io

helm install external-secrets \
    external-secrets/external-secrets \
    -n external-secrets \
    --create-namespace 
```

Next, lets create following Kubernetes generic secret in to your cluster for setting ClusterSecretStore to access AWS Secrets Manager to pull your secrets required for installation of your product:

```bash
aws iam create-access-key \
  --user-name external-secrets-${EKS_DEPLOYMENT_MODEL_SHORT} > aws_creds.json

ACCESS_KEY=$(cat aws_creds.json | jq -r .AccessKey.AccessKeyId)
SECRET_KEY=$(cat aws_creds.json | jq -r .AccessKey.SecretAccessKey)

kubectl create secret generic aws-secret \
  --from-literal=access-key=$ACCESS_KEY \
  --from-literal=secret=$SECRET_KEY

rm -rf aws_creds.json
```

Next, lets create the following Kubernetes resource `ClusterSecretStore` to to access AWS Secrets Manager to pull your secrets required for installation of your product:

```bash
cat <<EOF | kubectl apply -f - 
apiVersion: external-secrets.io/v1beta1
kind: ClusterSecretStore
metadata:
  name: eksa-configmap-store
spec:
  provider:
    aws:  # set secretStore provider to AWS.
      service: ParameterStore # Configure service to be Parameter Store
      region: us-west-2  # Region where the secret is.
      auth:
        secretRef:
          accessKeyIDSecretRef: 
            name: aws-secret # References the secret we created
            namespace: default
            key: access-key  
          secretAccessKeySecretRef:
            name: aws-secret
            namespace: default
            key: secret
EOF
```

Add `GitRepository` for your fork:
```bash
flux create source git addons \
    --url=<forked repo from https://github.com/aws-samples/eks-anywhere-addons>\
    --branch=main # This should be replaced with your branch for testing your changes
```

This creates a flux GitRepository resource. The flux GitRepository resource will periodically check the configured repo and branch for changes and sync any new commits. Since this project uses git, we are creating a `GitRepository` resource.

**Note:** If you need/want to work in a disconnected fashion you need to run a git server on your system and push the *eks-anywhere-addons* repository to your git server.

The name in the above command, *addons*, is arbitrary but must match the name used as the value of the *--source* argument in the following command.

🚀 Add Kustomization for your add-on:
```bash
# Example for Snowball Edge (replace --path with the target env as required)
flux create kustomization addons-snow-partner \
    --source=addons \
    --path="./eks-anywhere-snow/Addons/Partner" \
    --prune=true \
    --interval=5m 
```

The given example will attempt to deploy all solutions it can find in the *./eks-anywhere-snow/Addons/Partner* directory tree. You can limit your testing to only your application by providing a more specific path, *./eks-anywhere-common/Addons/Partner/foobar* for example will deploy anything found in the *foobar* subdirectory. The *--path* setting must match the location where your deployment is setup, not the location for the testJob. 

The name, in this example *addons-snow-partner*, is arbitrary. As mentioned the value for the *--source* argument must match the name given when the source reference was created.

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

For functional testing you need to create a **testJob**. See *eks-anywhere-addons/eks-anywhere-common/Testers* for examples. The descriptions about [Jobs](https://kubernetes.io/docs/concepts/workloads/controllers/job/) from upstream kubernetes provides helpful information and additional details.

Presumably your application will provide a service that can be accessed to verify the application deployed as expected. In the test job performs a basic functional verification of your deployed product. The generic access pattern to access a service in the cluster is `servicename.namespace.svc.cluster.local:port` where `servicename` is the name of your service, `namespace` is the namespace you assigned in your deployment yaml description and `port` is the port number your service is running on. 

If you are uncertain about the service name you can use the following where *$NAMESPACE* is the namespace you assigned in your deployment yaml description. 

```bash
kubectl get services -n $NAMESPACE
```

🚀 Add Kustomization for testing your test job :

```bash
flux create kustomization addons-snow-partner \
    --source=addons \
    --path="./eks-anywhere-snow/testers/Partner" \
    --prune=true \
    --interval=5m 
```

Use the below command to delete the existing job :

```bash
kubectl delete job $NAME_OF_TESTJOB -n $NAMESPACE
```

To debug the test job use the `kubectl logs` command.

## Troubleshooting

The[FluxCD Troubleshooting](https://fluxcd.io/flux/cheatsheets/troubleshooting/) guide provides information on most commands to troubleshoot the deployment and helps you understand any issues you may encounter.

## 🤝 Support & Feedback
Amazon EKS Anywhere (EKS-A) Conformance and Validation Framework is maintained by AWS Solution Architects and is not an AWS service. Support is provided on a best effort basis. If you have feedback, feature ideas, or wish to report bugs, please use the [Issues](https://github.com/aws-samples/eks-anywhere-addons/issues) section of this GitHub.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

## 🙌 Community

We welcome all individuals who are enthusiastic about Kubernetes to become a part of this open source conformance framework. Your contributions and participation are invaluable to the success of this project.

## 🙌 Collaboration

Please join us on slack at [AWS Developers](awsdevelopers.slack.com). Get onboarded to slack by sharing your emails with us.

Built with ❤️ at AWS.
