# OfficeWhere Provider Notes

OfficeWhere already exposes a read-oriented provider boundary intended for local automation.

## Provider base path

```text
/api/provider/v1
```

Expected discovery flow:

1. Use `OFFICEWHERE_BASE_URL` if supplied.
2. Otherwise try development default `http://127.0.0.1:18765`.
3. Future: discover packaged Electron's dynamic backend URL from an OfficeWhere app-data discovery file if OfficeWhere adds one.

## Provider-safe operations

- `GET /api/provider/v1/health`
- `GET /api/provider/v1/manifest`
- `POST /api/provider/v1/search`
- `GET /api/provider/v1/files`
- `GET /api/provider/v1/duplicates`
- `GET /api/provider/v1/groups`
- `GET /api/provider/v1/groups/{group_id}`
- `POST /api/provider/v1/compare` — may write app-owned comparison cache but must not modify source documents.

## Rules for where-skills

- Never read OfficeWhere SQLite directly.
- Treat source paths and snippets as local sensitive data.
- Do not call reindex/rescan/settings/file registration/deletion/open operations automatically.
- Ask for explicit future approval before any OS-visible open/show action.
- Preserve OfficeWhere's role as document provider; keep business workflow orchestration in where-skills.

## Search request shape

A typical provider search request should map to OfficeWhere's existing schema:

```json
{
  "query": "신입교육",
  "limit": 100,
  "file_limit": 20,
  "file_types": ["PowerPoint", "Word", "Excel", "PDF"],
  "search_scope": "filename_content",
  "modified_from": null,
  "modified_to": null,
  "excluded_folder_paths": []
}
```

where-skills should deduplicate results by `file_id`, preserve snippets/locations, and cite file IDs/names/paths in briefings.
