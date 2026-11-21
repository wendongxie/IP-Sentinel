"""Network observations and provider evidence."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timezone
from ipaddress import ip_address

import httpx

from .network import open_client

ENDPOINTS = {4: ("https://api.ipify.org", "https://v4.ident.me"),
             6: ("https://api6.ipify.org", "https://v6.ident.me")}
TAGS = ("vpn", "proxy", "tor", "hosting")


@dataclass
class Observation:
    family: int
    ip: str = ""
    source: str = ""
    metadata_source: str = ""
    info: dict = field(default_factory=dict)
    tags: dict = field(default_factory=lambda: dict.fromkeys(TAGS))
    issues: list = field(default_factory=list)
    previous: str = ""
    list_evidence: list = field(default_factory=list)


def public_ip(value, family):
    if not isinstance(value, str):
        raise ValueError("Invalid address")
    address = ip_address(value.strip())
    if (address.version != family or not address.is_global or address.is_multicast
            or getattr(address, "scope_id", None) or getattr(address, "ipv4_mapped", None)):
        raise ValueError("Invalid public address")
    return str(address)


def failure(exc):
    if isinstance(exc, httpx.HTTPStatusError):
        return f"HTTP {exc.response.status_code}"
    return type(exc).__name__


def enrich(client, obs, key):
    providers = []
    if key:
        providers.append(("https://ipwhois.pro", {"key": key, "security": "1"}))
    providers.append(("https://ipwho.is", {}))
    for source, params in providers:
        try:
            response = client.get(f"{source}/{obs.ip}", params=params)
            response.raise_for_status()
            data = response.json()
            if (not isinstance(data, dict) or data.get("success") is not True
                    or public_ip(data.get("ip"), obs.family) != obs.ip):
                raise ValueError("Provider rejected lookup or returned a different IP")
            connection = data.get("connection")
            connection = connection if isinstance(connection, dict) else {}
            security = data.get("security")
            security = security if isinstance(security, dict) else {}
            obs.info = {
                name: value for name, value in (
                    *((name, data.get(name)) for name in ("country", "region", "city")),
                    *((name, connection.get(name)) for name in ("asn", "isp", "org")),
                ) if type(value) in (str, int)
            }
            obs.tags = {tag: security[tag] if type(security.get(tag)) is bool else None
                        for tag in TAGS}
            obs.metadata_source = source
            return
        except (httpx.HTTPError, ValueError) as exc:
            obs.issues.append(f"{source} 查询失败 ({failure(exc)})")


def observe(client, family, key):
    obs = Observation(family)
    for source in ENDPOINTS[family]:
        try:
            response = client.get(source)
            response.raise_for_status()
            obs.ip = public_ip(response.text, family)
            obs.source = source
            break
        except (httpx.HTTPError, ValueError) as exc:
            obs.issues.append(f"{source} 探测失败 ({failure(exc)})")
    if obs.ip:
        enrich(client, obs, key)
    return obs


def detect(key="", transport=None):
    timestamp = datetime.now(timezone.utc)
    with open_client(6, transport) as client, ThreadPoolExecutor(2) as pool:
        jobs = [pool.submit(observe, client, family, key) for family in (4, 6)]
        return timestamp, [job.result() for job in jobs]


