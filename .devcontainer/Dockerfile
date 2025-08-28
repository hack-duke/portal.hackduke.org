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
        python3 python3-pip \
        nodejs npm \
    && apt-get clean