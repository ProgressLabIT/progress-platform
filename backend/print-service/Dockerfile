FROM python:3.11-slim

COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install --no-cache-dir -r /app/requirements.txt

COPY main.py config.py tcp_sender.py /app/

WORKDIR /app

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8200/health')" || exit 1

CMD ["python", "main.py"]
