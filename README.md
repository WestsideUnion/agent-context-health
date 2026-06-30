# Agent Context Health

A Westside Union diagnostic tool for AI coding-agent projects.

It checks whether a repo is healthy for long-running work with Claude Code, Codex, Cursor, OpenClaw, Hermes-style agents, and similar coding assistants.

## What it checks

- missing project instruction files
- oversized memory/context files
- missing handoff notes
- missing development logs
- duplicated/conflicting agent instructions
- tool/MCP config without context policy
- TODO markers inside always-read context

## Output modes

```bash
python3 -m agent_context_health.cli .
python3 -m agent_context_health.cli . --json
python3 -m agent_context_health.cli . --markdown
```

## Why this exists

Agent failures often look mysterious, but many come from ordinary context hygiene problems:

- stale instructions
- missing handoffs
- huge memory files
- too many tools loaded
- no record of what was tested
- long sessions resumed from weak state

This tool gives teams a small, repeatable check before blaming the model.

## Westside Union opinion

AI agents need operating discipline, not just bigger context windows. A good project should have:

- concise durable instructions
- dated decisions
- verification logs
- handoff notes
- clear tool-loading rules

That is the difference between “vibe coding” and a real operating system.
