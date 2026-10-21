#!/bin/sh
# One command to rebuild everything from scratch: images, scans, normalization, report and chart.
# Needs Docker. Network is used only while building images. Takes roughly 15-25 minutes.
set -eu
. "$(dirname "$0")/common.sh"
sh "$ROOT/harness/build_images.sh"
sh "$ROOT/harness/run_scanners.sh"
# Everything below runs in the pinned report image: no network, read-only root, only /work is writable.
RUN_REPORT="docker run --rm --network none --read-only --tmpfs /tmp:rw,size=256m --cap-drop ALL \
 --security-opt no-new-privileges --memory 1g --pids-limit 256 --user $(id -u 2>/dev/null || echo 10001):$(id -g 2>/dev/null || echo 10001) \
 -e MPLCONFIGDIR=/tmp/mpl -e HOME=/tmp -v $ROOT:/work -w /work shootout-report:mpl3.11.2"
# Part 2 (optional): local-LLM configs. Needs a GPU for sensible speed; takes about an hour per run.
if [ "${LLM:-0}" = "1" ]; then
  sh "$ROOT/harness/llm_setup.sh"
  sh "$ROOT/harness/run_llm.sh"
  RUN_TAG=-r2 sh "$ROOT/harness/run_llm.sh"
fi
$RUN_REPORT harness/make_meta.py /work
$RUN_REPORT harness/normalize.py /work
$RUN_REPORT harness/make_report.py /work
$RUN_REPORT harness/make_chart.py /work
$RUN_REPORT harness/make_gif.py /work
if [ "${LLM:-0}" = "1" ]; then $RUN_REPORT harness/make_chart2.py /work; fi
echo "Done. Open report/index.html and visual/shootout-headline.png"
