"""
Nmap parser — Nmap XML (`-oX`) into Canonical JSON.

Each open port becomes one finding. Nmap does not assign severities, so open
ports are recorded as `informational`; any CVE ids surfaced by NSE scripts
(e.g. the `vulners` script) are collected into the `cve` field.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

from parser.canonical import canonical_document, finding_id, make_finding

_CVE_RE = re.compile(r"CVE-\d{4}-\d{4,7}", re.IGNORECASE)


def matches(sample: str) -> bool:
    """Nmap XML documents open with an <nmaprun> root element."""
    return "<nmaprun" in sample


def _iso(epoch: str | None) -> str | None:
    """Convert an Nmap epoch-seconds attribute to an ISO-8601 UTC string."""
    if not epoch:
        return None
    try:
        return datetime.fromtimestamp(int(epoch), tz=timezone.utc).isoformat()
    except (ValueError, OverflowError):
        return None


def parse(path: str | Path) -> dict:
    root = ET.parse(path).getroot()

    args = root.get("args", "")
    started = _iso(root.get("start")) or root.get("startstr", "unknown")

    hosts: list[dict] = []
    findings: list[dict] = []

    for host_el in root.findall("host"):
        status = host_el.find("status")
        host_state = status.get("state", "unknown") if status is not None else "unknown"

        # Prefer an IP address; fall back to whatever address is present.
        addr = "unknown"
        for a in host_el.findall("address"):
            if a.get("addrtype") in ("ipv4", "ipv6"):
                addr = a.get("addr", "unknown")
                break
        else:
            first = host_el.find("address")
            if first is not None:
                addr = first.get("addr", "unknown")

        hostnames = [
            h.get("name")
            for h in host_el.findall("hostnames/hostname")
            if h.get("name")
        ]
        host_ts = _iso(host_el.get("endtime")) or started

        hosts.append({"host": addr, "hostnames": hostnames, "state": host_state})

        ports_el = host_el.find("ports")
        if ports_el is None:
            continue

        for port_el in ports_el.findall("port"):
            state_el = port_el.find("state")
            port_state = state_el.get("state") if state_el is not None else "unknown"
            if port_state != "open":
                continue  # only open ports are findings

            proto = port_el.get("protocol", "tcp")
            portid = port_el.get("portid", "")

            svc = port_el.find("service")
            service = svc.get("name", "unknown") if svc is not None else "unknown"
            product = svc.get("product", "") if svc is not None else ""
            version = svc.get("version", "") if svc is not None else ""
            extrainfo = svc.get("extrainfo", "") if svc is not None else ""
            banner = " ".join(x for x in (product, version, extrainfo) if x)

            # Collect any CVEs reported by NSE scripts on this port.
            cves: set[str] = set()
            for script in port_el.findall("script"):
                cves.update(m.upper() for m in _CVE_RE.findall(script.get("output", "")))
            cve = ", ".join(sorted(cves)) or "none"

            description = f"Open {proto} port {portid} running {service} on {addr}."
            if banner:
                description = description[:-1] + f" ({banner})."

            findings.append(
                make_finding(
                    finding_id=finding_id("nmap", addr, proto, portid),
                    host=addr,
                    port=int(portid) if portid.isdigit() else None,
                    protocol=proto,
                    service=service,
                    scanner="nmap",
                    tool="nmap",
                    severity="informational",
                    cve=cve,
                    name=f"Open {proto}/{portid} ({service})",
                    description=description,
                    evidence=banner or f"{proto}/{portid} {service}",
                    banner=banner,
                    product=product,
                    version=version,
                    state=port_state,
                    timestamp=host_ts,
                )
            )

    return canonical_document(
        "nmap", findings, hosts=hosts, args=args, started=started, raw_file=path
    )
