#!/usr/bin/env python3
"""Small read-only MailWhere CLI provider wrapper for where-skills.

This wrapper does not read MailWhere SQLite directly. It only locates and invokes
MailWhere.Cli with --json, then returns the provider JSON envelope.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

PROVIDER = "MailWhere"
CONTRACT_VERSION = "v1"
ENV_CLI_PATH = "MAILWHERE_CLI_PATH"
ENV_DB_PATH = "MAILWHERE_DB_PATH"
CLI_NAMES = ("MailWhere.Cli.exe", "MailWhere.Cli")
DATA_COMMANDS = {"export", "list-tasks", "list-review-candidates"}


class MailWhereProviderError(RuntimeError):
    """Raised when MailWhere.Cli cannot be resolved or returns invalid output."""


@dataclass(frozen=True)
class MailWhereCliConnection:
    source: str
    cli_path: str


def _existing_file(path: str | Path) -> Path | None:
    candidate = Path(path).expanduser()
    return candidate if candidate.is_file() else None


def _path_from_env(env: Mapping[str, str]) -> MailWhereCliConnection | None:
    value = env.get(ENV_CLI_PATH, "").strip()
    if not value:
        return None
    path = _existing_file(value)
    if path is None:
        raise MailWhereProviderError(f"MAILWHERE_CLI_PATH does not point to a file: {value}")
    return MailWhereCliConnection(source=f"env:{ENV_CLI_PATH}", cli_path=str(path))


def _path_from_path_env() -> MailWhereCliConnection | None:
    for name in CLI_NAMES:
        resolved = shutil.which(name)
        if resolved:
            return MailWhereCliConnection(source="PATH", cli_path=resolved)
    return None


def _mailwhere_process_paths(timeout: float = 2.0) -> list[Path]:
    if os.name != "nt":
        return []

    command = [
        "powershell",
        "-NoProfile",
        "-Command",
        "Get-Process -Name MailWhere -ErrorAction SilentlyContinue | "
        "Where-Object { $_.Path } | Select-Object -First 3 -ExpandProperty Path",
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return []

    if result.returncode != 0:
        return []
    return [Path(line.strip()) for line in result.stdout.splitlines() if line.strip()]


def _path_from_running_process(timeout: float = 2.0) -> MailWhereCliConnection | None:
    for app_path in _mailwhere_process_paths(timeout=timeout):
        for name in CLI_NAMES:
            candidate = app_path.with_name(name)
            if candidate.is_file():
                return MailWhereCliConnection(source="running-process", cli_path=str(candidate))
    return None


def discover_mailwhere_cli(*, env: Mapping[str, str] | None = None, timeout: float = 2.0) -> MailWhereCliConnection:
    """Locate MailWhere.Cli in preference order."""

    values = env if env is not None else os.environ
    return (
        _path_from_env(values)
        or _path_from_path_env()
        or _path_from_running_process(timeout=timeout)
        or _raise_missing_cli()
    )


def _raise_missing_cli() -> MailWhereCliConnection:
    raise MailWhereProviderError(
        "MailWhere.Cli was not found. Start from a portable folder containing MailWhere.Cli.exe, "
        "add it to PATH, or set MAILWHERE_CLI_PATH."
    )


def _validate_envelope(payload: Any) -> None:
    if not isinstance(payload, Mapping):
        raise MailWhereProviderError("MailWhere.Cli returned a non-object JSON payload")
    provider = payload.get("provider")
    contract = payload.get("contract_version")
    if provider != PROVIDER:
        raise MailWhereProviderError(f"Unexpected provider from MailWhere.Cli: {provider!r}")
    if contract != CONTRACT_VERSION:
        raise MailWhereProviderError(f"Unsupported MailWhere contract: {contract!r}")


def _command_args(command: str, *, db: str | None = None, options: Sequence[str] = ()) -> list[str]:
    args = [command, "--json"]
    if db and command in DATA_COMMANDS:
        args.extend(["--db", db])
    args.extend(options)
    return args


def run_mailwhere_cli(
    command: str,
    *,
    options: Sequence[str] = (),
    env: Mapping[str, str] | None = None,
    timeout: float = 10.0,
) -> Any:
    values = env if env is not None else os.environ
    connection = discover_mailwhere_cli(env=values, timeout=timeout)
    db = values.get(ENV_DB_PATH, "").strip() or None
    args = [connection.cli_path, *_command_args(command, db=db, options=options)]

    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise MailWhereProviderError(f"Could not run MailWhere.Cli: {connection.cli_path}") from exc

    stdout = result.stdout.strip()
    if not stdout:
        raise MailWhereProviderError(f"MailWhere.Cli returned no JSON output; exit code {result.returncode}")
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise MailWhereProviderError("MailWhere.Cli returned invalid JSON") from exc

    _validate_envelope(payload)
    if result.returncode not in {0, 2}:
        code = payload.get("code") if isinstance(payload, Mapping) else None
        raise MailWhereProviderError(f"MailWhere.Cli failed with exit code {result.returncode}: {code}")
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Locate and invoke MailWhere.Cli read-only JSON provider.")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("discover", help="Print resolved MailWhere.Cli path.")
    for command in ["health", "manifest", "export", "list-tasks", "list-review-candidates"]:
        sub = subparsers.add_parser(command, help=f"Run MailWhere.Cli {command} --json.")
        sub.add_argument("provider_args", nargs=argparse.REMAINDER, help="Additional arguments passed after --json.")
    parser.add_argument("--timeout", type=float, default=10.0, help="CLI timeout in seconds.")
    return parser


def _print_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    command = args.command or "discover"
    try:
        if command == "discover":
            _print_json(asdict(discover_mailwhere_cli(timeout=args.timeout)))
        else:
            provider_args = getattr(args, "provider_args", [])
            if provider_args[:1] == ["--"]:
                provider_args = provider_args[1:]
            _print_json(run_mailwhere_cli(command, options=provider_args, timeout=args.timeout))
    except MailWhereProviderError as exc:
        print(f"mailwhere_provider: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
