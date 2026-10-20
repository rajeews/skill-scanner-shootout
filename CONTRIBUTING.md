# Contributing

The most useful contributions are more samples, more scanners and corrections. Everything runs in Docker and the
results are meant to be reproducible, so a change should be easy to verify.

## Add a sample Skill
1. Add a directory under `corpus/` (`SKILL.md` plus any scripts). Keep it **inert**: only `example.com` / `.invalid`
   hosts, no working payloads, no real or secret-looking credentials, nothing that does harm if run.
2. Add its answer key to `expected/<id>.json` (family, file, line, severity; benign controls have an empty list).
   The scanners never see `expected/`.
3. If it belongs to a new rule family, add it to `frameworks/frameworks.json` with framework references. Every ID must be
   checked at the framework owner's page (OWASP, MITRE ATLAS, CWE, ATT&CK). The mapping is a judgement call; say why.
4. Run `sh harness/reproduce.sh` and include the changed `results/` in your pull request.
`harness/make_corpus.py` is the generator used for the first set; you can edit it or add files by hand.

## Add a scanner
Add a Dockerfile in `docker/` (pin base image digests and the exact tool version), a config line in
`harness/run_scanners.sh` (no API keys, no LLM stage unless you add it as a clearly labelled separate config), and a
parser in `harness/normalize.py`. Run it with the same lock-down as the others.

## Report a wrong result
Open an issue with the sample id, the scanner config and what you expected. If a tool was run in a way that doesn't
reflect its intended use, say how, and the maintainers of that tool are welcome to propose a configuration. Confirmed
mistakes are fixed in the open.

## Sign-off
Please sign off your commits (`git commit -s`) to confirm you have the right to submit your changes under the MIT licence.
