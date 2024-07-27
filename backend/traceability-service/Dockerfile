FROM python:3.11-slim

# Install dependencies
COPY requirements.txt /traceability-service/requirements.txt

RUN pip install --upgrade pip && pip install -r /traceability-service/requirements.txt

COPY . /traceability-service

WORKDIR /traceability-service

CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8100", "--graceful-timeout", "1", "main:app"]
