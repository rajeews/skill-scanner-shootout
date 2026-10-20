#!/bin/sh
# Builds the scanner images. This is the ONLY step that needs network access.
set -eu
. "$(dirname "$0")/common.sh"
docker build -t shootout-cisco:2.3.0 -f "$ROOT/docker/cisco.Dockerfile" "$ROOT/docker"
docker build -t shootout-skillspector:2.13.0 -f "$ROOT/docker/skillspector.Dockerfile" "$ROOT/docker"
docker build -t shootout-report:mpl3.11.2 -f "$ROOT/docker/report.Dockerfile" "$ROOT/docker"
mkdir -p "$ROOT/results"
for img in shootout-cisco:2.3.0 shootout-skillspector:2.13.0 shootout-report:mpl3.11.2; do
  name=$(echo "$img" | cut -d: -f1)
  docker image inspect "$img" --format '{{.Id}}' > "$ROOT/results/$name.image-id.txt"
  docker run --rm --entrypoint cat "$img" /opt/resolved-versions.txt > "$ROOT/results/$name.resolved-versions.txt"
done
