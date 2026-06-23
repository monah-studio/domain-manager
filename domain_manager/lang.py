"""Multi-language support for Domain Manager.

Usage:
    from .lang import _, set_lang
    set_lang('zh')  # or 'en'
    print(_('domain_list_title'))  # auto-picks right language
"""

import os
import sys

# ── Current language ────────────────────────────────────────────────────

_current_lang = os.environ.get("DOMAIN_MANAGER_LANG", "en")

def set_lang(code):
    global _current_lang
    if code in ("en", "zh"):
        _current_lang = code
    else:
        print(f"Warning: unsupported language '{code}', falling back to en")
        _current_lang = "en"

def get_lang():
    return _current_lang

# ── Translation table ───────────────────────────────────────────────────

_STRINGS = {
    # config
    "config_creds_saved": {
        "en": "✅ {provider} credentials saved",
        "zh": "✅ {provider} 凭据已保存",
    },
    "config_not_configured": {
        "en": "❌ {provider} ({name}) — not configured",
        "zh": "❌ {provider} ({name}) — 未配置",
    },
    "config_configured": {
        "en": "✅ {provider:<20} ({name})",
        "zh": "✅ {provider:<20} ({name})",
    },
    "config_unknown_provider": {
        "en": "Unknown provider: {name}",
        "zh": "未知提供商：{name}",
    },
    "config_missing_field": {
        "en": "  --{field}  ({prompt})",
        "zh": "  --{field}  ({prompt})",
    },
    "config_title": {
        "en": "Configured providers:",
        "zh": "已配置的域名商：",
    },

    # list
    "list_title": {
        "en": "\n── {provider} ──",
        "zh": "\n── {provider} ──",
    },

    # dns
    "dns_title": {
        "en": "\n── {provider} — {domain} ──",
        "zh": "\n── {provider} — {domain} ──",
    },
    "dns_update_usage": {
        "en": "Usage: domain-manager dns update <domain> --type A --name @ --value <IP>",
        "zh": "用法：domain-manager dns update <domain> --type A --name @ --value <IP>",
    },

    # ddns
    "ddns_no_ip": {
        "en": "Error [{provider}]: Could not detect public IP",
        "zh": "错误 [{provider}]：无法检测公网 IP",
    },
    "ddns_already": {
        "en": "✓ {type} {name}.{domain} already {ip}",
        "zh": "✓ {type} {name}.{domain} 已经是 {ip}",
    },

    # record update
    "record_updated": {
        "en": "✅ {type} {name}.{domain} → {value}",
        "zh": "✅ {type} {name}.{domain} → {value}",
    },
    "record_created": {
        "en": "✅ {type} {name}.{domain} → {value} (created)",
        "zh": "✅ {type} {name}.{domain} → {value}（已创建）",
    },
    "record_not_found": {
        "en": "Error [{provider}]: Record not found",
        "zh": "错误 [{provider}]：未找到记录",
    },
    "record_not_found_zone": {
        "en": "Error [{provider}]: Zone not found",
        "zh": "错误 [{provider}]：未找到域名区域",
    },
    "record_not_found_domain": {
        "en": "Error [{provider}]: Domain '{domain}' not found",
        "zh": "错误 [{provider}]：域名 '{domain}' 未找到",
    },

    # generic errors
    "error_prefix": {
        "en": "Error [{provider}]:",
        "zh": "错误 [{provider}]：",
    },
    "http_error": {
        "en": "HTTP {code}: {body}",
        "zh": "HTTP {code}：{body}",
    },
    "connection_failed": {
        "en": "Connection failed: {reason}",
        "zh": "连接失败：{reason}",
    },

    # ip command
    "ip_could_not_detect": {
        "en": "Could not detect public IPv{version} address",
        "zh": "无法检测到公网 IPv{version} 地址",
    },

    # provider descriptions
    "provider_godaddy": {"en": "GoDaddy (API Key + Secret)", "zh": "GoDaddy（API 密钥 + 密钥）"},
    "provider_namecheap": {"en": "Namecheap (Username + API Key + Client IP)", "zh": "Namecheap（用户名 + API 密钥 + 客户端 IP）"},
    "provider_domaincom": {"en": "Domain.com (User ID + API Key)", "zh": "Domain.com（用户 ID + API 密钥）"},
    "provider_cloudflare": {"en": "Cloudflare (API Token)", "zh": "Cloudflare（API 令牌）"},
    "provider_porkbun": {"en": "Porkbun (API Key + Secret)", "zh": "Porkbun（API 密钥 + 密钥）"},
    "provider_gandi": {"en": "Gandi (Personal Access Token)", "zh": "Gandi（个人访问令牌）"},
    "provider_digitalocean": {"en": "DigitalOcean (Personal Access Token)", "zh": "DigitalOcean（个人访问令牌）"},
    "provider_vultr": {"en": "Vultr (Personal Access Token)", "zh": "Vultr（个人访问令牌）"},
    "provider_hetzner": {"en": "Hetzner DNS (API Token)", "zh": "Hetzner DNS（API 令牌）"},
    "provider_ovh": {"en": "OVH (App Key + App Secret + Consumer Key)", "zh": "OVH（应用密钥 + 应用密文 + 用户令牌）"},
    "provider_dnsimple": {"en": "DNSimple (API Token)", "zh": "DNSimple（API 令牌）"},
    "provider_namesilo": {"en": "NameSilo (API Key)", "zh": "NameSilo（API 密钥）"},
    "provider_bunny": {"en": "Bunny.net (API Key)", "zh": "Bunny.net（API 密钥）"},
    "provider_duckdns": {"en": "DuckDNS (Token) — free DDNS only", "zh": "DuckDNS（令牌）— 仅免费 DDNS"},
    "provider_noip": {"en": "No-IP (Username + Password) — DDNS only", "zh": "No-IP（用户名 + 密码）— 仅 DDNS"},
    "provider_dynu": {"en": "Dynu (API Token)", "zh": "Dynu（API 令牌）"},
    "provider_aliyun": {"en": "阿里云 DNS (AccessKey ID + AccessKey Secret)", "zh": "阿里云 DNS（AccessKey ID + AccessKey Secret）"},
    "provider_tencentcloud": {"en": "腾讯云 DNS (SecretId + SecretKey)", "zh": "腾讯云 DNS（SecretId + SecretKey）"},

    # duckdns specific
    "duckdns_subdomain": {
        "en": "Subdomain: {sub}",
        "zh": "子域名：{sub}",
    },
    "duckdns_hint": {
        "en": "Use: domain-manager ddns {domain} --provider duckdns --type A --name @",
        "zh": "用法：domain-manager ddns {domain} --provider duckdns --type A --name @",
    },

    # noip specific
    "noip_dashboard": {
        "en": "{label}: Use dashboard to manage hosts.",
        "zh": "{label}：请使用控制面板管理主机。",
    },
    "noip_ddns_only": {
        "en": "{label}: DDNS-only — records managed via dashboard.",
        "zh": "{label}：仅 DDNS — 记录通过控制面板管理。",
    },

    # namecheap zone update
    "namecheap_zone_required": {
        "en": "{label} requires full zone re-submission via setHosts.\nUse the Namecheap dashboard or API directly for now.",
        "zh": "{label} 需要通过 setHosts 提交完整 DNS 区域。\n暂时请使用 Namecheap 控制面板或直接调用 API。",
    },
}


def _(key, **kwargs):
    """Translate a string key with formatting."""
    entry = _STRINGS.get(key)
    if not entry:
        return f"??{key}??"
    text = entry.get(_current_lang, entry.get("en", str(entry)))
    if kwargs:
        try:
            return text.format(**kwargs)
        except KeyError:
            return text
    return text
