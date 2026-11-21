import csv
from datetime import datetime, timezone
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event
import unittest
from unittest.mock import patch

import httpx

from ip_sentinel.detection import Observation
from ip_sentinel.notifications import format_change_alert
from ip_sentinel.risk_lists import FEEDS, RiskCache, evidence_line
from ip_sentinel.storage import History, history


STAMP = datetime(2026, 11, 21, tzinfo=timezone.utc)
EDGES = {
    "vpn-ipv4": ["8.8.8.0/24"],
    "vpn-ipv6": ["2606:4700::/32"],
    "datacenter-ipv4": ["8.8.0.0/16"],
    "datacenter-ipv6": ["2001:4860::/32"],
}


def feed_reply(request):
    if request.url.host == "check.torproject.org":
        return httpx.Response(200, text="# comment\n8.8.8.8\n")
    feed = request.url.path.split("/")[-2]
    return httpx.Response(200, json={"type": "cidr", "version": 20261121,
                                     "list": EDGES[feed]})


class RiskListTests(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name)
        self.cache = RiskCache(self.path / "risk-lists")

    def test_ipv4_ipv6_tor_hits_and_missing_coverage(self):
        self.assertTrue(all(item["status"] == "未知" for item in self.cache.evidence("8.8.8.8")))
        self.assertEqual(self.cache.refresh(httpx.MockTransport(feed_reply)), {})
        v4 = self.cache.evidence("8.8.8.8")
        self.assertEqual([x["status"] for x in v4], ["名单命中"] * 3)
        self.assertEqual(v4[-1]["label"], "机房或 VPN 网段")
        self.assertTrue(all(x["fetched_at"] for x in v4))
        self.assertEqual([x["status"] for x in self.cache.evidence("2606:4700::123")],
                         ["未知", "名单命中", "该名单未收录"])
        self.assertEqual([x["status"] for x in self.cache.evidence("1.1.1.1")],
                         ["该名单未收录"] * 3)

    def test_retains_previous_on_invalid_empty_and_failed_responses(self):
        self.cache.refresh(httpx.MockTransport(feed_reply))
        previous = self.cache.evidence("8.8.8.8")
        original = (self.cache.path / "tor.json").read_bytes()

        def broken(request):
            if request.url.host == "check.torproject.org":
                return httpx.Response(200, text="# no valid records")
            if "vpn-ipv4" in request.url.path:
                return httpx.Response(200, json={"type": "cidr", "version": 20261122,
                                                 "list": ["2001:4860::/32"]})
            return httpx.Response(503)
        errors = self.cache.refresh(httpx.MockTransport(broken), force=True)
        self.assertEqual(set(errors), {feed.id for feed in FEEDS})
        self.assertEqual((self.cache.path / "tor.json").read_bytes(), original)
        loaded = RiskCache(self.cache.path)
        loaded.load()
        self.assertEqual(loaded.evidence("8.8.8.8"), previous)

    def test_refresh_in_progress_does_not_block_reading_previous_match(self):
        self.cache.refresh(httpx.MockTransport(feed_reply))
        previous = self.cache.evidence("8.8.8.8")
        started = Event()
        finish = Event()
        finished = Event()

        def slow_refresh():
            started.set()
            finish.wait(5)
            finished.set()

        with patch.object(self.cache, "refresh", side_effect=slow_refresh):
            try:
                self.cache.start()
                self.assertTrue(started.wait(2))
                self.assertEqual(self.cache.evidence("8.8.8.8"), previous)
                self.assertFalse(finished.is_set())
            finally:
                self.cache.stop()
                finish.set()
                self.assertTrue(finished.wait(2))

    def test_paid_and_list_conflict_and_message_size(self):
        self.cache.refresh(httpx.MockTransport(feed_reply))
        text = chr(0x1F600) * 100
        fields = dict.fromkeys(("country", "region", "city", "isp", "asn"), text)
        observations = [
            Observation(4, "8.8.8.8", previous="1.1.1.1", info=fields,
                        tags={"vpn": False, "proxy": None}, metadata_source="https://ipwhois.pro"),
            Observation(6, "2606:4700:ffff:ffff:ffff:ffff:ffff:1111", info=fields,
                        previous="2001:4860:ffff:ffff:ffff:ffff:ffff:2222"),
        ]
        for obs in observations:
            obs.list_evidence = self.cache.evidence(obs.ip)
        message = format_change_alert(STAMP, observations)
        self.assertIn("VPN 未标记", message)
        self.assertIn("PROXY 未知", message)
        self.assertIn("已知 VPN 网段（MISP / X4BNet）名单命中 · 版本 20261121", message)
        self.assertIn("Tor 出口（Tor Project）未知", message)
        self.assertIn("名单未收录仅表示该来源未找到记录", message)
        self.assertLessEqual(len(message.encode()), 2048)
        self.assertIn("获取于", evidence_line(observations[0].list_evidence[1]))

    def test_old_history_and_csv_compatibility(self):
        db = History(self.path / "history.sqlite3")
        self.addCleanup(db.engine.dispose)
        with db.engine.begin() as conn:
            conn.execute(history.insert().values(
                observed_at=STAMP.isoformat(), family=4, ip="1.1.1.1", previous="",
                evidence={"metadata_source": "", "tags": {}},
            ))
        self.cache.refresh(httpx.MockTransport(feed_reply))
        db.record(STAMP, [Observation(4, "8.8.8.8", list_evidence=self.cache.evidence("8.8.8.8"))])
        rows, _ = db.query()
        self.assertNotIn("list_evidence", rows[1]["evidence"])
        self.assertEqual(rows[0]["previous"], "1.1.1.1")
        target = self.path / "export.csv"
        db.export(target)
        with target.open(encoding="utf-8-sig", newline="") as stream:
            exported = list(csv.reader(stream))
        self.assertEqual(json.loads(exported[1][-1])["list_evidence"][0]["source"], "Tor Project")

