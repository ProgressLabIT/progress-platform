FROM python:3.8-slim

# Install dependencies
COPY api/requirements.txt /api/requirements.txt

RUN pip install --upgrade pip && pip install -r /api/requirements.txt

COPY api /api

WORKDIR /api

CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0", "main:app"]
