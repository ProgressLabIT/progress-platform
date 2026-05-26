"""Idempotent DDL bootstrap for the progress_historian database.

Per CONTEXT.md D-08 + RESEARCH §Pattern 1/2 — runs on every ingester startup.
All DDL is IF-NOT-EXISTS or has if_not_exists => TRUE; refresh policies do
their own existence check via timescaledb_information.jobs (RESEARCH §Pitfall 3).

Module is historian-local. Bridge process MUST NOT import this module
(RESEARCH §Pitfall 4 — keeps asyncpg out of bridge's runtime).
"""
import logging

import asyncpg

from .schema import (
    CAGG_1S_DDL,
    CAGG_30S_DDL,
    CAGG_5M_DDL,
    HYPERTABLE_DDL,
    INDEXES_DDL,
    POLICY_1S,
    POLICY_30S,
    POLICY_5M,
    RETENTION_POLICY,
    TABLE_DDL,
)

logger = logging.getLogger("sparkplug_bridge.historian.bootstrap")


async def ensure_database(admin_url: str, db_name: str) -> None:
    """Idempotent CREATE DATABASE on the postgres system DB.

    asyncpg connections are autocommit by default — CREATE DATABASE works
    directly. Do NOT wrap in a transaction (RESEARCH §Pitfall 2 —
    InvalidTransactionStateError otherwise).

    SECURITY: db_name MUST come from trusted config (env var via
    HistorianSettings), NEVER user input — Postgres does not allow
    placeholders for identifiers, so the f-string is the canonical pattern
    (RESEARCH §Pattern 1).
    """
    conn = await asyncpg.connect(admin_url)
    try:
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", db_name,
        )
        if not exists:
            await conn.execute(f'CREATE DATABASE "{db_name}"')
            logger.info("database created: %s", db_name)
        else:
            logger.info("database already exists: %s", db_name)
    finally:
        await conn.close()


async def ensure_schema(target_url: str) -> None:
    """Idempotent extension + table + hypertable + indexes + CAGGs + policies + retention.

    Order matters: extension before table (timescaledb types referenced by
    create_hypertable); table before indexes/CAGGs; CAGGs before policies.
    """
    conn = await asyncpg.connect(target_url)
    try:
        await conn.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")
        logger.info("extension ready: timescaledb")

        await conn.execute(TABLE_DDL)
        logger.info("table ready: metric_samples")

        await conn.execute(HYPERTABLE_DDL)
        logger.info("hypertable ready: metric_samples")

        await conn.execute(INDEXES_DDL)
        logger.info("indexes ready: metric_samples")

        for name, view_ddl in (
            ("metric_samples_1s", CAGG_1S_DDL),
            ("metric_samples_30s", CAGG_30S_DDL),
            ("metric_samples_5m", CAGG_5M_DDL),
        ):
            await conn.execute(view_ddl)
            logger.info("continuous aggregate ready: %s", name)

        for name, policy_ddl in (
            ("metric_samples_1s", POLICY_1S),
            ("metric_samples_30s", POLICY_30S),
            ("metric_samples_5m", POLICY_5M),
        ):
            await conn.execute(policy_ddl)
            logger.info("refresh policy ready: %s", name)

        await conn.execute(RETENTION_POLICY)
        logger.info("retention policy ready: metric_samples (7 days)")
    finally:
        await conn.close()


async def bootstrap(admin_url: str, target_url: str, target_db: str) -> None:
    """Top-level entrypoint — safe to call on every ingester startup.

    Order:
      1. ensure_database (admin connection to postgres system DB)
      2. ensure_schema   (target connection to progress_historian)
    """
    await ensure_database(admin_url, target_db)
    await ensure_schema(target_url)
