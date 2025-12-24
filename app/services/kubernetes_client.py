"""Kubernetes client for service diagnostics and monitoring."""

import os
from typing import Any

from kubernetes import client, config
from kubernetes.client import ApiException

from app.core.config import Settings


class KubernetesClient:
    """Client for Kubernetes diagnostics and pod management."""

    def __init__(self, settings: Settings) -> None:
        """
        Initialize Kubernetes client.

        Args:
            settings: Application settings
        """
        if settings.k8s_in_cluster:
            config.load_incluster_config()
        else:
            config_file = os.path.expanduser(settings.kubeconfig_path)
            config.load_kube_config(config_file=config_file)

        self.core_v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()

    async def get_pod_status(self, namespace: str, pod_name: str) -> dict[str, Any]:
        """
        Get pod status and health information.

        Args:
            namespace: Kubernetes namespace
            pod_name: Pod name

        Returns:
            Dictionary with pod status details

        Raises:
            ApiException: If pod not found or API error
        """
        try:
            pod = self.core_v1.read_namespaced_pod(name=pod_name, namespace=namespace)
            return {
                "name": pod.metadata.name,
                "namespace": pod.metadata.namespace,
                "phase": pod.status.phase,
                "conditions": [
                    {"type": c.type, "status": c.status, "reason": c.reason}
                    for c in (pod.status.conditions or [])
                ],
                "container_statuses": [
                    {
                        "name": c.name,
                        "ready": c.ready,
                        "restart_count": c.restart_count,
                        "state": str(c.state),
                    }
                    for c in (pod.status.container_statuses or [])
                ],
            }
        except ApiException as e:
            raise Exception(f"Failed to get pod status: {e}") from e

    async def get_pod_logs(
        self,
        namespace: str,
        pod_name: str,
        tail_lines: int = 100,
    ) -> list[str]:
        """
        Get pod logs.

        Args:
            namespace: Kubernetes namespace
            pod_name: Pod name
            tail_lines: Number of recent log lines to retrieve

        Returns:
            List of log lines

        Raises:
            ApiException: If pod not found or API error
        """
        try:
            logs = self.core_v1.read_namespaced_pod_log(
                name=pod_name,
                namespace=namespace,
                tail_lines=tail_lines,
            )
            return logs.split("\n")
        except ApiException as e:
            raise Exception(f"Failed to get pod logs: {e}") from e

    async def list_pods_in_namespace(self, namespace: str) -> list[dict[str, Any]]:
        """
        List all pods in a namespace.

        Args:
            namespace: Kubernetes namespace

        Returns:
            List of pod information dictionaries

        Raises:
            ApiException: If namespace not found or API error
        """
        try:
            pods = self.core_v1.list_namespaced_pod(namespace=namespace)
            return [
                {
                    "name": pod.metadata.name,
                    "phase": pod.status.phase,
                    "ready": sum(
                        1 for c in (pod.status.container_statuses or []) if c.ready
                    ),
                    "total": len(pod.status.container_statuses or []),
                    "restarts": sum(
                        c.restart_count for c in (pod.status.container_statuses or [])
                    ),
                }
                for pod in pods.items
            ]
        except ApiException as e:
            raise Exception(f"Failed to list pods: {e}") from e

    async def get_resource_usage(
        self,
        namespace: str,
        pod_name: str,
    ) -> dict[str, Any]:
        """
        Get pod resource usage metrics.

        Args:
            namespace: Kubernetes namespace
            pod_name: Pod name

        Returns:
            Dictionary with resource usage metrics

        Note:
            Requires metrics-server to be installed in the cluster
        """
        try:
            # This would require metrics-server API
            # For now, return placeholder
            return {
                "cpu_usage": "N/A - Requires metrics-server",
                "memory_usage": "N/A - Requires metrics-server",
            }
        except Exception as e:
            return {"error": str(e)}

    async def restart_pod(self, namespace: str, pod_name: str) -> dict[str, str]:
        """
        Restart a pod by deleting it (StatefulSet/Deployment will recreate).

        Args:
            namespace: Kubernetes namespace
            pod_name: Pod name

        Returns:
            Dictionary with restart status

        Raises:
            ApiException: If pod not found or API error
        """
        try:
            self.core_v1.delete_namespaced_pod(
                name=pod_name,
                namespace=namespace,
                body=client.V1DeleteOptions(),
            )
            return {
                "status": "success",
                "message": f"Pod {pod_name} is being restarted",
            }
        except ApiException as e:
            raise Exception(f"Failed to restart pod: {e}") from e
