"""Animated heatmap for LinkedIn: the part 1 results revealed cell by cell, then the five flaws both scanners missed.

Runs inside the shootout-report image (matplotlib + Pillow, no network).
Usage: python harness/make_gif.py <project-root>   ->  visual/shootout-headline.gif (about 800x1000, loops)
The GIF deliberately does not mention part 2.
"""
import io
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402
from PIL import Image  # noqa: E402

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
BG, FG, MUT, GRID, ACCENT = "#ffffff", "#1b1f24", "#5b6572", "#d8dde3", "#c2570c"
LOW, HIGH = (0.93, 0.96, 0.99), (0.04, 0.33, 0.66)

# Both-missed flaws (derived from the data, so the card can't drift from the results)
both_missed = [samples[s]["label"] for s in flawed if not any(N["configs"][c][s]["detected"] for c, _, _ in COLS)]
ITEMS = {"n01-remote-instructions": "Plain-English instructions to fetch and follow remote rules",
         "n09-aws-creds": "A script reading a cloud credentials file",
         "n11-bashrc-write": "A script writing to a shell startup file",
         "n12-path-traversal": "A path-traversal read",
         "n14-readonly-deletes": "A \"read-only\" Skill that deletes a folder"}
assert set(both_missed) == set(ITEMS), both_missed
ORDER = ["n01-remote-instructions", "n09-aws-creds", "n11-bashrc-write", "n12-path-traversal", "n14-readonly-deletes"]


def blend(x):
    return tuple(LOW[i] + (HIGH[i] - LOW[i]) * x for i in range(3))


def fam_got(cfg, fam):
    ss = [s for s in flawed if samples[s]["family"] == fam]
    return sum(N["configs"][cfg][s]["detected"] for s in ss), len(ss)


x0, w0, cw, gap = 54, 392, 280, 16
rh = 72
Y0 = 300


def draw(rev=(0, 0), totals=0, card=0):
    """rev: rows revealed per column; totals: 0 none, 1 caught totals, 2 + false alarms; card: items shown on the overlay (0 = no overlay)."""
    fig = plt.figure(figsize=(10.8, 13.5), dpi=74, facecolor=BG)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 1080); ax.set_ylim(1350, 0); ax.axis("off")
    ax.text(54, 74, "Skill scanners with no LLM stage:", fontsize=33, fontweight="bold", color=FG, va="top")
    ax.text(54, 122, "what do they catch?", fontsize=33, fontweight="bold", color=FG, va="top")
    ax.text(54, 184, f"{len(flawed)} planted flaws + {len(benign)} harmless controls, 2 open-source scanners", fontsize=16, color=MUT, va="top")
    for k, (cfg, name, sub) in enumerate(COLS):
        cx = x0 + w0 + 16 + k * (cw + gap)
        ax.text(cx + cw / 2, Y0 - 44, name, fontsize=18, fontweight="bold", color=FG, ha="center", va="bottom")
        ax.text(cx + cw / 2, Y0 - 18, sub, fontsize=12.5, color=MUT, ha="center", va="bottom")
    for r, fam in enumerate(families):
        y = Y0 + r * rh
        n = sum(samples[s]["family"] == fam for s in flawed)
        ax.text(x0, y + rh / 2 - 6, SHORT[fam], fontsize=17, color=FG, va="center")
        ax.text(x0, y + rh / 2 + 18, f"{n} samples", fontsize=11.5, color=MUT, va="center")
        for k, (cfg, _, _) in enumerate(COLS):
            cx = x0 + w0 + 16 + k * (cw + gap)
            if r < rev[k]:
                got, n2 = fam_got(cfg, fam); frac = got / n2
                ax.add_patch(Rectangle((cx, y + 4), cw, rh - 8, facecolor=blend(frac), edgecolor=GRID, linewidth=1))
                ax.text(cx + cw / 2, y + rh / 2, f"{got} / {n2} caught", fontsize=19, fontweight="bold",
                        color="#ffffff" if frac > 0.55 else FG, ha="center", va="center")
            else:
                ax.add_patch(Rectangle((cx, y + 4), cw, rh - 8, facecolor="#f4f6f8", edgecolor=GRID, linewidth=1))
    yb = Y0 + len(families) * rh + 14
    ax.plot([x0, 1026], [yb, yb], color=GRID, linewidth=1.5)
    if totals >= 1:
        ax.text(x0, yb + 48, "Total planted flaws caught", fontsize=18, fontweight="bold", color=FG, va="center")
        for k, (cfg, _, _) in enumerate(COLS):
            cx = x0 + w0 + 16 + k * (cw + gap)
            ax.text(cx + cw / 2, yb + 48, f"{sum(N['configs'][cfg][s]['detected'] for s in flawed)} of {len(flawed)}",
                    fontsize=26, fontweight="bold", color=FG, ha="center", va="center")
    if totals >= 2:
        ax.text(x0, yb + 112, "Harmless controls", fontsize=18, fontweight="bold", color=FG, va="center")
        ax.text(x0, yb + 138, "wrongly flagged (false alarms)", fontsize=18, fontweight="bold", color=FG, va="center")
        for k, (cfg, _, _) in enumerate(COLS):
            cx = x0 + w0 + 16 + k * (cw + gap)
            ax.text(cx + cw / 2, yb + 124, f"{sum(N['configs'][cfg][s]['fp'] for s in benign)} of {len(benign)}",
                    fontsize=26, fontweight="bold", color=FG, ha="center", va="center")
    ax.text(54, 1296, f"Run {META['run_date']}  |  open source, Docker, pinned versions  |  rajeew.com/blog/skill-scanner-shootout",
            fontsize=11.5, color=MUT, va="center")
    if card:
        ax.add_patch(Rectangle((0, 0), 1080, 1350, facecolor="#ffffff", alpha=0.93, edgecolor="none", zorder=10))
        ax.add_patch(Rectangle((54, 250), 972, 700, facecolor="#f6f8fa", edgecolor=GRID, linewidth=2, zorder=11))
        ax.text(90, 300, "Both scanners missed the same five", fontsize=30, fontweight="bold", color=FG, va="center", zorder=12)
        for i, key in enumerate(ORDER):
            if i < card:
                y = 400 + i * 100
                hot = key == "n14-readonly-deletes"
                ax.text(90, y, f"{i + 1}", fontsize=28, fontweight="bold", color=ACCENT if hot else MUT, va="center", zorder=12)
                ax.text(150, y, ITEMS[key], fontsize=19.5, fontweight="bold" if hot else "normal", color=ACCENT if hot else FG, va="center", zorder=12)
                if hot:
                    ax.text(150, y + 40, "What surprised me", fontsize=16, color=ACCENT, va="center", zorder=12)
        ax.text(90, 905, "Small synthetic sample set: a map of coverage, not a ranking.", fontsize=14, color=MUT, va="center", zorder=12)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=74, facecolor=BG)
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).convert("RGB")


frames, durations = [], []


def add(img, ms):
    frames.append(img); durations.append(ms)


add(draw((0, 0)), 1400)
for r in range(1, len(families) + 1):
    add(draw((r, 0)), 330)
add(draw((len(families), 0)), 500)
for r in range(1, len(families) + 1):
    add(draw((len(families), r)), 330)
full = (len(families), len(families))
add(draw(full), 600)
add(draw(full, totals=1), 1100)
add(draw(full, totals=2), 2200)
for c in range(1, 6):
    add(draw(full, totals=2, card=c), 900 if c < 5 else 4200)

# Quantise to a shared palette to keep the file small
# palette from the full heatmap frame AND the final card frame, side by side, so blues and the orange accent both survive
heat = frames[-6] if len(frames) > 6 else frames[0]
both = Image.new("RGB", (heat.width * 2, heat.height), "white")
both.paste(heat, (0, 0)); both.paste(frames[-1], (heat.width, 0))
pal = both.quantize(colors=64, method=Image.Quantize.MEDIANCUT)
q = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
out = ROOT / "visual"; out.mkdir(exist_ok=True)
path = out / "shootout-headline.gif"
q[0].save(path, save_all=True, append_images=q[1:], duration=durations, loop=0, optimize=True, disposal=1)
print("wrote", path, f"{path.stat().st_size / 1e6:.2f} MB,", len(frames), "frames,", f"{sum(durations) / 1000:.1f} s,", q[0].size)
