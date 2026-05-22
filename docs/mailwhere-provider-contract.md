# MailWhere Provider Contract Draft

MailWhere exposes the current read-only provider as `MailWhere.Cli.exe`; where-skills calls it through `scripts/mailwhere_provider.py`. This document keeps the v1 response shape and future SDK direction.

## Contract goal

MailWhere acts as the **mail/task provider** for where-skills. It should hide Outlook COM, local storage, deduplication, FTS, and privacy policy details behind a stable read-only provider or SDK.

## Non-goals for this seed

- No direct MailWhere product code changes from where-skills.
- No FTS implementation.
- No Outlook COM live-search implementation.
- No direct dependency on MailWhere SQLite as the intended interface.
- No mail mutation tools.

## Suggested capabilities

### Manifest

```json
{
  "provider": "MailWhere",
  "contract_version": "v1",
  "capabilities": [
    "task_list",
    "review_candidate_list",
    "mail_context_search",
    "source_mail_open_request"
  ],
  "safety": {
    "mailbox_policy": "read_only",
    "raw_body_export_default": false,
    "mutation_tools": []
  }
}
```

### `list_tasks`

Read-only task retrieval for today, overdue, upcoming, waiting, or all active tasks.

Inputs:

```json
{
  "due_window": "today|overdue|7d|30d|none|all",
  "status": "open|snoozed|all",
  "limit": 50
}
```

Outputs should include sanitized fields only:

```json
{
  "items": [
    {
      "kind": "task",
      "id": "local-task-id",
      "title": "...",
      "due_at": "2026-05-16T09:00:00+09:00",
      "reason": "...",
      "evidence_snippet": "...",
      "source_sender_display": "...",
      "source_received_at": "...",
      "recipient_role": "Direct",
      "provenance": "mailwhere_task"
    }
  ],
  "omitted_fields": ["raw_body", "full_addresses", "attachments", "prompt_logs"]
}
```

### `list_review_candidates`

Read-only retrieval of unresolved review candidates, using the same sanitized output policy.

### `search_mail_context`

Mail evidence search for questions such as “2월 임원 보고자료 메일 뭐였지?”.

Inputs:

```json
{
  "query": "임원 보고자료",
  "date_from": "2026-02-01",
  "date_to": "2026-02-29",
  "limit": 20,
  "include_raw_body": false
}
```

Outputs should include subject/title, sender display, received/sent time, short snippet, and provenance.

## FTS stance

FTS can be valuable inside MailWhere, but it should be a MailWhere product/provider choice.

Recommended layering:

1. task/review/evidence/search-hint FTS by default;
2. Outlook COM live search fallback for broader historical queries;
3. optional full-mail body FTS only with explicit product-level privacy, retention, encryption, and deletion policies.

where-skills should not care which internal method MailWhere uses. It should receive provider results with provenance such as `task_fts`, `evidence_index`, or `outlook_live`.

## Source mail opening

A future `open_source_mail` capability should be user-visible and explicit. It should not send, reply, delete, move, or mark mail.
