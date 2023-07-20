import os
from ghapi.all import GhApi
from kubernetes import client, config

gh_api = GhApi()

config.load_incluster_config()
kube_api = client.CoreV1Api()

# https://github.com/kubernetes-client/python
# Using the kubernetes client to get the exact information
# we need to write the feedback bot
def run_observer():
    print("Listing all pods along with if they're active or not")

    all_pods = kube_api.list_pod_for_all_namespaces(watch=False)

    for i in all_pods:
        print("%s/t%s/t%s" %
              (i.status.deployed, i.metadata.namespace, i.metadata.name))

    # Select pods that have deployed number < requested number
    # Send that data to get_pods_in_namespace ??
    pass

def get_pods_in_namespace():
    pass

def get_namespace_definition():
    pass

def add_comment_to_pr():
    pass


if __name__ == "__main__":
    run_observer()
