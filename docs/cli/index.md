---
title: CLI Reference
description: CLI Reference — Progress Platform.
---

# CLI Reference

The `progress` command-line tool spins up, restores, and inspects the Progress Platform Compose stack.

## Commands

| Command | Purpose |
|---------|---------|
| [`progress init`](/cli/init) | Initialize a new Progress Platform deployment from the Compose stack |
| [`progress restore`](/cli/restore) | Restore the database from a backup archive |
| [`progress tap`](/cli/tap) | Tap into NATS subjects for live event diagnostics |

## How CLI examples stay in sync

Every CLI code block in these pages is verified by a Typer `CliRunner` snapshot test in CI. If a flag is renamed or removed, the docs build fails. Pages that document commands not yet shipped are marked `cli_validated: false` and skipped by the gate until the implementation lands.

Related: [Events](/events/) · [API](/api/) · [Admins](/admins/) · [Home](/)
