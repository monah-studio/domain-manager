"""Domain Manager CLI — entry point for all commands."""

import argparse
import sys
import os

from . import __version__
from .core import get_public_ip, save_creds, load_creds
from .providers.registry import list_providers, get_provider, list_configured
from .lang import _, set_lang, get_lang


def cmd_config(args):
    creds = load_creds()
    p = args.provider.lower()

    prov = get_provider(p)
    if not prov:
        print(_("config_unknown_provider", name=args.provider))
        return

    fields = prov.config_fields
    entry = {}
    for field_name, prompt, is_secret in fields:
        val = getattr(args, field_name.replace("-", "_"), None)
        if not val:
            print(_("config_missing_field", field=field_name, prompt=prompt))
            return
        entry[field_name] = val

    creds[p] = entry
    save_creds(creds)
    print(_("config_creds_saved", provider=prov.label))


def cmd_status(args):
    providers = list_providers()
    print(_("config_title"))
    for name, prov in sorted(providers.items()):
        if prov.configured:
            print("  " + _("config_configured", provider=prov.label, name=name))
        else:
            print("  " + _("config_not_configured", provider=prov.label, name=name))


def cmd_list(args):
    if args.all:
        providers = list_providers()
    elif args.provider:
        p = get_provider(args.provider)
        providers = {args.provider: p} if p else {}
    else:
        providers = list_configured()

    for name, prov in sorted(providers.items()):
        if not prov.configured:
            continue
        if not args.json:
            title = _("list_title", provider=prov.label)
            print(title)
        prov.list_domains(json_mode=args.json)


def cmd_dns(args):
    if args.all or not args.provider:
        providers = list_configured()
    else:
        p = get_provider(args.provider)
        providers = {args.provider: p} if p else {}

    for name, prov in sorted(providers.items()):
        if not prov.configured:
            continue
        if args.action == "list":
            if not args.json:
                print(_("dns_title", provider=prov.label, domain=args.domain))
            prov.list_records(args.domain, json_mode=args.json)
        elif args.action == "update":
            if not all([args.domain, args.type, args.name, args.value]):
                print(_("dns_update_usage"))
                return
            prov.update_record(args.domain, args.type.upper(), args.name, args.value, args.ttl)


def cmd_ddns(args):
    if args.all or not args.provider:
        providers = list_configured()
    else:
        p = get_provider(args.provider)
        providers = {args.provider: p} if p else {}

    updated_any = False
    for name, prov in sorted(providers.items()):
        if prov.configured:
            if prov.ddns(args.domain, args.type, args.name, args.ttl, quiet=args.quiet):
                updated_any = True

    if args.quiet and not updated_any:
        sys.exit(0)


def cmd_public_ip(args):
    ip = get_public_ip(4 if args.type == "A" else 6)
    if ip:
        print(ip)
    else:
        print(_("ip_could_not_detect", version=4 if args.type == "A" else 6))
        sys.exit(1)


def build_parser():
    parser = argparse.ArgumentParser(
        description="Domain Manager — control 20+ domain/DNS providers from one CLI",
        epilog="Open source: https://github.com/monah-studio/domain-manager",
    )
    parser.add_argument("--version", action="version", version=f"domain-manager {__version__}")
    parser.add_argument("--lang", choices=["en", "zh"], default=None,
                        help="Language: en (English) / zh (中文)  [env: DOMAIN_MANAGER_LANG]")

    sub = parser.add_subparsers(dest="command")

    # ── config ──
    cfg = sub.add_parser("config", help="Set API credentials for a provider")
    cfg.add_argument("provider", metavar="PROVIDER", help="Provider name")
    cfg.add_argument("--key", help="API key or token")
    cfg.add_argument("--secret", help="API secret")
    cfg.add_argument("--id", help="User / App / Account ID")
    cfg.add_argument("--user", help="Username")
    cfg.add_argument("--ip", help="Client IP (Namecheap)")
    cfg.add_argument("--email", help="Account email (Cloudflare Global Key)")
    cfg.add_argument("--token", help="API token")

    # ── status ──
    sub.add_parser("status", help="Show configured providers")

    # ── list ──
    li = sub.add_parser("list", help="List domains from one or all providers")
    li.add_argument("--provider", "-p", help="Provider name (omit for all configured)")
    li.add_argument("--all", "-a", action="store_true", help="All providers (including unconfigured)")
    li.add_argument("--json", action="store_true", help="JSON output")

    # ── dns ──
    dns = sub.add_parser("dns", help="Manage DNS records")
    dns.add_argument("action", choices=["list", "update"])
    dns.add_argument("domain", nargs="?", help="Domain name")
    dns.add_argument("--provider", "-p", help="Provider name (omit for all configured)")
    dns.add_argument("--all", "-a", action="store_true", help="All configured providers")
    dns.add_argument("--type", "-t", default="A", help="Record type (A, AAAA, CNAME, MX, TXT)")
    dns.add_argument("--name", "-n", default="@", help="Record name (@ for root)")
    dns.add_argument("--value", "-v", help="Record value")
    dns.add_argument("--ttl", type=int, default=600, help="TTL in seconds")
    dns.add_argument("--json", action="store_true", help="JSON output")

    # ── ddns ──
    dd = sub.add_parser("ddns", help="Dynamic DNS — update record with your public IP")
    dd.add_argument("domain", help="Domain name")
    dd.add_argument("--provider", "-p", help="Provider name (omit for all configured)")
    dd.add_argument("--all", "-a", action="store_true", help="All configured providers")
    dd.add_argument("--type", "-t", default="A", choices=["A", "AAAA"], help="Record type")
    dd.add_argument("--name", "-n", default="@", help="Record name")
    dd.add_argument("--ttl", type=int, default=600, help="TTL in seconds")
    dd.add_argument("--quiet", "-q", action="store_true", help="Silent unless IP changed (for cron)")

    # ── ip ──
    ip_cmd = sub.add_parser("ip", help="Show your public IP address")
    ip_cmd.add_argument("--type", "-t", default="A", choices=["A", "AAAA"], help="IP version")

    return parser


PROVIDER_HELP = """Available providers:
  godaddy          GoDaddy (API Key + Secret)
  namecheap        Namecheap (Username + API Key + Client IP)
  domaincom        Domain.com (User ID + API Key)
  cloudflare       Cloudflare (API Token)
  porkbun          Porkbun (API Key + Secret)
  gandi            Gandi (Personal Access Token)
  digitalocean     DigitalOcean (Personal Access Token)
  vultr            Vultr (Personal Access Token)
  hetzner          Hetzner DNS (API Token)
  ovh              OVH (App Key + App Secret + Consumer Key)
  dnsimple         DNSimple (API Token)
  namesilo         NameSilo (API Key)
  bunny            Bunny.net (API Key)
  duckdns          DuckDNS (Token) — free DDNS only
  noip             No-IP (Username + Password) — DDNS only
  dynu             Dynu (API Token)
  aliyun           阿里云 DNS (AccessKey ID + AccessKey Secret)
  tencentcloud     腾讯云 DNS (SecretId + SecretKey)"""

def main():
    """Entry point for pip-installed console_script."""
    parser = build_parser()
    # Parse known args first to extract --lang, then parse fully
    args, remaining = parser.parse_known_args()
    if args.lang:
        set_lang(args.lang)
    # Re-parse with remaining args only (--lang already consumed)
    if remaining:
        args = parser.parse_args(remaining)
    else:
        args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
        print(PROVIDER_HELP)
        return

    # Auto-print provider list for config command
    if args.command == "config" and args.provider == "list":
        print(PROVIDER_HELP)
        return
    if args.command == "config" and not get_provider(args.provider):
        print(f"Unknown provider: {args.provider}")
        print(PROVIDER_HELP)
        return

    commands = {
        "config": cmd_config,
        "status": cmd_status,
        "list": cmd_list,
        "dns": cmd_dns,
        "ddns": cmd_ddns,
        "ip": cmd_public_ip,
    }

    handler = commands.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
