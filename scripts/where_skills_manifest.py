#!/usr/bin/env python3
"""Print the where-skills seed manifest.

This helper is intentionally local and side-effect free. It does not connect to
MailWhere, OfficeWhere, Outlook, SQLite, or external services.
"""

from __future__ import annotations

import json


MANIFEST = {
    "name": "where-skills",
    "status": "officewhere-provider-seed",
    "role_split": {
        "MailWhere": "mail/task provider",
        "OfficeWhere": "document provider",
        "where-skills": "Codex orchestration layer",
    },
    "default_policy": "read_only_suggestive",
    "current_capabilities": [
        "officewhere_provider_discovery_client"
    ],
    "forbidden": [
        "mail_send_reply_delete_move_mark",
        "source_document_edit_delete_move_overwrite",
        "officewhere_sqlite_direct_access",
        "mailwhere_sqlite_as_long_term_contract",
        "auto_installed_hooks_or_mcp",
    ],
    "future_capabilities": [
        "mailwhere_provider_client",
        "combined_evidence_brief",
        "routing_hints_after_explicit_approval",
        "optional_mcp_after_contracts_stabilize",
    ],
}


def main() -> None:
    print(json.dumps(MANIFEST, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
