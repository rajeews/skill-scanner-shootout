"""Part 2 chart: each scanner offline vs the same scanner with a local LLM judge (matplotlib, inside shootout-report).

Usage: python harness/make_chart2.py <project-root>   ->  visual/shootout-part2.png (1080x1350)
"""
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

ROOT = Path(sys.argv[1]).resolve()
N = json.loads((ROOT / "results" / "normalized.json").read_text(encoding="utf-8"))
FW = json.loads((ROOT / "frameworks" / "frameworks.json").read_text(encoding="utf-8"))
META = json.loads((ROOT / "results" / "run-meta.json").read_text(encoding="utf-8"))

COLS = [("cisco-default", "Cisco", "static"), ("cisco-llm", "Cisco", "+ local LLM"),
        ("skillspector-offline", "SkillSpector", "static"), ("skillspector-llm", "SkillSpector", "+ local LLM")]
samples = N["samples"]
flawed = [s for s, e in samples.items() if not e["benign"]]
benign = [s for s, e in samples.items() if e["benign"]]
families = list(FW["families"])
SHORT = {"network_fetch": "Network calls / URL fetch", "shell_exec": "Shell, eval, exec", "runtime_install": "Runtime installs, curl | sh",
         "obfuscation": "Obfuscated code", "credential_access": "Credential / secret access",
         "out_of_scope_file_access": "File access outside scope", "description_mismatch": "Description vs behaviour",
         "instruction_override": "Hidden / overriding instructions", "vulnerable_dependency": "Known-vulnerable dependencies"}
BG, FG, MUT = "#ffffff", "#1b1f24", "#5b6572"
LOW, HIGH = (0.93, 0.96, 0.99), (0.04, 0.33, 0.66)


def blend(x):
    return tuple(LOW[i] + (HIGH[i] - LOW[i]) * x for i in range(3))


fig = plt.figure(figsize=(10.8, 13.5), dpi=100, facecolor=BG)
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 1080); ax.set_ylim(1350, 0); ax.axis("off")
ax.text(54, 74, "Same scanners, now with a", fontsize=33, fontweight="bold", color=FG, va="top")
ax.text(54, 122, "local LLM judge  (part 2 of 2)", fontsize=33, fontweight="bold", color=FG, va="top")
ax.text(54, 184, f"{len(flawed)} planted flaws + {len(benign)} harmless controls, everything offline, model: qwen2.5:7b on a 6 GB GPU",
        fontsize=15, color=MUT, va="top")

x0, w0, cw, gap = 54, 352, 146, 8
y = 262
for k, (cfg, tool, sub) in enumerate(COLS):
    cx = x0 + w0 + 10 + k * (cw + gap)
    ax.text(cx + cw / 2, y - 6, tool, fontsize=15, fontweight="bold", color=FG, ha="center", va="bottom")
    ax.text(cx + cw / 2, y + 18, sub, fontsize=12.5, color=MUT, ha="center", va="bottom")
y += 38
rh = 72
for fam in families:
    n = sum(samples[s]["family"] == fam for s in flawed)
    ax.text(x0, y + rh / 2 - 8, SHORT[fam], fontsize=16, color=FG, va="center")
    ax.text(x0, y + rh / 2 + 16, f"{n} samples", fontsize=11, color=MUT, va="center")
    for k, (cfg, _, _) in enumerate(COLS):
        cx = x0 + w0 + 10 + k * (cw + gap)
        got = sum(N["configs"][cfg][s]["detected_reviewed"] for s in flawed if samples[s]["family"] == fam)
        frac = got / n if n else 0
        ax.add_patch(Rectangle((cx, y + 4), cw, rh - 8, facecolor=blend(frac), edgecolor="#d8dde3", linewidth=1))
        ax.text(cx + cw / 2, y + rh / 2, f"{got} / {n}", fontsize=19, fontweight="bold",
                color="#ffffff" if frac > 0.55 else FG, ha="center", va="center")
    y += rh
y += 14
ax.plot([x0, 1026], [y, y], color="#d8dde3", linewidth=1.5)
y += 20
ax.text(x0, y + 28, "Planted flaws caught", fontsize=17, fontweight="bold", color=FG, va="center")
ax.text(x0, y + 92, "Harmless controls", fontsize=17, fontweight="bold", color=FG, va="center")
ax.text(x0, y + 116, "wrongly flagged", fontsize=17, fontweight="bold", color=FG, va="center")
for k, (cfg, _, _) in enumerate(COLS):
    cx = x0 + w0 + 10 + k * (cw + gap)
    caught = sum(N["configs"][cfg][s]["detected_reviewed"] for s in flawed)
    fps = sum(N["configs"][cfg][s]["fp"] for s in benign)
    errs = sum(1 for s in N["configs"][cfg] if N["configs"][cfg][s]["error"])
    ax.text(cx + cw / 2, y + 28, f"{caught} of {len(flawed)}", fontsize=21, fontweight="bold", color=FG, ha="center", va="center")
    ax.text(cx + cw / 2, y + 104, f"{fps} of {len(benign)}", fontsize=21, fontweight="bold", color=FG, ha="center", va="center")
    if errs:
        ax.text(cx + cw / 2, y + 140, f"{errs} scan errors", fontsize=11, color=MUT, ha="center", va="center")
y += 176
ax.text(x0, y, "A 7B model on a consumer GPU is a small on-prem judge, not the best available. Cisco's docs used a larger", fontsize=12.5, color=MUT, va="top")
ax.text(x0, y + 22, "local model. \"Caught\" counts findings with a line number, or findings I read by hand to check the reason.", fontsize=12.5, color=MUT, va="top")
ax.text(x0, y + 44, "Small synthetic sample set, one model, not a ranking of the tools.", fontsize=12.5, color=MUT, va="top")
ax.text(x0, 1296, f"Run {META['run_date']}  |  samples and scripts open source, Docker, pinned versions  |  github.com/rajeews/skill-scanner-shootout",
        fontsize=11, color=MUT, va="center")
out = ROOT / "visual"; out.mkdir(exist_ok=True)
fig.savefig(out / "shootout-part2.png", dpi=100, facecolor=BG)
print("wrote", out / "shootout-part2.png")
