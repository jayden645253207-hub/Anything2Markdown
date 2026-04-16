FROM python:3.12-slim AS base

# Install Node.js for repomix (GitHub repo parsing)
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    npm install -g repomix && \
    apt-get purge -y curl && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY pyproject.toml README.md ./
COPY src/ ./src/
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -e .

# Create runtime directories
RUN mkdir -p input output logs/json logs/text

# Default environment
ENV INPUT_DIR=/app/input \
    OUTPUT_DIR=/app/output \
    LOG_DIR=/app/logs

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import anything2markdown; print('ok')" || exit 1

# Default command: show CLI help
CMD ["anything2md", "--help"]
