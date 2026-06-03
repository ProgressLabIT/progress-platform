---
title: progress tap
description: progress tap reference — Progress Platform.
cli_validated: false
---

# `progress tap`

> Subscribes to a broker subject pattern and pretty-prints incoming messages to stdout. Acts as a generic `nats sub` wrapper with subject-shape awareness so Sparkplug raw frames (`spBv1//0.>`) and Progress notification subjects (`progress.notification.>`) render with the metadata the operator actually needs. Diagnostic-only — does not modify state.

> 🚧 Coming soon — `progress tap` is in active development; this page will be promoted to validated content when the underlying source lands.

## When to use it

- When verifying that a freshly-deployed event publishes to its expected broker subject after the post-commit fan-out.
- When debugging the top-10 events' downstream notifications (`progress.notification.production`, `progress.notification.inventory`, etc.).
- When inspecting raw Sparkplug B frames the bridge consumes — pattern `'spBv1//0.>'` per ADR-0008's broker-MQTT subject mapping.
- When triaging a production incident where the operator suspects the broker is dropping or mis-routing messages — diagnostic role per ADM-04.

## Usage

```bash
progress tap <pattern> [OPTIONS]
```

`<pattern>` is a broker subject filter (wildcards `*` and `>` supported). Quote the pattern in shells that interpret `>` as redirection.

## Options

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--server` / `-s` | `TEXT` | `nats://localhost:4222` | Broker URL. Defaults to the local broker exposed by `deploy/compose/base.yaml`. |
| `--credentials` / `-c` | `PATH` | _(none)_ | Path to a broker credentials file (`.creds`) for authenticated brokers. |
| `--format` | `Choice[json\|raw\|pretty]` | `pretty` | Output format. `pretty` renders subject + decoded payload; `json` emits one JSON line per message; `raw` is byte-for-byte. |
| `--decode-sparkplug` / `--no-decode-sparkplug` | `FLAG` | auto-detect from pattern | Decode Sparkplug B protobuf payloads via the vendored Tahu schema. Auto-on when `<pattern>` starts with `spBv1/`. |
| `--queue` | `TEXT` | _(none)_ | Subscribe as part of a broker queue group (load-balanced delivery across taps). |
| `--max` / `-n` | `INTEGER` | _(unbounded)_ | Stop after N messages. Useful for one-shot diagnostics. |
| `--help` | `FLAG` | _(off)_ | Show the help text and exit. |

Source: ADR-0001 §"What ships in v1 demo" (locks `<pattern>` and Sparkplug pretty-print) + ADR-0008 (subject-mapping shape `spBv1//0.>`). Once `cli/tap.py` ships, this table is regenerated from the Typer-decorated function signature and `cli_validated` flips to `true`.

## Example

Tap the Progress notification fan-out for production events while running the demo:

```bash
$ progress tap 'progress.notification.production' --max 3

  → progress.notification.production    13:42:17.118
    {                                                     # one JSON object per notification message
      "event_type": "JobStartedEvent",
      "event_id":   "EVT-2026-05-04-0042",
      "actor":      "operator@example.com",
      "subject":    "WO-DEMO-001 / job=J-001"
    }

  → progress.notification.production    13:42:21.901
    {
      "event_type": "StepCompletedEvent",                 # follows the JobStarted in the demo flow
      "event_id":   "EVT-2026-05-04-0043",
      "subject":    "WO-DEMO-001 / step=S-003"
    }

  → progress.notification.production    13:42:24.330
    {
      "event_type": "BatchCompletedEvent",
      "event_id":   "EVT-2026-05-04-0044",
      "subject":    "WO-DEMO-001 / batch=B-007"
    }

  3 messages received; --max reached.
```

For Sparkplug raw frames (decode auto-enables on the `spBv1/` prefix):

```bash
$ progress tap 'spBv1//0.>' --max 1
  → spBv1/0/SimGroup1/NDATA/SimNode1                      # decoded via vendored Tahu protobuf
    seq=42 metrics=[
      {name="Pump3.Vibration", type=Float, value=87.4 mm/s, ts=2026-05-04T13:42:21Z}
    ]
```

Transcript shape grounded in ADR-0001 + ADR-0008; once `cli/tap.py` ships, this example is replaced with a captured live run.

## Related

- [Operations](/admins/operations) — `progress tap` as a diagnostic per ADM-04
- [Events Reference](/events/) — what `progress tap` subscribes to
- [Integration touchpoints](/admins/integration) — broker subject taxonomy and Sparkplug subject mapping
- [ADR-0008](https://github.com/ProgressLabIT/progress-platform/blob/DEV/km/decisions/0008-natsmqtt-subject-mapping.md) — Source of truth for Sparkplug subject patterns
