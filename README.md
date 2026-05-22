# where-skills

Codex skill + helper scripts that combine:

- **MailWhere**: mail/task context provider
- **OfficeWhere**: document evidence provider
- **where-skills**: read-only orchestration and briefing

## Install

Copy the skill directory into your Codex skills folder:

```bash
mkdir -p ~/.codex/skills
cp -R skills/where-skills ~/.codex/skills/
```

The skill directory includes its OfficeWhere helper. From this repo, run:

```bash
python scripts/officewhere_provider.py discover
python scripts/mailwhere_provider.py discover
```

After copying only the skill directory, the same helper is at:

```bash
python ~/.codex/skills/where-skills/scripts/officewhere_provider.py discover
python ~/.codex/skills/where-skills/scripts/mailwhere_provider.py discover
```

## MailWhere discovery

MailWhere has a read-only CLI provider in the portable zip: `MailWhere.Cli.exe`.

Discovery order:

1. `MAILWHERE_CLI_PATH` override, if set
2. `MailWhere.Cli.exe` on `PATH`
3. Windows running `MailWhere.exe` process path, then sibling `MailWhere.Cli.exe`

Optional data DB override: `MAILWHERE_DB_PATH`.

## OfficeWhere discovery

Normal use: start OfficeWhere, then run the skill. No env var is required.

Discovery order:

1. `OFFICEWHERE_BASE_URL` loopback override, if set
2. Windows v0.12+: `%LOCALAPPDATA%\OfficeWhere\provider-discovery.json`
3. Windows legacy: `%APPDATA%\OfficeWhere\provider-discovery.json`
4. macOS/Linux Electron userData discovery file
5. Dev default: `http://127.0.0.1:18765`

Provider URLs must be loopback/local (`localhost`, `127.0.0.1`, or `::1`).

## Usage

```text
$where-skills 오늘 해야 할 일 정리하고 관련 문서 찾아줘
$where-skills 신입교육 관련 최근 메일/문서 근거 정리해줘
```

Helper examples:

```bash
python scripts/officewhere_provider.py discover
python scripts/officewhere_provider.py health
python scripts/officewhere_provider.py manifest
python scripts/officewhere_provider.py search "신입교육" --limit 20
python scripts/mailwhere_provider.py list-tasks --status open --limit 20
```

## Safety rules

where-skills is read-only by default.

It must not:

- send, reply to, delete, move, or mark mail;
- edit, delete, move, overwrite, or save over source Office/PDF documents;
- read OfficeWhere SQLite directly;
- depend on MailWhere SQLite as the long-term interface;
- install hooks, MCP servers, or background automation without explicit approval.

## Status

- OfficeWhere provider discovery helper: implemented.
- MailWhere CLI provider helper: implemented.
- Combined briefing helper: planned.
