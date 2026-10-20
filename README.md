# Skill scanner shoot-out

> **Heads-up:** the sample Skills in `corpus/` are **intentionally suspicious-looking but inert** (fake hosts, no working
> payloads, no real credentials). Antivirus, EDR or corporate security tools may flag them. **Don't clone this repo onto a
> managed work machine.** The scanners only read the samples; nothing here executes them.

A small, reproducible benchmark of open-source scanners for AI-agent Skills (`SKILL.md` plus scripts). It runs each scanner
against a set of planted flaws and harmless controls, and records what each one catches, misses and falsely flags.

**Results page:** `report/index.html` (also published at https://rajeew.com/skill-scanner-shootout/).
**Write-up:** https://rajeew.com/blog/skill-scanner-shootout/

## Headline (18 planted flaws, 6 harmless controls, static analysis only)

| Config | Planted flaws caught | Harmless controls flagged |
|---|---|---|
| Cisco Skill Scanner 2.3.0, default | 7 / 18 | 1 / 6 |
| Cisco, + behavioral analyzer | 7 / 18 | 1 / 6 |
| Cisco, strict policy | 7 / 18 | 2 / 6 |
| Cisco, + behavioral + OSV.dev check (online) | 9 / 18 | 1 / 6 |
| NVIDIA SkillSpector v2.13.0, offline | 13 / 18 | 2 / 6 |
| NVIDIA SkillSpector, + OSV.dev check (online) | 13 / 18 | 2 / 6 |

These numbers describe **this small, synthetic sample set only**. They are not a ranking of the tools. No LLM review stage,
VirusTotal or cloud analyzer was run (no API keys). Cisco's README says every setup it recommends includes its LLM judge and
that rules alone catch only about 8% of its own held-out malicious Skills. Snyk Agent Scan was not run: it needs a Snyk
token and sends Skill content to Snyk's API.

## What is in here

| Path | What it is |
|---|---|
| `corpus/` | 24 sample Skills with neutral names (`skill-01` ...): 18 with a planted flaw (9 rule families, 2 each) and 6 benign controls |
| `expected/` | The answer key (family, file, line). Scanners never see this folder |
| `frameworks/` | Rule families mapped to OWASP LLM Top 10 2025, OWASP Top 10 for Agentic Applications, MITRE ATLAS, CWE and ATT&CK items. The mapping is the author's judgement, not an official crosswalk; each ID was checked at its owner's page |
| `docker/` | One Dockerfile per tool, base image pinned by digest, tool versions pinned |
| `harness/` | Build, run, normalize, report and chart scripts (standard library plus matplotlib for the chart) |
| `results/` | Raw scanner output per sample and config, the normalized results, pinned versions and image IDs |
| `report/index.html` | The self-contained results explorer (no external requests) |
| `visual/` | The headline chart |

## Reproduce

Needs Docker. Network is used only while building images; scans run with the network off (except the two configs marked
"online", which enable an OSV.dev dependency lookup).

```sh
sh harness/reproduce.sh
```

Each scan runs in its own container: non-root, read-only filesystem, all capabilities dropped, memory and process limits,
the corpus mounted read-only, output captured from stdout. Allow roughly 15 to 25 minutes. Re-running gives your own numbers;
tool versions move quickly, so results will change with newer releases.

## How results are counted

A planted flaw is **caught** if some finding above INFO severity is in the right file and either has no line number, sits within
5 lines of the planted line, or quotes the planted text in its snippet. A benign control is a **false alarm** if a scanner
reports any such finding on it. Manifest and policy hygiene notes (for example "no license field", SkillSpector's "MCP least
privilege" note, and SkillSpector's "OSV.dev unreachable" notice) are excluded from the main numbers; the report shows the
counts with them included. Category agreement is not required. See `harness/normalize.py`.

## Limits

Small, synthetic, author-written sample set (22 of the 24 samples were written before any scanner was installed; the last two (known-vulnerable pinned dependencies) were added after a first run to exercise the online dependency check, and every scan was then re-run on the full set. No sample was tuned to a tool's output.); static analysis
only; default or near-default settings; some samples are deliberately hard. A research paper cautions that scanner verdicts on
real marketplaces can be inflated: https://arxiv.org/pdf/2603.16572.

## Corrections

If you maintain one of these tools, or think a result is wrong or a tool was run in a way that doesn't reflect its intended
use, please open an issue. The results will be re-run with your recommended configuration and the change published, including
what was wrong. See `CONTRIBUTING.md` for adding samples or scanners.

## Licence

MIT (code and samples), see `LICENSE`. Third-party tools and attribution: `NOTICE`.
