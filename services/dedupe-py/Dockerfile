FROM python:3.13-slim

# Create non-root user
RUN groupadd -r app && useradd -r -g app app

WORKDIR /app

# Copy lock file with hashes
COPY core_engine/requirements.lock /app/core_engine/requirements.lock

# Install strictly pinned + hashed deps
RUN pip install --no-cache-dir --only-binary=:all: --require-hashes -r /app/core_engine/requirements.lock

# Copy only required runtime code
COPY core_engine /app/core_engine
COPY benchmarks /app/benchmarks
COPY api /app/api
COPY jobs /app/jobs
COPY worker /app/worker

ENV PYTHONPATH=/app

# Writable output directory
RUN mkdir -p /app/logs && chown -R app:app /app

USER app

CMD ["python", "-m", "benchmarks.benchmark_pipeline"]