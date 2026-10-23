#!/bin/bash

echo "starting uv installation and environment setup..."

# 1. verifies if uv is already installed
if ! command -v uv &> /dev/null; then
    echo "uv is not installed. installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # adds the uv path to the current shell session
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
    if [ -f "$HOME/.local/bin/env" ]; then
        source "$HOME/.local/bin/env"
    fi
else
    echo "uv is already installed."
fi

# 2. verifies if the uv command is functional
if ! command -v uv &> /dev/null; then
    echo "ERROR: uv installation failed or executable not found in PATH."
    exit 1
fi

echo "using uv version: $(uv --version)"

# 3. synchronizes the project dependencies
if [ -f "pyproject.toml" ]; then
    echo "pyproject.toml found. synchronizing dependencies with uv sync..."
    uv sync
else
    echo "pyproject.toml not found. initializing project with uv init..."
    uv init
    echo "synchronizing environment..."
    uv sync
fi

echo "uv setup completed successfully."