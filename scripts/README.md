# scripts

Provider-backed helpers for where-skills.

## Current helpers

- `officewhere_provider.py` — discovers and queries OfficeWhere `/api/provider/v1`.
- `where_skills_manifest.py` — prints the local capability/safety manifest.

## OfficeWhere examples

```bash
python scripts/officewhere_provider.py discover
python scripts/officewhere_provider.py health
python scripts/officewhere_provider.py manifest
python scripts/officewhere_provider.py search "신입교육" --limit 20
```

Discovery prefers OfficeWhere v0.12+ Windows LocalAppData, then legacy Roaming, then macOS/Linux userData, then the dev default. Provider URLs must be loopback/local.

## Planned helpers

- `mailwhere_provider.py` — pending MailWhere provider/SDK.
- `where_brief.py` — combine MailWhere context and OfficeWhere evidence into Markdown + JSON.

Do not add direct OfficeWhere SQLite readers or MailWhere SQLite readers as the default architecture.
