import csv
import ssl
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import httpx
from sqlalchemy.exc import IntegrityError

from ip_sentinel import detection, notifications
from ip_sentinel.monitor import Monitor
from ip_sentinel import network
from ip_sentinel.storage import History


class NetworkTests(unittest.TestCase):
    def test_certificate_verification_survives_missing_bundled_file(self):
        import certifi

        with patch.object(certifi, "__file__", "missing-package/certifi/__init__.py"), patch.object(
            certifi, "where", side_effect=FileNotFoundError,
        ), patch.object(network.httpx, "Client") as client:
            network.open_client(6)
        context = client.call_args.kwargs["verify"]
        self.assertTrue(context.check_hostname)
        self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)


class DetectionTests(unittest.TestCase):
    def test_public_address_validation(self):
        for address in ("192.168.1.1", "224.0.0.1", "::ffff:8.8.8.8", "8.8.8.8"):
            with self.assertRaises(ValueError):
                detection.public_ip(address, 6 if ":" in address or address == "8.8.8.8" else 4)

    def test_fallback_and_partial_evidence(self):
        def respond(request):
            host = request.url.host
            if host == "api.ipify.org":
                return httpx.Response(200, text="127.0.0.1")
            if host == "v4.ident.me":
                return httpx.Response(200, text="8.8.8.8")
            if host == "ipwhois.pro":
                return httpx.Response(403, text="dummy-secret")
            if host == "ipwho.is":
                return httpx.Response(200, json={
                    "ip": "8.8.8.8", "success": True, "connection": {"asn": 15169},
                    "security": {"vpn": False, "hosting": "false", "proxy": True},
                })
            raise httpx.ConnectTimeout("offline")
        _, (v4, v6) = detection.detect("dummy-secret", httpx.MockTransport(respond))
        self.assertEqual(v4.source, "https://v4.ident.me")
        self.assertEqual(v4.info["asn"], 15169)
        self.assertEqual(v4.tags, {"vpn": False, "proxy": True, "hosting": None, "tor": None})
        self.assertNotIn("dummy-secret", repr(v4))
        self.assertEqual(v6.ip, "")
        self.assertEqual(len(v6.issues), 2)

    def test_ipv6_canonical_address_and_pro_security(self):
        def respond(request):
            if request.url.host == "api6.ipify.org":
                return httpx.Response(200, text="2606:4700:0000:0000:0000:0000:0000:1111")
            self.assertEqual(request.url.host, "ipwhois.pro")
            self.assertEqual(request.url.path, "/2606:4700::1111")
            self.assertEqual(request.url.params["security"], "1")
            return httpx.Response(200, json={"ip": "2606:4700::1111", "success": True,
                                             "security": {"vpn": True, "tor": False}})
        with httpx.Client(transport=httpx.MockTransport(respond)) as client:
            obs = detection.observe(client, 6, "test-key")
        self.assertEqual(obs.ip, "2606:4700::1111")
        self.assertEqual(obs.metadata_source, "https://ipwhois.pro")
        self.assertEqual(obs.tags, {"vpn": True, "proxy": None, "tor": False, "hosting": None})

    def test_provider_ip_mismatch(self):
        obs = detection.Observation(6, ip="2606:4700::1111")
        response = {"success": True, "ip": "2001:4860:4860::8888", "security": {"tor": True}}
        with httpx.Client(transport=httpx.MockTransport(
            lambda request: httpx.Response(200, json=response)
        )) as client:
            detection.enrich(client, obs, "")
        self.assertIsNone(obs.tags["tor"])
        self.assertTrue(obs.issues)


class HistoryTests(unittest.TestCase):
    def test_changes_survive_failures_and_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "history.sqlite3"
            timestamp = datetime.now(timezone.utc)
            first = History(path)
            first.record(timestamp, [detection.Observation(4, "8.8.8.8"),
                                     detection.Observation(6, "2606:4700::1111")])
            first.record(timestamp, [detection.Observation(4)])
            first.engine.dispose()
            second = History(path)
            try:
                changed = detection.Observation(4, "1.1.1.1")
                second.record(timestamp, [changed, detection.Observation(6, "2606:4700::1111")])
                second.record(timestamp, [detection.Observation(4, "1.1.1.1")])
                self.assertEqual(changed.previous, "8.8.8.8")
                self.assertEqual(second.query()[1], (6, 1, 3))
                self.assertEqual(second.query("%")[1], (0, 0, 0))
                self.assertEqual(len(second.query(size=1, page=1)[0]), 1)
                export = path.with_suffix(".csv")
                second.export(export, "1.1.1.1")
                with export.open(encoding="utf-8-sig", newline="") as file:
                    self.assertEqual(len(list(csv.reader(file))), 3)
            finally:
                second.engine.dispose()

    def test_transaction_rolls_back_second_row_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            db = History(Path(directory) / "test.sqlite3")
            try:
                invalid = detection.Observation(None)
                with self.assertRaises(IntegrityError):
                    db.record(datetime.now(timezone.utc), [
                        detection.Observation(4, "1.1.1.1"), invalid,
                    ])
                self.assertEqual(db.query()[1], (0, 0, 0))
            finally:
                db.engine.dispose()


class NotificationTests(unittest.TestCase):
    def test_change_alert_uses_observed_evidence_and_fits_both_bots(self):
        timestamp = datetime(2026, 11, 21, tzinfo=timezone.utc)
        self.assertEqual(notifications.format_change_alert(timestamp, [
            detection.Observation(4, ip="1.1.1.1"),
        ]), "")
        info = dict.fromkeys(("country", "region", "city", "isp"), "示例" * 40)
        info["asn"] = 13335
        observations = [
            detection.Observation(4, "1.1.1.1", previous="8.8.8.8", info=info,
                                  tags={"vpn": True, "proxy": False},
                                  metadata_source="https://ipwhois.pro"),
            detection.Observation(6, "2606:4700::1111", previous="2001:4860::8888"),
        ]
        alert = notifications.format_change_alert(timestamp, observations)
        self.assertIn("检测时间  ", alert)
        self.assertIn("IPv4\n原 IP  8.8.8.8\n新 IP  1.1.1.1", alert)
        self.assertIn("网络  AS13335", alert)
        self.assertIn("VPN 命中 · PROXY 未标记 · TOR 未知", alert)
        self.assertIn("情报来源  https://ipwhois.pro", alert)
        self.assertIn("IPv6\n原 IP  2001:4860::8888\n新 IP  2606:4700::1111\n新出口归属  未知", alert)
        self.assertLessEqual(len(alert.encode("utf-8")), 2048)

    def test_service_error_and_success(self):
        values = dict(risk_key="", telegram_token="123:fake", telegram_chat="-100",
                      wecom="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=fake")

        def respond(request):
            if request.url.host == "api.telegram.org":
                self.assertIn(b'"chat_id":"-100"', request.content)
                return httpx.Response(200, json={"ok": False})
            self.assertIn(b'"msgtype":"text"', request.content)
            return httpx.Response(200, json={"errcode": 0})
        self.assertEqual(notifications.send(values, "test", httpx.MockTransport(respond)),
                         ["Telegram：服务拒绝请求", "企业微信：已发送"])
        with self.assertRaises(ValueError):
            notifications.validate({**values, "wecom": values["wecom"] + "&other=x"})

    def test_monitor_records_before_notifying(self):
        values = dict.fromkeys(notifications.FIELDS, "")
        with tempfile.TemporaryDirectory() as directory:
            db = History(Path(directory) / "test.sqlite3")
            stamp = datetime.now(timezone.utc)
            db.record(stamp, [detection.Observation(4, "8.8.8.8")])
            messages, completion = [], []
            monitor = Monitor(db, lambda: None, lambda *result: messages.append(result[-1]),
                              completion.append)
            try:
                self.assertEqual(monitor.scheduler.get_jobs()[0].trigger.interval.total_seconds(), 3600)
                with patch.object(notifications, "load", return_value=values), patch.object(
                    detection, "detect", return_value=(stamp, [detection.Observation(4, "1.1.1.1")])
                ), patch.object(notifications, "send", side_effect=lambda *_: [str(db.query()[1][1])]):
                    monitor.run()
                self.assertIn("原 IP  8.8.8.8\n新 IP  1.1.1.1", messages[0])
                self.assertEqual(completion, ["1"])
            finally:
                monitor.shutdown()
                db.engine.dispose()


if __name__ == "__main__":
    unittest.main()



