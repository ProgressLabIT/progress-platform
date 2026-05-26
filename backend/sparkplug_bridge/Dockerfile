# syntax=docker/dockerfile:1.7
# Build context: `backend/` (so we can COPY both sparkplug_bridge/ and api/utils/).
# Build command (from repo root):
#   docker build -t progress-sparkplug-bridge:dev -f backend/sparkplug_bridge/Dockerfile backend/

FROM python:3.11-slim

# Vendor the nats CLI for compose-level healthchecks (Plan 01-04).
# Pin per RESEARCH §Standard Stack — verified GitHub release 2026-04-29.
ARG NATSCLI_VERSION=0.3.2
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl unzip ca-certificates \
    && curl -sL "https://github.com/nats-io/natscli/releases/download/v${NATSCLI_VERSION}/nats-${NATSCLI_VERSION}-linux-amd64.zip" -o /tmp/nats.zip \
    && unzip -j /tmp/nats.zip "nats-${NATSCLI_VERSION}-linux-amd64/nats" -d /usr/local/bin/ \
    && chmod +x /usr/local/bin/nats \
    && rm /tmp/nats.zip \
    && apt-get purge -y curl unzip \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Verify the nats CLI is on PATH and runnable inside the slim base.
RUN nats --version

WORKDIR /app

# Bridge requirements first for layer cache.
COPY sparkplug_bridge/requirements.txt /app/sparkplug_bridge/requirements.txt
RUN pip install --no-cache-dir -r /app/sparkplug_bridge/requirements.txt

# Copy the bridge package + the existing api/utils/ helpers (nats_client, config).
# The vendored Tahu protobuf at backend/sparkplug/ is required by the decoder.
COPY sparkplug_bridge/ /app/sparkplug_bridge/
COPY api/utils/        /app/backend/api/utils/
COPY sparkplug/        /app/backend/sparkplug/

# api/utils/__init__.py needs to exist (mirrors the source tree).
RUN touch /app/backend/__init__.py /app/backend/api/__init__.py

# PYTHONPATH lets the bridge import `from utils import nats_client` (existing
# helper at backend/api/utils/nats_client.py) AND `from backend.sparkplug import
# sparkplug_b_pb2` (vendored Tahu).
ENV PYTHONPATH=/app:/app/backend/api

CMD ["python", "-m", "sparkplug_bridge.main"]
