# 0008 — NATS-MQTT Subject Mapping for Sparkplug

**Status:** decided
**Date:** 2026-04-28
**Audience:** S1 (bridge), S5 (demo data + walkthrough), anyone debugging on the NATS side
**Supersedes:** none

## Context

NATS-MQTT (the MQTT 3.1.1 endpoint built into NATS server 2.4+) accepts
MQTT clients but stores and routes their messages on the NATS subject
namespace. The two protocols use different separators:

- **MQTT** uses `/` as the topic separator and treats `.` as a literal
  character.
- **NATS** uses `.` as the subject separator and treats `/` as a literal
  character.

The NATS-MQTT bridge must translate. Sparkplug B v3.0.0 specifies the
literal MQTT topic prefix `spBv1.0/` — which contains a `.` — so this
mapping is a load-bearing detail for any debugging or alternate-consumer
work that happens on the NATS side of the bridge.

Two consumer paths exist for Sparkplug frames in this workstream:

1. **The Sparkplug bridge consumes via aiomqtt** (an MQTT client library)
   directly against the NATS-MQTT endpoint. This path uses MQTT semantics
   end-to-end. The escape rules below DO NOT affect bridge code.
2. **Debugging or alternate consumers via `nats sub`** subscribe directly
   to NATS subjects, where the bridged MQTT messages appear under their
   translated names. The escape rules ARE visible here.

Our decoded JSON output, published by the bridge to
`progress.sparkplug.<group>.<edge>...` (per ADR-0002), is plain NATS — no
escaping. The escape rules below apply only to the raw Sparkplug-protobuf
frames that the NATS-MQTT bridge surfaces under their translated topic
names.

## Decision

### Conversion rules

When the NATS-MQTT bridge translates an MQTT topic into a NATS subject:

| Source character | Replaced with | Direction |
|---|---|---|
| `/` (MQTT separator) | `.` | MQTT → NATS |
| `.` (literal in MQTT topic) | `//` | MQTT → NATS |

The replacement is **a substitution, not an insertion**. The single
character is replaced by the two characters. There is no extra `.` left
behind from the original `.`; the original `.` is gone.

### Worked example

The Sparkplug v3.0.0 NDATA topic for an edge node `edge1` and device
`pump3` in group `plant1`:

```
MQTT:  spBv1.0/plant1/NDATA/edge1/pump3
```

Apply the table left to right:

| Step | Input | Action | Output so far |
|---|---|---|---|
| 1 | `spBv1` | literal | `spBv1` |
| 2 | `.` | replace with `//` | `spBv1//` |
| 3 | `0` | literal | `spBv1//0` |
| 4 | `/` | replace with `.` | `spBv1//0.` |
| 5 | `plant1` | literal | `spBv1//0.plant1` |
| 6 | `/` | replace with `.` | `spBv1//0.plant1.` |
| 7 | `NDATA/edge1/pump3` | replace each `/` with `.` | `spBv1//0.plant1.NDATA.edge1.pump3` |

Result:

```
NATS:  spBv1//0.plant1.NDATA.edge1.pump3
```

The leading `spBv1//0` (no dot between `//` and `0`) is the part to watch
for — `//` is the replacement for the original dot, not a prefix to it.

### Wildcards on the NATS side

Subscribe to all Sparkplug v1.0 traffic on the NATS side:

```bash
nats sub 'spBv1//0.>'
```

Subscribe to a specific group's traffic:

```bash
nats sub 'spBv1//0.plant1.>'
```

Subscribe to NDATA only across all groups (cannot be done with a single
NATS wildcard because `NDATA` is the third token and NATS wildcards do not
have token-level filters; use `>` and filter client-side, or run a
dedicated subscription per group):

```bash
nats sub 'spBv1//0.>' | grep -E '\\.NDATA\\.'
```

### Reverse direction

Subscribers connecting via MQTT to the NATS-MQTT endpoint see the original
MQTT topic shape; they never see the escaped NATS form. The bridge handles
the translation in both directions transparently.

### Debugging recipe

For a presenter or developer who wants to verify Sparkplug traffic from the
NATS side without running the bridge:

```bash
# Tail all Sparkplug traffic with pretty hex output of protobuf payloads
nats sub 'spBv1//0.>' --raw | xxd

# Count frames per second to spot disconnects
nats sub 'spBv1//0.>' --count 100

# Watch the primary-host STATE retain
nats sub 'spBv1//0.STATE.>'
```

For protobuf-decoded readable output, `progress sparkplug tap` (per
ADR-0006) wraps `nats sub 'spBv1//0.>'` and decodes via the vendored Tahu
protobuf, printing JSON. That subcommand is the recommended debugging
surface; raw `nats sub` is the fallback if the CLI is not installed.

### What this DOES NOT affect

- The bridge's own MQTT subscription via aiomqtt. aiomqtt speaks MQTT to
  NATS-MQTT and receives original MQTT topic names; the NATS-side escape
  is invisible to it.
- The bridge's own publishes to `progress.sparkplug.<group>.<edge>...`,
  which are plain NATS subjects with no MQTT origin and no escape involved.
- The historian ingester, which consumes plain `progress.sparkplug.>` JSON
  payloads, not raw bridged Sparkplug frames.
- The webapp UI, which consumes `progress.sparkplug.>` (live) and the
  `/api/uns/*` endpoints (history/topology), neither of which surfaces the
  raw bridged form.

## Trade-offs and rejected options

**Custom subject prefix on the bridge instead of letting NATS-MQTT
translate.** Considered configuring the NATS-MQTT bridge to publish raw
Sparkplug frames under a custom prefix that avoids the dot. Rejected
because it would conflict with the standard NATS-MQTT behaviour and any
operator already familiar with NATS-MQTT would expect the documented
escape rule. Conformance to the standard wins.

**Asking the bridge to publish a "shadow" subject without escapes.**
Rejected. Doubles the message volume on a load-bearing subject for purely
cosmetic value. The decoded JSON path on `progress.sparkplug.>` already
provides a clean subject namespace; the escaped raw path is for
spec-debugging consumers who care about raw protobuf.

## Consequences

- S1 (bridge) does not need to handle the escape inside its code path; the
  documentation here is for ops and debugging.
- The `progress sparkplug tap` subcommand (per ADR-0006) bakes in
  `spBv1//0.>` as the default subscription pattern when invoked with
  `--sparkplug` or equivalent flag.
- The KM intro doc (`km/architecture/sparkplug.md`) reproduces the
  worked example so system integrators reading it find the rule on first
  search.
- The walkthrough script for the demo, if it surfaces raw NATS subjects on
  stage, uses the escaped form so the audience sees what they would see.

## Related

- ADR-0002 — NATS subject taxonomy. The decoded `progress.sparkplug.>`
  subjects defined there are unaffected by this mapping; only the raw
  bridged form is.
- ADR-0006 — `progress` CLI; `progress sparkplug tap` uses the escaped
  form as default.
- NATS-MQTT documentation: <https://docs.nats.io/running-a-nats-service/configuration/mqtt>
