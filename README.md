# Agent Context Health

A Westside Union diagnostic tool for AI coding-agent projects.

It checks whether a repo is healthy for long-running work with **OpenClaw**, **Hermes Agent**, **Claude Code**, **Codex**, Cursor, and similar coding assistants.

## What it checks

- missing project instruction files
- oversized memory/context files
- missing handoff notes
- missing development logs
- duplicated/conflicting agent instructions
- tool/MCP config without context policy
- TODO markers inside always-read context
- local `.env` secret risk without printing values
- dirty git working trees before handoff
- whether a project has obvious entrypoint files

## Usage

```bash
python3 -m agent_context_health.cli .
python3 -m agent_context_health.cli . --json
python3 -m agent_context_health.cli . --markdown
python3 -m agent_context_health.cli . --format markdown
python3 -m agent_context_health.cli . --fail-on high
```

`--fail-on` supports `none`, `low`, `medium`, and `high`, so teams can use it in CI or pre-handoff scripts.

## Why this exists

Agent failures often look mysterious, but many come from ordinary context hygiene problems:

- stale instructions
- missing handoffs
- huge memory files
- too many tools loaded
- no record of what was tested
- long sessions resumed from weak state

This tool gives teams a small, repeatable check before blaming the model.

## Agent workflow

1. Run the audit before a large session.
2. Fix high-severity issues first.
3. Add/update `HANDOFF.md` before switching agents.
4. Keep OpenClaw / Hermes / Claude Code / Codex context files short and explicit.
5. Paste the Markdown report into the next agent session when handing off.

See `docs/AGENT_SESSION_SAFETY.md` for the recommended checklist.

## Westside Union opinion

AI agents need operating discipline, not just bigger context windows. A good project should have:

- concise durable instructions
- dated decisions
- verification logs
- handoff notes
- clear tool-loading rules

That is the difference between “vibe coding” and a real operating system.
