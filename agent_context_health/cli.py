from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

CONTEXT_FILES = [
    'AGENTS.md', 'CLAUDE.md', 'MEMORY.md', 'DESIGN.md', 'DEVELOPMENT_LOG.md',
    'DECISIONS.md', 'HANDOFF.md', 'SECURITY_NOTES.md', '.cursorrules'
]
MAX_SOFT_BYTES = 40_000
MAX_HARD_BYTES = 120_000

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


def scan(root: Path) -> Report:
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

    if not (root / 'HANDOFF.md').exists():
        findings.append(finding('low', 'project root', 'Missing HANDOFF.md for long agent sessions and resume safety.', 'Add a short handoff file with current objective, touched files, blockers, and next action.'))

    if not (root / 'DEVELOPMENT_LOG.md').exists():
        findings.append(finding('low', 'project root', 'Missing DEVELOPMENT_LOG.md to preserve decisions and verification steps.', 'Log meaningful changes with test/build evidence.'))

    duplicated = duplicate_instruction_files(root)
    if len(duplicated) > 2:
        findings.append(finding('medium', 'context files', f'Multiple agent instruction files found: {", ".join(duplicated[:8])}.', 'Check for conflicts and define precedence.'))

    if tool_overload(root):
        findings.append(finding('medium', 'tooling config', 'Potential tool/MCP config present without a context policy.', 'Document when to load heavy tools and which tasks need them.'))

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
        if '.git' in path.parts or not path.is_file():
            continue
        if path.name.lower() in names:
            found.append(str(path.relative_to(root)))
    return found


def tool_overload(root: Path) -> bool:
    candidates = ['.mcp.json', 'mcp.json', 'settings.json', '.cursor']
    return any((root / name).exists() for name in candidates)


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


def to_markdown(report: Report) -> str:
    lines = [
        f'# {report.brand}',
        '',
        f'**Project:** `{report.root}`',
        f'**Score:** {report.score}/100 — {report.level.upper()}',
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
        '- Create handoffs before long breaks, compaction, or model changes.',
        '- Prefer fewer loaded tools unless the task genuinely needs them.',
    ]
    return '\n'.join(lines) + '\n'


def print_text(report: Report) -> None:
    print(f'{report.brand}: {report.root}')
    print(f'Score: {report.score}/100 ({report.level})')
    print()
    for item in report.findings:
        print(f'[{item.severity.upper()}] {item.target}: {item.message}')
        print(f'  → {item.recommendation}')


def main() -> None:
    parser = argparse.ArgumentParser(description='Audit project context health for AI coding agents.')
    parser.add_argument('path', nargs='?', default='.', help='Project path to scan')
    parser.add_argument('--json', action='store_true', help='Print JSON report')
    parser.add_argument('--markdown', action='store_true', help='Print Markdown report')
    args = parser.parse_args()

    report = scan(Path(args.path).resolve())
    if args.json:
        print(json.dumps(asdict(report), indent=2))
    elif args.markdown:
        print(to_markdown(report))
    else:
        print_text(report)


if __name__ == '__main__':
    main()
