# Architecture

`where-skills` was a thin Codex CLI orchestration layer. Its intended orchestration role now belongs to contextWhere; this repository remains only as a retirement-stage compatibility reference and should not gain new product features.

## Role split

```text
User prompt
  -> Codex CLI / where-skills
      -> MailWhere provider or SDK  (mail/task context)
      -> OfficeWhere provider API   (document evidence)
      -> Markdown/JSON briefing and draft next actions
```

- **MailWhere** owns Outlook integration, mail-derived task state, review candidates, mail search, and future FTS/live-search behavior.
- **OfficeWhere** owns document registration, indexing, search, version grouping, duplicate detection, and comparison.
- **contextWhere** owns provider call sequencing, evidence synthesis, Markdown wiki, context packs, and safe output formatting.
- **where-skills** retains only legacy helper/discovery code until retirement prerequisites are complete.

## Provider-first boundary

The core architectural rule is: **providers expose contracts; where-skills does not scrape product databases as its intended interface**.

This matters because MailWhere and OfficeWhere should be able to productize independently. Schema changes, UI changes, indexing choices, and provider internals should not break the orchestration layer when provider contracts remain stable.

## Safety model

All first-pass operations are read-only or suggestive.

Allowed:

- list mail-derived tasks/review candidates through MailWhere provider contracts;
- search registered documents through OfficeWhere provider APIs discovered from env/app-data metadata;
- return file names, snippets, IDs, paths, and provenance;
- draft a reply/report/checklist for the user to review.

Not allowed:

- mail send/reply/delete/move/read-state mutation;
- source Office/PDF edit/delete/move/overwrite;
- direct OfficeWhere SQLite access;
- direct MailWhere SQLite as the long-term integration;
- automatic hook-triggered provider calls without explicit future approval.

## Legacy output contract

An existing where-skills response should include:

- interpreted intent;
- MailWhere evidence with task/review/mail IDs when available;
- OfficeWhere evidence with file IDs, names, paths, locations, snippets, and freshness signals;
- suggested next action or draft;
- explicit `Not performed` section for mail/document mutation and unavailable provider steps.

## Current runtime discovery

OfficeWhere discovery is handled by the bundled `scripts/officewhere_provider.py`: env override, Windows LocalAppData, legacy Windows Roaming, macOS/Linux userData, then dev default. The helper validates `health` and `manifest` before use.

## Retirement boundary

The MailWhere helper is functionally replaced by `MailWhere.Cli` plus contextWhere's adapter. OfficeWhere's contract is canonical in OfficeWhere, but contextWhere does not yet consume the packaged dynamic-port discovery file. Archive the remote after that choice is resolved and references move to product-owned docs; do not add hooks, plugin packaging, MCP, or the previously planned combined helper here.
