from __future__ import annotations

import argparse
from pathlib import Path

CONTEXT_FILES = [
    'AGENTS.md', 'CLAUDE.md', 'MEMORY.md', 'DESIGN.md', 'DEVELOPMENT_LOG.md',
    'DECISIONS.md', 'HANDOFF.md', 'SECURITY_NOTES.md', '.cursorrules'
]
MAX_SOFT_BYTES = 40_000
MAX_HARD_BYTES = 120_000


def scan(root: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    present = []
    for name in CONTEXT_FILES:
        path = root / name
        if path.exists():
            present.append(name)
            size = path.stat().st_size
            if size > MAX_HARD_BYTES:
                findings.append(finding('high', name, f'Very large context file ({size} bytes). Split or summarize it.'))
            elif size > MAX_SOFT_BYTES:
                findings.append(finding('medium', name, f'Large context file ({size} bytes). Consider compacting stale sections.'))

    if not any((root / name).exists() for name in ['AGENTS.md', 'CLAUDE.md']):
        findings.append(finding('medium', 'project root', 'Missing AGENTS.md or CLAUDE.md project instructions.'))

    if not (root / 'HANDOFF.md').exists():
        findings.append(finding('low', 'project root', 'Missing HANDOFF.md for long agent sessions and resume safety.'))

    if not (root / 'DEVELOPMENT_LOG.md').exists():
        findings.append(finding('low', 'project root', 'Missing DEVELOPMENT_LOG.md to preserve decisions and verification steps.'))

    duplicate_hint_files = [p.name for p in root.glob('**/*') if p.is_file() and p.name.lower() in {'agents.md', 'claude.md'}]
    if len(duplicate_hint_files) > 2:
        findings.append(finding('medium', 'context files', 'Multiple agent instruction files found. Check for conflicting instructions.'))

    if not findings:
        findings.append(finding('info', 'project root', 'No obvious context health issues found.'))
    return findings


def finding(severity: str, target: str, message: str) -> dict[str, str]:
    return {'severity': severity, 'target': target, 'message': message}


def main() -> None:
    parser = argparse.ArgumentParser(description='Audit project context health for AI coding agents.')
    parser.add_argument('path', nargs='?', default='.', help='Project path to scan')
    args = parser.parse_args()
    root = Path(args.path).resolve()
    print(f'Agent Context Health: {root}')
    print()
    for item in scan(root):
        print(f"[{item['severity'].upper()}] {item['target']}: {item['message']}")


if __name__ == '__main__':
    main()
