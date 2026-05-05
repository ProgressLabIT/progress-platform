"""Snapshot tests for `progress {init,restore,tap} --help`.

CLI-04 drift gate: if a documented flag is renamed, removed, or added in
cli/main.py without updating docs/cli/{command}.md, this test fails.

Pitfall #1 (RESEARCH.md): docs/cli/{cmd}.md may set frontmatter
`cli_validated: false` while the underlying cli/{cmd}.py is still owned
by the Sparkplug demo S4 session and not yet shipped.
"""
import re
from pathlib import Path

import pytest
from typer.testing import CliRunner

from cli.main import app

REPO_ROOT = Path(__file__).parent.parent.parent
SNAPSHOTS_DIR = Path(__file__).parent / "snapshots"
SNAPSHOTS_DIR.mkdir(exist_ok=True)
DOCS_CLI_DIR = REPO_ROOT / "docs" / "cli"

_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
_CLI_VALIDATED_RE = re.compile(r"^cli_validated:\s*(false|true)\s*$", re.MULTILINE | re.IGNORECASE)


def _frontmatter_says_unvalidated(md_path: Path) -> bool:
    if not md_path.exists():
        return False
    text = md_path.read_text()
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return False
    v = _CLI_VALIDATED_RE.search(m.group(1))
    return bool(v and v.group(1).lower() == "false")


@pytest.mark.parametrize("command", ["init", "restore", "tap"])
def test_cli_help_matches_snapshot(command: str):
    md_path = DOCS_CLI_DIR / f"{command}.md"
    if not md_path.exists():
        pytest.skip(f"docs/cli/{command}.md not yet present")
    if _frontmatter_says_unvalidated(md_path):
        pytest.skip(
            f"docs/cli/{command}.md has cli_validated: false "
            f"(awaiting sparkplug-demo S4 to ship cli/{command}.py)"
        )

    runner = CliRunner()
    result = runner.invoke(app, [command, "--help"])
    assert result.exit_code == 0, (
        f"`progress {command} --help` failed (exit {result.exit_code}). "
        f"Either cli/{command}.py is not registered on the Typer app, "
        f"or its --help raised. Mark docs/cli/{command}.md "
        f"`cli_validated: false` until sparkplug-demo S4 ships the source."
        f"\n\nOutput:\n{result.output}"
    )

    snapshot_file = SNAPSHOTS_DIR / f"progress_{command}_help.txt"
    if not snapshot_file.exists():
        snapshot_file.write_text(result.output)
        pytest.skip(
            f"Wrote initial snapshot for `progress {command} --help`. Re-run."
        )

    expected = snapshot_file.read_text()
    assert result.output == expected, (
        f"`progress {command} --help` output drifted from snapshot. "
        f"Either update docs/cli/{command}.md to match the new help text, "
        f"or rm {snapshot_file} and re-run to refresh the snapshot intentionally."
    )
