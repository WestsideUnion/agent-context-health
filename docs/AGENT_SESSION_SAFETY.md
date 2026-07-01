# Agent Session Safety

Use this checklist before handing a repo to OpenClaw, Hermes Agent, Claude Code, Codex, Cursor, or any long-running coding agent.

## Fresh-session checklist

1. Confirm the goal in one sentence.
2. Read `AGENTS.md` or `CLAUDE.md` first.
3. Check `HANDOFF.md` for current state and blockers.
4. Check `DEVELOPMENT_LOG.md` for recent decisions and verification.
5. Run `agent-context-health . --format markdown` before major edits.
6. Keep secrets out of always-loaded context.
7. End with changed files, tests run, and next action.

## Common failure modes

- Stale instructions override newer project decisions.
- A huge memory/context file buries the important rules.
- One agent leaves uncommitted changes and the next agent guesses.
- Tool/MCP configs exist, but no one knows when to load them.
- `.env` files leak secret values into agent-visible context.

## Recommended handoff format

```markdown
# Handoff

- Current objective:
- Files touched:
- Decisions made:
- Tests/checks run:
- Known blockers:
- Next safest action:
```
