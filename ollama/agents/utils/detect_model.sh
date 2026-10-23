#!/bin/bash

DEFAULT_MODEL="qwen2.5-coder:7b" # fallback

if ! command -v ollama &> /dev/null; then
    echo "$DEFAULT_MODEL"
    exit 0
fi

OLLAMA_OUTPUT=$(ollama list 2>/dev/null)

LINE_COUNT=$(echo "$OLLAMA_OUTPUT" | wc -l)

if [ "$LINE_COUNT" -gt 1 ]; then
    DETECTED_MODEL=$(echo "$OLLAMA_OUTPUT" | sed -n '2p' | awk '{print $1}')
    if [ -n "$DETECTED_MODEL" ]; then
        echo "$DETECTED_MODEL"
        exit 0
    fi
fi

echo "$DEFAULT_MODEL"