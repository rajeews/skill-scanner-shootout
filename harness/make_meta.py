"""Collect run metadata (pinned versions, image IDs, date) into results/run-meta.json (standard library only)."""
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
R = ROOT / "results"
rd = lambda n: (R / n).read_text(encoding="utf-8").strip()
meta = {
    "run_date": date.today().isoformat(),
    "cisco_version": "2.3.0 (PyPI cisco-ai-skill-scanner)",
    "skillspector_version": "v2.13.0 (github.com/NVIDIA/skillspector)",
    "skillspector_commit": "091a509b3d6ba8ff5be528966e1f43c2e68cf214",
    "images": {
        "base python:3.12-slim-bookworm": "sha256:34386ef0cb081344d7ec1c103ba398e6e9f64e9ab3a1509accc92a4e24a07258",
        "shootout-cisco:2.3.0": rd("shootout-cisco.image-id.txt"),
        "shootout-skillspector:2.13.0": rd("shootout-skillspector.image-id.txt"),
        "shootout-report:mpl3.11.2": rd("shootout-report.image-id.txt"),
    },
}
(R / "run-meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
print("wrote results/run-meta.json")
