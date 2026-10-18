FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
COPY requirements-embeddings.txt /app/requirements-embeddings.txt

RUN pip install --no-cache-dir -r /app/requirements.txt \
    && pip install --no-cache-dir -r /app/requirements-embeddings.txt

COPY src /app/src
COPY configs /app/configs
COPY kb /app/kb
# Only public runtime artifacts. Never copy evaluation datasets or research runs.
COPY domain/engine /app/domain/engine
COPY domain/retrieval /app/domain/retrieval
COPY domain/policy /app/domain/policy
COPY domain/schemas /app/domain/schemas
COPY domain/sops /app/domain/sops
COPY domain/examples /app/domain/examples

ENV PYTHONPATH=/app
CMD ["python", "-m", "src.app"]
