# Architecture

`where-skills` is a thin Codex CLI orchestration layer. It should not become the owner of mail extraction, document indexing, or product-specific persistence.

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
- **where-skills** owns prompt interpretation, provider call sequencing, evidence synthesis, and safe output formatting.

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

## Output contract

A mature where-skills response should include:

- interpreted intent;
- MailWhere evidence with task/review/mail IDs when available;
- OfficeWhere evidence with file IDs, names, paths, locations, snippets, and freshness signals;
- suggested next action or draft;
- explicit `Not performed` section for mail/document mutation and unavailable provider steps.

## Current runtime discovery

OfficeWhere discovery is handled by the bundled `scripts/officewhere_provider.py`: env override, Windows LocalAppData, legacy Windows Roaming, macOS/Linux userData, then dev default. The helper validates `health` and `manifest` before use.

## Future runtime layers

Staged additions should happen in this order:

1. skill and documentation seed;
2. provider-backed helper scripts;
3. optional safe routing hints/hooks;
4. plugin packaging;
5. optional local MCP server after contracts stabilize.
