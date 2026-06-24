#!/usr/bin/env python3
"""
Seed the default product & position print templates into ArangoDB.

Loads every *.json file in ./print-templates/ (each a PrintTemplateRecord with
a stable `_key`) and upserts it into the `PrintTemplate` collection of the
target database(s). Idempotent: re-running overwrites the documents in place,
so it doubles as an "update the defaults" step.

Designed to run inside the API container / `progress` network, same as
db_init.py (connects to http://db:8529 with root creds from /run/secrets).

Usage (inside the network):
    python3 seed_default_print_templates.py PROGRESS [OTHER_DB ...]

After seeding, point the warehouse app at them via app config:
    product_label_template  = "default_product_label"
    position_label_template = "default_position_label"
"""

import json
import logging
import sys
from pathlib import Path

from arango import ArangoClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).resolve().parent / "print-templates"


def get_secret(name: str) -> str:
    with open(f"/run/secrets/{name}") as secret:
        return secret.read().rstrip("\n")


def load_templates() -> list[dict]:
    docs = []
    for path in sorted(TEMPLATES_DIR.glob("*.json")):
        with open(path) as fh:
            doc = json.load(fh)
        if "_key" not in doc:
            logger.warning("Skipping %s: no _key", path.name)
            continue
        docs.append(doc)
    return docs


def seed_db(db, templates: list[dict]) -> None:
    collection = db.collection("PrintTemplate")
    for doc in templates:
        # overwrite=True makes this an upsert keyed on _key (insert or replace).
        collection.insert(doc, overwrite=True, overwrite_mode="replace")
        logger.info("  upserted PrintTemplate/%s (%s)", doc["_key"], doc.get("name", ""))


def main(argv: list[str]) -> int:
    dbs = argv[1:]
    if not dbs:
        logger.error("Usage: seed_default_print_templates.py DB_NAME [DB_NAME ...]")
        return 2

    templates = load_templates()
    if not templates:
        logger.error("No template JSON files found in %s", TEMPLATES_DIR)
        return 1
    logger.info("Loaded %d template(s): %s", len(templates), ", ".join(t["_key"] for t in templates))

    client = ArangoClient(hosts="http://db:8529")
    root_creds = dict(username="root", password=get_secret("progress_db_root_pwd"))

    for db_name in dbs:
        logger.info("Seeding database '%s'...", db_name)
        db = client.db(db_name, **root_creds)
        if not db.has_collection("PrintTemplate"):
            logger.error("  '%s' has no PrintTemplate collection — run db_init first. Skipping.", db_name)
            continue
        seed_db(db, templates)

    logger.info("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
