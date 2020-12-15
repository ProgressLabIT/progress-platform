FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8-slim

# Install dependencies
COPY requirements.txt ./requirements.txt
RUN pip install --upgrade pip && pip install -r ./requirements.txt

# In DEV environment use dev folder as bind mount and add --reload to gunicorn:
# --mount type=bind,source=${HOME}/dev/Progress/backend/api,target=/app -e GUNICORN_CMD_ARGS="--reload --log-level=debug"


