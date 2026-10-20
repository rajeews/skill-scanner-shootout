#!/bin/sh
# Part 2: scanners with an LLM stage, using a LOCAL model so nothing leaves the machine.
#
# Ollama runs in its own container with NO network (loopback only). Each scan container joins that container's network
# namespace (--network container:shootout-ollama), so the scanner reaches the model at 127.0.0.1:11434 and has no other
# route out. Cisco's Ollama route only accepts a loopback address, which this satisfies.
#
# Prerequisites (see README, "Part 2"): a container named shootout-ollama running the model below. Pull the model once with
# network access into the volume, then start the container with --network none:
#   docker volume create shootout-ollama-models
#   docker run --rm -v shootout-ollama-models:/root/.ollama ollama/ollama:latest ... ollama pull qwen2.5:7b
#   docker run -d --name shootout-ollama --network none --gpus all -v shootout-ollama-models:/root/.ollama ollama/ollama:latest
# Usage: run_llm.sh [config-name]     (RUN_TAG=-r2 stores a repeat run as cisco-llm-r2 / skillspector-llm-r2)
set -u
. "$(dirname "$0")/common.sh"
RAW="$ROOT/results/raw"
ONLY="${1:-}"
TAG="${RUN_TAG:-}"
MODEL="qwen2.5:7b"
LIMIT="${SCAN_TIMEOUT:-900}"   # seconds per sample
LLM_FLAGS="${SCAN_FLAGS/--network none/--network container:shootout-ollama}"

run() {  # run <config-name> <image> "<env args>" <scanner args...>
  cfg="$1"; img="$2"; envargs="$3"; shift 3
  if [ -n "$ONLY" ] && [ "$ONLY" != "$cfg" ]; then return; fi
  cfg="$cfg$TAG"
  rm -rf "$RAW/$cfg"; mkdir -p "$RAW/$cfg"
  for d in "$ROOT"/corpus/skill-*; do
    id=$(basename "$d")
    start=$(date +%s)
    # shellcheck disable=SC2086
    timeout "$LIMIT" docker run $LLM_FLAGS $envargs -v "$ROOT/corpus:/corpus:ro" "$img" "$@" "/corpus/$id" \
      > "$RAW/$cfg/$id.out" 2> "$RAW/$cfg/$id.err"
    echo "$? $(( $(date +%s) - start ))" > "$RAW/$cfg/$id.meta"
    echo "$cfg $id $(cat "$RAW/$cfg/$id.meta")"
  done
  echo "done: $cfg"
}

# Cisco's recommended "highest F1" recipe, with the judge on the local model.
run cisco-llm        shootout-cisco:2.3.0        "-e SKILL_SCANNER_LLM_MODEL=ollama/$MODEL"                              scan --use-llm --policy balanced --format json
# SkillSpector with its LLM stage on (default when a provider is set), judge on the local model.
run skillspector-llm shootout-skillspector:2.13.0 "-e SKILLSPECTOR_PROVIDER=ollama -e SKILLSPECTOR_MODEL=$MODEL"          scan --format json
