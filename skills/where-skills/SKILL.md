---
name: where-skills
description: "Connect MailWhere mail/task context with OfficeWhere document evidence in Codex CLI. Use for Korean or English work questions that combine mail-derived tasks, recent business context, related documents, or draft next actions."
argument-hint: "<mail/task/document question>"
---

# where-skills

Use this skill when the user asks Codex CLI to answer work questions that may require both:

- MailWhere mail/task context; and
- OfficeWhere document search/version/duplicate evidence.

Examples:

- `오늘 해야 할 일 정리하고 관련 문서 찾아서 초안 만들어줘`
- `2월 임원 보고자료 관련 메일 뭐였지? 관련 문서도 찾아줘`
- `신입교육 관련 최근 내용 알려줘`

## Role split

- MailWhere = mail/task provider.
- OfficeWhere = document provider.
- where-skills = orchestration and briefing layer.

## Required safety boundaries

Do not:

- send, reply to, delete, move, or mark mail;
- edit, delete, move, overwrite, or save over source Office/PDF documents;
- read OfficeWhere SQLite directly;
- depend on MailWhere SQLite as the intended long-term contract;
- trigger reindex/rescan/settings/file registration/deletion/open operations without explicit user intent;
- install hooks or MCP servers automatically.

## Preferred workflow

1. Restate the interpreted work question.
2. Query MailWhere through its provider/SDK when available.
3. Derive document search hints from sanitized MailWhere task/review/mail context.
4. Discover OfficeWhere with the bundled `scripts/officewhere_provider.py` helper when needed, then query `/api/provider/v1`.
5. Produce a concise briefing with evidence and provenance.
6. Include a `Not performed` section listing blocked or intentionally skipped side effects.


## OfficeWhere discovery

Use the bundled helper when provider access is needed:

```bash
python scripts/officewhere_provider.py discover
```

Discovery order:

1. loopback `OFFICEWHERE_BASE_URL`
2. Windows `%LOCALAPPDATA%\OfficeWhere\provider-discovery.json`
3. legacy Windows `%APPDATA%\OfficeWhere\provider-discovery.json`
4. macOS/Linux Electron userData
5. `http://127.0.0.1:18765` dev default

## Provider unavailable behavior

If MailWhere or OfficeWhere provider access is unavailable, do not scrape product databases by default. For OfficeWhere, first try the helper discovery order above. Provider URLs must be loopback/local. Report the missing provider and explain which part of the answer is blocked.

A future fallback may be added only after explicit approval and must preserve raw-body and SQLite boundary rules.

## Output shape

```md
## 업무 증거 브리프

### 1. <업무/질문>
- MailWhere: <task/review/mail id, sender, received_at, snippet, provenance>
- OfficeWhere: <file id, name, path, location, snippet, provenance>
- Suggested next action: <draft/check/review/ask-human>

## Not performed
- No mail send/reply/delete/move.
- No source Office/PDF edit/delete/move.
- No provider maintenance operation unless explicitly requested.
```
