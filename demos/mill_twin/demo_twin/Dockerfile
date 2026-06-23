# Build context: `demos/mill_twin/` (so demo_twin/ + physics.py are reachable).
# Build command (from repo root):
#   docker build -t progress-demo-twin:dev -f demos/mill_twin/demo_twin/Dockerfile demos/mill_twin/

FROM python:3.11-slim

WORKDIR /app

# Install deps first for layer cache — requirements change less often than source.
COPY demo_twin/requirements.txt /app/demo_twin/requirements.txt
RUN pip install --no-cache-dir -r /app/demo_twin/requirements.txt

# Copy the twin package (includes physics.py — already a flat sibling from Plan 02).
# physics.py lives inside demo_twin/ so this COPY is sufficient; no separate
# bridge simulator copy needed (PUB-03: no cross-package import).
COPY demo_twin/ /app/demo_twin/

# PYTHONPATH=/app lets uvicorn resolve `demo_twin.main:app` from /app/demo_twin/.
ENV PYTHONPATH=/app

# Single-worker constraint (A3): the physics loop and HTTP handlers share one
# EngineState dataclass without a lock (asyncio GIL atomicity guarantee).
# Multiple workers = multiple processes = multiple EngineState copies = broken.
CMD ["uvicorn", "demo_twin.main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "1"]
