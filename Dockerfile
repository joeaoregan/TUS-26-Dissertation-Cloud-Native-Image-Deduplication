FROM python:3.13-slim

# Prevent Python from writing .pyc files and force stdout/stderr flush
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install Python dependencies first (better layer caching)
COPY core_engine/requirements.txt /app/core_engine/requirements.txt
RUN pip install --no-cache-dir -r /app/core_engine/requirements.txt

# Copy project
COPY . /app

# Default command (can be overridden at runtime)
CMD ["python", "-m", "benchmarks.benchmark_pipeline"]