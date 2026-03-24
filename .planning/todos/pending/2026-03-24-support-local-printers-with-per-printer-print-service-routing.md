---
created: 2026-03-24T14:44:39.955Z
title: Support local printers with per-printer print service routing
area: api
files:
  - backend/print-service/main.py
  - backend/print-service/tcp_sender.py
  - backend/print-service/config.py
  - backend/api/endpoints/print.py
  - backend/api/models/print_job.py
  - backend/api/managers/server_event_manager.py
---

## Problem

The print service currently subscribes to a single shared SSE topic (`print-jobs`). If multiple instances run on different machines — which is necessary for locally-connected (USB/driver-only) printers — all instances receive every job and would all attempt to relay the same print job to their local printer.

This also blocks Dymo LabelWriter support: Dymo printers don't speak raw TCP/9100 (Zebra protocol). They require a local HTTP web service (`http://127.0.0.1:41951`, Dymo Label Web Service) running on the same machine as the print service. So a Dymo-capable print service instance must run on the Windows/macOS host where Dymo software is installed, and it should only receive jobs intended for that specific printer.

## Solution

**Per-printer SSE routing** using the printer's DB key as the topic discriminator:

1. **`ServerEventManager`**: Already supports arbitrary topic strings. No changes needed.
2. **`print.py` API endpoint**: Change `subtopic` from `"print-jobs"` to `f"print-jobs:{printer_key}"` when enqueuing a job. Requires `printer_key` in `PrintJobRequest`.
3. **`/print-jobs/stream` endpoint**: Accept `?printer_key=` query param; subscribe to `print-jobs:{printer_key}` topic.
4. **`print_job.py` model**: Add `printer_key: str` field to `PrintJobRequest`. Keep `printer_host`/`printer_port` for TCP printers; make optional for local printer types.
5. **`config.py` (print service)**: Add `printer_key` setting (`PROGRESS_PRINT_SERVICE_PRINTER_KEY`).
6. **`main.py` (print service)**: Subscribe to `/print-jobs/stream?printer_key={config.printer_key}` instead of the unfiltered stream. Add `dymo` branch in `handle_job()` that HTTP-POSTs to `localhost:41951` instead of raw TCP.

**For Dymo specifically:** Add `send_dymo()` in `tcp_sender.py` using `httpx` to POST to the Dymo Label Web Service. Printer type `dymo` added to the printer model and `PrintFormat` enum. Deployment constraint: print service host must be Windows or macOS (Dymo software runs on these only, not Linux).
