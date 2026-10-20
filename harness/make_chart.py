"""Draw the headline chart PNG for LinkedIn and the blog (matplotlib, run inside the shootout-report image).

Usage: python harness/make_chart.py <project-root>
Writes visual/shootout-headline.png (1080x1350).
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

COLS = [("cisco-osv", "Cisco Skill Scanner", "v2.3.0, static + behavioral + OSV"),
        ("skillspector-osv", "NVIDIA SkillSpector", "v2.13.0, static + OSV")]
samples = N["samples"]
flawed = [s for s, e in samples.items() if not e["benign"]]
benign = [s for s, e in samples.items() if e["benign"]]
families = list(FW["families"])
SHORT = {"network_fetch": "Network calls / URL fetch", "shell_exec": "Shell, eval, exec", "runtime_install": "Runtime installs, curl | sh",
         "obfuscation": "Obfuscated code", "credential_access": "Credential / secret access",
         "out_of_scope_file_access": "File access outside scope", "description_mismatch": "Description vs behaviour",
         "instruction_override": "Hidden / overriding instructions", "vulnerable_dependency": "Known-vulnerable dependencies"}

BG, FG, MUT = "#ffffff", "#1b1f24", "#5b6572"
LOW, HIGH = (0.93, 0.96, 0.99), (0.04, 0.33, 0.66)  # light -> strong blue (colour-blind safe, no red/green)


def blend(x):
    return tuple(LOW[i] + (HIGH[i] - LOW[i]) * x for i in range(3))


fig = plt.figure(figsize=(10.8, 13.5), dpi=100, facecolor=BG)
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 1080); ax.set_ylim(1350, 0); ax.axis("off")

ax.text(54, 74, "Do AI-agent Skill scanners catch what", fontsize=33, fontweight="bold", color=FG, va="top")
ax.text(54, 122, "they should?", fontsize=33, fontweight="bold", color=FG, va="top")
ax.text(54, 184, f"{len(flawed)} planted flaws + {len(benign)} harmless controls, 2 open-source scanners, static analysis only", fontsize=16, color=MUT, va="top")

x0, w0 = 54, 392          # label column
cw = 280                  # data columns
y = 262
for k, (cfg, name, sub) in enumerate(COLS):
    cx = x0 + w0 + 16 + k * (cw + 16)
    ax.text(cx + cw / 2, y - 6, name, fontsize=18, fontweight="bold", color=FG, ha="center", va="bottom")
    ax.text(cx + cw / 2, y + 20, sub, fontsize=12.5, color=MUT, ha="center", va="bottom")
y += 38
rh = 72
for fam in families:
    n = sum(samples[s]["family"] == fam for s in flawed)
    ax.text(x0, y + rh / 2, SHORT[fam], fontsize=17, color=FG, va="center")
    ax.text(x0, y + rh / 2 + 24, f"{n} samples", fontsize=11.5, color=MUT, va="center")
    for k, (cfg, _, _) in enumerate(COLS):
        cx = x0 + w0 + 16 + k * (cw + 16)
        got = sum(N["configs"][cfg][s]["detected"] for s in flawed if samples[s]["family"] == fam)
        frac = got / n if n else 0
        col = blend(frac)
        ax.add_patch(Rectangle((cx, y + 4), cw, rh - 8, facecolor=col, edgecolor="#d8dde3", linewidth=1))
        ax.text(cx + cw / 2, y + rh / 2, f"{got} / {n} caught", fontsize=19, fontweight="bold",
                color="#ffffff" if frac > 0.55 else FG, ha="center", va="center")
    y += rh

# totals and false alarms
y += 14
ax.plot([x0, 1026], [y, y], color="#d8dde3", linewidth=1.5)
y += 20
ax.text(x0, y + 28, "Total planted flaws caught", fontsize=18, fontweight="bold", color=FG, va="center")
ax.text(x0, y + 92, "Harmless controls", fontsize=18, fontweight="bold", color=FG, va="center")
ax.text(x0, y + 118, "wrongly flagged (false alarms)", fontsize=18, fontweight="bold", color=FG, va="center")
for k, (cfg, _, _) in enumerate(COLS):
    cx = x0 + w0 + 16 + k * (cw + 16)
    caught = sum(N["configs"][cfg][s]["detected"] for s in flawed)
    fps = sum(N["configs"][cfg][s]["fp"] for s in benign)
    ax.text(cx + cw / 2, y + 28, f"{caught} of {len(flawed)}", fontsize=26, fontweight="bold", color=FG, ha="center", va="center")
    ax.text(cx + cw / 2, y + 108, f"{fps} of {len(benign)}", fontsize=26, fontweight="bold", color=FG, ha="center", va="center")

y += 168
ax.text(x0, y, "No LLM review stage was run. Cisco's docs recommend one and say rules alone catch", fontsize=13, color=MUT, va="top")
ax.text(x0, y + 22, "only about 8% of its own held-out set. Results describe this small, synthetic", fontsize=13, color=MUT, va="top")
ax.text(x0, y + 44, "sample set only. They are not a ranking of the tools.", fontsize=13, color=MUT, va="top")
ax.text(x0, 1296, f"Run {META['run_date']}  |  samples and scripts open source, Docker, pinned versions  |  rajeew.com/blog/skill-scanner-shootout",
        fontsize=11.5, color=MUT, va="center")

out = ROOT / "visual"; out.mkdir(exist_ok=True)
fig.savefig(out / "shootout-headline.png", dpi=100, facecolor=BG)
print("wrote", out / "shootout-headline.png")
