---
name: domain-manager
description: |
  Use when managing domains/DNS across GoDaddy, Namecheap, Domain.com, or any
  registrar with an API. Lists domains, reads/updates DNS records,
  auto-updates DDNS (Dynamic DNS), or sets up cron-based DDNS. Ideal for
  Raspberry Pi / self-hosted setups needing persistent domain access.
version: 1.0.0
author: Monah Limited
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [domains, dns, ddns, godaddy, namecheap, domaincom, networking, raspberry-pi]
    related_skills: [cronjob]
---

# Domain Manager — Registrar API + DDNS

## Overview

Open-source repo: **https://github.com/monah-studio/domain-manager**
MIT licensed — contributions welcome via PR or issue.

A Python CLI tool at `~/.hermes/scripts/domain_manager.py` (symlinked as
`domain-manager`) that talks to three major domain registrars:

| Registrar | Auth | API Docs |
|-----------|------|----------|
| **GoDaddy** | API Key + Secret (OAuth) | `https://developer.godaddy.com/doc` |
| **Namecheap** | Username + API Key + Client IP | `https://www.namecheap.com/support/api/methods/` |
| **Domain.com** | User ID + API Key | `https://developer.domain.com/docs` |

## When to Use

- User says "set up DDNS for my domain" or "update my DNS record"
- User asks to list, check, or manage domains across registrars
- User needs automatic DDNS for a Raspberry Pi / home server
- User wants to integrate external API services (Tesla, Home Assistant,
  etc.) via domain management

## Setup (one-time)

### 1. Get API credentials from your registrar

**GoDaddy:**
1. Go to https://developer.godaddy.com/keys
2. Create a Production Key (not Test)
3. Save the **Key** and **Secret**

**Namecheap:**
1. Go to https://ap.www.namecheap.com/settings/api/
2. Enable API + whitelist your public IP
3. Save the **API Key** (username is your Namecheap login)

**Domain.com:**
1. Go to https://www.domain.com/account/manage-api
2. Enable API access
3. Save your **User ID** and **API Key**

### 2. Configure credentials

```bash
domain-manager config godaddy --key <KEY> --secret <SECRET>
domain-manager config namecheap --user <USER> --key <KEY> --ip <YOUR_PUBLIC_IP>
domain-manager config domaincom --id <USER_ID> --key <API_KEY>
```

Credentials are stored at `~/.hermes/scripts/domain_manager/creds.json`
(file permissions: 600).

### 3. Verify

```bash
domain-manager status
domain-manager list --all
```

## Commands

### List Domains

```bash
# All configured providers
domain-manager list --all

# Specific provider
domain-manager list --provider godaddy

# JSON output (for programmatic use)
domain-manager list --all --json
```

### View DNS Records

```bash
domain-manager dns list example.com
domain-manager dns list example.com --provider namecheap
domain-manager dns list example.com --json
```

### Update a DNS Record

```bash
domain-manager dns update example.com --type A --name @ --value 1.2.3.4
domain-manager dns update example.com --type AAAA --name home --value 2001:db8::1
domain-manager dns update example.com --type CNAME --name www --value example.com
```

### Dynamic DNS (DDNS) — Auto-detect public IP

```bash
# Update once
domain-manager ddns example.com --type A --name home

# AAAA (IPv6)
domain-manager ddns example.com --type AAAA --name home

# Quiet mode — only outputs if IP actually changed (for cron)
domain-manager ddns example.com --type A --name home --quiet
```

## Setting Up Automatic DDNS with Cron

### Raspberry Pi / Linux (cron)

```bash
# Edit crontab
crontab -e

# Add one of these:
*/5 * * * * /home/pi/.local/bin/domain-manager ddns example.com --type A --name home --quiet --ttl 300
@hourly /home/pi/.local/bin/domain-manager ddns example.com --type AAAA --name home --quiet
```

### Using Hermes Agent Cron Jobs

The agent can schedule this directly:

```bash
# In Hermes, say: "set up DDNS for home.example.com every 5 minutes"
# The agent will create a cron job like:
hermes cron schedule "*/5 * * * *" domain-manager ddns example.com --type A --name home --quiet
```

Or using the cronjob tool:

```json
{
  "prompt": "Run domain-manager ddns for home.example.com A record",
  "schedule": "*/5 * * * *",
  "script": "~/.hermes/scripts/domain_manager.py",
  "no_agent": true
}
```

### macOS (launchd)

```bash
# Create a plist or just use cron via:
brew install cronie
crontab -e
```

## Hermes Agent Integration

When the user asks the agent to manage domains, the agent should:

1. **Check credentials first:**
   ```bash
   domain-manager status
   ```

2. **If not configured**, guide the user through the Setup steps above
   (step-by-step, one registrar at a time).

3. **For DDNS setup**, offer to schedule a cron job using `cronjob`
   action='create' with `no_agent=True` so it runs the script directly
   without consuming LLM tokens on every tick.

4. **For Tesla API or other API-based apps**, the domain-manager can be
   used to set up DNS entries that point to those services.

## Common Pitfalls

1. **GoDaddy Test vs Production keys.** GoDaddy provides both Test and
   Production key types. Production keys are needed for real domains.
   Test keys only work with `.test` domains in the sandbox.

2. **Namecheap requires whitelisted IP.** Set the `--ip` to the public IP
   of the machine that will run the script. For a Raspberry Pi behind a
   dynamic IP, you may need to update this periodically or use a broader
   whitelist.

3. **Namecheap DNS updates require full zone re-submission.** The
   `namecheap.domains.dns.setHosts` command requires sending ALL host
   records for the domain, not just the changed one. The current script
   supports reading records; full zone updates need the complete record
   set.

4. **Domain.com API rate limits.** Approximately 60 requests/hour.
   DDNS checks every 5 minutes (12 req/h) are well within limits.

5. **The `--quiet` flag is for cron.** It suppresses output when no update
   is needed. When the IP changes, it prints the update message. Exit
   code 0 means "no change," 0+output means "updated."

6. **IPv6 detection may fail on some networks.** If `--type AAAA` returns
   an error, the network likely doesn't have IPv6 connectivity. Use
   `--type A` (IPv4) instead.

## Verification Checklist

- [ ] `domain-manager status` shows at least one configured provider
- [ ] `domain-manager list --all` returns domains
- [ ] `domain-manager dns list example.com` shows records
- [ ] `domain-manager ddns example.com --type A --name @` updates successfully
- [ ] Cron job runs without error (check `/tmp/domain-manager-cron.log`)
