from __future__ import annotations

import json
import base64
from dataclasses import dataclass
from textwrap import dedent

from .base_client import BaseCLIRunner


@dataclass(frozen=True)
class KubeClusterInfo:
    name: str
    control_plane_url: str


@dataclass(frozen=True)
class ServiceAccountInfo:
    name: str
    namespace: str
    token: str
    certificate_authority_data: str


KUBECONFIG_TEMPLATE = dedent(
    """\
    apiVersion: v1
    kind: Config
    clusters:
    - name: {cluster_info.name}
      cluster:
        certificate-authority-data: {sa_info.certificate_authority_data}
        server: {cluster_info.control_plane_url}
    contexts:
    - name: {sa_info.name}@{cluster_info.name}
      context:
        cluster: {cluster_info.name}
        namespace: {sa_info.namespace}
        user: {sa_info.name}
    users:
    - name: {sa_info.name}
      user:
        token: {sa_info.token}
    current-context: {sa_info.name}@{cluster_info.name}
"""
)


class KubeClient(BaseCLIRunner):
    async def _get_current_kubeconfig(self) -> KubeClusterInfo:
        base_opts = self._cli_options.add(output="json", minify=True)

        cmd = f"kubectl config view {base_opts}"
        _, stdout, _ = await self._run(cmd, capture_stdout=True)
        cfg = json.loads(stdout)

        current_cluster = cfg["clusters"][0]
        cluster_name = current_cluster["name"]
        control_plane_url = current_cluster["cluster"]["server"]
        return KubeClusterInfo(name=cluster_name, control_plane_url=control_plane_url)

    async def _get_service_account_data(
        self, sa_name: str, namespace: str
    ) -> ServiceAccountInfo:
        base_opts = self._cli_options.add(namespace=namespace)

        secret_name_opts = base_opts.add(output="jsonpath={.secrets[0].name}")
        secret_name_cmd = f"kubectl get serviceAccount {sa_name} {secret_name_opts}"
        _, secret_name, _ = await self._run(secret_name_cmd, capture_stdout=True)

        if not secret_name:
            # We seem to be using a newer version of k8s,
            # which does not create SA secrets automatically
            # However, we create a dedicated secret for SA in helm squal to SA name
            secret_name = sa_name

        sa_secret_opts = base_opts.add(output="json")
        get_sa_secret_cmd = f"kubectl get secret {secret_name} {sa_secret_opts}"
        _, stdout, _ = await self._run(get_sa_secret_cmd, capture_stdout=True)
        secret = json.loads(stdout)
        ca_data = secret["data"]["ca.crt"]
        token = base64.b64decode(secret["data"]["token"], validate=True).decode()

        return ServiceAccountInfo(sa_name, namespace, token, ca_data)

    async def get_kubect_config(
        self,
        service_account_name: str,
        namespace: str,
    ) -> str:
        cluster_info = await self._get_current_kubeconfig()
        service_account_info = await self._get_service_account_data(
            service_account_name, namespace
        )
        return KUBECONFIG_TEMPLATE.format(
            cluster_info=cluster_info, sa_info=service_account_info
        )

    async def delete(
        self,
        res_type: str,
        res_name: str,
        namespace: str | None = None,
    ) -> None:
        cli_opts = self._cli_options
        if namespace:
            cli_opts = cli_opts.add(namespace=namespace)
        cmd = f"kubectl delete {res_type}/{res_name} {cli_opts}"
        await self._run(cmd)
