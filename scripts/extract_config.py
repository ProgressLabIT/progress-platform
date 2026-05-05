#!/usr/bin/env python3
"""Static AST extraction of PROGRESS_* env vars from backend/api/utils/config.py.

No backend imports — pure ast module parsing. Runs in CI without
a backend venv, but Python 3.10+ is required for `ast.unparse`.
"""
import ast
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
CONFIG_PATH = REPO_ROOT / "backend" / "api" / "utils" / "config.py"
OUT_PATH = REPO_ROOT / "docs" / "public" / "config-metadata.md"


def _extract_env_prefix(cls_node: ast.ClassDef) -> str:
    """Return the `env_prefix` value from `model_config = SettingsConfigDict(...)` or "" if absent."""
    for stmt in cls_node.body:
        if not isinstance(stmt, ast.Assign):
            continue
        for target in stmt.targets:
            if not (isinstance(target, ast.Name) and target.id == "model_config"):
                continue
            if not isinstance(stmt.value, ast.Call):
                continue
            for kw in stmt.value.keywords:
                if kw.arg == "env_prefix" and isinstance(kw.value, ast.Constant):
                    return kw.value.value
    return ""


def _extract_secrets_doc(cls_node: ast.ClassDef) -> list[str]:
    """Walk class-body string-literal expressions; harvest bullet items under `docker secrets`."""
    secrets: list[str] = []
    for stmt in cls_node.body:
        if not (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant)):
            continue
        text = stmt.value.value
        if not isinstance(text, str):
            continue
        if "docker secrets" not in text.lower():
            continue
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("- "):
                secrets.append(stripped[2:].strip())
    return secrets


def extract_config_metadata() -> tuple[list[dict], list[str]]:
    """Parse the Settings class and return (fields, secrets)."""
    source = CONFIG_PATH.read_text()
    tree = ast.parse(source)
    fields: list[dict] = []
    secrets: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        if not any("BaseSettings" in ast.unparse(b) for b in node.bases):
            continue
        env_prefix = _extract_env_prefix(node)
        secrets = _extract_secrets_doc(node)
        secret_field_names = {
            s[len(env_prefix):] if env_prefix and s.startswith(env_prefix) else s
            for s in secrets
        }
        for stmt in node.body:
            if not (isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name)):
                continue
            field_name = stmt.target.id
            fields.append({
                "name": field_name,
                "env_var": f"{env_prefix.upper()}{field_name.upper()}",
                "type": ast.unparse(stmt.annotation),
                "default": ast.unparse(stmt.value) if stmt.value is not None else "—",
                "is_secret": field_name in secret_field_names,
            })
    return fields, secrets


def render_markdown(fields: list[dict], secrets: list[str]) -> str:
    """Render the markdown table + Docker secrets bullet list."""
    lines: list[str] = []
    lines.append("| Env var | Type | Default | Notes |")
    lines.append("|---------|------|---------|-------|")
    for f in fields:
        default = f["default"]
        default_display = "_(empty)_" if default == "''" else default
        notes = "**Provided as Docker secret**" if f["is_secret"] else ""
        lines.append(
            f"| `{f['env_var']}` | `{f['type']}` | `{default_display}` | {notes} |"
        )
    output = "\n".join(lines) + "\n"
    if secrets:
        output += (
            "\n### Docker secrets\n\n"
            "These values are provided via Docker secrets (mounted under "
            "`/run/secrets/`) and are read directly from those files at startup:\n\n"
        )
        output += "\n".join(f"- `{s}`" for s in secrets) + "\n"
    return output


def main() -> None:
    fields, secrets = extract_config_metadata()
    OUT_PATH.write_text(render_markdown(fields, secrets))
    print(f"Extracted {len(fields)} env vars + {len(secrets)} secrets to {OUT_PATH}")


if __name__ == "__main__":
    main()
