FROM python:3.12-slim

# curl is needed to install Ollama and to healthcheck it during the pull
RUN apt-get update && apt-get install -y --no-install-recommends curl zstd && \
    rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Pull gemma4 at build time so it is baked into the image.
# Start the server in the background, wait until the API responds, pull, done.
RUN ollama serve & \
    until curl -sf http://localhost:11434 > /dev/null; do sleep 1; done && \
    ollama pull gemma4

WORKDIR /app

# Python dependencies (own layer so code changes don't bust it)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY src/ ./src/
COPY frontend/ ./frontend/

# Entrypoint: starts Ollama, waits for it, then launches uvicorn
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# gemma4 is the bundled model; override with -e DUNGEONEER_MODEL=... if needed
ENV DUNGEONEER_MODEL=gemma4

EXPOSE 8000

CMD ["./entrypoint.sh"]
