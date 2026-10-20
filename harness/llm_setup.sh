#!/bin/sh
# One-time setup for part 2: a local Ollama with the judge model, running with NO network.
# Network is used only for the single `ollama pull`, in a throwaway container. Model: qwen2.5:7b (digest id 845dbda0ea48).
set -eu
docker volume create shootout-ollama-models >/dev/null
docker run --rm --name shootout-ollama-pull -v shootout-ollama-models:/root/.ollama --entrypoint sh ollama/ollama:latest \
  -c 'ollama serve >/dev/null 2>&1 & sleep 5; ollama pull qwen2.5:7b'
docker rm -f shootout-ollama >/dev/null 2>&1 || true
# Drop --gpus all to run on CPU (about 5x slower here). The container has no network: loopback only.
docker run -d --name shootout-ollama --network none --gpus all --cap-drop ALL --security-opt no-new-privileges --memory 9g \
  -v shootout-ollama-models:/root/.ollama ollama/ollama:latest
sleep 6
docker exec shootout-ollama ollama list
