#!/usr/bin/env python3
"""Small read-only OfficeWhere provider client for where-skills.

Discovery order:
1. OFFICEWHERE_BASE_URL override.
2. OfficeWhere app-data discovery file, Windows LocalAppData first.
3. Legacy Windows Roaming discovery file.
4. Development default http://127.0.0.1:18765.
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import os
import platform as platform_module
import posixpath
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

PROVIDER = "OfficeWhere"
CONTRACT_VERSION = "v1"
DISCOVERY_FILE = "provider-discovery.json"
DEV_BASE_URL = "http://127.0.0.1:18765"
ENV_BASE_URL = "OFFICEWHERE_BASE_URL"


class OfficeWhereProviderError(RuntimeError):
    """Raised when a usable OfficeWhere provider cannot be resolved."""


@dataclass(frozen=True)
class OfficeWhereConnection:
    source: str
    base_url: str
    health_url: str
    manifest_url: str
    discovery_path: str | None = None
    app_version: str | None = None
    backend_pid: int | None = None


def _clean_base_url(value: str) -> str:
    base_url = value.strip().rstrip("/")
    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise OfficeWhereProviderError(f"Invalid OfficeWhere base URL: {value!r}")
    _require_loopback_host(parsed.hostname, value=value)
    return base_url


def _require_loopback_host(hostname: str | None, *, value: str) -> None:
    if hostname is None:
        raise OfficeWhereProviderError(f"Invalid OfficeWhere base URL: {value!r}")
    if hostname.lower() == "localhost":
        return
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError as exc:
        raise OfficeWhereProviderError(f"OfficeWhere provider URL must be loopback-only: {value!r}") from exc
    if not address.is_loopback:
        raise OfficeWhereProviderError(f"OfficeWhere provider URL must be loopback-only: {value!r}")


def provider_url(base_url: str, suffix: str) -> str:
    """Return a provider API URL for a base server URL."""

    base = _clean_base_url(base_url)
    return urljoin(f"{base}/", posixpath.join("api/provider/v1", suffix.lstrip("/")))


def discovery_path_candidates(
    *,
    system: str | None = None,
    env: Mapping[str, str] | None = None,
    home: Path | None = None,
) -> list[Path]:
    """Return OfficeWhere discovery-file candidates in preference order."""

    system_name = system or platform_module.system()
    values = env if env is not None else os.environ
    candidates: list[Path] = []

    if system_name == "Windows":
        local_app_data = values.get("LOCALAPPDATA", "").strip()
        user_profile = values.get("USERPROFILE", "").strip()
        app_data = values.get("APPDATA", "").strip()

        if local_app_data:
            candidates.append(Path(local_app_data) / PROVIDER / DISCOVERY_FILE)
        elif user_profile:
            candidates.append(Path(user_profile) / "AppData" / "Local" / PROVIDER / DISCOVERY_FILE)

        if app_data:
            candidates.append(Path(app_data) / PROVIDER / DISCOVERY_FILE)
        elif user_profile:
            candidates.append(Path(user_profile) / "AppData" / "Roaming" / PROVIDER / DISCOVERY_FILE)
    elif system_name == "Darwin":
        root = home or Path.home()
        candidates.append(root / "Library" / "Application Support" / PROVIDER / DISCOVERY_FILE)
    else:
        xdg_config_home = values.get("XDG_CONFIG_HOME", "").strip()
        if xdg_config_home:
            candidates.append(Path(xdg_config_home) / PROVIDER / DISCOVERY_FILE)
        else:
            root = home or Path.home()
            candidates.append(root / ".config" / PROVIDER / DISCOVERY_FILE)

    # Keep first occurrence only while preserving order.
    unique: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate)
        if key not in seen:
            seen.add(key)
            unique.append(candidate)
    return unique


def _pid_is_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def _http_json(url: str, *, method: str = "GET", body: Mapping[str, Any] | None = None, timeout: float = 2.0) -> Any:
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=timeout) as response:  # noqa: S310 - local provider URL only after validation.
            payload = response.read().decode("utf-8")
    except HTTPError as exc:
        raise OfficeWhereProviderError(f"OfficeWhere provider returned HTTP {exc.code}: {url}") from exc
    except URLError as exc:
        raise OfficeWhereProviderError(f"OfficeWhere provider is unavailable: {url} ({exc.reason})") from exc
    except TimeoutError as exc:
        raise OfficeWhereProviderError(f"OfficeWhere provider timed out: {url}") from exc

    if not payload:
        return None
    try:
        return json.loads(payload)
    except json.JSONDecodeError as exc:
        raise OfficeWhereProviderError(f"OfficeWhere provider returned non-JSON: {url}") from exc


def _validate_provider_payload(payload: Any, *, endpoint: str, require_identity: bool = False) -> None:
    if not isinstance(payload, Mapping):
        if require_identity:
            raise OfficeWhereProviderError(f"OfficeWhere {endpoint} returned an invalid payload")
        return
    provider = payload.get("provider")
    contract = payload.get("contract_version")
    if require_identity and (provider is None or contract is None):
        raise OfficeWhereProviderError(f"OfficeWhere {endpoint} did not include provider identity")
    if provider is not None and provider != PROVIDER:
        raise OfficeWhereProviderError(f"Unexpected provider from {endpoint}: {provider!r}")
    if contract is not None and contract != CONTRACT_VERSION:
        raise OfficeWhereProviderError(f"Unsupported provider contract from {endpoint}: {contract!r}")


def validate_connection(connection: OfficeWhereConnection, *, timeout: float = 2.0) -> OfficeWhereConnection:
    if connection.backend_pid is not None and not _pid_is_alive(connection.backend_pid):
        raise OfficeWhereProviderError(f"Stale OfficeWhere discovery pid: {connection.backend_pid}")

    health = _http_json(connection.health_url, timeout=timeout)
    _validate_provider_payload(health, endpoint="health")
    manifest = _http_json(connection.manifest_url, timeout=timeout)
    _validate_provider_payload(manifest, endpoint="manifest", require_identity=True)
    return connection


def _connection_from_base_url(base_url: str, *, source: str) -> OfficeWhereConnection:
    clean = _clean_base_url(base_url)
    return OfficeWhereConnection(
        source=source,
        base_url=clean,
        health_url=provider_url(clean, "health"),
        manifest_url=provider_url(clean, "manifest"),
    )


def _read_discovery(path: Path) -> OfficeWhereConnection:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise OfficeWhereProviderError(f"Cannot read OfficeWhere discovery file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise OfficeWhereProviderError(f"Invalid OfficeWhere discovery JSON: {path}") from exc

    if not isinstance(data, Mapping):
        raise OfficeWhereProviderError(f"Invalid OfficeWhere discovery payload: {path}")
    if data.get("provider") != PROVIDER:
        raise OfficeWhereProviderError(f"Wrong provider in discovery file: {path}")
    if data.get("contract_version") != CONTRACT_VERSION:
        raise OfficeWhereProviderError(f"Unsupported discovery contract in file: {path}")

    base_url = data.get("base_url")
    if not isinstance(base_url, str) or not base_url.strip():
        raise OfficeWhereProviderError(f"Missing base_url in OfficeWhere discovery file: {path}")

    backend_pid: int | None = None
    raw_pid = data.get("backend_pid")
    if isinstance(raw_pid, int):
        backend_pid = raw_pid

    clean = _clean_base_url(base_url)
    return OfficeWhereConnection(
        source="discovery-file",
        base_url=clean,
        health_url=provider_url(clean, "health"),
        manifest_url=provider_url(clean, "manifest"),
        discovery_path=str(path),
        app_version=data.get("app_version") if isinstance(data.get("app_version"), str) else None,
        backend_pid=backend_pid,
    )


def discover_officewhere(
    *,
    env: Mapping[str, str] | None = None,
    system: str | None = None,
    home: Path | None = None,
    validate: bool = True,
    timeout: float = 2.0,
    include_dev_default: bool = True,
) -> OfficeWhereConnection:
    """Discover and optionally validate a read-only OfficeWhere provider."""

    values = env if env is not None else os.environ
    errors: list[str] = []

    override = values.get(ENV_BASE_URL, "").strip()
    if override:
        connection = _connection_from_base_url(override, source=f"env:{ENV_BASE_URL}")
        return validate_connection(connection, timeout=timeout) if validate else connection

    for path in discovery_path_candidates(system=system, env=values, home=home):
        if not path.is_file():
            continue
        try:
            connection = _read_discovery(path)
            return validate_connection(connection, timeout=timeout) if validate else connection
        except OfficeWhereProviderError as exc:
            errors.append(str(exc))

    if include_dev_default:
        connection = _connection_from_base_url(DEV_BASE_URL, source="dev-default")
        try:
            return validate_connection(connection, timeout=timeout) if validate else connection
        except OfficeWhereProviderError as exc:
            errors.append(str(exc))

    detail = "; ".join(errors[-3:]) if errors else "no discovery file or override found"
    raise OfficeWhereProviderError(f"No usable OfficeWhere provider found ({detail})")


def health(**kwargs: Any) -> Any:
    connection = discover_officewhere(**kwargs)
    return _http_json(connection.health_url, timeout=kwargs.get("timeout", 2.0))


def manifest(**kwargs: Any) -> Any:
    connection = discover_officewhere(**kwargs)
    return _http_json(connection.manifest_url, timeout=kwargs.get("timeout", 2.0))


def search(query: str, *, limit: int = 20, file_limit: int = 10, **kwargs: Any) -> Any:
    connection = discover_officewhere(**kwargs)
    payload = {
        "query": query,
        "limit": limit,
        "file_limit": file_limit,
        "search_scope": "filename_content",
        "excluded_folder_paths": [],
    }
    return _http_json(provider_url(connection.base_url, "search"), method="POST", body=payload, timeout=kwargs.get("timeout", 2.0))


def _print_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def _add_common_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--no-validate", action="store_true", help="Resolve paths/URLs without health/manifest validation.")
    parser.add_argument("--timeout", type=float, default=2.0, help="Provider HTTP timeout in seconds.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Discover and query OfficeWhere's read-only provider API.")
    subparsers = parser.add_subparsers(dest="command")

    discover_parser = subparsers.add_parser("discover", help="Print resolved provider connection metadata.")
    _add_common_flags(discover_parser)

    health_parser = subparsers.add_parser("health", help="Call provider health endpoint.")
    _add_common_flags(health_parser)

    manifest_parser = subparsers.add_parser("manifest", help="Call provider manifest endpoint.")
    _add_common_flags(manifest_parser)

    search_parser = subparsers.add_parser("search", help="Search OfficeWhere documents.")
    search_parser.add_argument("query")
    search_parser.add_argument("--limit", type=int, default=20)
    search_parser.add_argument("--file-limit", type=int, default=10)
    _add_common_flags(search_parser)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    command = args.command or "discover"
    common = {"validate": not getattr(args, "no_validate", False), "timeout": getattr(args, "timeout", 2.0)}

    try:
        if command == "discover":
            _print_json(asdict(discover_officewhere(**common)))
        elif command == "health":
            _print_json(health(**common))
        elif command == "manifest":
            _print_json(manifest(**common))
        elif command == "search":
            _print_json(search(args.query, limit=args.limit, file_limit=args.file_limit, **common))
        else:
            parser.error(f"Unknown command: {command}")
    except OfficeWhereProviderError as exc:
        print(f"officewhere_provider: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
