# Build context: `demos/mill_twin/` (so mill_automation/ is reachable).
# Build command (from repo root):
#   docker build -t progress-mill-automation:dev -f demos/mill_twin/mill_automation/Dockerfile demos/mill_twin/

FROM python:3.11-slim

WORKDIR /app

# Install deps first for layer cache — requirements change less often than source.
COPY mill_automation/requirements.txt /app/mill_automation/requirements.txt
RUN pip install --no-cache-dir -r /app/mill_automation/requirements.txt

# Copy the automation package.
COPY mill_automation/ /app/mill_automation/

# PYTHONPATH=/app lets Python resolve `mill_automation` from /app/mill_automation/.
ENV PYTHONPATH=/app

# Single-process subscriber — minimal deps only (nats-py, httpx, pydantic-settings).
CMD ["python", "-m", "mill_automation"]
