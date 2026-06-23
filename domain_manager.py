#!/usr/bin/env python3
"""
Domain Manager — Unified CLI for GoDaddy, Namecheap & Domain.com APIs

Usage:
  # Set up credentials (first time)
  domain-manager config godaddy --key <KEY> --secret <SECRET>
  domain-manager config namecheap --user <USER> --key <KEY> --ip <CLIENT_IP>
  domain-manager config domaincom --id <ID> --key <KEY>

  # List domains
  domain-manager list [--provider godaddy] [--json]

  # View DNS records
  domain-manager dns list example.com [--json]

  # Update a DNS record (DDNS)
  domain-manager dns update example.com --type A --name @ --value 1.2.3.4
  domain-manager dns update example.com --type AAAA --name @ --value ::1

  # DDNS: auto-detect your public IP and update a record
  domain-manager ddns example.com --type A --name home
  domain-manager ddns example.com --type AAAA --name home

  # Watch mode (for cron jobs — silent unless IP changed)
  domain-manager ddns example.com --type A --name home --quiet

  # List all domains across all providers
  domain-manager list --all

Environment:
  Credentials stored in ~/.hermes/scripts/domain_manager/creds.json
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error
import urllib.parse
import xml.etree.ElementTree as ET
import hashlib
import hmac
import base64

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CREDS_FILE = os.path.join(SCRIPT_DIR, "domain_manager", "creds.json")


# ── Utilities ────────────────────────────────────────────────────────────

def _load_creds():
    if not os.path.exists(CREDS_FILE):
        return {}
    with open(CREDS_FILE) as f:
        return json.load(f)


def _save_creds(creds):
    os.makedirs(os.path.dirname(CREDS_FILE), exist_ok=True)
    with open(CREDS_FILE, "w") as f:
        json.dump(creds, f, indent=2)
    os.chmod(CREDS_FILE, 0o600)


def _get_public_ip(version=4):
    """Detect public IPv4 or IPv6 address."""
    if version == 4:
        services = [
            "https://api.ipify.org",
            "https://ipv4.icanhazip.com",
            "https://checkip.amazonaws.com",
        ]
    else:
        services = [
            "https://api6.ipify.org",
            "https://ipv6.icanhazip.com",
        ]
    for url in services:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "curl/8.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.read().decode().strip()
        except Exception:
            continue
    return None


def _json_out(data, json_mode):
    if json_mode:
        print(json.dumps(data, indent=2))
    else:
        return data  # caller handles


# ── GoDaddy API ──────────────────────────────────────────────────────────

GODADDY_API = "https://api.godaddy.com"


def _godaddy_headers(creds):
    return {
        "Authorization": f"sso-key {creds['key']}:{creds['secret']}",
        "Content-Type": "application/json",
    }


def _godaddy_request(method, path, data=None, params=None):
    creds = _load_creds().get("godaddy", {})
    if not creds.get("key") or not creds.get("secret"):
        return {"error": "GoDaddy credentials not configured. Run: domain-manager config godaddy --key <KEY> --secret <SECRET>"}

    url = f"{GODADDY_API}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)

    headers = _godaddy_headers(creds)
    body = json.dumps(data).encode() if data else None

    try:
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = resp.read().decode()
            if result:
                return json.loads(result)
            return []
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        return {"error": f"GoDaddy HTTP {e.code}: {body}"}
    except Exception as e:
        return {"error": f"GoDaddy error: {e}"}


def godaddy_list_domains(json_mode=False):
    data = _godaddy_request("GET", "/v1/domains")
    if isinstance(data, dict) and "error" in data:
        print(f"Error: {data['error']}")
        return

    if json_mode:
        print(json.dumps(data, indent=2))
        return

    print(f"{'Domain':<30} {'Status':<12} {'Expires':<15} {'AutoRenew':<10}")
    print("-" * 70)
    for d in data:
        print(f"{d.get('domain',''):<30} {d.get('status',''):<12} "
              f"{d.get('expires',''):<15} {str(d.get('renewAuto',False)):<10}")


def godaddy_list_records(domain, json_mode=False):
    data = _godaddy_request("GET", f"/v1/domains/{domain}/records")
    if isinstance(data, dict) and "error" in data:
        print(f"Error: {data['error']}")
        return

    if json_mode:
        print(json.dumps(data, indent=2))
        return

    print(f"{'Type':<8} {'Name':<30} {'Value':<50} {'TTL':<8}")
    print("-" * 100)
    for r in data:
        print(f"{r.get('type',''):<8} {r.get('name',''):<30} "
              f"{r.get('data',''):<50} {r.get('ttl',3600):<8}")


def godaddy_update_record(domain, record_type, name, value, ttl=600):
    data = [{"type": record_type, "name": name, "data": value, "ttl": ttl}]
    result = _godaddy_request(
        "PUT", f"/v1/domains/{domain}/records/{record_type}/{name}", data=data
    )
    if isinstance(result, dict) and "error" in result:
        print(f"Error: {result['error']}")
        return False
    print(f"✅ {record_type} {name}.{domain} → {value}")
    return True


# ── Namecheap API ────────────────────────────────────────────────────────

NAMECHEAP_API = "https://api.namecheap.com/xml.response"


def _namecheap_sign(creds, params):
    """Namecheap uses MD5 signature."""
    param_str = "".join(f"{k}{v}" for k, v in sorted(params.items()))
    sig_str = f"{creds['key']}{param_str}"
    return hashlib.md5(sig_str.encode()).hexdigest()


def _namecheap_request(command, payload=None, json_mode=False):
    creds = _load_creds().get("namecheap", {})
    if not all(creds.get(k) for k in ["user", "key", "ip"]):
        return {"error": "Namecheap credentials not configured"}

    params = {
        "ApiUser": creds["user"],
        "ApiKey": creds["key"],
        "UserName": creds["user"],
        "ClientIp": creds["ip"],
        "Command": command,
    }
    if payload:
        params.update(payload)

    url = f"{NAMECHEAP_API}?{urllib.parse.urlencode(params)}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "domain-manager/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            xml_data = resp.read().decode()
            return xml_data
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        return {"error": f"Namecheap HTTP {e.code}: {body[:500]}"}
    except Exception as e:
        return {"error": f"Namecheap error: {e}"}


def namecheap_list_domains(json_mode=False):
    xml = _namecheap_request("namecheap.domains.getList")
    if isinstance(xml, dict) and "error" in xml:
        print(f"Error: {xml['error']}")
        return

    try:
        root = ET.fromstring(xml)
        ns = {"nc": "http://api.namecheap.com/xml.response"}
        domains = []
        for d in root.findall(".//nc:Domain", ns):
            domains.append({
                "name": d.get("Name"),
                "status": d.get("Status"),
                "expires": d.get("Expires"),
                "auto_renew": d.get("AutoRenew"),
            })

        if json_mode:
            print(json.dumps(domains, indent=2))
            return

        print(f"{'Domain':<30} {'Status':<12} {'Expires':<15} {'AutoRenew':<10}")
        print("-" * 70)
        for d in domains:
            print(f"{d['name']:<30} {d['status']:<12} {d['expires']:<15} {d['auto_renew']:<10}")

    except ET.ParseError as e:
        print(f"Error parsing Namecheap response: {e}")
        print(f"Raw: {xml[:500]}")


def namecheap_list_records(domain, json_mode=False):
    xml = _namecheap_request("namecheap.domains.dns.getHosts", {"SLD": domain.split(".")[0], "TLD": ".".join(domain.split(".")[1:])})
    if isinstance(xml, dict) and "error" in xml:
        print(f"Error: {xml['error']}")
        return

    try:
        root = ET.fromstring(xml)
        ns = {"nc": "http://api.namecheap.com/xml.response"}
        hosts = root.findall(".//nc:host", ns)

        if json_mode:
            records = []
            for h in hosts:
                records.append({
                    "type": h.get("Type"),
                    "name": h.get("Name"),
                    "value": h.get("Address"),
                    "ttl": h.get("TTL"),
                })
            print(json.dumps(records, indent=2))
            return

        print(f"{'Type':<8} {'Name':<30} {'Value':<50} {'TTL':<8}")
        print("-" * 100)
        for h in hosts:
            print(f"{h.get('Type',''):<8} {h.get('Name',''):<30} "
                  f"{h.get('Address',''):<50} {h.get('TTL',1800):<8}")

    except ET.ParseError as e:
        print(f"Error parsing Namecheap response: {e}")
        print(f"Raw: {xml[:500]}")


# ── Domain.com API ───────────────────────────────────────────────────────

DOMAINCOM_API = "https://api.domain.com/v1"


def _domaincom_headers(creds):
    return {
        "X-Auth-User": creds["id"],
        "X-Auth-Key": creds["key"],
        "Content-Type": "application/json",
    }


def _domaincom_request(method, path, data=None):
    creds = _load_creds().get("domaincom", {})
    if not creds.get("id") or not creds.get("key"):
        return {"error": "Domain.com credentials not configured"}

    url = f"{DOMAINCOM_API}{path}"
    headers = _domaincom_headers(creds)
    body = json.dumps(data).encode() if data else None

    try:
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = resp.read().decode()
            if result:
                return json.loads(result)
            return {}
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        return {"error": f"Domain.com HTTP {e.code}: {body}"}
    except Exception as e:
        return {"error": f"Domain.com error: {e}"}


def domaincom_list_domains(json_mode=False):
    data = _domaincom_request("GET", "/domains")
    if isinstance(data, dict) and "error" in data:
        print(f"Error: {data['error']}")
        return

    domains = data if isinstance(data, list) else data.get("domains", [])

    if json_mode:
        print(json.dumps(domains, indent=2))
        return

    print(f"{'Domain':<30} {'Expires':<15}")
    print("-" * 50)
    for d in domains:
        name = d.get("domain", d.get("domainName", ""))
        exp = d.get("expires", d.get("expirationDate", ""))
        print(f"{name:<30} {exp:<15}")


def domaincom_list_records(domain, json_mode=False):
    data = _domaincom_request("GET", f"/domains/{domain}/records")
    if isinstance(data, dict) and "error" in data:
        print(f"Error: {data['error']}")
        return

    records = data if isinstance(data, list) else data.get("records", [])

    if json_mode:
        print(json.dumps(records, indent=2))
        return

    print(f"{'Type':<8} {'Name':<30} {'Value':<50}")
    print("-" * 100)
    for r in records:
        print(f"{r.get('type',''):<8} {r.get('name',''):<30} {r.get('value',''):<50}")


# ── Unified DDNS ─────────────────────────────────────────────────────────

def ddns_update(provider, domain, record_type, name, quiet=False, ttl=600):
    """Check public IP and update DNS if changed. Returns True if updated."""
    if record_type.upper() == "AAAA":
        ip = _get_public_ip(version=6)
    else:
        ip = _get_public_ip(version=4)

    if not ip:
        print("Error: Could not detect public IP")
        return False

    # Get current records
    current_value = None
    if provider == "godaddy":
        records = _godaddy_request("GET", f"/v1/domains/{domain}/records/{record_type}/{name}")
        if isinstance(records, list) and len(records) > 0:
            current_value = records[0].get("data")
    elif provider == "namecheap":
        sld = domain.split(".")[0]
        tld = ".".join(domain.split(".")[1:])
        xml = _namecheap_request("namecheap.domains.dns.getHosts", {"SLD": sld, "TLD": tld})
        if isinstance(xml, str):
            try:
                root = ET.fromstring(xml)
                ns = {"nc": "http://api.namecheap.com/xml.response"}
                for h in root.findall(".//nc:host", ns):
                    h_name = h.get("Name")
                    h_type = h.get("Type")
                    if h_name == name and h_type == record_type:
                        current_value = h.get("Address")
                        break
            except ET.ParseError:
                pass

    if current_value == ip:
        if not quiet:
            print(f"✓ {record_type} {name}.{domain} already {ip} — no update needed")
        return False

    # Update
    if provider == "godaddy":
        return godaddy_update_record(domain, record_type, name, ip, ttl)
    elif provider == "namecheap":
        print(f"Namecheap DDNS: {record_type} {name}.{domain} → {ip}")
        print("(Namecheap DDNS requires setHosts with full zone — see docs)")
        return False
    elif provider == "domaincom":
        print(f"Domain.com DDNS: {record_type} {name}.{domain} → {ip}")
        result = _domaincom_request(
            "PATCH", f"/domains/{domain}/records",
            data={"name": name, "type": record_type, "value": ip}
        )
        if isinstance(result, dict) and "error" in result:
            print(f"Error: {result['error']}")
            return False
        print(f"✅ {record_type} {name}.{domain} → {ip}")
        return True

    return False


# ── Config ───────────────────────────────────────────────────────────────

def cmd_config(args):
    creds = _load_creds()
    provider = args.provider.lower()

    if provider == "godaddy":
        if not args.key or not args.secret:
            print("Usage: domain-manager config godaddy --key <KEY> --secret <SECRET>")
            return
        creds["godaddy"] = {"key": args.key, "secret": args.secret}
        _save_creds(creds)
        print("✅ GoDaddy credentials saved")

    elif provider == "namecheap":
        if not args.user or not args.key or not args.ip:
            print("Usage: domain-manager config namecheap --user <USER> --key <KEY> --ip <CLIENT_IP>")
            return
        creds["namecheap"] = {"user": args.user, "key": args.key, "ip": args.ip}
        _save_creds(creds)
        print("✅ Namecheap credentials saved")

    elif provider == "domaincom":
        if not args.id or not args.key:
            print("Usage: domain-manager config domaincom --id <USER_ID> --key <API_KEY>")
            return
        creds["domaincom"] = {"id": args.id, "key": args.key}
        _save_creds(creds)
        print("✅ Domain.com credentials saved")

    else:
        print(f"Unknown provider: {provider}. Supported: godaddy, namecheap, domaincom")


def cmd_status(args):
    """Show configured providers."""
    creds = _load_creds()
    print("Configured providers:")
    for p in ["godaddy", "namecheap", "domaincom"]:
        if p in creds:
            keys = list(creds[p].keys())
            masked = {k: v[:4] + "****" for k, v in creds[p].items()}
            print(f"  ✅ {p}: {masked}")
        else:
            print(f"  ❌ {p}: not configured")


def cmd_list(args):
    """List domains from one or all providers."""
    providers = []
    if args.all:
        providers = ["godaddy", "namecheap", "domaincom"]
    elif args.provider:
        providers = [args.provider]
    else:
        providers = ["godaddy"]

    for p in providers:
        print(f"\n=== {p.upper()} ===" if not args.json else "")
        if p == "godaddy":
            godaddy_list_domains(json_mode=args.json)
        elif p == "namecheap":
            namecheap_list_domains(json_mode=args.json)
        elif p == "domaincom":
            domaincom_list_domains(json_mode=args.json)


def cmd_dns(args):
    """Manage DNS records."""
    if args.action == "list":
        providers = []

        if args.provider:
            providers = [args.provider]
        else:
            # Try all
            creds = _load_creds()
            for p in ["godaddy", "namecheap", "domaincom"]:
                if p in creds:
                    providers.append(p)

        for p in providers:
            print(f"\n=== {p.upper()} — {args.domain} ===" if not args.json else "")
            if p == "godaddy":
                godaddy_list_records(args.domain, json_mode=args.json)
            elif p == "namecheap":
                namecheap_list_records(args.domain, json_mode=args.json)
            elif p == "domaincom":
                domaincom_list_records(args.domain, json_mode=args.json)

    elif args.action == "update":
        provider = args.provider or "godaddy"
        if not all([args.domain, args.type, args.name, args.value]):
            print("Usage: domain-manager dns update <domain> --type A --name @ --value <IP>")
            return

        if provider == "godaddy":
            godaddy_update_record(args.domain, args.type.upper(), args.name, args.value, args.ttl)
        elif provider == "namecheap":
            print("Namecheap DNS updates require full zone re-submission — see docs")
        elif provider == "domaincom":
            result = _domaincom_request(
                "PATCH", f"/domains/{args.domain}/records",
                data={"name": args.name, "type": args.type.upper(), "value": args.value}
            )
            if isinstance(result, dict) and "error" in result:
                print(f"Error: {result['error']}")
            else:
                print(f"✅ {args.type} {args.name}.{args.domain} → {args.value}")


def cmd_ddns(args):
    """Dynamic DNS: update record with current public IP."""
    provider = args.provider or "godaddy"
    updated = ddns_update(provider, args.domain, args.type, args.name,
                          quiet=args.quiet, ttl=args.ttl)
    if args.quiet:
        # Silent mode for cron — only output if changed
        if not updated:
            sys.exit(0)
    return updated


# ── Main CLI ─────────────────────────────────────────────────────────────

def build_parser():
    """Build argument parser. Exposed for reuse."""
    parser = argparse.ArgumentParser(description="Domain Manager — control GoDaddy, Namecheap, Domain.com")
    sub = parser.add_subparsers(dest="command")

    cfg = sub.add_parser("config", help="Set API credentials")
    cfg.add_argument("provider", choices=["godaddy", "namecheap", "domaincom"])
    cfg.add_argument("--key", help="API key")
    cfg.add_argument("--secret", help="API secret (GoDaddy)")
    cfg.add_argument("--user", help="Username (Namecheap)")
    cfg.add_argument("--ip", help="Client IP (Namecheap)")
    cfg.add_argument("--id", help="User ID (Domain.com)")

    sub.add_parser("status", help="Show configured providers")

    li = sub.add_parser("list", help="List domains")
    li.add_argument("--provider", choices=["godaddy", "namecheap", "domaincom"])
    li.add_argument("--all", action="store_true", help="All configured providers")
    li.add_argument("--json", action="store_true", help="JSON output")

    dns = sub.add_parser("dns", help="Manage DNS records")
    dns.add_argument("action", choices=["list", "update"])
    dns.add_argument("domain", nargs="?", help="Domain name")
    dns.add_argument("--provider", choices=["godaddy", "namecheap", "domaincom"])
    dns.add_argument("--type", default="A", help="Record type (A, AAAA, CNAME, MX, TXT)")
    dns.add_argument("--name", default="@", help="Record name (@ for root)")
    dns.add_argument("--value", help="Record value (IP, hostname)")
    dns.add_argument("--ttl", type=int, default=600, help="TTL in seconds")

    dd = sub.add_parser("ddns", help="Dynamic DNS — auto-update with your public IP")
    dd.add_argument("domain", help="Domain name")
    dd.add_argument("--provider", choices=["godaddy", "namecheap", "domaincom"])
    dd.add_argument("--type", default="A", choices=["A", "AAAA"], help="Record type")
    dd.add_argument("--name", default="@", help="Record name")
    dd.add_argument("--ttl", type=int, default=600, help="TTL in seconds")
    dd.add_argument("--quiet", action="store_true", help="Silent unless IP changed (for cron)")

    return parser


def main():
    """Entry point for pip-installed console_script."""
    parser = build_parser()
    args = parser.parse_args()
    _route(args, parser)


def _route(args, parser):
    """Route parsed args to command handlers."""
    if args.command == "config":
        cmd_config(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "dns":
        cmd_dns(args)
    elif args.command == "ddns":
        cmd_ddns(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
