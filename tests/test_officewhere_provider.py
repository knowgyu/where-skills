from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "skills" / "where-skills" / "scripts" / "officewhere_provider.py"
SPEC = importlib.util.spec_from_file_location("officewhere_provider", HELPER)
assert SPEC is not None and SPEC.loader is not None
ow = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = ow
SPEC.loader.exec_module(ow)


class OfficeWhereProviderTests(unittest.TestCase):
    def test_env_override_wins_without_file_discovery(self) -> None:
        connection = ow.discover_officewhere(
            env={ow.ENV_BASE_URL: "http://127.0.0.1:19000/"},
            validate=False,
            include_dev_default=False,
        )

        self.assertEqual(connection.source, "env:OFFICEWHERE_BASE_URL")
        self.assertEqual(connection.base_url, "http://127.0.0.1:19000")
        self.assertEqual(connection.health_url, "http://127.0.0.1:19000/api/provider/v1/health")

    def test_remote_env_override_is_rejected(self) -> None:
        with self.assertRaises(ow.OfficeWhereProviderError):
            ow.discover_officewhere(
                env={ow.ENV_BASE_URL: "https://officewhere.example.test"},
                validate=False,
                include_dev_default=False,
            )

    def test_windows_candidates_prefer_local_app_data_then_roaming(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            candidates = ow.discovery_path_candidates(
                system="Windows",
                env={
                    "LOCALAPPDATA": str(root / "Local"),
                    "APPDATA": str(root / "Roaming"),
                },
            )

        self.assertEqual(candidates[0].parts[-3:], ("Local", "OfficeWhere", "provider-discovery.json"))
        self.assertEqual(candidates[1].parts[-3:], ("Roaming", "OfficeWhere", "provider-discovery.json"))

    def test_windows_candidates_fall_back_from_user_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            candidates = ow.discovery_path_candidates(
                system="Windows",
                env={"USERPROFILE": str(root / "me")},
            )

        self.assertIn("AppData", candidates[0].parts)
        self.assertIn("Local", candidates[0].parts)
        self.assertIn("Roaming", candidates[1].parts)

    def test_unix_candidates_use_electron_user_data_locations(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            mac = ow.discovery_path_candidates(system="Darwin", env={}, home=home)
            linux = ow.discovery_path_candidates(system="Linux", env={}, home=home)

        self.assertEqual(mac[0], home / "Library" / "Application Support" / "OfficeWhere" / "provider-discovery.json")
        self.assertEqual(linux[0], home / ".config" / "OfficeWhere" / "provider-discovery.json")

    def test_valid_discovery_file_resolves_without_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            local = Path(temp_dir) / "Local"
            discovery_dir = local / "OfficeWhere"
            discovery_dir.mkdir(parents=True)
            discovery_path = discovery_dir / "provider-discovery.json"
            discovery_path.write_text(
                json.dumps(
                    {
                        "provider": "OfficeWhere",
                        "contract_version": "v1",
                        "app_version": "0.12.0",
                        "base_url": "http://127.0.0.1:31000",
                        "health_url": "http://127.0.0.1:31000/api/provider/v1/health",
                        "manifest_url": "http://127.0.0.1:31000/api/provider/v1/manifest",
                    }
                ),
                encoding="utf-8",
            )

            connection = ow.discover_officewhere(
                system="Windows",
                env={"LOCALAPPDATA": str(local)},
                validate=False,
                include_dev_default=False,
            )

        self.assertEqual(connection.source, "discovery-file")
        self.assertEqual(connection.discovery_path, str(discovery_path))
        self.assertEqual(connection.app_version, "0.12.0")
        self.assertEqual(connection.base_url, "http://127.0.0.1:31000")

    def test_discovery_urls_are_derived_from_loopback_base_url(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            local = Path(temp_dir) / "Local"
            discovery_dir = local / "OfficeWhere"
            discovery_dir.mkdir(parents=True)
            (discovery_dir / "provider-discovery.json").write_text(
                json.dumps(
                    {
                        "provider": "OfficeWhere",
                        "contract_version": "v1",
                        "base_url": "http://127.0.0.1:31000",
                        "health_url": "https://officewhere.example.test/health",
                        "manifest_url": "https://officewhere.example.test/manifest",
                    }
                ),
                encoding="utf-8",
            )

            connection = ow.discover_officewhere(
                system="Windows",
                env={"LOCALAPPDATA": str(local)},
                validate=False,
                include_dev_default=False,
            )

        self.assertEqual(connection.health_url, "http://127.0.0.1:31000/api/provider/v1/health")
        self.assertEqual(connection.manifest_url, "http://127.0.0.1:31000/api/provider/v1/manifest")

    def test_remote_discovery_base_url_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            local = Path(temp_dir) / "Local"
            discovery_dir = local / "OfficeWhere"
            discovery_dir.mkdir(parents=True)
            (discovery_dir / "provider-discovery.json").write_text(
                json.dumps(
                    {
                        "provider": "OfficeWhere",
                        "contract_version": "v1",
                        "base_url": "https://officewhere.example.test",
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaises(ow.OfficeWhereProviderError):
                ow.discover_officewhere(
                    system="Windows",
                    env={"LOCALAPPDATA": str(local)},
                    validate=False,
                    include_dev_default=False,
                )

    def test_invalid_discovery_provider_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            local = Path(temp_dir) / "Local"
            discovery_dir = local / "OfficeWhere"
            discovery_dir.mkdir(parents=True)
            (discovery_dir / "provider-discovery.json").write_text(
                json.dumps(
                    {
                        "provider": "MailWhere",
                        "contract_version": "v1",
                        "base_url": "http://127.0.0.1:31000",
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaises(ow.OfficeWhereProviderError):
                ow.discover_officewhere(
                    system="Windows",
                    env={"LOCALAPPDATA": str(local)},
                    validate=False,
                    include_dev_default=False,
                )

    def test_stale_local_discovery_can_fall_back_to_roaming(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            local = root / "Local"
            roaming = root / "Roaming"
            local_dir = local / "OfficeWhere"
            roaming_dir = roaming / "OfficeWhere"
            local_dir.mkdir(parents=True)
            roaming_dir.mkdir(parents=True)
            (local_dir / "provider-discovery.json").write_text(
                json.dumps(
                    {
                        "provider": "OfficeWhere",
                        "contract_version": "v1",
                        "base_url": "http://127.0.0.1:31000",
                        "backend_pid": 999999999,
                    }
                ),
                encoding="utf-8",
            )
            (roaming_dir / "provider-discovery.json").write_text(
                json.dumps(
                    {
                        "provider": "OfficeWhere",
                        "contract_version": "v1",
                        "base_url": "http://127.0.0.1:32000",
                    }
                ),
                encoding="utf-8",
            )

            with patch.object(
                ow,
                "_http_json",
                side_effect=[
                    {"provider": "OfficeWhere", "contract_version": "v1", "status": "ok"},
                    {"provider": "OfficeWhere", "contract_version": "v1"},
                ],
            ):
                connection = ow.discover_officewhere(
                    system="Windows",
                    env={"LOCALAPPDATA": str(local), "APPDATA": str(roaming)},
                    validate=True,
                    include_dev_default=False,
                )

        self.assertEqual(connection.base_url, "http://127.0.0.1:32000")
        self.assertEqual(connection.discovery_path, str(roaming_dir / "provider-discovery.json"))

    def test_validation_rejects_stale_pid_before_http(self) -> None:
        connection = ow.OfficeWhereConnection(
            source="discovery-file",
            base_url="http://127.0.0.1:31000",
            health_url="http://127.0.0.1:31000/api/provider/v1/health",
            manifest_url="http://127.0.0.1:31000/api/provider/v1/manifest",
            backend_pid=999999999,
        )

        with patch.object(ow, "_http_json") as http_json:
            with self.assertRaises(ow.OfficeWhereProviderError):
                ow.validate_connection(connection)
            http_json.assert_not_called()

    def test_validation_accepts_provider_health_and_manifest(self) -> None:
        connection = ow.OfficeWhereConnection(
            source="env:OFFICEWHERE_BASE_URL",
            base_url="http://127.0.0.1:31000",
            health_url="http://127.0.0.1:31000/api/provider/v1/health",
            manifest_url="http://127.0.0.1:31000/api/provider/v1/manifest",
        )

        with patch.object(
            ow,
            "_http_json",
            side_effect=[
                {"provider": "OfficeWhere", "contract_version": "v1", "status": "ok"},
                {"provider": "OfficeWhere", "contract_version": "v1"},
            ],
        ):
            self.assertEqual(ow.validate_connection(connection), connection)


if __name__ == "__main__":
    unittest.main()
