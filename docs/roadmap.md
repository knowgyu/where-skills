# Roadmap

## Phase 0 — Working MVP seed

- Create public `where-skills` repo.
- Draft `where-skills` Codex skill.
- Document MailWhere provider contract direction.
- Document OfficeWhere provider usage.
- Keep all operations read-only/suggestive.

## Phase 1 — Provider-backed helpers

- Done: `officewhere_provider.py` discovers OfficeWhere and calls `/api/provider/v1`.
- Next: add `mailwhere_provider.py` once MailWhere exposes a provider/SDK.
- Next: add `where_brief.py` to combine mail/task context and document evidence into Markdown + JSON artifacts.

## Phase 2 — Routing hints and safety guards

- Add optional routing hook drafts after explicit approval.
- Hooks should only suggest/route to `where-skills`; they must not scan mail or documents automatically.
- Safety guards can block destructive patterns such as mail mutation or source document deletion.

## Phase 3 — Plugin packaging

- Package skill, helper scripts, optional agents, and optional hooks into a local Codex plugin.

## Phase 4 — Optional MCP

- Add a local MCP server only after provider contracts and helper scripts are stable.
- MCP tools should remain read-only by default.

## Future MailWhere FTS note

MailWhere FTS is worth considering as a product/provider capability, especially for task/review/evidence/search-hint search. Full raw mail body FTS should remain opt-in and requires explicit privacy/retention/deletion policy in MailWhere, not where-skills.
