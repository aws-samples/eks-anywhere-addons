import argparse

import kubernetes.client
import concurrent.futures
from ghapi.all import GhApi
from kubernetes import client, config
from kubernetes.client import *


# https://github.com/kubernetes-client/python
# Using the kubernetes client to get the exact information
# we need to write the feedback bot
def run_observer():
    # Start the search at the namespace level since we want to watch for all things
    all_namespaces = core_api.list_namespace()

    risky_pods = [ get_at_risk_pods(i) for i in all_namespaces.items ]

    risky_deployments = [ get_at_risk_deployments(i) for i in risky_pods if i ]

    reports = [build_report(i) for i in risky_deployments]

    # If we wanna go F A S T - maybe
    # with concurrent.futures.ThreadPoolExecutor(max_workers=len(all_namespaces)) as observer:
    #     responses = list(observer.map(lambda ns: observe_orchestrate(ns), all_namespaces))

    return 0


# Multithreaded orchestrator for going F A S T - maybe
def observe_orchestrate(ns: V1Namespace):

    pass


"""
    Add various methods to check if a pod is failing or has failed.
"""
def get_at_risk_pods(ns: V1Namespace) -> []:
    all_ns_pods: [V1Pod] = core_api.list_namespaced_pod(ns.metadata.name).items

    at_risk_pods: [] = []
    for pod in all_ns_pods:
        # If state is not Pending, Running Succeeded
        pod_status: V1PodStatus = pod.status

        # If the pod isn't in a "Success/Pending" state, immediately flag it
        if pod_status.phase not in { "Running", "Pending", "Succeeded" }:
            at_risk_pods.append({
                "ns": ns.metadata.name,
                "pod": pod,
                "reason_type": V1PodStatus,
                "reason": pod.status
            })
            continue

        # If it's in one of those phases, check the containers inside
        container_statuses: [V1ContainerStatus] = pod_status.container_statuses
        for status in container_statuses:
            # If state is CrashLoopBackoff - definitely bad
            # If state is ImagePullError - definitely bad
            # If state is Error - definitely bad
            # Something is bad and the pod has restarted a bunch of times
            if not status.ready and status.restart_count >= 1:
                at_risk_pods.append({
                    "ns": ns.metadata.name,
                    "pod": pod,
                    "reason_type": V1ContainerStatus,
                    "reason": status
                })
                continue

    # If delta in replicas and ready replicas - this might lead to false positives
    return at_risk_pods


"""
    Drill up from the failing pod level to the deployment that's causing the trouble
"""
def get_at_risk_deployments(risk_report):
    # risk_report is [risk]
    # metadata.owner_references.name - to get the owner of a pod
    # Find out the exact owners of the pods that are failing

    deployment_ns = risk_report[0]["ns"]

    # If the containers belong to the same replica sets, they
    # belong to the same deployment?
    at_risk_replica_sets = {}

    at_risk_deployments = []

    # Get at risk replica sets
    for risk in risk_report:
        pod_owner = risk["pod"].metadata.owner_references[0].name

        if pod_owner in at_risk_replica_sets:
            at_risk_replica_sets[pod_owner].append(risk)
        else:
            at_risk_replica_sets[pod_owner] = [risk]

    for replica_set in at_risk_replica_sets:
        # Gets the replica set associated with the at risk pod
        replica_set_info = apps_api.read_namespaced_replica_set(replica_set, deployment_ns)

        replica_owner = replica_set_info.metadata.owner_references[0].name
        deployment = apps_api.read_namespaced_deployment(replica_owner, deployment_ns)

        # Might have to deep copy this one
        at_risk = {
            "deployment": deployment,
            "ns": deployment_ns,
            "risks": at_risk_replica_sets[replica_set]
        }

        at_risk_deployments.append(at_risk)

    return at_risk_deployments


"""
    Retrieve and return logs from the pod
"""
def get_pod_logs(pod: kubernetes.client.V1Pod):
    return core_api.read_namespaced_pod_log(pod.metadata.name, pod.metadata.namespace)
    pass


"""
    Build the Github PR comment here, providing all the information they would need to
    debug the problem (hopefully)
"""
def build_report(risk_info):
    # risk:
    #   deployment: V1Deployment
    #   ns: String
    #   risks:
    #     ns: String
    #     pod: V1Pod
    #     reason_type: Any
    #     reason: typeof(reason_type)

    namespace_report = {
        'ns': risk_info[0]['ns'],
        'reports': []
    }

    for risk in risk_info:
        report = f"Looks like your deployment `{risk['deployment'].metadata.name}` is failing.\n" \
                 f"Specifically, it looks like these pods are failing: \n"
        for pod_risk in risk["risks"]:
            report += f"* Pod: `{pod_risk['pod'].metadata.name}` with the error listed below.\n"

        report += '\n ---- \n'

        for pod_risk in risk["risks"]:
            report += f"Logs for pod `{pod_risk['pod'].metadata.name}`: ```{get_pod_logs(pod_risk['pod'])}```\n ---- "

        namespace_report["reports"].append(report)


    return namespace_report

"""
    Get Issue Number from the namespace
    
    Send the information to GitHub using the api
"""
def add_comment_to_pr(report):
    # comment_response = gh_api.issues.create_comment(
    #     owner='aws-samples',
    #     repo='eks-anywhere-addons',
    #     issue_number=101,  # namespace.metadata.name derived from PR and namespace configmap
    #     body='This is a comment made by the conformitron feedback provider with feedback for your pod.'
    #          'It has failed with the following logs: '
    #          '```' + get_pod_logs(pod) + '```'
    # )
    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="KubeObserverBot")
    parser.add_argument("-l", action='store_true')
    args = parser.parse_args()
    if args.l:
        print("loading kubeconfig")
        from dotenv import load_dotenv

        load_dotenv(".dev.env")
        config.load_kube_config()
    else:
        print("loading incluster config")
        config.load_incluster_config()

    gh_api = GhApi()

    apps_api = client.AppsV1Api()
    core_api = client.CoreV1Api()

    run_observer()
