from pathlib import Path

from agent_context_health.cli import scan


def test_clean_minimal_repo_scores_high(tmp_path: Path):
    (tmp_path / 'README.md').write_text('# Demo\n')
    (tmp_path / 'AGENTS.md').write_text('Run tests before final.\n')
    (tmp_path / 'HANDOFF.md').write_text('No blockers.\n')
    (tmp_path / 'DEVELOPMENT_LOG.md').write_text('Initial setup.\n')

    report = scan(tmp_path)

    assert report.score >= 90
    assert report.summary['high'] == 0


def test_env_secret_risk_is_high(tmp_path: Path):
    (tmp_path / 'README.md').write_text('# Demo\n')
    (tmp_path / 'AGENTS.md').write_text('Run tests before final.\n')
    (tmp_path / 'HANDOFF.md').write_text('No blockers.\n')
    (tmp_path / 'DEVELOPMENT_LOG.md').write_text('Initial setup.\n')
    (tmp_path / '.env').write_text('API_KEY=real-looking-value\n')

    report = scan(tmp_path)

    assert report.summary['high'] >= 1
    assert any('secret' in item.message.lower() for item in report.findings)


def test_missing_agent_instructions_is_medium(tmp_path: Path):
    (tmp_path / 'README.md').write_text('# Demo\n')

    report = scan(tmp_path)

    assert report.summary['medium'] >= 1
