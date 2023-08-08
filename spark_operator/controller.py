from __future__ import annotations

import logging
import typing as t

from .helm_client import (
    HelmClient,
    Release,
    SPARK_OPERATOR_CHART_NAME,
)
from .kube_client import KubeClient
from .base_client import CLIOptions


LOGGER = logging.getLogger()


class SparkOperatorController:
    def __init__(self, global_cli_options: CLIOptions | None = None) -> None:
        self._helm_client = HelmClient(global_cli_options)
        self._kube_client = KubeClient(global_cli_options)

    async def list_releases(self, namespace: str) -> list[Release]:
        return await self._helm_client.list_releases(namespace)

    async def get_kubectl_config(self, namespace: str) -> str:
        releases = await self._helm_client.list_releases(namespace)
        assert releases, f"No releases found in {namespace=}"
        assert len(releases) == 1, f"Found more than one release in {namespace=}"
        release = releases[0]

        release_values = await self._helm_client.get_release_values(
            release.name, release.namespace
        )

        extra_perms = release_values["rbac"]["extraPermissions"]
        if not extra_perms["enabled"]:
            raise ValueError(
                "Extra RBAC was not enabled during operator installation, "
                "cannot generate kubectl config."
            )
        sa_name = extra_perms["serviceAccountName"]
        return await self._kube_client.get_kubect_config(sa_name, release.namespace)

    async def install(
        self, namespace: str, release_name: str, values: dict[str, t.Any]
    ) -> Release:
        # Verify there is no other operators installed in the namespace
        # In future, we probably will support updating installation
        releases = await self.list_releases(namespace)
        if releases:
            LOGGER.error(
                f"Found existing installation in {namespace=}:"
                f"{[r.name for r in releases]}"
            )
            raise RuntimeError(f"Found existing installation in {namespace=}")

        # Create a new release
        await self._helm_client.upgrade(
            release_name=release_name,
            chart_name=SPARK_OPERATOR_CHART_NAME,
            namespace=namespace,
            values=values,
            install=True,
            wait=True,
        )
        releases = await self.list_releases(namespace)
        assert (
            len(releases) == 1
        ), "More than one Spark operator found after installation"
        return releases[0]
