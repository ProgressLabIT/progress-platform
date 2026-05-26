# Vendored: Eclipse Tahu Sparkplug B Protobuf

**Upstream:** https://github.com/eclipse-tahu/tahu
**Commit SHA:** 5736e404889d4b95910613040a99ba79589ffb13
**Fetched:** 2026-04-29 (master HEAD at fetch time)
**License:** Eclipse Public License 2.0 (see `LICENSE`)
**NOTICE preserved:** see `NOTICE` (required by EPL-2.0 § 4(b))

## Purpose

The Progress Sparkplug bridge (`backend/sparkplug_bridge/`) decodes inbound
Sparkplug B protobuf frames using these bindings. Decoupling the bridge from
`pysparkplug` (which the simulator uses for encoding) keeps Phase 2's
session-state work free to swap encoders without touching the decoder.

## What is vendored

- `sparkplug_b.proto` — upstream `.proto` schema (verbatim from upstream `sparkplug_b/sparkplug_b.proto`).
- `sparkplug_b_pb2.py` — **REGENERATED** by us against modern protobuf, NOT
  copied from upstream. See "Why regenerate" below.
- `LICENSE` — upstream EPL-2.0 license text (upstream filename: `LICENCE`,
  British spelling; renamed to `LICENSE` to match the conventional Python /
  GitHub filename. Content is byte-for-byte identical to upstream).
- `NOTICE` — upstream `notice.html` (Eclipse Foundation Software User
  Agreement) preserved verbatim and renamed to `NOTICE` to match the
  conventional Python project filename. Content is byte-for-byte identical
  to upstream `notice.html`.

## Why regenerate `_pb2.py`

Upstream's checked-in `sparkplug_b_pb2.py` was generated against
`protobuf<3.20` and uses `reflection.GeneratedProtocolMessageType` plus the
pre-API-2 descriptor shape. These APIs were removed in `protobuf>=4`.
`pysparkplug==0.6.1` pulls in `protobuf>=5.28.2`, so importing the upstream
`_pb2.py` blows up at import time with errors like:

    AttributeError: module 'google.protobuf.descriptor' has no attribute
    'GeneratedProtocolMessageType'

Regenerating produces a modern API-compatible binding. The regenerated file
in this directory was produced against `protobuf 7.34.1` (verified locally
2026-04-29) and is forward-compatible with `protobuf>=5.28.2`.

## Regeneration command

To re-vendor (when upstream proto changes):

```bash
cd backend/sparkplug
# delete the old generated file
rm sparkplug_b_pb2.py
# regenerate from the proto with whatever protoc is on PATH
protoc --python_out=. sparkplug_b.proto
# OR (if protoc is not installed locally — recommended for this repo
# since uv is the project's standard)
uv tool run --from grpcio-tools python -m grpc_tools.protoc --python_out=. -I. sparkplug_b.proto
```

The second form is what produced the file currently checked in — it pulls
`grpcio-tools` (which bundles `protoc`) into an ephemeral uv tool venv and
runs it against the local `.proto`.

Verify with:

```bash
uv run --no-project --with 'protobuf>=5.28.2' python -c "from backend.sparkplug import sparkplug_b_pb2; print(sparkplug_b_pb2.Payload.__name__)"
```

Should print `Payload` and exit 0.

## When to refresh

- When upstream Eclipse Tahu publishes a Sparkplug spec update (rare).
- When `protobuf` major version bumps in our requirements force a regen.

Update the commit SHA above when refreshing.
