from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "skills" / "where-skills" / "scripts" / "mailwhere_provider.py"
SPEC = importlib.util.spec_from_file_location("mailwhere_provider", HELPER)
assert SPEC is not None and SPEC.loader is not None
mw = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mw
SPEC.loader.exec_module(mw)


class MailWhereProviderTests(unittest.TestCase):
    def test_env_cli_path_wins(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            cli = Path(temp_dir) / "MailWhere.Cli.exe"
            cli.write_text("stub", encoding="utf-8")
            connection = mw.discover_mailwhere_cli(env={mw.ENV_CLI_PATH: str(cli)})

        self.assertEqual(connection.source, "env:MAILWHERE_CLI_PATH")
        self.assertEqual(connection.cli_path, str(cli))

    def test_missing_env_cli_path_is_error(self) -> None:
        with self.assertRaises(mw.MailWhereProviderError):
            mw.discover_mailwhere_cli(env={mw.ENV_CLI_PATH: "/missing/MailWhere.Cli.exe"})

    def test_running_process_finds_sibling_cli(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            app = Path(temp_dir) / "MailWhere.exe"
            cli = Path(temp_dir) / "MailWhere.Cli.exe"
            app.write_text("stub", encoding="utf-8")
            cli.write_text("stub", encoding="utf-8")
            with patch.object(mw, "_path_from_env", return_value=None), patch.object(
                mw, "_path_from_path_env", return_value=None
            ), patch.object(mw, "_mailwhere_process_paths", return_value=[app]):
                connection = mw.discover_mailwhere_cli(env={})

        self.assertEqual(connection.source, "running-process")
        self.assertEqual(connection.cli_path, str(cli))

    def test_command_invocation_adds_json_and_db_env_for_data_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            cli = Path(temp_dir) / "MailWhere.Cli.exe"
            db = Path(temp_dir) / "followups.sqlite"
            cli.write_text("stub", encoding="utf-8")
            envelope = {
                "provider": "MailWhere",
                "contract_version": "v1",
                "ok": True,
                "tasks": [],
            }
            completed = mw.subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout=json.dumps(envelope),
                stderr="",
            )
            with patch.object(mw.subprocess, "run", return_value=completed) as run:
                payload = mw.run_mailwhere_cli(
                    "list-tasks",
                    options=["--limit", "5"],
                    env={mw.ENV_CLI_PATH: str(cli), mw.ENV_DB_PATH: str(db)},
                )

        self.assertEqual(payload["provider"], "MailWhere")
        self.assertEqual(
            run.call_args.args[0],
            [str(cli), "list-tasks", "--json", "--db", str(db), "--limit", "5"],
        )

    def test_health_does_not_add_db_env(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            cli = Path(temp_dir) / "MailWhere.Cli.exe"
            db = Path(temp_dir) / "followups.sqlite"
            cli.write_text("stub", encoding="utf-8")
            envelope = {
                "provider": "MailWhere",
                "contract_version": "v1",
                "ok": True,
                "status": "ok",
            }
            completed = mw.subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout=json.dumps(envelope),
                stderr="",
            )
            with patch.object(mw.subprocess, "run", return_value=completed) as run:
                mw.run_mailwhere_cli("health", env={mw.ENV_CLI_PATH: str(cli), mw.ENV_DB_PATH: str(db)})

        self.assertEqual(run.call_args.args[0], [str(cli), "health", "--json"])

    def test_invalid_provider_envelope_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            cli = Path(temp_dir) / "MailWhere.Cli.exe"
            cli.write_text("stub", encoding="utf-8")
            completed = mw.subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout=json.dumps({"provider": "OfficeWhere", "contract_version": "v1"}),
                stderr="",
            )
            with patch.object(mw.subprocess, "run", return_value=completed):
                with self.assertRaises(mw.MailWhereProviderError):
                    mw.run_mailwhere_cli("health", env={mw.ENV_CLI_PATH: str(cli)})


if __name__ == "__main__":
    unittest.main()
