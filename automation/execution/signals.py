"""
Typed signal taxonomy — the vocabulary the planner reasons over.

Connectors declare what they consume and produce in these terms, so the
execution graph (who can run after whom) is *derived* from data dependencies
rather than hand-drawn in a workflow file.

Signals are namespaced by domain. A signal token is either a bare type
("technology") or a type=value pair ("technology=wordpress"). A value token
implies its type, so a tool consuming "technology" is satisfied by
"technology=wordpress". Value tokens are what make conditional branches
(when=...) possible: they only appear at runtime, from actual tool output.
"""

from __future__ import annotations

# Assets
ASSET_DOMAIN = "asset.domain"
ASSET_SUBDOMAIN = "asset.subdomain"
ASSET_HOST = "asset.host"

# Network
NETWORK_RANGE = "network.range"
NETWORK_PORT = "network.port"
NETWORK_SERVICE = "network.service"

# Web
WEB_ENDPOINT = "web.endpoint"
WEB_DIRECTORY = "web.directory"
WEB_PARAMETER = "web.parameter"

# Intelligence
TECHNOLOGY = "technology"
CREDENTIAL = "credential"
CERTIFICATE = "certificate"
VULNERABILITY = "vulnerability"
FINDING = "finding"


def signal_type(token: str) -> str:
    """The type part of a signal token ('technology=wordpress' -> 'technology')."""
    return token.split("=", 1)[0]


def parse(token: str) -> tuple[str, str | None]:
    """Split a token into (type, value); value is None for a bare type."""
    if "=" in token:
        type_, value = token.split("=", 1)
        return type_, value
    return token, None
