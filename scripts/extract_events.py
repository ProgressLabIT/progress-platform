#!/usr/bin/env python3
"""Static AST extraction of event metadata from backend/api/events/.

No backend imports — pure ast module parsing. Runs in CI without
a backend venv, but Python 3.10+ is required for `ast.unparse`.
"""
import ast
import json
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
EVENTS_ROOT = REPO_ROOT / "backend" / "api" / "events"
OUT_PATH = REPO_ROOT / "docs" / "public" / "events-metadata.json"

# Base / scaffolding files to skip — they define base classes or mixins,
# not concrete events. Pitfall 2: production/commons/ contains mixin classes.
SKIP_FILES = {
    "base_event.py", "base_production.py", "base_inventory.py",
    "base_serial.py", "base_collaboration.py", "base_issue.py",
    "base_message.py", "base_task.py", "base_admin.py",
    "__init__.py",
}


def _extract_event_type(cls_node):
    """Find `return EventType.X` inside get_event_type() and return X."""
    for item in ast.walk(cls_node):
        if isinstance(item, ast.FunctionDef) and item.name == "get_event_type":
            for child in ast.walk(item):
                if isinstance(child, ast.Return) and isinstance(child.value, ast.Attribute):
                    return child.value.attr
    return None


def _extract_tx_collections(cls_node):
    """Find `return [...]` inside get_tx_collections() and return the list of constants."""
    for item in ast.walk(cls_node):
        if isinstance(item, ast.FunctionDef) and item.name == "get_tx_collections":
            for child in ast.walk(item):
                if isinstance(child, ast.Return) and isinstance(child.value, ast.List):
                    return [
                        elt.value for elt in child.value.elts
                        if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                    ]
    return None  # not overridden — inherited from base class


def _extract_info_model(cls_node):
    """Walk nested `class InfoModel(...):` body for AnnAssign nodes."""
    fields = []
    for item in cls_node.body:
        if isinstance(item, ast.ClassDef) and item.name == "InfoModel":
            for stmt in item.body:
                if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                    fields.append({
                        "name": stmt.target.id,
                        "type": ast.unparse(stmt.annotation),
                    })
    return fields


def _extract_subtopic(cls_node):
    """Find class-level assignment `_notification_subtopic = "..."`."""
    for stmt in cls_node.body:
        if isinstance(stmt, ast.Assign):
            for t in stmt.targets:
                if isinstance(t, ast.Name) and t.id == "_notification_subtopic":
                    if isinstance(stmt.value, ast.Constant):
                        return stmt.value.value
    return None  # inherited (or genuinely unset — extractor cannot tell from AST alone)


def extract_event_metadata(path: Path):
    """Return a metadata dict for the event class in `path`, or None if no event class found."""
    source = path.read_text()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        # Must extend at least one base whose unparsed name contains "Event"
        if not any("Event" in ast.unparse(b) for b in node.bases):
            continue
        # Pitfall 2: skip classes without get_event_type() (commons/ mixins)
        event_type = _extract_event_type(node)
        if event_type is None:
            continue
        return {
            "class_name": node.name,
            "file": str(path.relative_to(REPO_ROOT)),
            "domain": path.parent.name,
            "event_type": event_type,
            "tx_collections": _extract_tx_collections(node),
            "info_model_fields": _extract_info_model(node),
            "notification_subtopic": _extract_subtopic(node),
        }
    return None


def main():
    events = []
    for path in sorted(EVENTS_ROOT.rglob("*.py")):
        if path.name in SKIP_FILES or "__pycache__" in str(path):
            continue
        meta = extract_event_metadata(path)
        if meta:
            events.append(meta)
    OUT_PATH.write_text(json.dumps(events, indent=2))
    print(f"Extracted {len(events)} events to {OUT_PATH}")


if __name__ == "__main__":
    main()
