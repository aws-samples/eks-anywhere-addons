import os
import argparse
from datetime import datetime

import kubernetes.client
from config_data import *
from ghapi.all import GhApi
from urllib.error import HTTPError
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
    This method retrieves at-risk pods in a given namespace.

    :param ns: The namespace in which to search for at-risk pods.
    :type ns: V1Namespace
    :return: A list of at-risk pods.
    :rtype: list
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
    Get at risk deployments based on the provided risk report.

    :param risk_report: A list of dictionaries representing the risk report.
    :return: A list of dictionaries representing the at risk deployments.
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
        pod_owner = risk["pod"].metadata.owner_references[0].name

        if pod_owner in at_risk_replica_sets:
            at_risk_replica_sets[pod_owner].append(risk)
        else:
            at_risk_replica_sets[pod_owner] = [risk]

    for replica_set in at_risk_replica_sets:
        # Gets the replica set associated with the at risk pod
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
    Get the logs and status information for a given pod.

    :param pod: The pod object for which to retrieve logs and status.
    :type pod: kubernetes.client.V1Pod
    :return: A dictionary containing the status code and the logs.
             The status code will be 500 and the logs will be a string
             representation of the pod's status and container statistics.
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
    :param conformitron_cm: A V1ConfigMap object containing the necessary information about the commit.
    :return: A boolean value indicating whether a comment has already been made for the commit.

    This method checks if a comment has already been made for a specific commit in a specific namespace.
    It uses a CommitStorage object to store and update the information.

    Example usage:
    ```
    conformitron_cm = V1ConfigMap()  # Instantiate the V1ConfigMap object with the necessary data
    result = commit_notified(conformitron_cm)  # Call the commit_notified method
    print(result)  # Output: False (indicating that a comment has not been made for the commit)
    ```
    """
    notified_cm_name = 'notified-prs'

    commit_storage = CommitStorage('observer')
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
    :param ns_name: The name of the namespace to search for the configuration map.
    :return: The first usable configuration map found in the specified namespace with the label "bot=conformitron".
        Returns `None` if no usable configuration map is found.
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
    :param risk_info: list of dictionaries containing risk information
    :return: dictionary containing the report for each namespace

    This method builds a report for each namespace based on the provided risk information.
    The risk information should be in the following format:

    ```
    risk_info = [
        {
            'deployment': V1Deployment,
            'ns': str,
            'risks': [
                {
                    'ns': str,
                    'pod': V1Pod,
                    'reason_type': Any,
                    'reason': type of reason_type
                },
                ...
            ]
        },
        ...
    ]
    ```

    The method retrieves the issue number from the namespace's configmap and creates a report for each risk.
    Each risk is represented in the report as a failing deployment and a list of pods associated with that deployment.
    The report also includes the logs for each pod.
    The final report is returned as a dictionary with the following structure:

    ```
    namespace_report = {
        'ns': str (namespace),
        'issue_number': str (issue number from configmap),
        'reports': [
            str (report for each risk),
            ...
        ]
    }
    ```
    """

    try:
        if risk_info:
            issue_number = find_namespace_configmap(risk_info[0]['ns'])

            if not issue_number:
                return
        else:
            return
    except Exception as e:
        print(f"ConfigMap returned null: {e}")
        return

    namespace_report = {
        'ns': risk_info[0]['ns'],
        'issue_number': issue_number.data["prNumber"],
        'reports': []
    }

    for risk in risk_info:
        report = f"Looks like your deployment `{risk['deployment'].metadata.name}` is failing.\n" \
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
    Adds a comment to a pull request with the given report.

    :param report: A dictionary that contains the following:
                    - "issue_number": The issue number of the pull request.
                    - "reports": A list of strings representing the deployment reports.
    :return: A dictionary with the response from the GitHub API.
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
        # TODO: If create_comment fails, drop the fact that we ever commented on it, so in the next run it should flair
        print(f"GH_Error: {e}")
        commit_store = CommitStorage('observer')
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
