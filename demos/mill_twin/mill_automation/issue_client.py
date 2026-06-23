"""HTTP client for creating Issues via POST /api/event (ISSUE_CREATED).

Retargeted from the pump_anomaly automation pattern (copy — not imported).
Do NOT import from the bridge package (D-12 / AUTO-04).

Key exports:
  read_token(path)           — reads the JWT bearer token from a file
  build_linked_to(cfg)       — constructs the linked_to list (serial/work_order/operation)
  fire_issue(cfg, token, *)  — POSTs a FLAT ISSUE_CREATED body via httpx
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import httpx

from .config import MillAutomationSettings

log = logging.getLogger("mill_automation.issue_client")

# JSON field in the binding file  ->  MillAutomationSettings attribute (env fallback).
_BINDING_MAP = {
    "issue_type_key": "issue_type_key",
    "serial":         "linked_serial_key",
    "work_order":     "linked_work_order_key",
    "operation":      "linked_operation_key",
}


def read_token(path: str) -> str:
    """Read a JWT bearer token from a file (strips trailing whitespace/newlines)."""
    with open(path, "r") as f:
        return f.read().strip()


def load_binding(cfg: MillAutomationSettings) -> dict:
    """Read the live Issue binding from cfg.binding_file — fresh on every call.

    Returns a dict keyed by the cfg attribute names (issue_type_key,
    linked_serial_key, linked_work_order_key, linked_operation_key).  Each value
    comes from the JSON file when present and a non-empty string, otherwise from
    the env-configured cfg default.  Reading at call time (i.e. at fire time) is
    what lets the operator change the target Issue type / linked records at any
    moment without restarting.  Never raises — a missing/invalid file logs and
    the env defaults are used.
    """
    out = {attr: getattr(cfg, attr) for attr in _BINDING_MAP.values()}
    try:
        raw = Path(cfg.binding_file).read_text()
    except FileNotFoundError:
        return out
    except OSError as exc:
        log.warning("binding file %s unreadable (%s) — using env defaults", cfg.binding_file, exc)
        return out
    try:
        data = json.loads(raw)
    except ValueError as exc:
        log.warning("binding file %s is not valid JSON (%s) — using env defaults", cfg.binding_file, exc)
        return out
    if not isinstance(data, dict):
        log.warning("binding file %s is not a JSON object — using env defaults", cfg.binding_file)
        return out
    for jkey, attr in _BINDING_MAP.items():
        val = data.get(jkey)
        if isinstance(val, str) and val.strip():
            out[attr] = val.strip()
    return out


def build_linked_to(cfg: MillAutomationSettings, binding: dict | None = None) -> list[dict]:
    """Return the three-item linked_to list required by AUTO-03 / D-05.

    Link keys come from the live binding (``binding`` if supplied, else read
    fresh via load_binding with env fallback).  All three link types — serial,
    work_order, operation — are valid IssueLinkType values
    (backend/api/models/collaboration.py:162).
    """
    b = binding if binding is not None else load_binding(cfg)
    return [
        {"type": "serial", "key": b["linked_serial_key"]},
        {"type": "work_order", "key": b["linked_work_order_key"]},
        {"type": "operation", "key": b["linked_operation_key"]},
    ]


async def fire_issue(
    cfg: MillAutomationSettings,
    token: str,
    *,
    title: str,
    critical: bool,
    source_metric: str,
) -> None:
    """POST a FLAT ISSUE_CREATED body to the Progress API.

    Body shape mirrors pump_anomaly._fire exactly (RESEARCH §Pitfall 2):
    issue_data is at the TOP LEVEL of the body (not nested under "info").

    Authorization is via the JWT bearer token — identity fields (user_key,
    user_session_key, created_by) are env-configured to match the JWT user
    so audit trails reconcile (JWT-only-identity rule).  The token is NEVER
    logged.
    """
    binding = load_binding(cfg)
    issue_type_key = binding["issue_type_key"]
    if not issue_type_key:
        log.error(
            "issue fire skipped (%s): no issue_type_key — set it in %s or MILL_AUTO_ISSUE_TYPE_KEY",
            source_metric,
            cfg.binding_file,
        )
        return
    linked_to = build_linked_to(cfg, binding)
    body = {
        "event_type": "ISSUE_CREATED",
        "user_key": cfg.user_key,
        "user_session_key": cfg.user_session_key,
        "primary": True,
        "issue_data": {
            "issue_type_key": issue_type_key,
            "created_by": cfg.created_by,
            "critical": critical,
            "title": title,
            "linked_to": linked_to,
        },
        "source_metric": source_metric,
    }
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.post(
                f"{cfg.api_base_url}/event",
                headers={"Authorization": f"Bearer {token}"},
                json=body,
            )
    except httpx.HTTPError as exc:
        log.error("issue fire transport error: %s", exc)
        return
    if r.status_code >= 300:
        log.error(
            "issue fire failed: status=%d body=%s source=%s",
            r.status_code,
            r.text,
            source_metric,
        )
    else:
        log.info("issue fired: %s critical=%s title=%r", source_metric, critical, title)
