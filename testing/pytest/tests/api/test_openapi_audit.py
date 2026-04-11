"""OpenAPI coverage audit — warn-only report.

Enumerates all FastAPI APIRoutes via app.routes introspection and reports
coverage across three dimensions: input_model, response_model, docstring.

Decisions: D-01 through D-05 (context doc).
- Test FAILS only on unhandled exceptions during the audit itself.
- Missing coverage produces WARNING-level log lines + printed table; no assertion failure.
"""
import logging

import pytest
from fastapi import UploadFile
from fastapi.routing import APIRoute
from pydantic import BaseModel

logger = logging.getLogger(__name__)


def _has_pydantic_input(route: APIRoute) -> str:
    """Return 'yes', 'multipart', or 'no' for input model presence."""
    try:
        body_params = route.dependant.body_params
    except Exception:
        return "no"

    if not body_params:
        return "no"

    for param in body_params:
        annotation = param.field_info.annotation if hasattr(param, "field_info") else None
        # UploadFile params — multipart, not a Pydantic model
        try:
            if annotation is not None and (annotation is UploadFile or (
                hasattr(annotation, "__origin__") is False and
                issubclass(annotation, UploadFile)
            )):
                return "multipart"
        except TypeError:
            pass
        # Pydantic BaseModel subclass
        try:
            if annotation is not None and issubclass(annotation, BaseModel):
                return "yes"
        except TypeError:
            pass

    # Fallback: at least one body param exists but no clear model
    return "no"


def _has_response_model(route: APIRoute) -> bool:
    return route.response_model is not None


def _has_docstring(route: APIRoute) -> bool:
    doc = getattr(route.endpoint, "__doc__", None)
    return bool(doc and doc.strip())


def _fmt(flag) -> str:
    if flag is True:
        return "Y"
    if flag is False:
        return "N"
    return str(flag)  # "multipart", "yes", "no"


def test_openapi_coverage_audit(db, mock_nats):
    """Enumerate all routes and print a coverage report. Warn-only — never fails on missing coverage."""
    from main import app

    api_routes = [r for r in app.routes if isinstance(r, APIRoute)]

    # Report columns: method | path | input_model | response_model | docstring
    rows = []
    warnings = []

    for route in api_routes:
        methods = ",".join(sorted(route.methods or []))
        path = route.path

        input_model = _has_pydantic_input(route)
        response_model = _has_response_model(route)
        has_doc = _has_docstring(route)

        rows.append((methods, path, input_model, response_model, has_doc))

        # Accumulate warnings — do NOT assert/fail on them
        if input_model == "no" and methods not in ("GET", "DELETE", "GET,DELETE"):
            warnings.append(f"WARN  {methods:8s} {path}: no Pydantic input model")
        if not response_model:
            warnings.append(f"WARN  {methods:8s} {path}: no response_model declared")
        if not has_doc:
            warnings.append(f"WARN  {methods:8s} {path}: missing docstring")

    # Print structured report
    header = f"{'METHOD':<12} {'PATH':<55} {'INPUT':>7} {'RESP':>5} {'DOC':>4}"
    sep = "-" * len(header)
    print(f"\n{sep}")
    print("OPENAPI COVERAGE AUDIT")
    print(sep)
    print(header)
    print(sep)
    for methods, path, inp, resp, doc in sorted(rows, key=lambda r: (r[1], r[0])):
        inp_flag = {"yes": "Y", "no": "N", "multipart": "M"}.get(inp, inp)
        print(f"{methods:<12} {path:<55} {inp_flag:>7} {_fmt(resp):>5} {_fmt(doc):>4}")
    print(sep)
    print(f"Total routes: {len(rows)}")
    print(f"Warnings: {len(warnings)}")
    print(sep)

    for w in warnings:
        logger.warning(w)

    # Assert: audit ran without crashing and found at least the known routes
    assert len(rows) >= 20, f"Expected >=20 API routes, found {len(rows)}"
