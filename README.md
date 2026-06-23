# 🖥️ Domain Manager

> **Unified CLI for 20+ domain & DNS providers** — list domains, manage records, auto-update DDNS from one terminal.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](pyproject.toml)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![GitHub](https://img.shields.io/badge/GitHub-Monah--Limited%2Fdomain--manager-blue)](https://github.com/monah-studio/domain-manager)

```bash
# One-command DDNS for your Raspberry Pi
domain-manager ddns example.com --type A --name home --provider cloudflare

# Or update all configured providers at once
domain-manager ddns example.com --type A --name @ --all
```

---

## ✨ Features

- **19+ providers** in one CLI (add yours via PR!)
- **List domains** across all registrars
- **DNS management** — A, AAAA, CNAME, MX, TXT
- **Dynamic DNS (DDNS)** — auto-detect IP, update if changed
- **Bulk mode** — `--all` flag updates every configured provider
- **Cron-ready** — `--quiet` flag only outputs on change
- **JSON output** — `--json` for piping
- **Zero external dependencies** — pure Python 3 stdlib
- **Hermes Agent skill** — included in `hermes-skill/`

## Supported Providers

| # | Provider | Auth | DDNS | List | Edit |
|---|----------|------|:----:|:----:|:----:|
| 1 | **GoDaddy** | Key + Secret | ✅ | ✅ | ✅ |
| 2 | **Namecheap** | User + Key + IP | ✅ | ✅ | ⚠️ |
| 3 | **Domain.com** | User ID + Key | ✅ | ✅ | ✅ |
| 4 | **Cloudflare** | API Token | ✅ | ✅ | ✅ |
| 5 | **Porkbun** | Key + Secret | ✅ | ✅ | ✅ |
| 6 | **Gandi** | Token | ✅ | ✅ | ✅ |
| 7 | **DigitalOcean** | Token | ✅ | ✅ | ✅ |
| 8 | **Vultr** | Token | ✅ | ✅ | ✅ |
| 9 | **Hetzner DNS** | Token | ✅ | ✅ | ✅ |
| 10 | **OVH** | App Key + Consumer Key | ✅ | ✅ | ✅ |
| 11 | **DNSimple** | Token | ✅ | ✅ | ✅ |
| 12 | **NameSilo** | Key | ✅ | ✅ | ✅ |
| 13 | **Bunny.net** | Key | ✅ | ✅ | ✅ |
| 14 | **DuckDNS** | Token | ✅ | — | — |
| 15 | **No-IP** | User + Password | ✅ | — | — |
| 16 | **Dynu** | Token | ✅ | ✅ | ✅ |
| 17 | **阿里云 DNS** | AccessKey ID + Secret | ✅ | ✅ | ✅ |
| 18 | **腾讯云 DNS** | SecretId + Key | ✅ | ✅ | ✅ |

*Namecheap DNS edits require full zone re-submission.*

## 🚀 Quick Start

```bash
pip install domain-manager
```

Or clone & run:

```bash
git clone https://github.com/monah-studio/domain-manager.git
cd domain-manager
python3 -m domain_manager --help
```

## 🔧 Setup

```bash
# See all providers
domain-manager config list

# Configure one
domain-manager config cloudflare --token <CF_API_TOKEN>
domain-manager config godaddy --key <KEY> --secret <SECRET>
domain-manager config aliyun --key <AccessKeyId> --secret <AccessKeySecret>

# Verify
domain-manager status
domain-manager list --all
```

## 📖 Usage

```bash
# List domains
domain-manager list
domain-manager list --all --json

# View DNS records
domain-manager dns list example.com
domain-manager dns list example.com --json

# Update record
domain-manager dns update example.com --type A --name @ --value 1.2.3.4

# DDNS: auto-detect IP
domain-manager ddns example.com --type A --name home --provider porkbun

# DDNS: all providers at once
domain-manager ddns example.com --type A --name @ --all

# DDNS: cron mode (silent unless IP changed)
domain-manager ddns example.com --type A --name home --quiet

# Check your public IP
domain-manager ip
domain-manager ip --type AAAA
```

## 🥋 Raspberry Pi / Cron DDNS

```bash
# Every 5 minutes
*/5 * * * * domain-manager ddns home.example.com --type A --name @ --provider cloudflare --quiet

# With log
*/5 * * * * domain-manager ddns home.example.com --type A --name @ --provider godaddy --quiet >> /tmp/ddns.log 2>&1
```

## 🧩 Add a New Provider

1. Create `domain_manager/providers/<name>.py`
2. Define a `Provider` class inheriting `BaseProvider`
3. Implement: `list_domains`, `list_records`, `update_record`, `ddns`
4. Open a PR!

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## 🙏 Credits

This project communicates with these provider APIs — thank you for maintaining them:

| Provider | API Docs |
|----------|----------|
| [**GoDaddy**](https://developer.godaddy.com/doc) | Domain management REST API |
| [**Cloudflare**](https://developers.cloudflare.com/api) | DNS zone & record API |
| [**Namecheap**](https://www.namecheap.com/support/api/methods/) | XML-RPC domain & DNS API |
| [**Porkbun**](https://porkbun.com/api/json/v3/documentation) | JSON API for domains & DNS |
| [**Gandi**](https://api.gandi.net/docs) | LiveDNS REST API |
| [**DigitalOcean**](https://docs.digitalocean.com/reference/api/api-reference/) | Domains & DNS API |
| [**Vultr**](https://www.vultr.com/api/) | DNS API |
| [**Hetzner**](https://dns.hetzner.com/api-docs) | DNS API |
| [**OVH**](https://eu.api.ovh.com) | Domain & DNS API |
| [**DNSimple**](https://developer.dnsimple.com) | Domain & DNS REST API |
| [**NameSilo**](https://www.namesilo.com/api) | Domain API |
| [**Bunny.net**](https://docs.bunny.net/reference) | DNS zone API |
| [**Domain.com**](https://developer.domain.com) | Domain API |
| [**DuckDNS**](https://www.duckdns.org) | Free DDNS API |
| [**No-IP**](https://www.noip.com/integrate) | Dynamic DNS API |
| [**Dynu**](https://www.dynu.com/API) | DNS & DDNS API |
| [**阿里云 DNS**](https://help.aliyun.com/product/29697.html) | DNS API |
| [**腾讯云 DNSPod**](https://docs.dnspod.cn/api) | DNS API |

**Architecture inspiration:** [octodns](https://github.com/octodns/octodns) (multi-provider DNS sync), [acme.sh](https://github.com/acmesh-official/acme.sh) (provider plugin pattern).

**Sister projects:** [OpenBalance](https://github.com/monah-studio/OpenBalance), [SmartClipAI](https://github.com/monah-studio/SmartClipAI)

---

## 📄 License

MIT — [Monah Limited](https://monah.ai)
