FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8-slim

# Install dependencies
COPY ./requirements.txt ./requirements.txt
RUN pip install --upgrade pip && pip install -r ./requirements.txt

# Copy app
COPY ./app /app
