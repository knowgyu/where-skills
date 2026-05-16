# where-skills

`where-skills` is a Codex CLI orchestration seed for connecting MailWhere and OfficeWhere safely.

- **MailWhere = mail/task provider**: owns mail-derived tasks, review candidates, reminders, and future mail search/provider behavior.
- **OfficeWhere = document provider**: owns local Office/PDF document search, version groups, duplicates, and comparison evidence.
- **where-skills = Codex orchestration layer**: turns a user request into read-only provider calls, evidence briefings, and draft next actions.

The first version is intentionally a **working MVP seed**, not a full runtime integration. It defines the skill surface, provider contracts, and safety boundaries so MailWhere and OfficeWhere can evolve as separate products.

## Example target prompts

```text
$where-skills 오늘 해야 할 일 정리하고 관련 문서 찾아서 초안 만들어줘
$where-skills 2월 임원 보고자료 관련 메일과 문서가 뭐였지?
$where-skills 신입교육 관련 최근 내용 알려줘
```

## Safety boundaries

`where-skills` is read-only by default.

It must not:

- send, reply to, delete, move, or mark mail;
- edit, delete, move, overwrite, or save over source Office/PDF documents;
- read OfficeWhere SQLite directly;
- depend on MailWhere SQLite as the intended long-term contract;
- install active hooks, MCP servers, or background automation without explicit future approval.

## Current repo status

This seed contains:

```text
docs/architecture.md                 provider-first architecture
docs/mailwhere-provider-contract.md  desired MailWhere SDK/provider v1 shape
docs/officewhere-provider-notes.md   OfficeWhere provider API usage notes
docs/roadmap.md                      staged delivery path
skills/where-skills/SKILL.md         Codex skill draft
scripts/README.md                    helper script roadmap
scripts/where_skills_manifest.py     local seed manifest helper
```

## Design stance

MailWhere full-text search (FTS) is a **MailWhere product/provider concern**, not a where-skills implementation detail. A future MailWhere provider may use task/evidence FTS, Outlook COM live search, or optional full-mail indexing internally, but where-skills should call the provider contract and preserve provenance in results.

## First useful milestone

The first functional milestone after this seed is:

1. MailWhere exposes a read-only provider or CLI SDK for task/review/search context.
2. OfficeWhere base URL discovery is available or supplied by `OFFICEWHERE_BASE_URL`.
3. where-skills helper scripts call those providers and generate a markdown + JSON evidence brief.

## License

MIT. This repository is an orchestration layer and does not embed MailWhere or OfficeWhere source code.
