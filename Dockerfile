FROM python:3.13-slim

# Create non-root user
RUN groupadd -r app && useradd -r -g app app

WORKDIR /app

# Copy dependency file first for layer caching
COPY core_engine/requirements.txt /app/core_engine/requirements.txt

# Upgrade pip and install with binary-only wheels
# (mitigates setup.py/script execution risk)
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir --only-binary=:all: -r /app/core_engine/requirements.txt

# Copy only required runtime code
COPY core_engine /app/core_engine
COPY benchmarks /app/benchmarks

# Create writable output dir and assign ownership
RUN mkdir -p /app/logs && chown -R app:app /app

USER app

CMD ["python", "-m", "benchmarks.benchmark_pipeline"]