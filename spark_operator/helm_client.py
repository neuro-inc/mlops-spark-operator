from __future__ import annotations

import enum
import json
import logging
from dataclasses import dataclass
from typing import Any

from .base_client import BaseCLIRunner

import yaml

logger = logging.getLogger()


SPARK_OPERATOR_CHART_NAME = "charts/spark-operator"


class HelmException(Exception):
    pass


class ReleaseStatus(enum.Enum):
    UNKNOWN = "unknown"
    DEPLOYED = "deployed"
    UNINSTALLED = "uninstalled"
    SUPERSEDED = "superseded"
    FAILED = "failed"
    UNINSTALLING = "uninstalling"
    PENDINGINSTALL = "pending-install"
    PENDINGUPGRADE = "pending-upgrade"
    PENDINGROLLBACK = "pending-rollback"


@dataclass(frozen=True)
class Release:
    name: str
    namespace: str
    chart: str
    status: ReleaseStatus

    @classmethod
    def parse(cls, payload: dict[str, Any]) -> Release:
        return cls(
            name=payload["name"],
            namespace=payload["namespace"],
            chart=payload["chart"],
            status=ReleaseStatus(payload["status"]),
        )


class HelmClient(BaseCLIRunner):
    async def list_releases(
        self, namespace: str | None = None, labels: tuple[str] = ()
    ) -> list[Release]:
        if not namespace or namespace.lower() == "all":
            options = self._cli_options.add(all_namespaces=True, output="json")
        else:
            options = self._cli_options.add(namespace=namespace, output="json")
        if labels:
            options = options.add(selector=",".join(labels))
        cmd = f"helm list {options}"
        logger.info("Running %s", cmd)
        process, stdout_text, stderr_text = await self._run(
            cmd, capture_stdout=True, capture_stderr=True
        )
        if process.returncode != 0:
            logger.error("Failed to list releases: %s", stderr_text.strip())
            raise HelmException("Failed to list releases")
        if not stdout_text:
            logger.info("Received empty response")
            return None
        logger.debug("Received response %s", stdout_text)
        releases = json.loads(stdout_text)
        return [Release.parse(r) for r in releases]

    async def get_release_values(
        self, release_name: str, namespace: str
    ) -> dict[str, Any] | None:
        options = self._cli_options.add(namespace=namespace, output="json", all=True)
        cmd = f"helm get values {release_name} {options}"
        logger.info("Running %s", cmd)
        process, stdout_text, stderr_text = await self._run(
            cmd,
            capture_stdout=True,
            capture_stderr=True,
        )
        if process.returncode != 0:
            if "not found" in stdout_text:
                logger.info("Release %s not found", release_name)
                return None
            logger.error("Failed to get values: %s", stderr_text.strip())
            raise HelmException("Failed to get values")
        logger.debug("Received response %s", stdout_text)
        return json.loads(stdout_text)

    async def upgrade(
        self,
        release_name: str,
        chart_name: str,
        namespace: str,
        *,
        version: str = "",
        values: dict[str, Any] | None = None,
        install: bool = False,
        wait: bool = False,
        timeout_s: int = 600,
        labels: tuple[str] = (),
    ) -> None:
        options = self._cli_options.add(
            version=version or None,
            values="-",
            install=install,
            wait=wait,
            timeout=f"{timeout_s}s",
            namespace=namespace,
            create_namespace=True,
            labels=f'{",".join(labels)}',
        )
        cmd = f"helm upgrade {release_name} {chart_name} {options}"
        logger.info(f"Running {cmd}")
        values_yaml = yaml.safe_dump(values or {})
        process, _, stderr_text = await self._run(
            cmd,
            values_yaml,
            capture_stdout=False,
            capture_stderr=True,
        )
        if process.returncode != 0:
            logger.error(
                "Failed to upgrade helm release %s: %s",
                release_name,
                stderr_text.strip(),
            )
            raise HelmException(f"Failed to upgrade release {release_name}")
        logger.info("Upgraded helm release %s", release_name)

    async def delete(
        self,
        release_name: str,
        namespace: str,
        wait: bool = False,
        timeout_s: int = 600,
    ) -> None:
        options = self._cli_options.add(
            wait=wait,
            namespace=namespace,
            timeout=f"{timeout_s}s" if timeout_s else None,
        )
        cmd = f"helm delete {release_name} {options}"
        logger.info("Running %s", cmd)
        process, _, stderr_text = await self._run(
            cmd,
            capture_stdout=False,
            capture_stderr=True,
        )
        if process.returncode == 0:
            logger.info("Deleted helm release %s", release_name)
        else:
            if "not found" in stderr_text:
                logger.info("Helm release %s has already been deleted", release_name)
            else:
                logger.error(
                    "Failed to delete helm release %s: %s",
                    release_name,
                    stderr_text.strip(),
                )
                raise HelmException(f"Failed to delete release {release_name}")
