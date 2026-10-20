#!/bin/sh
# Runs every scanner config on every sample skill, one container per skill. Network is OFF except for the two
# configs that deliberately enable an online OSV.dev dependency check (see below).
# Usage: run_scanners.sh [config-name]   (a single config name re-runs just that one and keeps the others)
# The corpus is mounted read-only; output is captured from stdout, so nothing in the container is writable.
set -u
. "$(dirname "$0")/common.sh"
RAW="$ROOT/results/raw"
ONLY="${1:-}"
if [ -z "$ONLY" ]; then rm -rf "$RAW"; fi
mkdir -p "$RAW"

FLAGS="$SCAN_FLAGS"
run() {  # run <config-name> <image> <args...>  (skill path is appended); uses $FLAGS
  cfg="$1"; img="$2"; shift 2
  if [ -n "$ONLY" ] && [ "$ONLY" != "$cfg" ]; then return; fi
  rm -rf "$RAW/$cfg"
  mkdir -p "$RAW/$cfg"
  for d in "$ROOT"/corpus/skill-*; do
    id=$(basename "$d")
    start=$(date +%s)
    # shellcheck disable=SC2086
    docker run $FLAGS -v "$ROOT/corpus:/corpus:ro" "$img" "$@" "/corpus/$id" \
      > "$RAW/$cfg/$id.out" 2> "$RAW/$cfg/$id.err"
    echo "$? $(( $(date +%s) - start ))" > "$RAW/$cfg/$id.meta"
  done
  echo "done: $cfg"
}

# Cisco: default static config, and with the behavioural (AST dataflow) analyzer. No LLM, no API keys.
run cisco-default        shootout-cisco:2.3.0       scan --format json
run cisco-behavioral     shootout-cisco:2.3.0       scan --use-behavioral --format json
# Cisco with its strict policy preset, to show how much the policy choice matters (still no LLM, no keys).
run cisco-strict         shootout-cisco:2.3.0       scan --use-behavioral --policy strict --format json
# NVIDIA: static analysis only (--no-llm), no network: its OSV.dev lookup falls back to a small built-in list.
run skillspector-offline shootout-skillspector:2.13.0 scan --no-llm --format json

# Online dependency checks (OSV.dev). Network is ON for these configs only; the only data that can leave is the
# package names and versions found in the sample skills (public, fake or example packages).
FLAGS="$SCAN_FLAGS_ONLINE"
run skillspector-osv     shootout-skillspector:2.13.0 scan --no-llm --format json
# Cisco's equivalent switch, for like-for-like comparison with skillspector-osv.
run cisco-osv            shootout-cisco:2.3.0       scan --use-behavioral --use-osv --format json
