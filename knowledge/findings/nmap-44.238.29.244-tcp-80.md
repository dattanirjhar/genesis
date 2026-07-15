---
finding_id: nmap-44.238.29.244-tcp-80
host: 44.238.29.244
service: http
scanner: nmap
severity: informational
tool: nmap
cve: CVE-2014-4078
validated: false
confidence: medium
timestamp: 2026-07-15T09:55:13+00:00
---

## Summary
Port 80 on host 44.238.29.244 is running Microsoft IIS httpd version 8.5.

## Evidence
Microsoft IIS httpd 8.5

## Impact
An attacker could exploit known vulnerabilities in Microsoft IIS httpd 8.5, such as those described by CVE-2014-4078, to gain unauthorized access or perform other malicious actions on the web server.

## Recommendation
Update the Microsoft IIS httpd service to a more recent version that is not affected by known vulnerabilities. Verify the update process and ensure all dependencies are correctly configured.

## References
None provided by scanner.

## Commands Used
nmap -p 80 --script http-iis-enum-users,http-iis-vuln-cve20144078

## Timeline
- 2026-07-15T09:55:13+00:00: Finding produced by nmap.
