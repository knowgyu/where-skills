# Historical roadmap and retirement gate

This roadmap is closed. MailWhere and OfficeWhere own provider behavior; contextWhere owns orchestration.

## Phase 0 — Working MVP seed

- Create public `where-skills` repo.
- Draft `where-skills` Codex skill.
- Document MailWhere provider contract direction.
- Document OfficeWhere provider usage.
- Keep all operations read-only/suggestive.

## Phase 1 — Provider-backed helpers

- Done: `officewhere_provider.py` discovers OfficeWhere and calls `/api/provider/v1`.
- Done: `mailwhere_provider.py` locates and invokes MailWhere.Cli read-only JSON provider.
- Cancelled here: `where_brief.py`; contextWhere evidence/context-pack flows replace it.

## Cancelled phases

- Routing hooks, plugin packaging, and a local MCP server will not be added to this repository.

## Archive gate

1. Replace live `local:where-skills/...` references with MailWhere/OfficeWhere product docs.
2. Decide whether contextWhere consumes OfficeWhere `provider-discovery.json` or requires an explicit base URL.
3. Confirm no installed skill or active automation depends on this checkout.
4. Archive the remote; delete the local checkout only after the reference check passes.
