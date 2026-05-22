# OfficeWhere Provider Notes

OfficeWhere exposes a read-oriented provider API for local automation.

## Base path

```text
/api/provider/v1
```

## Discovery order

where-skills resolves OfficeWhere in this order:

1. `OFFICEWHERE_BASE_URL` if supplied and loopback/local.
2. Windows v0.12+: `%LOCALAPPDATA%\OfficeWhere\provider-discovery.json`.
3. Windows legacy fallback: `%APPDATA%\OfficeWhere\provider-discovery.json`.
4. macOS: `~/Library/Application Support/OfficeWhere/provider-discovery.json`.
5. Linux: `${XDG_CONFIG_HOME:-~/.config}/OfficeWhere/provider-discovery.json`.
6. Development default: `http://127.0.0.1:18765`.

The helper accepts only loopback/local provider URLs, derives provider endpoints from `base_url`, and validates providers with `health` and `manifest` calls. Stale files are ignored when another candidate is available.

## Helper

```bash
python scripts/officewhere_provider.py discover
python scripts/officewhere_provider.py health
python scripts/officewhere_provider.py manifest
python scripts/officewhere_provider.py search "query" --limit 20
```

## Safe operations

- `GET /api/provider/v1/health`
- `GET /api/provider/v1/manifest`
- `POST /api/provider/v1/search`
- `GET /api/provider/v1/files`
- `GET /api/provider/v1/duplicates`
- `GET /api/provider/v1/groups`
- `GET /api/provider/v1/groups/{group_id}`
- `POST /api/provider/v1/compare` — may write app-owned comparison cache; must not modify source documents.

## Rules

- Never read OfficeWhere SQLite directly.
- Treat source paths and snippets as local sensitive data.
- Do not call reindex/rescan/settings/file registration/deletion/open operations automatically.
- Ask before any OS-visible open/show action.
