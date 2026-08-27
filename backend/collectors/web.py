"""Shared HTTP helpers: retries, backoff, JSON helpers. No API keys anywhere."""
from __future__ import annotations

import json
import random
import shutil
import ssl
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode = ssl.CERT_NONE


def _open(url: str, headers: dict, data: bytes | None, timeout: int, use_insecure_ssl: bool):
    req = urllib.request.Request(url, data=data, headers=headers)
    kwargs = {"timeout": timeout}
    if use_insecure_ssl:
        kwargs["context"] = _SSL_CTX
    return urllib.request.urlopen(req, **kwargs)


def _retry(fn, retries, backoff, jitter):
    last = None
    for attempt in range(retries):
        try:
            return fn()
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (429, 500, 502, 503, 504) and attempt < retries - 1:
                wait = backoff * (2 ** attempt) + random.uniform(0, jitter)
                time.sleep(wait)
                continue
            if e.code != 404:
                raise
            raise
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            last = e
            if attempt < retries - 1:
                time.sleep(backoff * (2 ** attempt) + random.uniform(0, jitter))
                continue
            raise
    raise last


def http_get(url, headers=None, timeout=25, retries=3, backoff=2.0, jitter=1.0,
             use_insecure_ssl=True, ua=None) -> bytes:
    hdrs = {"User-Agent": ua or DEFAULT_UA, **(headers or {})}

    def fn():
        with _open(url, hdrs, None, timeout, use_insecure_ssl) as r:
            return r.read()

    return _retry(fn, retries, backoff, jitter)


def http_get_json(url, headers=None, timeout=25, retries=3, backoff=2.0, jitter=1.0,
                  use_insecure_ssl=True, ua=None):
    data = http_get(url, headers=headers, timeout=timeout, retries=retries,
                    backoff=backoff, jitter=jitter, use_insecure_ssl=use_insecure_ssl, ua=ua)
    return json.loads(data.decode("utf-8", "replace"))


def http_post_json(url, payload: dict, headers=None, timeout=30, retries=3,
                   backoff=2.0, jitter=1.0, use_insecure_ssl=True, ua=None):
    body = json.dumps(payload).encode("utf-8")
    hdrs = {
        "User-Agent": ua or DEFAULT_UA,
        "Content-Type": "application/json",
        "Accept": "application/json",
        **(headers or {}),
    }

    def fn():
        with _open(url, hdrs, body, timeout, use_insecure_ssl) as r:
            return json.loads(r.read().decode("utf-8", "replace"))

    return _retry(fn, retries, backoff, jitter)


CURL_EXE = shutil.which("curl") or "curl"


def curl_get(url: str, timeout=40, retries=3, backoff=3.0, jitter=2.0) -> bytes:
    """Fetch via curl.exe — some sites block python TLS fingerprints but not curl."""
    cmd = [
        CURL_EXE, "-sS", "-L", "--max-time", str(timeout),
        "-A", DEFAULT_UA,
        "-H", "Accept-Language: en-US,en;q=0.9",
        "-H", "sec-ch-ua: \"Not/A)Brand\";v=\"8\", \"Chromium\";v=\"126\"",
        "-H", "sec-ch-ua-mobile: ?0",
        "-H", "sec-ch-ua-platform: \"Windows\"",
        "-H", "Sec-Fetch-Dest: document",
        "-H", "Sec-Fetch-Mode: navigate",
        "-H", "Sec-Fetch-Site: none",
        "-o", "-",
        url,
    ]

    def fn():
        proc = subprocess.run(cmd, capture_output=True, timeout=timeout + 10)
        if proc.returncode != 0:
            raise RuntimeError(f"curl exit {proc.returncode}: {proc.stderr[:200]}")
        return proc.stdout

    return _retry(fn, retries, backoff, jitter)