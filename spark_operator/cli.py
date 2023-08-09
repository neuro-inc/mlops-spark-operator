from __future__ import annotations

import functools
import logging
import typing as t
import sys
from asyncio import iscoroutinefunction, run
from importlib.metadata import version

import click

from .controller import SparkOperatorController

_T = t.TypeVar("_T")


def wrap_async() -> t.Callable[[t.Callable[..., t.Awaitable[_T]]], t.Callable[..., _T]]:
    def _decorator(callback: t.Callable[..., t.Awaitable[_T]]) -> t.Callable[..., _T]:
        assert iscoroutinefunction(callback)

        @functools.wraps(callback)
        def wrapper(*args: t.Any, **kwargs: t.Any) -> _T:
            return run(callback(*args, **kwargs))

        return wrapper

    return _decorator


def setup_logging(verbosity: int) -> None:
    if verbosity < -1:
        loglevel = logging.CRITICAL
    elif verbosity == -1:
        loglevel = logging.ERROR
    elif verbosity == 0:
        loglevel = logging.WARNING
    elif verbosity == 1:
        loglevel = logging.INFO
    else:
        loglevel = logging.DEBUG

    logging.basicConfig(
        level=loglevel,
        format="%(module)s.%(funcName)s#%(lineno)d: %(message)s",
    )


@click.group()
@click.version_option(
    version=version("mlops-spark-operator"),
    message="spark-operator package version: %(version)s",
)
@click.option(
    "-v",
    "--verbose",
    count=True,
    type=int,
    default=0,
    help="Give more output. Option is additive, and can be used up to 2 times.",
)
def main(verbose: int) -> None:
    setup_logging(verbose)
    pass


@main.command()
@click.option(
    "-n",
    "--namespace",
    type=str,
    default="all",
    show_default=True,
    help="Show operators in specified namespace, or all namespaces.",
)
@wrap_async()
async def list(namespace: str) -> None:
    "Listing Spark operator installations in cluster"
    try:
        releases = await SparkOperatorController().list_releases(namespace)
    except Exception as e:
        click.echo(str(e), err=True)
    for release in releases:
        click.echo(str(release))


@main.command()
@click.option(
    "--release-name",
    type=str,
    default="platform-spark",
    show_default=True,
    help="Helm chart release name.",
)
@click.option(
    "-s",
    "--set",
    type=(str, str),
    multiple=True,
    help="Set chart values",
)
@click.option(
    "-o",
    "--output",
    type=click.File("w"),
    default=sys.stdout,
    help="Generate Kubectl for installed Spark operator",
)
@click.argument(
    "namespace",
    required=True,
)
@wrap_async()
async def install(
    release_name: str | None,
    output: t.IO,
    set: list[tuple[str, str]],
    namespace: str | None,
) -> None:
    """Install new instance of Spark operator"""
    controller = SparkOperatorController()
    try:
        release = await controller.install(namespace, release_name, values=dict(set))
        click.echo(f"Installed Spark operator into {namespace} namespace")
    except Exception as e:
        click.echo(f"Exception while installing Spark operator: {str(e)}", err=True)

    try:
        kubectl = await controller.get_kubectl_config(release.namespace)
        click.echo(kubectl, file=output)
        click.echo(f"Generated Kubectl config dumped into '{output.name}'")
    except Exception as e:
        click.echo(f"Exception while generating kubectl: {str(e)}", err=True)


@main.command()
@click.argument(
    "namespace",
    required=True,
)
@wrap_async()
async def uninstall(namespace: str) -> None:
    "Uninstall instance of spark operator"
    controller = SparkOperatorController()
    try:
        await controller.uninstall(namespace)
        click.echo(f"Spark operator was removed from the namespace {namespace}")
    except Exception as e:
        click.echo(str(e))


@main.command()
@click.option(
    "-n",
    "--namespace",
    type=str,
    default="all",
    show_default=True,
    help="Generates kubectl config for operator in specified namespace.",
)
@click.option(
    "-o",
    "--output",
    type=click.File("w"),
    default=sys.stdout,
    show_default=True,
    help="Filename, where kubectl will be dumped.",
)
@wrap_async()
async def get_kubectl_config(namespace: str | None, output: click.File) -> None:
    "Generates and shows kubectl config for a given Spark operator installation"
    controller = SparkOperatorController()
    try:
        kubectl = await controller.get_kubectl_config(namespace)
        click.echo(kubectl, file=output)
    except Exception as e:
        click.echo(str(e), err=True)
