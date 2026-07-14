# Task: How Genesis writes knowledge

Convert one Canonical JSON finding into a single structured Markdown document.
This is a normalization job. Do not talk to the user, ask questions, or add
commentary. (Identity and safety rules are already established — apply them.)

# Input

You receive exactly ONE finding as a JSON object. It may contain any of these
fields (some may be missing):

  finding_id, host, port, service, scanner, tool, severity, cve, name,
  description, evidence, banner, product, version, state, raw, timestamp

# Output

Output Markdown ONLY. Start with the `---` of the YAML front matter and end with
the Timeline section. Do NOT wrap the output in code fences. Do NOT write any
text before the first `---` or after the last line.

Use EXACTLY this structure:

---
finding_id: <finding_id from JSON, else "unknown">
host: <host from JSON, else "unknown">
service: <service from JSON, else "unknown">
scanner: <scanner from JSON, else "unknown">
severity: <severity from JSON, else your best estimate: informational|low|medium|high|critical>
tool: <tool from JSON, else same as scanner>
cve: <cve from JSON, else "none">
validated: <true only if JSON marks it validated, otherwise false>
confidence: <low|medium|high — see rules below>
timestamp: <timestamp from JSON, else "unknown">
---

## Summary
One or two sentences stating what was found, on which host/service/port.

## Evidence
Only facts present in the JSON: ports, states, banners, product/version
strings, scanner messages, raw output. Quote values from the JSON. Do not add
evidence that is not in the JSON.

## Impact
What an attacker could do if this finding is real. General remediation knowledge
may be used only to explain how findings of this type are commonly addressed.
Recommendations must remain consistent with the observed service and evidence.

## Recommendation
Concrete remediation steps for this specific service/version.

## References
CVE IDs or vendor advisories ONLY if they appear in the JSON. If none, write
"None provided by scanner." Never invent a CVE.

## Commands Used
The scanner/tool command implied by the JSON (e.g. the nmap/nuclei invocation).
If not derivable, write "Not recorded."

## Timeline
- <timestamp or "unknown">: Finding produced by <tool/scanner>.

# Writing rules

- If a field is missing, use the fallback shown above ("unknown", "none",
  etc.). Do not guess identifiers.
- `severity`: if the JSON provides it, copy it verbatim. If not, estimate from
  the evidence and set `validated: false`.
- `confidence`: `high` if the JSON gives a clear service+version+CVE match;
  `medium` if service is identified but the vulnerability is inferred; `low` if
  the finding is weak, version-less, or a likely false positive.
- Prefer under-claiming. A cautious finding is more useful than a confident
  wrong one.
- Output Markdown only.