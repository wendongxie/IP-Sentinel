"""Download public risk lists and match addresses locally."""
from bisect import bisect_right
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from ipaddress import collapse_addresses, ip_address, ip_network
import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from threading import Event, Lock, Thread

import httpx

from .network import open_client

MAX_BYTES = 8 * 1024 * 1024
REFRESH_HOURS = 12
MISP_ROOT = "https://raw.githubusercontent.com/MISP/misp-warninglists/main/lists/"


@dataclass(frozen=True)
class Feed:
    id: str
    label: str
    source: str
    url: str
    family: int | None = None


FEEDS = (
    Feed("tor", "Tor 出口", "Tor Project", "https://check.torproject.org/torbulkexitlist"),
    *(Feed(f"{kind}-ipv{family}", label, "MISP / X4BNet",
           f"{MISP_ROOT}{kind}-ipv{family}/list.json", family)
      for kind, label in (("vpn", "已知 VPN 网段"), ("datacenter", "机房或 VPN 网段"))
      for family in (4, 6)),
)


@dataclass(frozen=True)
class Snapshot:
    entries: tuple[str, ...]
    version: str
    fetched_at: datetime
    indexes: dict

    def lookup(self, address):
        index = self.indexes.get(address.version)
        if index is None:
            return "未知"
        starts, ends = index
        value = int(address)
        position = bisect_right(starts, value) - 1
        return "名单命中" if position >= 0 and value <= ends[position] else "该名单未收录"


def parse_snapshot(feed, entries, version, fetched_at):
    valid_version = version == "" if feed.family is None else (
        isinstance(version, str) and version.isascii() and version.isdecimal() and len(version) <= 12
    )
    if not isinstance(entries, list) or not entries or not valid_version or fetched_at.tzinfo is None:
        raise ValueError("Invalid snapshot metadata")
    families = {4: [], 6: []}
    for entry in entries:
        if not isinstance(entry, str) or "%" in entry:
            raise ValueError("Invalid address entry")
        if feed.family is None:
            network = ip_network(ip_address(entry))
        else:
            network = ip_network(entry)
            if network.version != feed.family or network.prefixlen == 0:
                raise ValueError("Invalid network family or prefix")
        families[network.version].append(network)

    indexes = {}
    for family, networks in families.items():
        if networks:
            ordered = tuple(collapse_addresses(networks))
            indexes[family] = (
                tuple(int(net.network_address) for net in ordered),
                tuple(int(net.broadcast_address) for net in ordered),
            )
    return Snapshot(tuple(entries), version, fetched_at, indexes)


def download(feed, client):
    with client.stream("GET", feed.url) as response:
        response.raise_for_status()
        payload = bytearray()
        for chunk in response.iter_bytes():
            payload.extend(chunk)
            if len(payload) > MAX_BYTES:
                raise ValueError("Risk list exceeds size limit")
    if feed.family is None:
        entries = [line.strip() for line in payload.decode("ascii").splitlines()
                   if line.strip() and not line.lstrip().startswith("#")]
        version = ""
    else:
        data = json.loads(payload)
        if not isinstance(data, dict) or data.get("type") != "cidr":
            raise ValueError("Unexpected MISP list type")
        entries, version = data.get("list"), data.get("version")
        if not isinstance(entries, list) or type(version) is not int or version <= 0:
            raise ValueError("Invalid MISP entries or version")
        version = str(version)
    return parse_snapshot(feed, entries, version, datetime.now(timezone.utc))


class RiskCache:
    def __init__(self, path):
        self.path = Path(path)
        self._snapshots = {}
        self._lock = Lock()
        self._stop = Event()

    def start(self):
        Thread(target=self._run, name="risk-list-refresh", daemon=True).start()

    def stop(self):
        self._stop.set()

    def _run(self):
        self.load()
        while not self._stop.is_set():
            self.refresh()
            self._stop.wait(REFRESH_HOURS * 3600)

    def load(self):
        for feed in FEEDS:
            path = self.path / f"{feed.id}.json"
            try:
                if path.stat().st_size > MAX_BYTES:
                    continue
                data = json.loads(path.read_bytes())
                snapshot = parse_snapshot(feed, data["entries"], data["version"],
                                          datetime.fromisoformat(data["fetched_at"]))
            except (OSError, ValueError, TypeError, KeyError):
                continue
            with self._lock:
                self._snapshots[feed.id] = snapshot

    def _save(self, feed, snapshot):
        self.path.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(dir=self.path, suffix=".tmp", delete=False) as temp:
            path = Path(temp.name)
            try:
                temp.write(json.dumps({
                    "entries": snapshot.entries,
                    "version": snapshot.version,
                    "fetched_at": snapshot.fetched_at.isoformat(),
                }, separators=(",", ":")).encode("ascii"))
            except BaseException:
                temp.close()
                path.unlink(missing_ok=True)
                raise
        try:
            path.replace(self.path / f"{feed.id}.json")
        finally:
            path.unlink(missing_ok=True)

    def refresh(self, transport=None, *, force=False):
        failures = {}
        try:
            with open_client(6, transport) as client:
                for feed in FEEDS:
                    if self._stop.is_set():
                        break
                    with self._lock:
                        old = self._snapshots.get(feed.id)
                    if not force and old and datetime.now(timezone.utc) - old.fetched_at < timedelta(
                        hours=REFRESH_HOURS
                    ):
                        continue
                    try:
                        snapshot = download(feed, client)
                        if old and snapshot.version and int(snapshot.version) < int(old.version):
                            raise ValueError("Older upstream version")
                        self._save(feed, snapshot)
                    except (httpx.HTTPError, OSError, ValueError) as exc:
                        failures[feed.id] = type(exc).__name__
                        continue
                    with self._lock:
                        self._snapshots[feed.id] = snapshot
        except (httpx.HTTPError, OSError, ValueError) as exc:
            failures["client"] = type(exc).__name__
        return failures

    def evidence(self, ip):
        address = ip_address(ip)
        with self._lock:
            snapshots = self._snapshots.copy()
        result = []
        for feed in FEEDS:
            if feed.family not in (None, address.version):
                continue
            snapshot = snapshots.get(feed.id)
            result.append({
                "id": feed.id,
                "label": feed.label,
                "source": feed.source,
                "url": feed.url,
                "status": snapshot.lookup(address) if snapshot else "未知",
                "coverage": bool(snapshot and address.version in snapshot.indexes),
                "version": snapshot.version if snapshot else "",
                "fetched_at": snapshot.fetched_at.isoformat() if snapshot else "",
            })
        return result


def evidence_line(item, *, compact=False):
    fetched = item["fetched_at"]
    stamp = f"版本 {item['version']}" if item["version"] else (
        f"{fetched[:16].replace('T', ' ')} UTC" if fetched else "暂无可用名单"
    )
    if not compact and fetched and item["version"]:
        stamp += f" · 获取于 {fetched}"
    status = item["status"]
    if fetched and not item["coverage"]:
        status += "（协议未覆盖）"
    return f"{item['label']}（{item['source']}）{status} · {stamp}"


