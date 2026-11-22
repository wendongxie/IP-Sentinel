"""Fail-closed checks for the Windows release pipeline."""

import argparse
import hashlib
from importlib import metadata
import json
from pathlib import Path
import platform
import re
import ssl
import subprocess
import sys
import zipfile


ROOT = Path(__file__).resolve().parents[1]
COMPLIANCE = ROOT / "release-compliance"
POLICY = json.loads((ROOT / "packaging/release-policy.json").read_text(encoding="utf-8"))
SECRET = re.compile(
    rb"\b\d{6,12}:[A-Za-z0-9_-]{30,}\b|"
    rb"qyapi\.weixin\.qq\.com/cgi-bin/webhook/send\?key=[A-Za-z0-9_-]{16,}",
    re.IGNORECASE,
)
PRIVATE_FILES = re.compile(
    r"(^|/)(\.env(\.[^/]+)?|logs|secrets|credentials|runtime|user_data)(/|$)"
    r"|\.(db|sqlite3?|log)(-(wal|shm|journal))?$", re.IGNORECASE,
)


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def ensure(condition, message):
    if not condition:
        raise ValueError(message)


def runtime_files():
    import _hashlib
    import _ssl

    ssl_path = Path(_ssl.__file__).resolve()
    return {
        "_ssl.pyd": ssl_path,
        "_hashlib.pyd": Path(_hashlib.__file__).resolve(),
        "libssl-3-x64.dll": ssl_path.with_name("libssl-3-x64.dll"),
        "libcrypto-3-x64.dll": ssl_path.with_name("libcrypto-3-x64.dll"),
        f"python{sys.version_info.major}{sys.version_info.minor}.dll":
            Path(sys.base_prefix) / f"python{sys.version_info.major}{sys.version_info.minor}.dll",
    }


def runtime():
    actual = ssl.OPENSSL_VERSION_INFO[:3]
    ensure(sys.platform == "win32" and platform.machine().lower() in {"amd64", "x86_64"}
           and sys.maxsize > 2**32, "Windows x64 Python is required")
    ensure(ssl.OPENSSL_VERSION.startswith("OpenSSL "), "Unexpected TLS implementation")
    ensure(actual[:2] != (3, 5) or actual >= tuple(POLICY["openssl_minimum_3_5"]),
           f"{ssl.OPENSSL_VERSION} is below the required security baseline")
    # A version string alone never authorizes new binaries or a different release series.
    import ctypes
    from ctypes import wintypes

    paths = runtime_files()
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetModuleHandleW.argtypes = (wintypes.LPCWSTR,)
    kernel.GetModuleHandleW.restype = wintypes.HMODULE
    kernel.GetModuleFileNameW.argtypes = (wintypes.HMODULE, wintypes.LPWSTR, wintypes.DWORD)
    kernel.GetModuleFileNameW.restype = wintypes.DWORD
    for name in ("libssl-3-x64.dll", "libcrypto-3-x64.dll"):
        handle = kernel.GetModuleHandleW(name)
        buffer = ctypes.create_unicode_buffer(32768)
        length = kernel.GetModuleFileNameW(handle, buffer, len(buffer)) if handle else 0
        ensure(0 < length < len(buffer) and paths[name].samefile(buffer.value),
               f"Loaded {name} differs from the approved runtime location")
    files = {name: sha256(path) for name, path in paths.items()}
    for entry in POLICY["approved_runtimes"]:
        if (
            entry["python"] == platform.python_version()
            and entry["openssl"] == list(actual)
            and entry["files"] == files
            and set(POLICY["required_fixes"]) <= set(entry["verified_fixes"])
            and re.fullmatch(r"[a-f0-9]{64}", entry["archive_sha256"])
            and entry["source"].startswith("https://")
            and entry["evidence"].strip()
        ):
            return {"python": entry["python"], "openssl": ssl.OPENSSL_VERSION, "files": files}
    raise ValueError(f"Unapproved runtime binaries: Python {platform.python_version()}, {ssl.OPENSSL_VERSION}")


def dependencies():
    expected = dict(line.split("==") for line in (ROOT / "packaging/release-lock.txt").read_text().splitlines())
    for name, version in expected.items():
        ensure(metadata.version(name) == version, f"Unexpected dependency version: {name}")
    subprocess.run([sys.executable, "-m", "pip", "check"], check=True)
    return expected


def version():
    number = POLICY["version"]
    manual = ROOT / f"docs/IP_Sentinel_V{number}_用户使用手册.docx"
    for path, marker in (
        ("ip_sentinel/__init__.py", f'DISPLAY_VERSION = "V{number}"'),
        ("packaging/setup.iss", f"AppVersion={number}"),
        ("packaging/windows-version.txt", f"'ProductVersion', '{number}'"),
    ):
        ensure(marker in (ROOT / path).read_text(encoding="utf-8"), f"Inconsistent version: {path}")
    with zipfile.ZipFile(manual) as archive:
        ensure(archive.testzip() is None, "Invalid Word manual")
        ensure(f"V{number}".encode() in archive.read("word/document.xml"), "Word version missing")
    return number


def compliance():
    for name in ("LGPL-3.0-only", "GPL-3.0-only"):
        ensure((COMPLIANCE / "licenses" / f"{name}.txt").stat().st_size > 1000,
               f"Missing complete license: {name}")
    manifest = json.loads((COMPLIANCE / "inventory.json").read_text(encoding="utf-8"))
    ensure(bool(manifest["components"]), "Native component inventory is empty")
    audit = json.loads((COMPLIANCE / "review.json").read_text(encoding="utf-8"))
    ensure(set(audit) == {"native_inventory", "corresponding_source", "third_party_notices", "lgpl_distribution"},
           "Mandatory review record is missing or unrecognized")
    unresolved = [item for item, conclusion in audit.items() if conclusion["status"] != "PASS"]
    unresolved += [item["path"] for item in manifest["components"]
                   if item["review"] != "PASS"]
    if unresolved:
        return "NEEDS_REVIEW", unresolved
    for item in manifest["components"]:
        ensure(all(item.get(key) for key in ("version", "source", "license", "copyright", "evidence")),
               f"Incomplete reviewed component: {item['path']}")
    for conclusion in audit.values():
        ensure(all(conclusion.get(key) for key in ("reviewer", "date", "evidence")),
               "Review acceptance requires reviewer, date and evidence")
        ensure(conclusion.get("inventory_sha256") == sha256(COMPLIANCE / "inventory.json"),
               "Review acceptance does not cover the current component inventory")
        ensure(conclusion.get("source_index_sha256") == sha256(COMPLIANCE / "sources.json"),
               "Review acceptance does not cover the current source index")
    return "PASS", "Reviewed native inventory and source index"


def sources(source_store):
    index = json.loads((COMPLIANCE / "sources.json").read_text(encoding="utf-8"))
    ensure(bool(index), "Source index is empty")
    ensure(source_store is not None, "An external source delivery directory is required")
    for item in index:
        name = item["archive"]
        ensure(Path(name).name == name, "Invalid archive filename")
        ensure(sha256(source_store / name) == item["sha256"], f"Source hash mismatch: {name}")
    return [item["archive"] for item in index]


def scan_file(name, data):
    normalized = name.replace("\\", "/")
    ensure(not PRIVATE_FILES.search(normalized), f"Private data filename: {normalized}")
    ensure(not data.startswith(b"SQLite format 3\0"), f"SQLite payload: {normalized}")
    matches = [match.group() for match in SECRET.finditer(data)]
    for offset in (0, 1):
        utf16 = data[offset:offset + 2 * ((len(data) - offset) // 2)]
        if utf16:
            matches.extend(match.group() for match in SECRET.finditer(
                utf16.decode("utf-16-le", errors="replace").encode("utf-8")
            ))
    # The standard JPEG Huffman symbol table contains this exact ASCII run.
    jpeg_huffman = b"456789:" + b"CDEFGHIJSTUVWXYZcdefghijstuvwxyz"
    if normalized.lower().endswith((".jpeg", ".jpg")) and data.startswith(b"\xff\xd8\xff"):
        matches = [match for match in matches if match != jpeg_huffman]
    ensure(not matches, f"Credential signature: {normalized}")


def scan_tree(path, gitleaks):
    subprocess.run([gitleaks, "dir", "--redact", "--no-banner", str(path)], check=True)
    for entry in sorted(path.rglob("*")):
        if entry.is_file():
            name = entry.relative_to(path).as_posix()
            scan_file(name, entry.read_bytes())
            if entry.suffix.lower() in {".zip", ".docx"}:
                with zipfile.ZipFile(entry) as archive:
                    for member in archive.infolist():
                        if not member.is_dir():
                            scan_file(f"{name}/{member.filename}", archive.read(member))
    return "Local Gitleaks and payload inspection completed"


def payload(path):
    import pefile

    expected = {name.lower(): sha256(file) for name, file in runtime_files().items()}
    entries = [file for file in path.rglob("*") if file.is_file()]
    found = {}
    for file in entries:
        name = file.name.lower()
        if name in expected or re.match(r"(libssl|libcrypto|ssleay|libeay|openssl).*[.]dll$", name):
            ensure(name in expected and name not in found and sha256(file) == expected[name],
                   f"Unexpected, duplicate or altered TLS payload: {file.relative_to(path)}")
            found[name] = expected[name]
    ensure(found == expected, "Frozen Python/OpenSSL modules are missing")
    inventory = json.loads((COMPLIANCE / "inventory.json").read_text(encoding="utf-8"))
    reviewed = {item["path"].casefold(): item for item in inventory["components"]}
    actual = {file.relative_to(path).as_posix().casefold(): file for file in entries
              if file.suffix.lower() in {".dll", ".pyd", ".exe"}}
    ensure(set(actual) == set(reviewed), "Frozen native file list differs from reviewed inventory")
    # The project EXE is built for this run. All external native binaries are pinned.
    for name, file in actual.items():
        if name != "ip sentinel.exe":
            ensure(reviewed[name]["sha256"] == sha256(file), f"Unreviewed native binary: {name}")
    with pefile.PE(str(path / "IP Sentinel.exe")) as exe:
        version_info = exe.VS_FIXEDFILEINFO[0]
        actual_version = (version_info.FileVersionMS >> 16, version_info.FileVersionMS & 65535,
                          version_info.FileVersionLS >> 16, version_info.FileVersionLS & 65535)
    ensure(actual_version == (*map(int, POLICY["version"].split(".")), 0), "EXE version mismatch")
    return {"native_files": len(actual), "runtime_files": found}


def tests():
    result = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
                            cwd=ROOT, text=True, encoding="utf-8", errors="replace", capture_output=True)
    details = (result.stdout + result.stderr).strip()
    count = re.search(r"Ran ([1-9]\d*) tests?", details)
    ensure(result.returncode == 0 and count, f"Test run failed or found no tests:\n{details}")
    return {"count": int(count[1]), "output": details}


def artifacts(directory):
    version_number = POLICY["version"]
    names = [
        f"IPSentinel_Setup_v{version_number}.exe", f"IPSentinel_Portable_v{version_number}.zip",
        f"IP_Sentinel_V{version_number}_用户使用手册.docx", f"IPSentinel_Sources_v{version_number}.zip",
    ]
    expected = {name: sha256(directory / name) for name in names}
    recorded = (directory / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()
    ensure(sorted(recorded) == sorted(f"{digest}  {name}" for name, digest in expected.items()),
           "Published SHA-256 manifest does not match the artifacts")
    return expected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("runtime", "pre", "payload", "artifacts"))
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--sources", type=Path)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--gitleaks", default="gitleaks")
    args = parser.parse_args()
    checks = {}

    def run(name, check):
        try:
            outcome = check()
            status, details = outcome if isinstance(outcome, tuple) else ("PASS", outcome)
        except Exception as exc:
            status, details = "FAIL", str(exc)
        checks[name] = {"status": status, "details": details}

    run("openssl_runtime", runtime)
    if args.phase == "pre":
        run("versions", version)
        run("locked_dependencies", dependencies)
        run("compliance", compliance)
        run("source_delivery", lambda: sources(args.sources))
        run("source_secret_scan", lambda: scan_tree(ROOT, args.gitleaks))
        run("tests", tests)
    if args.phase == "payload":
        run("native_payload", lambda: payload(args.input))
        run("payload_secret_scan", lambda: scan_tree(args.input, args.gitleaks))
    if args.phase == "artifacts":
        run("sha256", lambda: artifacts(args.input))
        run("artifact_secret_scan", lambda: scan_tree(args.input, args.gitleaks))
    statuses = {check["status"] for check in checks.values()}
    overall = "FAIL" if "FAIL" in statuses else "NEEDS_REVIEW" if "NEEDS_REVIEW" in statuses else "PASS"
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.with_suffix(".json").write_text(json.dumps(
        {"phase": args.phase, "status": overall, "checks": checks}, indent=2, ensure_ascii=False
    ) + "\n", encoding="utf-8")
    lines = [f"# Release {args.phase}: {overall}", ""]
    for name, result in checks.items():
        lines.extend([f"## {name} — {result['status']}", "", str(result["details"]), ""])
    args.report.with_suffix(".md").write_text("\n".join(lines), encoding="utf-8")
    print(f"{args.phase}: {overall}")
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
