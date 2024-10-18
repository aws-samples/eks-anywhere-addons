## Development Setup for the TestJob

* Set Environment variables, replacing NR license keys, API Keys and Account as appropriate

``
export newrelic_licensekey=YOUR_LICENSE_KEY
export newrelic_account=YOUR_ACCOUNT
export newrelic_apikey=YOUR_APIKEY

``

* Install NR K8 instrumentation 

```
function ver { printf "%03d%03d" $(echo "$1" | tr '.' ' '); } && \
K8S_VERSION=$(kubectl version --short 2>&1 | grep 'Server Version' | awk -F' v' '{ print $2; }' | awk -F. '{ print $1"."$2; }') && \
if [[ $(ver $K8S_VERSION) -lt $(ver "1.25") ]]; then KSM_IMAGE_VERSION="v2.6.0"; else KSM_IMAGE_VERSION="v2.7.0"; fi && \
helm repo add newrelic https://helm-charts.newrelic.com && helm repo update && \
kubectl create namespace newrelic ; helm upgrade --install newrelic-bundle newrelic/nri-bundle \
 --set global.licenseKey=$newrelic_licensekey \
 --set global.cluster=development \
 --namespace=newrelic \
 --set newrelic-infrastructure.privileged=false \
 --set global.lowDataMode=true \
 --set kube-state-metrics.image.tag=${KSM_IMAGE_VERSION} \
 --set kube-state-metrics.enabled=true \
 --set kubeEvents.enabled=true 
```

* Create Secret

```
kubectl create secret generic newrelic-secret -n newrelic \
    --from-literal=newrelic-licensekey=$newrelic_licensekey \
    --from-literal=newrelic-account=$newrelic_account \
    --from-literal=newrelic-apikey=$newrelic_apikey
```

* Modify Cron job time

Make changes in spec.schedule in eks-cloud/Testers/newrelic/test-job.yaml reflect the time when you want the cron job to run in your development environment

* Install K8 manifest files

```
kubectl apply -f eks-cloud/Testers/newrelic/
```