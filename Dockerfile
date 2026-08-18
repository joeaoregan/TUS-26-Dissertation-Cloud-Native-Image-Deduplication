FROM python:3.13-slim

# Create non-root user
RUN groupadd -r app && useradd -r -g app app

WORKDIR /app

COPY core_engine/requirements.txt /app/core_engine/requirements.txt

# Pin pip version (avoid unpinned dependency warning)
RUN python -m pip install --no-cache-dir --upgrade "pip==25.2" && \
    pip install --no-cache-dir --only-binary=:all: -r /app/core_engine/requirements.txt

COPY core_engine /app/core_engine
COPY benchmarks /app/benchmarks

RUN mkdir -p /app/logs && chown -R app:app /app

USER app

CMD ["python", "-m", "benchmarks.benchmark_pipeline"]