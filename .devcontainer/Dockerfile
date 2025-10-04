FROM mcr.microsoft.com/devcontainers/base:ubuntu-24.04

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        build-essential \
        git \
        curl \
        unzip \
        vim \
        nano \
        htop \
        zsh \
        python3 python3-pip python3-dev\
        nodejs npm \
        libpq-dev \
        postgresql \
        postgresql-client \
    && apt-get clean

USER vscode
ENV PATH="/home/vscode/.local/bin:$PATH"
ENV POETRY_VERSION=1.8.3

RUN curl -sSL https://install.python-poetry.org | python3 - --version $POETRY_VERSION && \
    poetry config virtualenvs.in-project true