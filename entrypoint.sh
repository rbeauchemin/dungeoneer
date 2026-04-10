#!/bin/sh
set -e

# Start Ollama server in the background
ollama serve &

# Wait until the Ollama API is responsive
echo "Waiting for Ollama..."
until curl -sf http://localhost:11434 > /dev/null; do
  sleep 1
done
echo "Ollama ready."

# Replace the shell with uvicorn so signals (SIGTERM etc.) reach it directly
exec uvicorn src.agent.server:app --host 0.0.0.0 --port 8000
