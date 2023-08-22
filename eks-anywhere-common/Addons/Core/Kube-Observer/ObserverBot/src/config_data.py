from kubernetes import client, config


class CommitStorage:
    def __init__(self, namespace):
        config.load_kube_config()
        self.namespace = namespace
        self.api_instance = client.CoreV1Api()

    def create_configmap(self, name, data):
        body = client.V1ConfigMap(
            api_version="v1",
            kind="ConfigMap",
            metadata=client.V1ObjectMeta(name=name),
            data=data
        )
        return self.api_instance.create_namespaced_config_map(namespace=self.namespace, body=body)

    def create_if_not_exist_or_get(self, name, data) -> client.V1ConfigMap | None:
        cm = self.get_configmap(name)
        if not self.get_configmap(name):
            body = client.V1ConfigMap(
                api_version="v1",
                kind="ConfigMap",
                metadata=client.V1ObjectMeta(name=name),
                data=data
            )
            self.create_configmap(name, data)
        else:
            return cm

    def get_configmap(self, name):
        return self.api_instance.read_namespaced_config_map(name=name, namespace=self.namespace)

    def update_configmap(self, name, data) -> None:
        body = client.V1ConfigMap(
            api_version="v1",
            kind="ConfigMap",
            metadata=client.V1ObjectMeta(name=name),
            data=data
        )
        self.api_instance.replace_namespaced_config_map(name=name, namespace=self.namespace, body=body)

    def delete_configmap(self, name):
        body = client.V1DeleteOptions()
        return self.api_instance.delete_namespaced_config_map(name=name, namespace=self.namespace, body=body)
