FROM python:3.11-slim

# Install dependencies
COPY requirements.txt /robot-framework/requirements.txt

RUN pip install --upgrade pip && pip install -r /robot-framework/requirements.txt

COPY . /robot-framework

WORKDIR /robot-framework

CMD ["robot", "--outputdir", "reports", "tests"]
