from __future__ import annotations

import asyncio
import typing as t
import shlex
import logging
from asyncio import subprocess


LOGGER = logging.getLogger()


class CLIOptions:
    def __init__(self, **kwargs: t.Any) -> None:
        self._options_dict: dict[str, t.Any] = {}
        options: list[str] = []

        for key, value in kwargs.items():
            if value is None:
                value = ""
            self._options_dict[key] = value
            option_name = "--" + key.replace("_", "-")
            if isinstance(value, bool):
                if value:
                    options.append(option_name)
            else:
                options.extend((option_name, shlex.quote(str(value))))
        self._options_str = " ".join(options)

    def add(self, **kwargs: t.Any) -> CLIOptions:
        new_options = dict(**self._options_dict)
        new_options.update(**kwargs)
        return CLIOptions(**new_options)

    # @property
    # def masked(self) -> CLIOptions:
    #     if "password" not in self._options_dict:
    #         return self
    #     new_options = dict(**self._options_dict)
    #     new_options["password"] = "*****"
    #     return CLIOptions(**new_options)

    def __str__(self) -> str:
        return self._options_str

    def __repr__(self) -> str:
        return str(self)


class BaseCLIRunner:
    def __init__(self, options: CLIOptions | None = None) -> None:
        # TODO: do we need it in class field?
        self._cli_options = options or CLIOptions()

    async def _run(
        self,
        cmd: str,
        input_text: str = "",
        capture_stdout: bool = False,
        capture_stderr: bool = False,
    ) -> tuple[subprocess.Process, str, str]:
        input_bytes = input_text.encode("utf-8")
        LOGGER.debug(f"Command '{cmd}'")
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdin=subprocess.PIPE if input_bytes else None,
            stdout=subprocess.PIPE if capture_stdout else subprocess.DEVNULL,
            stderr=subprocess.PIPE if capture_stderr else subprocess.DEVNULL,
        )
        stdout, stderr = await process.communicate(input_bytes or None)
        stdout_text = (stdout or b"").decode("utf-8")
        stderr_text = (stderr or b"").decode("utf-8")
        LOGGER.debug(
            f"Command output for '{cmd[:20]}...': {stdout_text=} {stderr_text=}"
        )
        return (process, stdout_text, stderr_text)
