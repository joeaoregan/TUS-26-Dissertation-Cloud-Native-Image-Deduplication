FROM python:3.13-slim

WORKDIR /app

COPY core_engine/requirements.txt /app/core_engine/requirements.txt
RUN pip install --no-cache-dir -r /app/core_engine/requirements.txt

# Copy only runtime code needed for benchmark execution
COPY core_engine /app/core_engine
COPY benchmarks /app/benchmarks

# Optional: if your benchmark imports shared utils/config from repo root, copy only those explicitly
# COPY <needed_path> /app/<needed_path>

# Ensure logs dir exists
RUN mkdir -p /app/logs

CMD ["python", "-m", "benchmarks.benchmark_pipeline"]