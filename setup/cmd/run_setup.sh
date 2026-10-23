#!/bin/bash

echo "========================================"
read -p "do you want to install Ollama and download a local model? (y/n): " ollama_choice

case "$ollama_choice" in 
  y|Y|yes|Yes ) 
    bash setup/cmd/ollama_install.sh 
    ;;
  n|N|no|No ) 
    echo "skipping Ollama installation..."
    ;;
  * ) 
    echo "invalid input. skipping Ollama installation..."
    ;;
esac

echo "----------------------------------------"
echo "starting Python environment setup with uv..."
bash setup/cmd/uv_setup.sh

echo "----------------------------------------"
echo "all setups completed successfully."
echo "========================================"