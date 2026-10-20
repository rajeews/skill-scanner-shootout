# Shared settings for the shoot-out scripts (POSIX shell; works on Linux, macOS, WSL and Git Bash).
export MSYS_NO_PATHCONV=1
ROOT="$(cd "$(dirname "$0")/.." && (pwd -W 2>/dev/null || pwd))"
# Scan containers are locked down: no network, read-only root, no capabilities, resource limits.
SCAN_FLAGS="--rm --network none --read-only --tmpfs /tmp:rw,size=256m --cap-drop ALL \
 --security-opt no-new-privileges --memory 1g --pids-limit 256 --user 10001:10001 -e HOME=/tmp/home"
# Same lock-down but WITH network, used only for configs that deliberately enable an online dependency check
# (OSV.dev lookups). Everything else (read-only root, no capabilities, limits) stays.
SCAN_FLAGS_ONLINE="${SCAN_FLAGS/--network none/}"
