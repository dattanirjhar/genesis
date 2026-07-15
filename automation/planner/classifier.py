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


def seed_signals(target: str) -> set[str]:
    """Initial signals a target provides, to prime the planner's graph."""
    return set(_SEEDS.get(classify(target), {S.ASSET_HOST}))
