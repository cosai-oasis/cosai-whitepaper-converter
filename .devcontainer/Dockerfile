FROM mcr.microsoft.com/devcontainers/base:ubuntu-24.04

# Install Python 3.12 from apt
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    bash-completion \
    vim \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    ca-certificates \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 22 LTS from NodeSource (EOL: April 2027)
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*
