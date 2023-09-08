import os
import argparse
from datetime import datetime

import kubernetes.client
from config_data import *
from ghapi.all import GhApi
from kubernetes.client import *
from kubernetes import client, config


# https://github.com/kubernetes-client/python
# Using the kubernetes client to get the exact information
# we need to write the feedback bot
def run_observer():
    """
    Runs the observer to monitor Kubernetes deployments for risk.

    :return: 0 if the observer run was successful.
    """
    # Start the search at the namespace level since we want to watch for all things
    all_namespaces = core_api.list_namespace()

    risky_pods = [get_at_risk_pods(i) for i in all_namespaces.items]

    risky_deployments = [get_at_risk_deployments(i) for i in risky_pods if i]

    reports = [build_report(i) for i in risky_deployments]

    responses = [add_comment_to_pr(i) for i in reports]

    # If we wanna go F A S T - maybe
    # with concurrent.futures.ThreadPoolExecutor(max_workers=len(all_namespaces)) as observer:
    #     responses = list(observer.map(lambda ns: observe_orchestrate(ns), all_namespaces))

    return 0


# Multithreaded orchestrator for going F A S T - maybe
def observe_orchestrate(ns: V1Namespace):
    pass


def get_at_risk_pods(ns: V1Namespace) -> []:
    """
    :param ns: V1Namespace object representing the namespace for which to retrieve at-risk pods.
    :return: A list of dictionaries, each representing an at-risk pod. Each dictionary contains the following keys:
        - 'ns': The name of the namespace.
        - 'pod': The V1Pod object representing the at-risk pod.
        - 'reason_type': The type of reason (V1PodStatus or V1ContainerStatus) indicating why the pod is at risk.
        - 'reason': The reason for the pod being at risk.
    """
    try:
        all_ns_pods: [V1Pod] = core_api.list_namespaced_pod(ns.metadata.name).items
    except Exception as e:
        print(f"Error in get_at_risk_pods: {e}")
        return

    at_risk_pods: [] = []
    for pod in all_ns_pods:
        # If state is not Pending, Running Succeeded
        pod_status: V1PodStatus = pod.status

        # If the pod isn't in a "Success/Pending" state, immediately flag it
        # Checks if it's failed/unknown
        if pod_status.phase in {"Failed", "Unknown"}:
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
            if not status.ready or status.restart_count >= 1:
                at_risk_pods.append({
                    "ns": ns.metadata.name,
                    "pod": pod,
                    "reason_type": V1ContainerStatus,
                    "reason": status
                })
                continue

    # If delta in replicas and ready replicas - this might lead to false positives
    return at_risk_pods


def get_at_risk_deployments(risk_report):
    """
    :param risk_report: A list of dictionaries representing the risk report.
    :return: A list of dictionaries representing the at-risk deployments.

    The `get_at_risk_deployments` method takes a risk report as input and returns a list of at-risk deployments.
    The risk report is expected to be a list of dictionaries where each dictionary represents a risk. Each risk
    contains information about a failing pod, including the namespace (`ns`) and the pod metadata. The method uses
    this information to determine the at-risk deployments.

    If the extraction of the pod owner fails (due to a `TypeError`), the method assumes that the pod is a raw pod
    (not associated with a replica set) and adds it to a special key `"raw_pod"` in the `at_risk_replica_sets` dictionary.

    In case of any exceptions during the retrieval of replica set or deployment information, an error message is printed.

    Finally, the method returns the `at_risk_deployments` list, which contains the at-risk deployments.
    """
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
        try:
            pod_owner = risk["pod"].metadata.owner_references[0].name
        except TypeError as e:
            print("Using a raw pod stop. get some help.")
            print(f"Raw pod vals: {risk['pod']}")
            raw_pods_key = 'raw_pod'

            if raw_pods_key in at_risk_replica_sets:
                at_risk_replica_sets[raw_pods_key].append(risk)
            else:
                at_risk_replica_sets[raw_pods_key] = [risk]
            continue

        if pod_owner in at_risk_replica_sets:
            at_risk_replica_sets[pod_owner].append(risk)
        else:
            at_risk_replica_sets[pod_owner] = [risk]

    for replica_set in at_risk_replica_sets:
        # Gets the replica set associated with the at risk pod
        if replica_set == "raw_pod":
            at_risk = {
                "deployment": "raw_pods",
                "ns": deployment_ns,
                "risks": at_risk_replica_sets[replica_set]
            }
            at_risk_deployments.append(at_risk)
            continue

        try:
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
        except Exception as e:
            print(f"Error in get_at_risk_deployments: {e}")

    return at_risk_deployments


def get_pod_logs(pod: kubernetes.client.V1Pod):
    """
    Get the logs and status of a given pod.

    :param pod: The pod for which to retrieve logs and status.
    :type pod: kubernetes.client.V1Pod
    :return: A dictionary containing the status code and logs.
    :rtype: dict
    """
    # try:
    #     pod_logs = core_api.read_namespaced_pod_log(pod.metadata.name, pod.metadata.namespace)
    # except Exception as e:
    #     print(f"Error in getting get_pods_logs: {e}")
    #     return

    conditions = pod.status.conditions
    no_logs = "The last conditions your pods went through were: \n"

    for idx, condition in enumerate(conditions):
        last_tr_time: datetime = condition.last_transition_time
        no_logs += (f"{idx + 1}. {last_tr_time.isoformat()} - Reason: `{condition.reason}`"
                    f" \t Type: `{condition.type}`\n")

    no_logs += "---- \n"

    container_statuses = pod.status.container_statuses
    no_logs += "Containers launched under your pods with their stats: \n"
    for idx, status in enumerate(container_statuses):
        no_logs += (f"{idx + 1}. Container {status.container_id} has restarted:"
                    f" {status.restart_count} number of times.\n")

    return {
        'status': 500,
        'logs': no_logs
    }


def commit_notified(conformitron_cm: V1ConfigMap) -> bool:
    """
    Checks if a specific commit has already been notified.

    :param conformitron_cm: V1ConfigMap object representing the Conformitron ConfigMap
    :return: boolean value indicating if the commit has already been notified
    """
    notified_cm_name = 'notified-prs'

    commit_storage = CommitStorage(core_api, 'observer')
    cm_ns = conformitron_cm.data['Namespace']
    cm_commit_hash = conformitron_cm.data['commitHash']

    # This will always return a CM
    observer_config = commit_storage.create_if_not_exist_or_get(notified_cm_name, {})

    pre_existing_config = observer_config.data
    try:
        if pre_existing_config[cm_ns] == cm_commit_hash:
            # we've already commented on that specific hash
            return True
    except (KeyError, TypeError):
        # we've never seen the namespace
        if pre_existing_config:
            pre_existing_config[cm_ns] = cm_commit_hash
        else:
            pre_existing_config = {
                f"{cm_ns}": f"{cm_commit_hash}"
            }

        commit_storage.update_configmap(notified_cm_name, pre_existing_config)
        return False
    else:
        # we haven't commented on the current hash
        pre_existing_config[cm_ns] = cm_commit_hash
        commit_storage.update_configmap(notified_cm_name, pre_existing_config)
        return False


def find_namespace_configmap(ns_name: str) -> V1ConfigMap | None:
    """
    :param ns_name: The name of the namespace to search for the configmap in.
    :return: The first usable configmap found in the specified namespace with the label "bot=conformitron",
        or None if none are found.

    """
    usable_config_maps = core_api.list_namespaced_config_map(ns_name, label_selector="bot=conformitron")

    if usable_config_maps.items:
        # There's def items in the usable config maps
        if not commit_notified(usable_config_maps.items[0]):
            return usable_config_maps.items[0]
        else:
            return None
    else:
        raise AssertionError(f"Looks like there isn't a configuration for this ns: {ns_name}")


def build_report(risk_info):
    """
    :param risk_info: A list containing information about deployment risks. Each element in the list should be a
        dictionary with the following keys:
        - 'ns': The name of the namespace.
        - 'deployment': The name of the deployment or 'raw_pod' if it is a raw pod.
        - 'risks': A list of dictionaries, where each dictionary represents a specific risk associated with a pod. Each
            dictionary should have the following keys:
            - 'pod': The pod object.
    :return: A dictionary containing the namespace, associated issue number, and reports of deployment risks.
    """

    try:
        if risk_info:
            issue_number = find_namespace_configmap(risk_info[0]['ns'])

            if not issue_number:
                return
        else:
            return
        print(f"Found associated issue number: {issue_number}")
    except Exception as e:
        print(f"ConfigMap returned null: {e}")
        return

    namespace_report = {
        'ns': risk_info[0]['ns'],
        'issue_number': issue_number.data["prNumber"],
        'reports': []
    }

    for risk in risk_info:
        if risk['deployment'] == "raw_pod":
            report = f"Looks like you're using a raw pod: `{risk['pod'].metadata.name}`. Please stop doing that. \n"

            namespace_report["reports"].append(report)
        else:
            deployment = risk['deployment'].metadata.name

            report = f"Looks like your deployment `{deployment}` is failing.\n" \
                     f"Specifically, it looks like these pods are failing: \n"
            for pod_risk in risk["risks"]:
                report += f"* Pod: `{pod_risk['pod'].metadata.name}` with the error listed below.\n"

            report += '---- \n'

            for pod_risk in risk["risks"]:
                pod_logs = f"{get_pod_logs(pod_risk['pod'])['logs']} ---- \n"
                report += f"Logs for pod `{pod_risk['pod'].metadata.name}`: \n {pod_logs}"

            namespace_report["reports"].append(report)

    return namespace_report


def add_comment_to_pr(report):
    """
    Adds a comment to a pull request on GitHub.

    :param report: The report containing information about the comment to be added.
                   It should have the following structure:
                   {
                       "ns": str,  # The namespace of the pull request
                       "issue_number": int,  # The issue number of the pull request
                       "reports": [str]  # A list of strings representing the reports to be added
                   }
    :return: None
    """
    gh_api = GhApi()
    # report
    #   ns: str
    #   issue_number: number
    #   reports: [ string ]
    if report is None:
        return {}

    print(report)

    try:
        comment_response = gh_api.issues.create_comment(
            owner=repo_owner,
            repo=repo,
            issue_number=report["issue_number"],  # namespace.metadata.name derived from PR and namespace configmap
            body="---- New Deployment Report: \n".join(report["reports"])
        )
    except Exception as e:
        # If create_comment fails, drop the fact that we ever commented on it, so in the next run it should flair
        print(f"GH_Error: {e}")
        commit_store = CommitStorage(core_api, 'observer')
        observer_cm_data = commit_store.get_configmap('notified-prs').data
        observer_cm_data[report['ns']] = ""
        commit_store.update_configmap('notified-prs', observer_cm_data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="KubeObserverBot")
    parser.add_argument("-l", action='store_true')
    args = parser.parse_args()
    if args.l:
        print("loading kubeconfig")
        from dotenv import load_dotenv

        load_dotenv(".dev.env")
        config.load_kube_config()

        repo = os.environ['REPO']
        repo_owner = os.environ['OWNER']
    else:
        print("loading incluster config")
        repo_owner = os.environ['OWNER']
        repo = os.environ['REPO']

        config.load_incluster_config()

    apps_api = client.AppsV1Api()
    core_api = client.CoreV1Api()

    run_observer()
