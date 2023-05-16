FROM python:3.11-slim

# Install dependencies
COPY requirements.txt /requirements.txt

RUN pip install --upgrade pip && pip install -r /requirements.txt

COPY ./flows /flows

WORKDIR /flows

RUN python sys_loader.py system

CMD ["prefect", "agent", "start", "-q", "system"]
