# scripts

This directory is reserved for provider-backed helper scripts.

Planned helpers:

- `mailwhere_provider.py` — client for a future MailWhere read-only provider/SDK.
- `officewhere_provider.py` — client for OfficeWhere `/api/provider/v1`.
- `where_brief.py` — combines MailWhere context and OfficeWhere document evidence into Markdown + JSON.

Current seed helper:

- `where_skills_manifest.py` — prints the seed capability/safety manifest for verification and future tooling.

Do not add direct OfficeWhere SQLite readers or MailWhere SQLite readers as the default architecture. Any temporary fallback must be explicitly approved and documented as such.
