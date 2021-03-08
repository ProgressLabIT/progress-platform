FROM python:3.8-slim

# Install dependencies
COPY api/requirements.txt /api/requirements.txt

RUN pip install --upgrade pip && pip install -r /api/requirements.txt

COPY api /api

WORKDIR /api

# In DEV environment use dev folder as bind mount and add --reload to gunicorn:
# --mount type=bind,source=${HOME}/dev/Progress/backend/api,target=/app -e GUNICORN_CMD_ARGS="--reload --log-level=debug"

