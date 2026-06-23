# 🖥️ Domain Manager

> **Unified CLI for GoDaddy, Namecheap & Domain.com** — list domains, manage DNS records, and auto-update DDNS from your terminal.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](pyproject.toml)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

```bash
# One-command DDNS for your Raspberry Pi
domain-manager ddns example.com --type A --name home
```

---

## ✨ Features

- **3 registrars, 1 CLI** — GoDaddy, Namecheap, Domain.com in one tool
- **List domains** — see all your domains across providers
- **DNS management** — view and update A, AAAA, CNAME, MX, TXT records
- **Dynamic DNS (DDNS)** — auto-detect your public IP and update DNS
- **Cron-ready** — `--quiet` flag only outputs when IP changes
- **JSON output** — pipe to other tools (`--json`)
- **No dependencies** — pure Python 3, stdlib only
- **Hermes Agent ready** — works as a cron job via [Hermes Agent](https://hermes-agent.nousresearch.com)

---

## 🚀 Quick Start

### Install

```bash
pip install domain-manager
```

Or from source:

```bash
git clone https://github.com/Monah-Limited/domain-manager.git
cd domain-manager
python3 domain_manager.py --help
```

### Get API Credentials

| Provider | Where to get it |
|----------|----------------|
| **GoDaddy** | https://developer.godaddy.com/keys → Create Production Key |
| **Namecheap** | https://ap.www.namecheap.com/settings/api/ → Enable API + whitelist IP |
| **Domain.com** | https://www.domain.com/account/manage-api → Enable API |

### Configure

```bash
domain-manager config godaddy --key <KEY> --secret <SECRET>
domain-manager config namecheap --user <USER> --key <KEY> --ip <YOUR_IP>
domain-manager config domaincom --id <USER_ID> --key <API_KEY>
```

Credentials are stored at `~/.config/domain-manager/creds.json` (permissions 600).

### Verify

```bash
domain-manager status
domain-manager list --all
```

---

## 📖 Usage

### List Domains

```bash
# All configured providers
domain-manager list --all

# Specific provider
domain-manager list --provider godaddy

# JSON output
domain-manager list --all --json
```

### View DNS Records

```bash
domain-manager dns list example.com
domain-manager dns list example.com --json
```

### Update DNS Records

```bash
# A record (IPv4)
domain-manager dns update example.com --type A --name @ --value 1.2.3.4

# AAAA record (IPv6)
domain-manager dns update example.com --type AAAA --name home --value 2001:db8::1

# CNAME
domain-manager dns update example.com --type CNAME --name www --value example.com
```

### Dynamic DNS (DDNS)

Auto-detect your public IP and update a DNS record:

```bash
# IPv4
domain-manager ddns example.com --type A --name home

# IPv6
domain-manager ddns example.com --type AAAA --name home

# Cron mode — silent unless IP changed
domain-manager ddns example.com --type A --name home --quiet
```

---

## 🥧 Raspberry Pi / Self-Hosted DDNS

The most common use case: your home server's IP keeps changing, and you need your domain to always point to it.

### With cron (Linux)

```bash
# Edit crontab
crontab -e

# Update every 5 minutes
*/5 * * * * domain-manager ddns myhome.duckdns.org --type A --name @ --quiet
```

### With launchd (macOS)

```xml
<!-- ~/Library/LaunchAgents/com.monah.ddns.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.monah.ddns</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/domain-manager</string>
        <string>ddns</string>
        <string>example.com</string>
        <string>--type</string>
        <string>A</string>
        <string>--name</string>
        <string>@</string>
        <string>--quiet</string>
    </array>
    <key>StartInterval</key>
    <integer>300</integer>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
```

### With Hermes Agent

```bash
hermes cron create --schedule "*/5 * * * *" \
  --script domain-manager \
  --args "ddns example.com --type A --name @ --quiet"
```

---

## 🔌 API Integration Examples

### Tesla API — check car battery from your desk

```bash
# Combined with curl to Tesla Fleet API
TOKEN=$(cat ~/.tesla/token)
BATTERY=$(curl -s -H "Authorization: Bearer $TOKEN" \
  "https://fleet-api.prd.na.vn.cloud.tesla.com/api/1/vehicles/$(cat ~/.tesla/vehicle_id)/data" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['response']['battery_level'])")

echo "🔋 Tesla battery: $BATTERY%"
```

### Home Assistant — auto-update DNS when server IP changes

```bash
# In Home Assistant automation, run:
domain-manager ddns home.example.com --type A --name @ --quiet
```

---

## 🤝 Contributing

All contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

- 🐛 Found a bug? [Open an issue](https://github.com/Monah-Limited/domain-manager/issues/new?template=bug_report.md)
- 💡 Have an idea? [Open a feature request](https://github.com/Monah-Limited/domain-manager/issues/new?template=feature_request.md)
- 🔧 Want to add a new registrar? PRs welcome!

### Roadmap

- [ ] Cloudflare DNS support
- [ ] AWS Route53 support
- [ ] Porkbun support
- [ ] Python SDK (import domain_manager)
- [ ] Docker image

---

## 📄 License

MIT — see [LICENSE](LICENSE).

Built by [Monah Limited](https://monah.ai) · Hong Kong
