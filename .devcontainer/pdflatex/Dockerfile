FROM mcr.microsoft.com/playwright:v1.58.0

ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=${USER_UID}
ARG WORKSPACE=/workspace
ARG WORKSPACE_REPO=cosai-whitepaper-converter

# Remove ubuntu user if it exists
RUN userdel -r ubuntu 2>/dev/null || true

# Install essential system packages
RUN apt-get update && apt-get install -y \
    sudo \
    build-essential \
    bash-completion \
    vim \
	texlive-latex-base \
    texlive-fonts-recommended \
    texlive-latex-extra \
    texlive-fonts-extra \
    texlive-extra-utils \
    ca-certificates \
    libfontconfig1 \
    libgraphite2-3 \
    libharfbuzz0b \
    librsvg2-bin \
    && rm -rf /var/lib/apt/lists/*

# Create vscode user with different IDs to avoid conflicts
RUN groupadd --gid ${USER_GID} ${USERNAME} && \
    useradd --uid ${USER_UID} --gid ${USER_GID} --shell /bin/bash --create-home vscode \
    && echo vscode ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/vscode \
    && chmod 0440 /etc/sudoers.d/vscode

# Set up workspace with proper permissions
RUN mkdir -p ${WORKSPACE}/${WORKSPACE_REPO} && chown -R vscode:vscode ${WORKSPACE}

# Pre-install Playwright chromium browser as vscode user
# This is the slowest part of container setup, so we bake it into the image
USER vscode
RUN npx playwright@1.56.1 install chromium --with-deps

WORKDIR ${WORKSPACE}/${WORKSPACE_REPO}