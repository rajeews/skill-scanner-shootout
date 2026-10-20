"""Build the self-contained results explorer (report/index.html) from results/normalized.json.

Standard library only. No external requests, fonts or scripts are referenced by the page.
Usage: python harness/make_report.py [project-root]
"""
import html
import json
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
N = json.loads((ROOT / "results" / "normalized.json").read_text(encoding="utf-8"))
FW = json.loads((ROOT / "frameworks" / "frameworks.json").read_text(encoding="utf-8"))
META = json.loads((ROOT / "results" / "run-meta.json").read_text(encoding="utf-8"))

CONFIGS = {  # id -> (label, scanner, description)
    "cisco-default": ("Cisco default", "Cisco", "skill-scanner scan, no LLM, no keys, offline"),
    "cisco-behavioral": ("Cisco + behavioral", "Cisco", "adds --use-behavioral (AST dataflow), offline"),
    "cisco-strict": ("Cisco strict policy", "Cisco", "--use-behavioral --policy strict, offline"),
    "cisco-osv": ("Cisco + behavioral + OSV (online)", "Cisco", "--use-behavioral --use-osv, network on (most capable key-free config)"),
    "skillspector-offline": ("SkillSpector offline", "NVIDIA", "scan --no-llm, offline (OSV falls back to built-in list)"),
    "skillspector-osv": ("SkillSpector + OSV (online)", "NVIDIA", "scan --no-llm, network on for OSV.dev dependency check"),
}
HEADLINE = ["cisco-osv", "skillspector-osv"]  # each tool at its most capable key-free config, both with the online OSV.dev check
FAMILY_TITLES = {k: v["title"] for k, v in FW["families"].items()}

samples = N["samples"]
flawed = [s for s, e in samples.items() if not e["benign"]]
benign = [s for s, e in samples.items() if e["benign"]]
cfgs = [c for c in CONFIGS if c in N["configs"]]


def status(cfg, sid):
    e = N["configs"][cfg][sid]
    if samples[sid]["benign"]:
        return "fp" if e["fp"] else "ok"
    return "caught" if e["detected"] else "missed"


def finding_text(f):
    line = f" line {f['line']}" if f.get("line") else " (file-level)"
    return f"{f['severity']}{line}: {f.get('title') or f.get('rule')} [{f.get('rule')}]"


data = {"configs": {}, "samples": [], "families": FW["families"], "frameworks": FW["frameworks"]}
for cfg in cfgs:
    label, scanner, desc = CONFIGS[cfg]
    d = sum(status(cfg, s) == "caught" for s in flawed)
    fp = sum(status(cfg, s) == "fp" for s in benign)
    data["configs"][cfg] = {"label": label, "scanner": scanner, "desc": desc, "caught": d, "flawed": len(flawed),
                            "fp": fp, "benign": len(benign),
                            "caught_all": sum(N["configs"][cfg][s]["detected_all"] for s in flawed),
                            "fp_all": sum(N["configs"][cfg][s]["fp_all"] for s in benign),
                            "caught_medium": sum(N["configs"][cfg][s]["detected_medium"] for s in flawed)}
for sid in sorted(samples):
    s = samples[sid]
    row = {"id": sid, "label": s["label"], "benign": s["benign"], "family": s["family"], "difficulty": s["difficulty"],
           "expected": s["expected"], "results": {}}
    for cfg in cfgs:
        e = N["configs"][cfg][sid]
        row["results"][cfg] = {"status": status(cfg, sid), "findings": [finding_text(f) for f in (
            e["findings"] if s["benign"] else [m for x in e["matches"] for m in x["matches"]] + e["extra"])]}
    data["samples"].append(row)

page = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Skill scanner shoot-out</title>
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:">
<style>
:root{--bg:#fff;--fg:#1b1f24;--mut:#5b6572;--line:#d8dde3;--card:#f6f8fa;--caught:#0b6bcb;--missed:#c2570c;--fp:#7b3fa0;--ok:#8a94a0}
@media (prefers-color-scheme:dark){:root{--bg:#0f1318;--fg:#e8ecf1;--mut:#9aa6b2;--line:#2b333c;--card:#171d24;--caught:#5aa7ff;--missed:#ff9a52;--fp:#c79bff;--ok:#7c8794}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.55 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
main{max-width:980px;margin:0 auto;padding:16px}h1{font-size:1.7rem;margin:.4em 0}h2{margin-top:1.8em;font-size:1.25rem;border-bottom:1px solid var(--line);padding-bottom:.2em}
.mut{color:var(--mut)}.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px;margin:12px 0}
table{border-collapse:collapse;width:100%;font-size:.92rem}th,td{border:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}th{background:var(--card)}
.scroll{overflow-x:auto}.cell{font-weight:600;text-align:center;white-space:nowrap}
.caught{color:var(--caught)}.missed{color:var(--missed)}.fp{color:var(--fp)}.ok{color:var(--ok)}
.tag{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:0 8px;font-size:.78rem;color:var(--mut);margin:1px 2px 1px 0}
label.opt{display:inline-flex;gap:6px;align-items:center;margin:4px 12px 4px 0;font-size:.92rem}
details{border:1px solid var(--line);border-radius:8px;padding:6px 10px;margin:6px 0}summary{cursor:pointer;font-weight:600}
code,pre{font:13px/1.45 ui-monospace,Menlo,Consolas,monospace}pre{background:var(--card);padding:8px;border-radius:6px;overflow-x:auto;white-space:pre-wrap}
.bar{height:10px;background:var(--line);border-radius:5px;overflow:hidden;min-width:70px}.bar i{display:block;height:100%;background:var(--caught)}
.legend span{margin-right:14px;white-space:nowrap}
</style></head><body><main>
<h1>Skill scanner shoot-out</h1>
<p class="mut">Independent, reproducible comparison of open-source scanners for AI agent Skills on a small synthetic sample set. <b>__RUNDATE__</b>. Results describe this sample set only; they are not a ranking of the tools.</p>
<div class="card"><b>Read this first.</b> No LLM review stage, VirusTotal or cloud analyzer was run (no API keys, static analysis only). Cisco's README says every setup it recommends includes its LLM judge, and that rules alone catch only about 8% of its own held-out set of malicious Skills; SkillSpector also has an optional LLM stage, off here. Cisco also describes its scan as best-effort: a clean result is not a guarantee. 22 of the 24 samples were written before any scanner was installed; the last two (known-vulnerable pinned dependencies) were added after a first run to exercise the online dependency check, and every scan was then re-run on the full set. No sample was tuned to a tool's output. Treat the numbers as a map of what static checks cover, not as a verdict.</div>

<h2>Headline: caught or missed, per sample</h2>
<p class="legend"><span class="caught">&#10003; caught</span><span class="missed">&#10007; missed</span><span class="fp">! false alarm (benign sample flagged)</span><span class="ok">&#8211; correctly quiet</span></p>
<div id="cfgpick"></div>
<div class="scroll"><table id="matrix"></table></div>
<p class="mut" id="summaryline"></p>

<h2>Detection by rule family</h2>
<div class="scroll"><table id="families"></table></div>

<h2>View by framework</h2>
<p class="mut">Pick one or more frameworks. Each rule family is mapped to items in the framework (the mapping is the author's judgement, not an official crosswalk; every ID was checked at the owner's page). Results regroup by the selected items.</p>
<div id="fwpick"></div>
<div class="scroll"><table id="fwtable"></table></div>

<h2>Every sample, in detail</h2>
<div id="detail"></div>

<h2>Method</h2>
<div class="card">
<ul>
<li><b>Sample set:</b> __NF__ flawed Skills (two or more per rule family, 8 families) and __NB__ benign controls, including benign Skills that legitimately use the network or run a command. Samples are inert (example.com / .invalid hosts, no working payloads). Sample folders have neutral names; the answer key is kept outside the folder the scanners see.</li>
<li><b>Scanners:</b> Cisco AI Defense Skill Scanner __CISCOV__ and NVIDIA SkillSpector __SSV__ (commit __SSC__). Snyk Agent Scan was not run: it requires a Snyk account token and sends Skill content to Snyk's API.</li>
<li><b>Isolation:</b> each scan runs in its own Docker container: non-root, read-only filesystem, all capabilities dropped, memory and process limits, sample folder mounted read-only, output captured from stdout. Network is off except for the two configs marked "online", which enable an OSV.dev dependency lookup (only package names and versions of the sample Skills can leave).</li>
<li><b>Configs:</b> default settings of each tool, plus the variants shown in the toggles above. No LLM analyzers, VirusTotal or cloud analyzers.</li>
<li><b>Caught:</b> at least one finding above INFO severity in the right file within __WIN__ lines of the planted flaw, a file-level finding on that file, or a finding whose quoted snippet contains the planted text (even if its line number is off). <b>False alarm:</b> any such finding on a benign control. Manifest and policy hygiene notes (e.g. "no license field", SkillSpector's "MCP least privilege" note, and SkillSpector's "OSV.dev unreachable" notice) are excluded; with them included the counts are shown in the table below.</li>
<li><b>Category agreement was not required:</b> a catch under a different category than the planted flaw still counts, because the aim is to see whether a reviewer would be pointed at the right code.</li>
</ul>
<div class="scroll"><table id="sens"></table></div>
</div>

<h2>Review notes (manual adjudication)</h2>
<div class="card"><ul>
<li><b>Cisco, curl | sh sample:</b> Cisco quoted the exact line but reported it as line 1 at LOW severity. Counted as caught under the snippet rule (a finding that quotes the planted text counts whatever its line number).</li>
<li><b>Dependency check:</b> Cisco found the two known-vulnerable pinned packages only with <code>--use-osv</code> (online). SkillSpector found them in both modes (its offline fallback list covers those versions); online it reported more advisories and a higher severity for the pyyaml pin.</li>
<li><b>False alarms are arguable:</b> the weather-API control makes one documented request with a user-supplied key, and both tools warned about network use and a sensitive source reaching a network sink. That warning is defensible, but it is still counted as a false alarm because the Skill is benign. SkillSpector also flagged a git status call that uses a list of arguments (no shell) as a subprocess call.</li>
<li><b>Cisco strict policy</b> added one low-severity false alarm ("vague description") on a benign control and changed no catches.</li>
<li><b>Missed by both:</b> instructions to fetch and follow remote rules written in prose, reading a cloud credentials file, writing to a shell startup file, a path-traversal read, and a "read-only" Skill that deletes a folder.</li>
</ul></div>

<h2>Limits</h2>
<div class="card"><ul>
<li>Small, synthetic, author-written sample set; real malicious Skills are messier. Some samples are deliberately hard (marked "hard").</li>
<li>Static analysis only, default or near-default settings, no LLM stage. Cisco's recommended settings use an LLM judge and were not tested; neither was SkillSpector's optional LLM stage.</li>
<li>Tool versions move fast; these are the versions listed above on the run date.</li>
<li>A research paper cautions that scanner verdicts on real marketplaces can be inflated: <a href="https://arxiv.org/pdf/2603.16572">arxiv.org/pdf/2603.16572</a>.</li>
<li>Framework tags are the author's mapping of rule families to items; they are not an official crosswalk. IDs and titles were verified at OWASP, MITRE ATLAS (atlas-data __ATLASV__), CWE and ATT&amp;CK on 2026-10-20.</li>
</ul></div>

<h2>Fairness and corrections</h2>
<div class="card">If a maintainer or reader believes a result is wrong or a tool was run in a way that doesn't reflect its intended use, please open an issue; I will rerun with your recommended configuration and publish the change, including what was wrong. Mistakes in matching or ground truth will be corrected in the open.</div>

<h2>Reproduce</h2>
<div class="card"><p>Everything runs in Docker (images pinned by digest, scanner versions pinned). Clone the repository, then run <code>sh harness/reproduce.sh</code>. Images built: <code>__IMGS__</code>.</p><pre id="vers"></pre></div>
</main>
<script>
const D = __DATA__;
const el = id => document.getElementById(id);
const SYM = {caught:"✓ caught", missed:"✗ missed", fp:"! false alarm", ok:"– quiet"};
const esc = s => String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const allCfgs = Object.keys(D.configs);
let shown = new Set(__HEADLINE__);
let fwSel = new Set();

function buildPick(){
  el("cfgpick").innerHTML = allCfgs.map(c => `<label class="opt"><input type="checkbox" data-c="${c}" ${shown.has(c)?"checked":""}> ${esc(D.configs[c].label)}</label>`).join("");
  el("cfgpick").querySelectorAll("input").forEach(i => i.onchange = () => { i.checked ? shown.add(i.dataset.c) : shown.delete(i.dataset.c); render(); });
  el("fwpick").innerHTML = Object.entries(D.frameworks).map(([k,v]) => `<label class="opt"><input type="checkbox" data-f="${k}"> ${esc(v.name)}</label>`).join("");
  el("fwpick").querySelectorAll("input").forEach(i => i.onchange = () => { i.checked ? fwSel.add(i.dataset.f) : fwSel.delete(i.dataset.f); renderFw(); });
}
const cols = () => allCfgs.filter(c => shown.has(c));
function cell(c, s){ const st = s.results[c].status; return `<td class="cell ${st}">${SYM[st]}</td>`; }

function renderMatrix(){
  const cs = cols();
  let h = `<tr><th>Sample</th><th>Family</th>${cs.map(c=>`<th>${esc(D.configs[c].label)}</th>`).join("")}</tr>`;
  for (const s of D.samples.filter(x=>!x.benign).sort((a,b)=>a.family.localeCompare(b.family)||a.id.localeCompare(b.id)))
    h += `<tr><td>${s.id} <span class="tag">${s.difficulty}</span></td><td>${esc(D.families[s.family].title)}</td>${cs.map(c=>cell(c,s)).join("")}</tr>`;
  h += `<tr><th colspan="${2+cs.length}">Benign controls (a flag here is a false alarm)</th></tr>`;
  for (const s of D.samples.filter(x=>x.benign))
    h += `<tr><td>${s.id} <span class="tag">${s.difficulty}</span></td><td>benign</td>${cs.map(c=>cell(c,s)).join("")}</tr>`;
  el("matrix").innerHTML = h;
  el("summaryline").textContent = cs.map(c => `${D.configs[c].label}: caught ${D.configs[c].caught}/${D.configs[c].flawed}, false alarms ${D.configs[c].fp}/${D.configs[c].benign}`).join("  |  ");
}
function famStats(c, fam){ const ss = D.samples.filter(s=>s.family===fam); const k = ss.filter(s=>s.results[c].status==="caught").length; return [k, ss.length]; }
function renderFamilies(){
  const cs = cols();
  let h = `<tr><th>Rule family</th>${cs.map(c=>`<th>${esc(D.configs[c].label)}</th>`).join("")}</tr>`;
  for (const fam of Object.keys(D.families)){
    h += `<tr><td>${esc(D.families[fam].title)}</td>` + cs.map(c => { const [k,n] = famStats(c,fam); return `<td><div class="bar"><i style="width:${n?100*k/n:0}%"></i></div>${k}/${n}</td>`; }).join("") + `</tr>`;
  }
  el("families").innerHTML = h;
}
function renderFw(){
  const cs = cols();
  if (!fwSel.size){ el("fwtable").innerHTML = `<tr><td class="mut">Select a framework above.</td></tr>`; return; }
  let h = "";
  for (const f of fwSel){
    const fw = D.frameworks[f]; h += `<tr><th colspan="${2+cs.length}">${esc(fw.name)}</th></tr>`;
    const byItem = {};
    for (const [fam, def] of Object.entries(D.families)) for (const it of (def.refs[f]||[])) (byItem[it] = byItem[it]||[]).push(fam);
    for (const [it, fams] of Object.entries(byItem)){
      const ss = D.samples.filter(s => fams.includes(s.family));
      h += `<tr><td><b>${esc(it)}</b> ${esc(fw.items[it]||"")}<br><span class="mut">${fams.map(x=>esc(D.families[x].title)).join("; ")}</span></td><td>${ss.length} samples</td>` +
        cs.map(c => `<td>${ss.filter(s=>s.results[c].status==="caught").length}/${ss.length} caught</td>`).join("") + `</tr>`;
    }
    h += `<tr><td colspan="${2+cs.length}" class="mut">Items of this framework with no mapped rule family are not tested by this sample set. Source: <a href="${esc(fw.root)}">${esc(fw.root)}</a></td></tr>`;
  }
  el("fwtable").innerHTML = h;
}
function renderDetail(){
  el("detail").innerHTML = D.samples.map(s => {
    const exp = s.benign ? "Benign control: no finding expected." : "Planted: " + s.expected.map(e=>`${e.file} line ${e.line} (${e.severity})`).join("; ");
    return `<details><summary>${s.id}: ${s.benign?"benign":esc(D.families[s.family].title)} <span class="tag">${s.difficulty}</span></summary><p>${esc(exp)}</p>` +
      allCfgs.map(c => { const r = s.results[c]; return `<p><b>${esc(D.configs[c].label)}</b>: <span class="${r.status}">${SYM[r.status]}</span>` + (r.findings.length ? `<pre>${r.findings.map(esc).join("\n")}</pre>` : " (no findings)") + `</p>`; }).join("") + `</details>`;
  }).join("");
}
function renderSens(){
  let h = `<tr><th>Config</th><th>Caught (main)</th><th>Caught, MEDIUM+</th><th>Caught, incl. hygiene notes</th><th>False alarms (main)</th><th>False alarms, incl. hygiene notes</th><th>What it is</th></tr>`;
  for (const c of allCfgs){ const x = D.configs[c]; h += `<tr><td>${esc(x.label)}</td><td>${x.caught}/${x.flawed}</td><td>${x.caught_medium}/${x.flawed}</td><td>${x.caught_all}/${x.flawed}</td><td>${x.fp}/${x.benign}</td><td>${x.fp_all}/${x.benign}</td><td>${esc(x.desc)}</td></tr>`; }
  el("sens").innerHTML = h;
}
function render(){ renderMatrix(); renderFamilies(); renderFw(); }
buildPick(); render(); renderDetail(); renderSens();
el("vers").textContent = __VERS__;
</script></body></html>
"""

meta = META
vers = "\n".join(f"{k}: {v}" for k, v in meta["images"].items())
out = (page.replace("__DATA__", json.dumps(data))
       .replace("__HEADLINE__", json.dumps(HEADLINE))
       .replace("__VERS__", json.dumps(vers))
       .replace("__RUNDATE__", html.escape("Run " + meta["run_date"]))
       .replace("__NF__", str(len(flawed))).replace("__NB__", str(len(benign)))
       .replace("__CISCOV__", html.escape(meta["cisco_version"])).replace("__SSV__", html.escape(meta["skillspector_version"]))
       .replace("__SSC__", html.escape(meta["skillspector_commit"][:12]))
       .replace("__WIN__", str(N["line_window"])).replace("__ATLASV__", "v5.6.0")
       .replace("__IMGS__", html.escape(", ".join(meta["images"].keys()))))
(ROOT / "report").mkdir(exist_ok=True)
(ROOT / "report" / "index.html").write_text(out, encoding="utf-8")
print("wrote report/index.html", len(out), "bytes")
