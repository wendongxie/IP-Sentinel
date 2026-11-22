"""Generate the CPython 3.12 Windows x64 wheel lock from a clean wheelhouse."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import quote


PACKAGING = Path(__file__).resolve().parent


def canonical(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def verify(pin, wheel):
    name, version = pin.split("==")
    url = f"https://pypi.org/pypi/{quote(name)}/{quote(version)}/json"
    response = subprocess.check_output([
        "curl.exe", "--fail", "--silent", "--show-error", "--retry", "2",
        "--connect-timeout", "10", "--max-time", "30", url,
    ])
    files = json.loads(response)["urls"]
    candidates = [entry for entry in files if entry["filename"] == wheel.name and not entry["yanked"]]
    with wheel.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    if len(candidates) != 1 or digest != candidates[0]["digests"]["sha256"]:
        raise ValueError(f"Wheel differs from official PyPI metadata: {wheel.name}")
    return f"# {wheel.name}\n{pin} --hash=sha256:{digest}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wheelhouse", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    pins = (PACKAGING / "release-lock.txt").read_text(encoding="utf-8").splitlines()
    wheels = {}
    for path in sorted(args.wheelhouse.glob("*.whl")):
        name, version, *_, interpreter, abi, system = path.stem.split("-")
        if (interpreter, abi, system) not in {
            ("py3", "none", "any"), ("py2.py3", "none", "any"),
            ("py3", "none", "win_amd64"), ("cp310", "abi3", "win_amd64"),
            ("cp312", "cp312", "win_amd64"),
        }:
            raise ValueError(f"Unexpected wheel tag: {path.name}")
        key = canonical(name), version
        if key in wheels:
            raise ValueError(f"Multiple wheels for {key}")
        wheels[key] = path
    keys = [(canonical(name), version) for name, version in (pin.split("==") for pin in pins)]
    if set(keys) != set(wheels):
        raise ValueError("Wheelhouse does not match release-lock.txt exactly")
    with ThreadPoolExecutor(max_workers=4) as pool:
        verified = list(pool.map(verify, pins, [wheels[key] for key in keys]))
    header = "# CPython 3.12, Windows x64; wheel names and hashes verified against PyPI.\n"
    args.output.write_text(header + "\n".join(verified) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
