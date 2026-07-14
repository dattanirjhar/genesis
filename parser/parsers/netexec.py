"""
NetExec parser — NetExec (nxc) console/log output into Canonical JSON.

NetExec does not emit XML or JSON by default; its usual artifact is the console
log, one line per result:

    PROTO   HOST            PORT   NAME       [status] message

    SMB     10.10.10.10     445    DC01       [*] Windows Server 2019 (name:DC01) (domain:corp.local) (signing:False) (SMBv1:True)
    SMB     10.10.10.10     445    DC01       [+] corp.local\\administrator:P@ssw0rd (Pwn3d!)
    LDAP    10.10.10.10     389    DC01       [+] corp.local\\svc_sql:Summer2024
    SSH     10.10.10.20     22     UBUNTU     [-] root:wrongpass

Unlike a scanner, NetExec results represent *confirmed* interaction, so this
parser records that:

  - `[+]`  successful authentication  -> severity high,     validated True
  - `(Pwn3d!)` administrative access  -> severity critical, validated True
  - `[*]` host info with `signing:False` / `SMBv1:True` -> severity medium
  - `[*]` other info                  -> severity informational
  - `[-]` failures are noise and are skipped

ANSI color codes are stripped defensively (logs are often saved with color).
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from parser.canonical import canonical_document, finding_id, make_finding

# NetExec protocol columns (the first token on a result line).
_PROTOCOLS = (
    "SMB|LDAP|LDAPS|MSSQL|WINRM|SSH|FTP|RDP|VNC|WMI|NFS|SMTP|HTTP|RPC"
)

# One NetExec result line: proto, host (IPv4/IPv6), port, name, [status], message.
_LINE = re.compile(
    r"^(?P<proto>(?:" + _PROTOCOLS + r"))\s+"
    r"(?P<host>\d{1,3}(?:\.\d{1,3}){3}|[0-9A-Fa-f:]+)\s+"
    r"(?P<port>\d+)\s+"
    r"(?P<name>\S+)\s+"
    r"(?P<status>\[[-+*!]\])\s*"
    r"(?P<msg>.*)$"
)

_ANSI = re.compile(r"\x1b\[[0-9;]*m")
_CVE_RE = re.compile(r"CVE-\d{4}-\d{4,7}", re.IGNORECASE)


def matches(sample: str) -> bool:
    """A NetExec log has result lines in the proto/host/port/status format."""
    clean = _ANSI.sub("", sample)
    if "(Pwn3d!)" in clean:
        return True
    return any(_LINE.match(line.strip()) for line in clean.splitlines())


def _classify(status: str, msg: str) -> tuple[str, bool, str]:
    """Map a NetExec status + message to (severity, validated, kind)."""
    msg_l = msg.lower()
    if "pwn3d" in msg_l:
        return "critical", True, "administrative access"
    if status == "[+]":
        return "high", True, "valid authentication"
    if "signing:false" in msg_l or "smbv1:true" in msg_l:
        return "medium", False, "weak configuration"
    return "informational", False, "enumeration"


def parse(path: str | Path) -> dict:
    text = _ANSI.sub("", Path(path).read_text(encoding="utf-8", errors="ignore"))

    findings: list[dict] = []
    hosts: dict[str, dict] = {}

    for raw in text.splitlines():
        match = _LINE.match(raw.strip())
        if not match:
            continue

        status = match["status"]
        if status == "[-]":
            continue  # failed attempt / negative result — not a finding

        proto = match["proto"]
        host = match["host"]
        port = match["port"]
        name = match["name"]
        msg = match["msg"].strip()

        severity, validated, kind = _classify(status, msg)
        cves = sorted({m.upper() for m in _CVE_RE.findall(msg)})
        cve = ", ".join(cves) or "none"

        # Deterministic id: a short digest of the full line keeps multiple
        # results on the same host/port distinct without randomness.
        tag = hashlib.sha1(raw.strip().encode("utf-8")).hexdigest()[:8]

        findings.append(
            make_finding(
                finding_id=finding_id("netexec", host, proto, port, tag),
                host=host,
                port=int(port) if port.isdigit() else None,
                protocol="tcp",
                service=proto.lower(),
                scanner="netexec",
                tool="netexec",
                severity=severity,
                cve=cve,
                validated=validated,
                name=f"{proto} {kind} on {host}",
                description=f"NetExec {proto} result on {host}:{port} ({name}) — {msg}",
                evidence=f"{proto} {host} {port} {name} {status} {msg}",
                banner=msg,
            )
        )

        entry = hosts.setdefault(host, {"host": host, "hostnames": [], "state": "up"})
        if name and name not in entry["hostnames"]:
            entry["hostnames"].append(name)

    return canonical_document(
        "netexec", findings, hosts=list(hosts.values()), raw_file=path
    )
