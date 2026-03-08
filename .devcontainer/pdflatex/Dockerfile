FROM mcr.microsoft.com/devcontainers/base:ubuntu-24.04

# Install Python and prepare for NodeSource
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 24 LTS (Krypton) from NodeSource
RUN curl -fsSL https://deb.nodesource.com/setup_24.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Core dev utilities + TeX Live (cached in Docker layer since ~2GB)
# Retry loop works around transient 403s from Ubuntu mirrors during BuildKit builds
RUN apt-get update \
    && for i in 1 2 3; do \
        apt-get install -y --no-install-recommends --fix-missing \
            build-essential \
            bash-completion \
            vim \
            python3 \
            python3-pip \
            python3-venv \
            texlive-latex-base \
            texlive-fonts-recommended \
            texlive-latex-extra \
            texlive-fonts-extra \
            texlive-extra-utils \
        && break || { echo "Attempt $i failed, retrying..."; apt-get update; }; \
    done \
    && rm -rf /var/lib/apt/lists/*
