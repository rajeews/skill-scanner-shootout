"""Normalize raw scanner output into one comparable result file (standard library only).

Reads  results/raw/<config>/<skill>.{out,err,meta}  and  expected/*.json
Writes results/normalized.json

Matching rules (documented in the report; identical for every scanner):
  * Findings of severity INFO are ignored (they are policy/hygiene notes such as "no license field").
  * HYGIENE findings are ignored for the main ("content") numbers: SkillSpector's "MCP Least Privilege" category
    (it fires on a missing tool declaration, at line 1 of nearly every skill), Cisco's manifest/policy findings, and
    SkillSpector's notice that OSV.dev was unreachable (that is the offline run being reported, not a finding).
    The planted flaws and benign controls are not about manifest hygiene. Numbers with these included are kept
    as "*_all" so the effect of this choice is visible.
  * A planted flaw is DETECTED if some non-INFO finding is in the expected file and either has no line number
    (file-level finding) or its line is within LINE_WINDOW lines of the planted line.
  * "detected_medium" additionally requires severity MEDIUM or higher.
  * A benign control is a FALSE POSITIVE if the scanner reports any non-INFO finding on it
    ("fp_medium": any finding of MEDIUM or higher).
  * Findings on a flawed sample that match no planted flaw are kept as "extra" and are not penalised.
  * A finding also counts if its quoted snippet contains the planted text (needle), even when its reported line
    number is outside the window.
  * A scanner crash or unparseable output is recorded as "error" and counted separately from a miss.
"""
import json
import sys
from pathlib import Path

LINE_WINDOW = 5
RANK = {"INFO": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
RAW = ROOT / "results" / "raw"
ADJ_FILE = ROOT / "expected" / "adjudication.json"


def is_hygiene(f):
    return (f.get("category") in ("MCP Least Privilege", "policy_violation")
            or str(f.get("rule") or "").startswith("MANIFEST_")
            or "OSV.dev unreachable" in str(f.get("title") or ""))  # tool noting the offline run, not a finding


def rank(sev):
    return RANK.get(str(sev or "").upper(), 0)


def parse_cisco(data):
    out = []
    for f in data.get("findings", []):
        out.append({"file": f.get("file_path"), "line": f.get("line_number"), "severity": str(f.get("severity", "")).upper(),
                    "rule": f.get("rule_id"), "category": f.get("category"), "title": f.get("title"),
                    "snippet": f.get("snippet"), "analyzer": f.get("analyzer"),
                    "framework_mappings": (f.get("metadata") or {}).get("framework_mappings") or []})
    return out


def parse_skillspector(data):
    out = []
    for i in data.get("issues", []):
        loc = i.get("location") or {}
        out.append({"file": loc.get("file"), "line": loc.get("start_line"), "severity": str(i.get("severity", "")).upper(),
                    "rule": i.get("id"), "category": i.get("category"), "title": i.get("pattern"),
                    "snippet": i.get("finding"), "analyzer": None, "framework_mappings": []})
    return out


def load(cfg, skill):
    base = RAW / cfg / skill
    meta = (base.with_suffix(".meta")).read_text().split() if base.with_suffix(".meta").exists() else ["?", "?"]
    res = {"exit_code": meta[0], "seconds": meta[1], "findings": [], "error": None}
    text = base.with_suffix(".out").read_text(encoding="utf-8", errors="replace") if base.with_suffix(".out").exists() else ""
    try:
        data = json.loads(text)
        res["findings"] = parse_cisco(data) if cfg.startswith("cisco") else parse_skillspector(data)
    except Exception as e:  # noqa: BLE001
        err = base.with_suffix(".err").read_text(encoding="utf-8", errors="replace")[:300] if base.with_suffix(".err").exists() else ""
        res["error"] = f"unparseable output ({e.__class__.__name__}); stderr: {err}"
    return res


def hit(finding, exp, minrank):
    if rank(finding["severity"]) < max(minrank, 1):
        return False
    if finding["file"] != exp["file"]:
        return False
    if finding["line"] is None or abs(int(finding["line"]) - int(exp["line"])) <= LINE_WINDOW:
        return True
    # A finding that quotes the planted text counts even if its line number is off (some tools report line 1
    # for text inside SKILL.md). Applied to every scanner the same way.
    return exp.get("needle") is not None and exp["needle"] in str(finding.get("snippet") or "")


def main():
    expected = {p.stem: json.loads(p.read_text()) for p in sorted((ROOT / "expected").glob("skill-*.json"))}
    adjudication = json.loads(ADJ_FILE.read_text(encoding="utf-8")) if ADJ_FILE.exists() else {}
    configs = sorted(p.name for p in RAW.iterdir() if p.is_dir())
    flawed = [s for s, e in expected.items() if not e["benign"]]
    benign = [s for s, e in expected.items() if e["benign"]]
    result = {"line_window": LINE_WINDOW, "configs": {}, "samples": expected}
    for cfg in configs:
        per = {}
        for sid, exp in expected.items():
            r = load(cfg, sid)
            sec_all = [f for f in r["findings"] if rank(f["severity"]) >= 1]
            sec = [f for f in sec_all if not is_hygiene(f)]
            ok = not r["error"]
            entry = {"exit_code": r["exit_code"], "seconds": r["seconds"], "error": r["error"],
                     "n_findings": len(sec), "n_hygiene_ignored": len(sec_all) - len(sec),
                     "n_info_ignored": len(r["findings"]) - len(sec_all)}
            if exp["benign"]:
                entry["fp"] = bool(sec) and ok
                entry["fp_medium"] = any(rank(f["severity"]) >= 2 for f in sec) and ok
                entry["fp_all"] = bool(sec_all) and ok
                entry["findings"] = sec
                entry["hygiene_findings"] = [f for f in sec_all if is_hygiene(f)]
            else:
                matched, used = [], set()
                for e in exp["expected"]:
                    m = [f for f in sec if hit(f, e, 1)]
                    m2 = [f for f in sec if hit(f, e, 2)]
                    ma = [f for f in sec_all if hit(f, e, 1)]
                    matched.append({"expected": e, "detected": bool(m) and ok, "detected_medium": bool(m2) and ok,
                                    "detected_all": bool(ma) and ok, "matches": m})
                    used.update(id(f) for f in m)
                entry["matches"] = matched
                # Reason check: a located match is accepted; a catch resting only on file-level findings needs a manual verdict.
                exp0 = exp["expected"][0] if exp["expected"] else None
                located = exp0 is not None and any(f["line"] is not None and hit(f, exp0, 1) for f in sec)
                verdict = adjudication.get(f"{cfg}/{sid}", {}).get("verdict")
                entry["match_is_located"] = located
                entry["adjudication"] = adjudication.get(f"{cfg}/{sid}")
                entry["detected_reviewed"] = bool(all(x["detected"] for x in matched) and ok and (located or verdict == "correct"))
                entry["unreviewed_file_level"] = bool(all(x["detected"] for x in matched) and ok and not located and verdict is None)
                entry["detected"] = all(x["detected"] for x in matched) and ok
                entry["detected_medium"] = all(x["detected_medium"] for x in matched) and ok
                entry["detected_all"] = all(x["detected_all"] for x in matched) and ok
                entry["extra"] = [f for f in sec if id(f) not in used]
            per[sid] = entry
        result["configs"][cfg] = per
    # Repeat runs (<cfg>-r2): how many samples got the same outcome (caught/missed, flagged/quiet) as the first run
    def outcome(cfg, sid):
        e = result["configs"][cfg][sid]
        return e["fp"] if expected[sid]["benign"] else e["detected"]
    result["repeatability"] = {}
    for cfg in list(result["configs"]):
        if cfg.endswith("-r2") and cfg[:-3] in result["configs"]:
            base = cfg[:-3]
            same = [s for s in expected if outcome(base, s) == outcome(cfg, s)]
            diff = [s for s in expected if s not in same]
            def keys(c, sid):
                r = load(c, sid)
                return {(f["rule"], f["severity"], f["file"]) for f in r["findings"] if rank(f["severity"]) >= 1 and not is_hygiene(f)}
            changed = [s for s in expected if keys(base, s) != keys(cfg, s)]
            result["repeatability"][base] = {"samples": len(expected), "same_outcome": len(same), "differing": diff,
                                              "finding_set_differs": len(changed), "finding_set_differs_ids": changed,
                                              "caught_run1": sum(result["configs"][base][s]["detected"] for s in flawed),
                                              "caught_run2": sum(result["configs"][cfg][s]["detected"] for s in flawed),
                                              "fp_run1": sum(result["configs"][base][s]["fp"] for s in benign),
                                              "fp_run2": sum(result["configs"][cfg][s]["fp"] for s in benign)}
    (ROOT / "results" / "normalized.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    # console summary
    print(f"{len(flawed)} flawed samples, {len(benign)} benign controls")
    for cfg, per in result["configs"].items():
        d = sum(per[s]["detected"] for s in flawed)
        dm = sum(per[s]["detected_medium"] for s in flawed)
        fp = sum(per[s]["fp"] for s in benign)
        fpm = sum(per[s]["fp_medium"] for s in benign)
        da = sum(per[s]["detected_all"] for s in flawed)
        dr = sum(per[s]["detected_reviewed"] for s in flawed)
        unrev = sum(per[s]["unreviewed_file_level"] for s in flawed)
        fpa = sum(per[s]["fp_all"] for s in benign)
        err = sum(1 for s in per if per[s]["error"])
        print(f"{cfg:22s} detected {d}/{len(flawed)} (>=MEDIUM {dm})  false positives {fp}/{len(benign)} (>=MEDIUM {fpm})  [as reported incl. hygiene: detected {da}, FP {fpa}]  reason-confirmed {dr}  unreviewed file-level {unrev}  errors {err}")

    for base, r in result["repeatability"].items():
        print(f"repeat {base}: same outcome on {r['same_outcome']}/{r['samples']} samples; caught {r['caught_run1']} then {r['caught_run2']}; false alarms {r['fp_run1']} then {r['fp_run2']}; differing: {r['differing']}; finding set (rule/severity/file) differs on {r['finding_set_differs']}")


if __name__ == "__main__":
    main()
