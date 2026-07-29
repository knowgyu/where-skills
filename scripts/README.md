# scripts

Provider-backed helpers for where-skills.

## Current helpers

- `officewhere_provider.py` — discovers and queries OfficeWhere `/api/provider/v1`.
- `mailwhere_provider.py` — locates and invokes MailWhere.Cli read-only JSON provider.
- `where_skills_manifest.py` — prints the local capability/safety manifest.

## OfficeWhere examples

```bash
python scripts/officewhere_provider.py discover
python scripts/officewhere_provider.py health
python scripts/officewhere_provider.py manifest
python scripts/officewhere_provider.py search "신입교육" --limit 20
```

## MailWhere examples

```bash
python scripts/mailwhere_provider.py discover
python scripts/mailwhere_provider.py health
python scripts/mailwhere_provider.py manifest
python scripts/mailwhere_provider.py list-tasks --status open --limit 20
python scripts/mailwhere_provider.py list-review-candidates --limit 20
```

Discovery prefers OfficeWhere v0.12+ Windows LocalAppData, then legacy Roaming, then macOS/Linux userData, then the dev default. Provider URLs must be loopback/local.

## Planned helpers

- `where_brief.py` was planned but never implemented; contextWhere now owns combined evidence and context-pack generation.

Do not add direct OfficeWhere SQLite readers or MailWhere SQLite readers as the default architecture.
