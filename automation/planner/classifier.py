"""
Target classifier and seed signals.

    URL    -> web.endpoint            (pure web flow; nmap does not run)
    domain -> asset.domain            (recon -> web; nmap only after httpx resolves)
    IP     -> asset.host              (network flow: nmap first)
    CIDR   -> asset.host

Classifying a target yields the *seed signals* that prime the execution graph.
The planner then traverses the graph from those seeds — there is no explicit
"mode", the reachable tools follow from what the target provides. A bare URL
stays a fast web engagement (no nmap); a domain resolves through httpx before any
network scanning; an IP/CIDR is a network engagement.
"""

from __future__ import annotations

import ipaddress
import re
from urllib.parse import urlparse

from automation.execution import signals as S

_DOMAIN = re.compile(
    r"^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?:\.[A-Za-z0-9-]{1,63})+$"
)

_SEEDS = {
    "url": {S.WEB_ENDPOINT},       # web only — nmap stays out of the URL flow
    "domain": {S.ASSET_DOMAIN},
    "ip": {S.ASSET_HOST},
    "cidr": {S.ASSET_HOST},
}


def classify(target: str) -> str:
    """Return one of: url | ip | cidr | domain | unknown."""
    t = target.strip()
    if "://" in t:
        return "url"
    try:
        ipaddress.ip_network(t, strict=False)
        return "cidr" if "/" in t else "ip"
    except ValueError:
        pass
    if _DOMAIN.match(t):
        return "domain"
    return "unknown"


def hostname(target: str) -> str:
    """The bare hostname/IP of a target (strips scheme and path)."""
    t = target.strip()
    if "://" in t:
        return urlparse(t).hostname or t
    return t.split("/")[0]


def registered_domain(target: str) -> str | None:
    """Best-effort registered domain from a target.

    Naive last-two-labels heuristic (vulnweb.com from testaspnet.vulnweb.com).
    Good enough for engagement scoping; multi-part TLDs like co.uk are not
    handled without a public-suffix list.
    """
    host = hostname(target)
    try:
        ipaddress.ip_address(host)
        return None  # an IP has no registered domain
    except ValueError:
        pass
    labels = host.split(".")
    return ".".join(labels[-2:]) if len(labels) >= 2 else None


def seed_signals(target: str, scope: str = "targeted") -> set[str]:
    """Initial signals a target provides, to prime the planner's graph.

    scope="full" (or "recon") expands a URL/domain engagement to the whole web
    footprint by also seeding asset.domain, which makes subfinder/amass/httpx
    reachable. scope="targeted" (default) keeps a URL to just that application.
    """
    kind = classify(target)
    seeds = set(_SEEDS.get(kind, {S.ASSET_HOST}))
    if scope in ("full", "recon") and kind in ("url", "domain"):
        if registered_domain(target):
            seeds.add(S.ASSET_DOMAIN)
    return seeds
