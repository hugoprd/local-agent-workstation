#!/bin/bash

TAG_OLLAMA=""

echo "do you want to choose a specific model or use the default (lightest) model?"
read -p "enter 's' for specific or 'd' for default: " choice_type

case "$choice_type" in
    s|S|specific)
        echo "select a model from the list below:"
        echo "[1] qwen3-14b (good at coding, ~10GB VRAM)"
        echo "[2] qwen2.5-7b (lightweight, very fast, ~5GB VRAM)"
        echo "[3] deepseek-7b (logical reasoning, ~5GB VRAM)"
        echo "[4] custom model (enter tag manually)"
        read -p "enter the number of your choice (1-4): " model_choice

        case "$model_choice" in
            1) TAG_OLLAMA="qwen3:14b" ;;
            2) TAG_OLLAMA="qwen2.5-coder:7b" ;;
            3) TAG_OLLAMA="deepseek-coder:7b" ;;
            4) 
                read -p "enter the exact Ollama model tag (e.g. qwen2.5:14b or llama3.1:8b): " custom_model
                if [ -z "$custom_model" ]; then
                    echo "ERROR: model name cannot be empty."
                    exit 1
                fi
                TAG_OLLAMA="$custom_model"
                ;;
            *) echo "ERROR: invalid choice."; exit 1 ;;
        esac
        ;;
    d|D|default)
        echo "default model selected."
        TAG_OLLAMA="qwen2.5-coder:7b"
        ;;
    *)
        echo "ERROR: invalid input. please enter 's' or 'd'."
        exit 1
        ;;
esac

echo "starting the Ollama installation..."
curl -fsSL https://ollama.com/install.sh | sh

echo "configuring the systemd service..."
sudo systemctl start ollama
sudo systemctl enable ollama

echo "downloading the selected model: $TAG_OLLAMA..."
ollama pull $TAG_OLLAMA

echo "downloading embedding model..."
ollama pull nomic-embed-text

echo "Ollama setup completed successfully."