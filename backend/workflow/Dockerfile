FROM python:3.11-slim

# Install dependencies
COPY requirements.txt /requirements.txt

RUN pip install --upgrade pip && pip install -r /requirements.txt

COPY flows /flows

WORKDIR /flows

RUN chmod +x /flows/entrypoint.sh

CMD ["/flows/entrypoint.sh"]
