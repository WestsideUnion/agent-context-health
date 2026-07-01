from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

CONTEXT_FILES = [
    'AGENTS.md', 'CLAUDE.md', 'MEMORY.md', 'DESIGN.md', 'DEVELOPMENT_LOG.md',
    'DECISIONS.md', 'HANDOFF.md', 'SECURITY_NOTES.md', '.cursorrules'
]
ENTRYPOINT_FILES = ['README.md', 'AGENTS.md', 'CLAUDE.md', 'pyproject.toml', 'package.json', 'Cargo.toml', 'go.mod']
MAX_SOFT_BYTES = 40_000
MAX_HARD_BYTES = 120_000
SEVERITY_ORDER = {'none': -1, 'info': 0, 'low': 1, 'medium': 2, 'high': 3}
SECRET_HINTS = ('api_key', 'apikey', 'secret', 'token', 'password', 'private_key', 'bearer ')

@dataclass
class Finding:
    severity: str
    target: str
    message: str
    recommendation: str

@dataclass
class Report:
    brand: str
    root: str
    score: int
    level: str
    findings: list[Finding]
    summary: dict[str, int]
    agent_targets: list[str]


def scan(root: Path) -> Report:
    root = root.resolve()
    findings: list[Finding] = []
    present = []

    for name in CONTEXT_FILES:
        path = root / name
        if path.exists():
            present.append(name)
            size = path.stat().st_size
            if size > MAX_HARD_BYTES:
                findings.append(finding('high', name, f'Very large context file ({size} bytes).', 'Split into smaller durable files and summarize stale sections.'))
            elif size > MAX_SOFT_BYTES:
                findings.append(finding('medium', name, f'Large context file ({size} bytes).', 'Compact old sections and move raw logs out of always-loaded context.'))
            stale = stale_file(path)
            if stale:
                findings.append(finding('low', name, stale, 'Add a dated update note or archive the stale file.'))

    if not any((root / name).exists() for name in ['AGENTS.md', 'CLAUDE.md']):
        findings.append(finding('medium', 'project root', 'Missing AGENTS.md or CLAUDE.md project instructions.', 'Add one concise project instruction file with build/test commands and safety rules.'))

    if not any((root / name).exists() for name in ENTRYPOINT_FILES):
        findings.append(finding('high', 'project root', 'Missing obvious project entrypoint files.', 'Add README.md and the relevant package manifest so agents know how to run the project.'))

    if not (root / 'HANDOFF.md').exists():
        findings.append(finding('low', 'project root', 'Missing HANDOFF.md for long agent sessions and resume safety.', 'Add a short handoff file with current objective, touched files, blockers, and next action.'))

    if not (root / 'DEVELOPMENT_LOG.md').exists():
        findings.append(finding('low', 'project root', 'Missing DEVELOPMENT_LOG.md to preserve decisions and verification steps.', 'Log meaningful changes with test/build evidence.'))

    duplicated = duplicate_instruction_files(root)
    if len(duplicated) > 2:
        findings.append(finding('medium', 'context files', f'Multiple agent instruction files found: {", ".join(duplicated[:8])}.', 'Check for conflicts and define precedence.'))

    if tool_overload(root):
        findings.append(finding('medium', 'tooling config', 'Potential tool/MCP config present without a context policy.', 'Document when to load heavy tools and which tasks need them.'))

    findings.extend(secret_risks(root))
    dirty = git_dirty(root)
    if dirty:
        findings.append(finding('medium', 'git', 'Working tree has uncommitted changes.', 'Commit, stash, or write a handoff before switching agents or compacting context.'))

    targets = detect_agent_targets(root)
    summary = summarize(findings)
    score = score_from(summary)
    level = 'excellent' if score >= 90 else 'healthy' if score >= 75 else 'watch' if score >= 55 else 'fragile'

    if not findings:
        findings.append(finding('info', 'project root', 'No obvious context health issues found.', 'Keep context files short, dated, and verified.'))
        summary = summarize(findings)

    return Report(
        brand='Westside Union Agent Context Health',
        root=str(root),
        score=score,
        level=level,
        findings=findings,
        summary=summary,
        agent_targets=targets,
    )


def stale_file(path: Path) -> str | None:
    text = safe_read(path, limit=5000)
    if not text:
        return None
    if 'TODO' in text and path.name in {'AGENTS.md', 'CLAUDE.md', 'HANDOFF.md'}:
        return 'Contains TODO markers in always-read context.'
    return None


def duplicate_instruction_files(root: Path) -> list[str]:
    names = {'agents.md', 'claude.md', '.cursorrules'}
    found = []
    for path in root.rglob('*'):
        if ignored_path(path) or not path.is_file():
            continue
        if path.name.lower() in names:
            found.append(str(path.relative_to(root)))
    return found


def tool_overload(root: Path) -> bool:
    candidates = ['.mcp.json', 'mcp.json', 'settings.json', '.cursor']
    return any((root / name).exists() for name in candidates)


def secret_risks(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for env_path in list(root.glob('.env*'))[:10]:
        if env_path.name.endswith('.example') or ignored_path(env_path):
            continue
        text = safe_read(env_path, limit=10_000).lower()
        if any(hint in text for hint in SECRET_HINTS):
            findings.append(finding('high', env_path.name, 'Local env file appears to contain secret-like keys.', 'Keep real secrets out of repos and agent-visible context; provide .env.example with placeholders.'))
    return findings


def git_dirty(root: Path) -> bool:
    if not shutil.which('git'):
        return False
    try:
        result = subprocess.run(['git', '-C', str(root), 'status', '--porcelain'], text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=5, check=False)
    except (OSError, subprocess.SubprocessError):
        return False
    return bool(result.stdout.strip())


def detect_agent_targets(root: Path) -> list[str]:
    targets = []
    probes = {
        'OpenClaw / generic agents': ['AGENTS.md'],
        'Claude Code': ['CLAUDE.md'],
        'Cursor': ['.cursorrules', '.cursor'],
        'Codex': ['AGENTS.md'],
        'Hermes-style agents': ['AGENTS.md', 'HANDOFF.md'],
    }
    for label, names in probes.items():
        if any((root / name).exists() for name in names):
            targets.append(label)
    return targets or ['generic coding agents']


def ignored_path(path: Path) -> bool:
    return any(part in {'.git', 'node_modules', '.venv', '__pycache__', 'dist', 'build'} for part in path.parts)


def safe_read(path: Path, limit: int) -> str:
    try:
        return path.read_text(errors='ignore')[:limit]
    except OSError:
        return ''


def finding(severity: str, target: str, message: str, recommendation: str) -> Finding:
    return Finding(severity, target, message, recommendation)


def summarize(findings: Iterable[Finding]) -> dict[str, int]:
    summary = {'high': 0, 'medium': 0, 'low': 0, 'info': 0}
    for item in findings:
        summary[item.severity] = summary.get(item.severity, 0) + 1
    return summary


def score_from(summary: dict[str, int]) -> int:
    score = 100 - summary.get('high', 0) * 25 - summary.get('medium', 0) * 12 - summary.get('low', 0) * 4
    return max(0, min(100, score))


def highest_severity(report: Report) -> str:
    highest = 'none'
    for item in report.findings:
        if SEVERITY_ORDER.get(item.severity, 0) > SEVERITY_ORDER.get(highest, 0):
            highest = item.severity
    return highest


def to_markdown(report: Report) -> str:
    lines = [
        f'# {report.brand}',
        '',
        f'**Project:** `{report.root}`',
        f'**Score:** {report.score}/100 — {report.level.upper()}',
        f'**Agent targets:** {", ".join(report.agent_targets)}',
        '',
        '## Findings',
        '',
    ]
    for item in report.findings:
        lines.append(f'- **{item.severity.upper()}** `{item.target}` — {item.message} _Recommendation:_ {item.recommendation}')
    lines += [
        '',
        '## Westside Union context rules',
        '',
        '- Keep always-loaded agent instructions short.',
        '- Log decisions and verification evidence outside the main prompt path.',
        '- Create handoffs before long breaks, compaction, model changes, or agent handoffs.',
        '- Prefer fewer loaded tools unless the task genuinely needs them.',
        '- Use the report as a preflight before OpenClaw, Hermes Agent, Claude Code, Codex, or Cursor takes over a repo.',
    ]
    return '\n'.join(lines) + '\n'


def print_text(report: Report) -> None:
    print(f'{report.brand}: {report.root}')
    print(f'Score: {report.score}/100 ({report.level})')
    print(f'Agent targets: {", ".join(report.agent_targets)}')
    print()
    for item in report.findings:
        print(f'[{item.severity.upper()}] {item.target}: {item.message}')
        print(f'  → {item.recommendation}')


def parse_fail_on(value: str) -> str:
    if value not in {'none', 'low', 'medium', 'high'}:
        raise argparse.ArgumentTypeError('must be one of: none, low, medium, high')
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description='Audit project context health for AI coding agents.')
    parser.add_argument('path', nargs='?', default='.', help='Project path to scan')
    parser.add_argument('--json', action='store_true', help='Print JSON report')
    parser.add_argument('--markdown', action='store_true', help='Print Markdown report')
    parser.add_argument('--format', choices=['text', 'json', 'markdown'], help='Output format alias')
    parser.add_argument('--fail-on', type=parse_fail_on, default='none', help='Exit non-zero when this severity or higher is found')
    args = parser.parse_args()

    report = scan(Path(args.path).resolve())
    fmt = args.format or ('json' if args.json else 'markdown' if args.markdown else 'text')
    if fmt == 'json':
        print(json.dumps(asdict(report), indent=2))
    elif fmt == 'markdown':
        print(to_markdown(report))
    else:
        print_text(report)

    threshold = SEVERITY_ORDER[args.fail_on]
    if threshold and SEVERITY_ORDER.get(highest_severity(report), 0) >= threshold:
        raise SystemExit(2)


if __name__ == '__main__':
    main()
