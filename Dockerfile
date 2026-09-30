FROM python:3.11-slim

# System dependencies (procfs inspection, rclone, curl, docker cli client)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    procps \
    sudo \
    rclone \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY claraos/ ./claraos/
COPY config/ ./config/

# Standard homelab mount volumes
VOLUME ["/config", "/data"]

# Default environment variables
ENV PYTHONUNBUFFERED=1 \
    CLARA_CONFIG_FILE=/config/config.yaml \
    MODULE_AGENTS_ENABLED=true \
    MODULE_APPS_ENABLED=true \
    MODULE_SYNC_ENABLED=true \
    MODULE_ORGANIZER_ENABLED=true \
    MODULE_DEBRID_ENABLED=true

EXPOSE 8080

CMD ["python", "-m", "claraos.main"]
