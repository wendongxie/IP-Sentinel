import importlib.util
from pathlib import Path
import ssl
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "packaging/release_check.py"
SPEC = importlib.util.spec_from_file_location("ip_sentinel_release_check", SCRIPT)
release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release)


class ReleaseCheckTest(unittest.TestCase):
    def test_known_old_runtime_fails_before_looking_up_native_files(self):
        with (
            patch.object(release.sys, "platform", "win32"),
            patch.object(release.platform, "machine", return_value="AMD64"),
            patch.object(ssl, "OPENSSL_VERSION_INFO", (3, 5, 9, 0, 0)),
            patch.object(ssl, "OPENSSL_VERSION", "OpenSSL 3.5.9"),
            patch.object(release, "runtime_files") as runtime_files,
        ):
            with self.assertRaisesRegex(ValueError, "below"):
                release.runtime()
            runtime_files.assert_not_called()

    def test_private_files_and_disguised_database_are_rejected(self):
        for name, data in (("nested/history.sqlite3-wal", b""), ("readme.txt", b"SQLite format 3\0")):
            with self.subTest(name=name), self.assertRaises(ValueError):
                release.scan_file(name, data)

    def test_utf16_credentials_are_rejected_without_disclosure(self):
        credential = "123456789:" + "A" * 35
        with self.assertRaisesRegex(ValueError, "^Credential signature: sample.bin$"):
            release.scan_file("sample.bin", credential.encode("utf-16-le"))

    def test_jpeg_huffman_symbols_do_not_exempt_credentials(self):
        header = b"\xff\xd8\xff"
        release.scan_file("thumbnail.jpeg", header + b"456789:" + b"CDEFGHIJSTUVWXYZcdefghijstuvwxyz")
        with self.assertRaisesRegex(ValueError, "^Credential signature: thumbnail.jpeg$"):
            release.scan_file("thumbnail.jpeg", header + b"123456789:" + b"A" * 35)

    def test_source_delivery_cannot_pass_without_archive_directory(self):
        with self.assertRaisesRegex(ValueError, "external source delivery directory"):
            release.sources(None)
