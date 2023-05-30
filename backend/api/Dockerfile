FROM python:3.11-slim

# Install dependencies
COPY requirements.txt /api/requirements.txt

RUN pip install --upgrade pip && pip install -r /api/requirements.txt

COPY . /api

WORKDIR /api

CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000", "main:app"]
