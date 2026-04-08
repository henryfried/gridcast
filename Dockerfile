FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
COPY ingestion/ ./ingestion/
RUN pip install --no-cache-dir .



