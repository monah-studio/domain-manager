"""NameSilo — API Key"""

from ..core import get_public_ip, http_request, print_table
from . import BaseProvider
import xml.etree.ElementTree as ET

API = "https://www.namesilo.com/api"


class Provider(BaseProvider):
    name = "namesilo"
    label = "NameSilo"
    config_fields = [("key", "API Key", True)]

    def _get(self, cmd, params=None):
        p = {"version": "1", "type": "xml", "key": self.creds()["key"]}
        if params:
            p.update(params)
        qs = "&".join(f"{k}={v}" for k, v in p.items())
        return http_request("GET", f"{API}/{cmd}?{qs}")

    def list_domains(self, json_mode=False):
        xml = self._get("listDomains")
        if isinstance(xml, str):
            root = ET.fromstring(xml)
            if root.find(".//reply/code") is not None and root.find(".//reply/code").text == "300":
                domains = []
                for d in root.findall(".//domains/domain"):
                    domains.append((d.find("domain").text, d.find("created").text, d.find("expires").text))
                print_table(domains, ["Domain", "Created", "Expires"], json_mode)

    def list_records(self, domain, json_mode=False):
        xml = self._get("dnsListRecords", {"domain": domain})
        if isinstance(xml, str):
            root = ET.fromstring(xml)
            if root.find(".//reply/code") is not None and root.find(".//reply/code").text == "300":
                records = []
                for r in root.findall(".//resource_record"):
                    records.append((
                        r.find("type").text, r.find("host").text,
                        r.find("value").text, r.find("record_id").text,
                    ))
                print_table(records, ["Type", "Host", "Value", "Record ID"], json_mode)

    def update_record(self, domain, record_type, name, value, ttl=600):
        xml = self._get("dnsUpdateRecord", {
            "domain": domain, "rrid": name,
            "rrhost": name, "rrvalue": value, "rrttl": ttl
        })
        if isinstance(xml, str):
            detail = xml[:200] if "300" in xml else xml[:200]
            print(f"✅ {record_type} {name}.{domain} → {value}")
            return True
        return False

    def ddns(self, domain, record_type, name, ttl=600, quiet=False):
        ip = get_public_ip(4 if record_type == "A" else 6)
        if not ip:
            return False
        xml = self._get("dnsListRecords", {"domain": domain})
        if isinstance(xml, str):
            root = ET.fromstring(xml)
            for r in root.findall(".//resource_record"):
                if r.find("type").text == record_type and r.find("host").text.split(".")[0] == name:
                    if r.find("value").text.strip() == ip.strip():
                        if not quiet:
                            print(f"✓ {record_type} {name}.{domain} already {ip}")
                        return False
                    return self.update_record(domain, record_type, r.find("record_id").text, ip, ttl)
        return self.update_record(domain, record_type, name, ip, ttl)
