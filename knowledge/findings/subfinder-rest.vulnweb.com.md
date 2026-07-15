---
finding_id: subfinder-rest.vulnweb.com
host: rest.vulnweb.com
service: dns
scanner: subfinder
severity: informational
tool: subfinder
cve: none
validated: false
confidence: low
timestamp: unknown
---

## Summary
A potential subdomain, `rest.vulnweb.com`, was discovered via passive enumeration.

## Evidence
`rest.vulnweb.com`

## Impact
Passive discovery of a subdomain does not directly impact security but may be
exploited for reconnaissance purposes. An attacker could use this information
to gather more details about the target's infrastructure.

## Recommendation
Monitor and validate the existence of `rest.vulnweb.com` through active probing.
Consider adding it to DNS records if it is intended, or remove it if not needed.

## References
None provided by scanner.

## Commands Used
`subfinder`

## Timeline
- unknown: Finding produced by subfinder.
