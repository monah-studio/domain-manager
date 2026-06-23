"""Namecheap — Username + API Key + Client IP (XML API)"""

import hashlib
import xml.etree.ElementTree as ET
import urllib.parse

from . import BaseProvider
from ..core import get_public_ip, http_request, print_table

API_BASE = "https://api.namecheap.com/xml.response"
NS = {"nc": "http://api.namecheap.com/xml.response"}


class Provider(BaseProvider):
    name = "namecheap"
    label = "Namecheap"
    config_fields = [
        ("user", "Username", False),
        ("key", "API Key", True),
        ("ip", "Whitelisted Client IP", False),
    ]

    def _call(self, command, payload=None):
        c = self.creds()
        params = {
            "ApiUser": c["user"], "ApiKey": c["key"],
            "UserName": c["user"], "ClientIp": c["ip"],
            "Command": command,
        }
        if payload:
            params.update(payload)
        url = f"{API_BASE}?{urllib.parse.urlencode(params)}"
        result = http_request("GET", url)
        if isinstance(result, dict) and "error" in result:
            return result
        return result  # raw XML string

    def list_domains(self, json_mode=False):
        xml = self._call("namecheap.domains.getList")
        if isinstance(xml, dict) and "error" in xml:
            print(f"Error [{self.label}]: {xml['error']}")
            return
        try:
            root = ET.fromstring(xml)
            domains = []
            for d in root.findall(".//nc:Domain", NS):
                domains.append((d.get("Name",""), d.get("Status",""),
                               d.get("Expires",""), str(d.get("AutoRenew",""))))
            print_table(domains, ["Domain", "Status", "Expires", "AutoRenew"], json_mode)
        except ET.ParseError as e:
            print(f"Error [{self.label}]: XML parse error: {e}")

    def list_records(self, domain, json_mode=False):
        sld, tld = domain.split(".")[0], ".".join(domain.split(".")[1:])
        xml = self._call("namecheap.domains.dns.getHosts", {"SLD": sld, "TLD": tld})
        if isinstance(xml, dict) and "error" in xml:
            print(f"Error [{self.label}]: {xml['error']}")
            return
        try:
            root = ET.fromstring(xml)
            records = [(h.get("Type",""), h.get("Name",""), h.get("Address",""),
                       h.get("TTL","1800")) for h in root.findall(".//nc:host", NS)]
            print_table(records, ["Type", "Name", "Value", "TTL"], json_mode)
        except ET.ParseError as e:
            print(f"Error [{self.label}]: XML parse error: {e}")

    def update_record(self, domain, record_type, name, value, ttl=600):
        print(self._("namecheap_zone_required", label=self.label))
        return False

    def ddns(self, domain, record_type, name, ttl=600, quiet=False):
        ip = get_public_ip(4 if record_type == "A" else 6)
        if not ip:
            print(f"Error [{self.label}]: Could not detect public IP")
            return False
        sld, tld = domain.split(".")[0], ".".join(domain.split(".")[1:])
        xml = self._call("namecheap.domains.dns.getHosts", {"SLD": sld, "TLD": tld})
        if isinstance(xml, dict) and "error" in xml:
            print(f"Error [{self.label}]: {xml['error']}")
            return False
        try:
            root = ET.fromstring(xml)
            current_ip = None
            for h in root.findall(".//nc:host", NS):
                if h.get("Name") == name and h.get("Type") == record_type:
                    current_ip = h.get("Address")
                    break
            if current_ip == ip:
                if not quiet:
                    print(f"✓ {record_type} {name}.{domain} already {ip}")
                return False
            print(f"{self.label} DDNS: {record_type} {name}.{domain} → {ip}")
            print("Full zone update not yet implemented — use dashboard for now.")
            return False
        except ET.ParseError:
            return False
