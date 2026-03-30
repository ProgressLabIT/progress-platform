"""
PrintTemplate Migration: v2/v4 → v5 Schema Format

Converts PrintTemplate documents in ArangoDB to pdfme v5 format:
  1. Schemas from keyed objects → arrays with 'name' property
  2. Link data (linkType, linkValue) embedded directly into schema fields
  3. backgroundColor guaranteed on text fields (defaults to empty string)
  4. pdfmeVersion marker set to '5.0.0'
  5. 'columns' key removed from template (names now live in schemas)

Usage:
  python 227-print-template-schema-v5.py                     # dry run (default)
  python 227-print-template-schema-v5.py --apply             # apply migration
  python 227-print-template-schema-v5.py --verify            # verify post-migration

Environment variables (all prefixed with PROGRESS_ to match platform convention):
  PROGRESS_ARANGO_URL       (default: http://localhost:8529)
  PROGRESS_DB_NAME          (default: PROGRESS_TEST)
  PROGRESS_API_DB_USERNAME  (default: root)
  PROGRESS_API_DB_PWD       (default: "")
"""

import argparse
import logging
import os
import sys
from copy import deepcopy
from datetime import datetime, timezone

from arango import ArangoClient
from arango.exceptions import (
    ArangoServerError,
    TransactionAbortError,
    TransactionCommitError,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("migration-227")

COLLECTION = "PrintTemplate"
TARGET_VERSION = "5.0.0"
VALID_LINK_TYPES = {"none", "preset", "custom_field", "template_expression"}


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def connect():
    url = os.getenv("PROGRESS_ARANGO_URL", "http://localhost:8529")
    db_name = os.getenv("PROGRESS_DB_NAME", "PROGRESS_TEST")
    username = os.getenv("PROGRESS_API_DB_USERNAME", "root")
    password = os.getenv("PROGRESS_API_DB_PWD", "")

    log.info("Connecting to %s  db=%s  user=%s", url, db_name, username)
    client = ArangoClient(hosts=url)
    return client.db(db_name, username=username, password=password)


def candidates(db):
    """Return PrintTemplate documents that still have the old keyed-object schema format."""
    aql = """
    FOR doc IN @@col
      FILTER doc.template != null AND doc.template.schemas != null
      FILTER LENGTH(doc.template.schemas) > 0
      FILTER !IS_ARRAY(doc.template.schemas[0])
      RETURN doc
    """
    return list(db.aql.execute(aql, bind_vars={"@col": COLLECTION}))


# ---------------------------------------------------------------------------
# Migration logic (pure data transforms)
# ---------------------------------------------------------------------------

def migrate_field(field_name: str, field_spec: dict, link_info: dict) -> dict:
    """Build a v5 field dict from a v2/v4 keyed field spec + its link record."""
    field = {**field_spec, "name": field_name}

    link_type = link_info.get("type", "none") or "none"
    link_value = link_info.get("value", "") or ""
    field["linkType"] = link_type
    field["linkValue"] = link_value

    if field.get("type") == "text" and "backgroundColor" not in field:
        field["backgroundColor"] = ""

    return field


def migrate_document(doc: dict) -> dict:
    """
    Return a copy of *doc* with template.schemas converted to v5 format.

    Raises ValueError if the result fails validation.
    """
    template = deepcopy(doc["template"])
    links = doc.get("links") or {}

    new_schemas: list[list[dict]] = []
    for page_schema in template["schemas"]:
        page_fields = []
        for field_name, field_spec in page_schema.items():
            field_link = links.get(field_name, {})
            page_fields.append(migrate_field(field_name, field_spec, field_link))
        new_schemas.append(page_fields)

    template["schemas"] = new_schemas
    template["pdfmeVersion"] = TARGET_VERSION
    template.pop("columns", None)

    validate_v5_template(template, doc.get("_key", "?"))
    return template


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_v5_template(template: dict, doc_key: str):
    """Raise ValueError if the template does not satisfy pdfme v5 invariants."""
    schemas = template.get("schemas", [])
    if not schemas:
        raise ValueError(f"[{doc_key}] schemas is empty after migration")

    for page_idx, page in enumerate(schemas):
        if not isinstance(page, list):
            raise ValueError(
                f"[{doc_key}] page {page_idx}: expected list, got {type(page).__name__}"
            )
        for field_idx, field in enumerate(page):
            _validate_field(field, doc_key, page_idx, field_idx)

    if template.get("pdfmeVersion") != TARGET_VERSION:
        raise ValueError(f"[{doc_key}] pdfmeVersion is not {TARGET_VERSION}")


def _validate_field(field: dict, doc_key: str, page_idx: int, field_idx: int):
    loc = f"[{doc_key}] page {page_idx} field {field_idx}"

    if "name" not in field:
        raise ValueError(f"{loc}: missing 'name' property")

    if "type" not in field:
        raise ValueError(f"{loc} ({field['name']}): missing 'type' property")

    link_type = field.get("linkType")
    if link_type not in VALID_LINK_TYPES:
        raise ValueError(
            f"{loc} ({field['name']}): linkType '{link_type}' not in {VALID_LINK_TYPES}"
        )

    if "linkValue" not in field:
        raise ValueError(f"{loc} ({field['name']}): missing 'linkValue'")

    if field["type"] == "text" and "backgroundColor" not in field:
        raise ValueError(f"{loc} ({field['name']}): text field missing 'backgroundColor'")


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def dry_run(db):
    docs = candidates(db)
    if not docs:
        log.info("No documents require migration.")
        return

    log.info("Found %d document(s) to migrate (dry run):\n", len(docs))
    for doc in docs:
        key = doc["_key"]
        name = doc.get("name", "")
        try:
            migrated_template = migrate_document(doc)
            page_summary = ", ".join(
                f"page {i}: {len(p)} fields" for i, p in enumerate(migrated_template["schemas"])
            )
            log.info("  OK  %-20s  %-30s  %s", key, name, page_summary)

            links = doc.get("links") or {}
            if links:
                embedded = []
                for page in migrated_template["schemas"]:
                    for f in page:
                        if f.get("linkType", "none") != "none":
                            embedded.append(f"    {f['name']}: {f['linkType']}={f.get('linkValue','')}")
                if embedded:
                    log.info("      Links embedded:\n%s", "\n".join(embedded))

        except ValueError as exc:
            log.error("  FAIL  %-20s  %-30s  %s", key, name, exc)

    log.info("\nDry run complete. Re-run with --apply to perform the migration.")


def apply_migration(db):
    docs = candidates(db)
    if not docs:
        log.info("No documents require migration. All templates are already v5.")
        return

    log.info("Migrating %d document(s) inside a transaction...", len(docs))

    # Pre-compute all updates and validate before touching the database
    updates: list[tuple[str, dict]] = []
    for doc in docs:
        try:
            migrated_template = migrate_document(doc)
        except ValueError as exc:
            log.error("Validation failed for %s: %s — aborting.", doc["_key"], exc)
            sys.exit(1)
        updates.append((doc["_key"], migrated_template))

    now = datetime.now(timezone.utc).isoformat()

    txn_db = db.begin_transaction(
        read=[COLLECTION],
        write=[COLLECTION],
    )

    try:
        col = txn_db.collection(COLLECTION)
        for doc_key, template in updates:
            col.update({
                "_key": doc_key,
                "template": template,
                "_migrated_at": now,
                "_migrated_from_version": "2.x",
            })
            log.info("  Updated %s", doc_key)

        # Final sanity: re-read every updated doc inside the txn and validate
        for doc_key, _ in updates:
            refreshed = col.get(doc_key)
            validate_v5_template(refreshed["template"], doc_key)

        txn_db.commit_transaction()
        log.info("Transaction committed. %d document(s) migrated successfully.", len(updates))

    except (ValueError, ArangoServerError, TransactionCommitError) as exc:
        log.error("Migration failed — aborting transaction: %s", exc)
        try:
            txn_db.abort_transaction()
        except TransactionAbortError:
            pass
        sys.exit(1)


def verify(db):
    aql = """
    FOR doc IN @@col
      FILTER doc.template != null AND doc.template.schemas != null
      LET isV5 = LENGTH(doc.template.schemas) > 0
                  AND IS_ARRAY(doc.template.schemas[0])
                  AND LENGTH(doc.template.schemas[0]) > 0
                  AND HAS(doc.template.schemas[0][0], 'name')

      LET textBgOk = (
        FOR page IN doc.template.schemas
          FOR field IN page
            FILTER field.type == 'text'
            RETURN HAS(field, 'backgroundColor')
      )

      LET linkFields = (
        FOR page IN doc.template.schemas
          FOR field IN page
            FILTER field.linkType != null AND field.linkType != 'none'
            RETURN { name: field.name, linkType: field.linkType, linkValue: field.linkValue }
      )

      RETURN {
        _key: doc._key,
        name: doc.name,
        isV5: isV5,
        pdfmeVersion: doc.template.pdfmeVersion,
        allTextBgOk: LENGTH(textBgOk) == 0 OR MIN(textBgOk) == true,
        linkedFields: linkFields,
        migratedAt: doc._migrated_at
      }
    """
    results = list(db.aql.execute(aql, bind_vars={"@col": COLLECTION}))
    if not results:
        log.info("No PrintTemplate documents found.")
        return

    all_ok = True
    for r in results:
        status = "OK" if (r["isV5"] and r["allTextBgOk"]) else "ISSUE"
        if status == "ISSUE":
            all_ok = False
        log.info(
            "  %s  %-20s  %-30s  v5=%s  bg=%s  ver=%s  migrated=%s  links=%d",
            status, r["_key"], r["name"],
            r["isV5"], r["allTextBgOk"], r.get("pdfmeVersion"),
            r.get("migratedAt", "-"), len(r.get("linkedFields", [])),
        )

    if all_ok:
        log.info("\nAll %d template(s) pass v5 validation.", len(results))
    else:
        log.warning("\nSome templates have issues — review the output above.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Migrate PrintTemplate schemas to pdfme v5 format."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--apply", action="store_true",
        help="Apply the migration inside a transaction (default is dry run).",
    )
    group.add_argument(
        "--verify", action="store_true",
        help="Verify all templates are in v5 format (post-migration check).",
    )
    args = parser.parse_args()

    db = connect()

    if args.verify:
        verify(db)
    elif args.apply:
        apply_migration(db)
    else:
        dry_run(db)


if __name__ == "__main__":
    main()
