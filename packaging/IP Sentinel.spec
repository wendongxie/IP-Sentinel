# -*- mode: python ; coding: utf-8 -*-


from pathlib import Path
import re
import _ssl
import ssl

root = Path(SPECPATH).parent
icon = root / "assets" / "icons" / "ip-sentinel.ico"

a = Analysis(
    [str(Path(SPECPATH).parent / "main.py")],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    icon=str(icon),
    version=str(root / "packaging" / "windows-version.txt"),
    name='IP Sentinel',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
# Qt on Windows imports the OS ICU ABI. Other software on PATH may ship
# an incompatible ICU DLL with the same filename.

def uses_system_icu(entry):
    filename = Path(entry[0]).name.lower()
    return filename in {"icuuc.dll", "icuin.dll", "icu.dll"} or bool(
        re.fullmatch(r"icudt\d+\.dll", filename)
    )

# _ssl.pyd and OpenSSL must come from the same Python installation.
openssl_dir = Path(_ssl.__file__).parent
openssl_names = {"libcrypto-3-x64.dll", "libssl-3-x64.dll"}
bundled_binaries = []
for entry in a.binaries:
    if uses_system_icu(entry):
        continue
    name = Path(entry[0]).name.lower()
    if name in openssl_names:
        matching_dll = openssl_dir / name
        if not matching_dll.is_file():
            raise FileNotFoundError(matching_dll)
        entry = (entry[0], str(matching_dll), entry[2])
    bundled_binaries.append(entry)
# Some Python distributions load an adjacent rejected-CA bundle when
# creating an SSL context. Keep that runtime policy alongside frozen ssl.py.
bundled_data = [*a.datas, ("assets/icons/ip-sentinel.ico", str(icon), "DATA")]
rejected_cas = Path(ssl.__file__).with_name("codex-rejected-cas.pem")
if rejected_cas.is_file():
    bundled_data.append((rejected_cas.name, str(rejected_cas), "DATA"))

coll = COLLECT(
    exe,
    bundled_binaries,
    bundled_data,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='IP Sentinel',
)





