"""Shared utilities: config storage, IP detection, HTTP helpers."""

import json
import os
import subprocess
import sys
import urllib.request
import urllib.error
import urllib.parse

CONFIG_DIR = os.path.expanduser("~/.config/domain-manager")
CREDS_FILE = os.path.join(CONFIG_DIR, "creds.json")


def load_creds():
    if not os.path.exists(CREDS_FILE):
        return {}
    with open(CREDS_FILE) as f:
        return json.load(f)


def save_creds(creds):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CREDS_FILE, "w") as f:
        json.dump(creds, f, indent=2)
    os.chmod(CREDS_FILE, 0o600)


def get_provider_creds(provider_name):
    return load_creds().get(provider_name, {})


def get_public_ip(version=4):
    """Detect public IPv4 or IPv6 address."""
    services_v4 = [
        "https://api.ipify.org",
        "https://ipv4.icanhazip.com",
        "https://checkip.amazonaws.com",
        "https://ifconfig.me/ip",
    ]
    services_v6 = [
        "https://api6.ipify.org",
        "https://ipv6.icanhazip.com",
        "https://ifconfig.me/ip",
    ]
    services = services_v6 if version == 6 else services_v4
    for url in services:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "domain-manager/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                ip = resp.read().decode().strip()
                if ip:
                    return ip
        except Exception:
            continue
    return None


def http_request(method, url, headers=None, data=None, timeout=15):
    """Generic HTTP request helper."""
    hdrs = {"User-Agent": "domain-manager/1.0"}
    if headers:
        hdrs.update(headers)
    body = json.dumps(data).encode() if data is not None else None
    if body and "Content-Type" not in hdrs:
        hdrs["Content-Type"] = "application/json"
    try:
        req = urllib.request.Request(url, data=body, headers=hdrs, method=method)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = resp.read().decode()
            if result and result.strip():
                try:
                    return json.loads(result)
                except json.JSONDecodeError:
                    return result
            return {}
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        return {"error": f"HTTP {e.code}: {body[:500]}"}
    except urllib.error.URLError as e:
        return {"error": f"Connection failed: {e.reason}"}
    except Exception as e:
        return {"error": str(e)}


def print_table(rows, headers, json_mode=False):
    """Print a table or JSON."""
    if json_mode:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
        return
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))
    fmt = "  ".join(f"{{:<{w+2}}}" for w in col_widths)
    print(fmt.format(*headers))
    print("  " + "  ".join("─" * w for w in col_widths))
    for row in rows:
        print(fmt.format(*[str(c) for c in row]))
