# syntax=docker/dockerfile:1.7
# Build context: repo root `.` (needs demos/sparkplug_sim/ + backend/api/utils/).
# Build command (from repo root):
#   docker build -t progress-sparkplug-sim:dev -f demos/sparkplug_sim/Dockerfile .

FROM python:3.11-slim

# Vendor the nats CLI for compose-level healthchecks (Plan 01-04).
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

RUN nats --version

WORKDIR /app

# Simulator deps first for layer cache.
COPY demos/sparkplug_sim/requirements.txt /app/sparkplug_sim/requirements.txt
RUN pip install --no-cache-dir -r /app/sparkplug_sim/requirements.txt

# Copy:
#  - the self-contained simulator package (its own heartbeat.py — no bridge dep),
#  - backend/api/utils/ (for nats_client + config helpers) on PYTHONPATH.
# Note: no vendored Tahu protobuf needed — the simulator encodes via pysparkplug.
COPY demos/sparkplug_sim/ /app/sparkplug_sim/
COPY backend/api/utils/   /app/backend/api/utils/

RUN touch /app/backend/__init__.py /app/backend/api/__init__.py

ENV PYTHONPATH=/app:/app/backend/api

CMD ["python", "-m", "sparkplug_sim.main"]
