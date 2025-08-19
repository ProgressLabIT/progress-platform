FROM python:3.11-slim

# Install dependencies
COPY requirements.txt /api/requirements.txt

RUN pip install --upgrade pip && pip install -r /api/requirements.txt

# Install Playwright browsers and system deps (Chromium)
RUN python -m playwright install --with-deps chromium

COPY . /api

WORKDIR /api

CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000", "--graceful-timeout", "1", "main:app"]
