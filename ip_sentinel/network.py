"""HTTP client with TLS verification and the Windows trust store."""
from pathlib import Path
import ssl

import certifi
import httpx


def open_client(timeout, transport=None):
    context = ssl.create_default_context()
    bundle = Path(certifi.__file__).with_name("cacert.pem")
    if bundle.is_file():
        context.load_verify_locations(cafile=str(bundle))
    return httpx.Client(timeout=timeout, transport=transport, verify=context)
