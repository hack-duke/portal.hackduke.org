FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev python3-dev pkg-config && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry
COPY pyproject.toml poetry.lock* ./
RUN poetry config virtualenvs.create false \
 && poetry install --no-root --no-interaction --no-ansi

COPY portal-backend-python/ ./portal-backend-python
COPY models/ ./models


ENV PYTHONPATH=/app

WORKDIR /app/portal-backend-python

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]

