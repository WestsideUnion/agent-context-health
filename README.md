# Agent Context Health

A small diagnostic tool for AI coding-agent projects.

It checks for common context-health problems in Claude Code, Codex, Cursor, OpenClaw, and similar agent workflows:

- missing project instruction files
- oversized memory/context files
- missing handoff notes
- missing development logs
- likely duplicated/conflicting agent instructions

Built by [Westside Union](https://github.com/WestsideUnion).

## Quick start

```bash
python3 -m agent_context_health.cli /path/to/project
```

From this repo:

```bash
python3 -m agent_context_health.cli .
```

## Why this exists

AI coding agents are strongest when project context is clean, current, and easy to resume. Long sessions, stale memory, giant instruction files, and missing handoffs make agents forget, repeat work, or confidently continue from the wrong assumptions.

This tool is intentionally small. It is a first-pass health check, not a replacement for human review.
