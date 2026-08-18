FROM python:3.13-slim

# Create non-root user
RUN groupadd -r app && useradd -r -g app app

WORKDIR /app

# Copy lock file with hashes
COPY services/dedupe-py/core_engine/requirements.lock /app/core_engine/requirements.lock

# Install strictly pinned + hashed deps
RUN pip install --no-cache-dir --only-binary=:all: --require-hashes -r /app/core_engine/requirements.lock

# Copy only required runtime code
COPY services/dedupe-py/core_engine /app/core_engine
COPY services/dedupe-py/benchmarks /app/benchmarks
COPY services/dedupe-py/api /app/api
COPY services/dedupe-py/jobs /app/jobs
COPY services/dedupe-py/worker /app/worker

ENV PYTHONPATH=/app

# Writable output directory
RUN mkdir -p /app/logs && chown -R app:app /app

USER app

CMD ["python", "-m", "benchmarks.benchmark_pipeline"]