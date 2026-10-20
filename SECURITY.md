# Security policy

**The sample Skills in `corpus/` are intentionally suspicious-looking but inert.** They use only `example.com` and `.invalid`
hosts, contain no working payloads and no real credentials, and the harness never runs them: the scanners only read them.
Antivirus, EDR or corporate scanners may still flag them. Don't clone this repo onto a managed work machine.

- Found a problem in this repository's harness, Dockerfiles or samples (for example a sample that is not inert, or a
  sensitive string that slipped in)? Please open a private security advisory on GitHub for this repo, or an issue if
  nothing sensitive is involved.
- Found a vulnerability in Cisco Skill Scanner or NVIDIA SkillSpector? Report it to their maintainers, not here.
