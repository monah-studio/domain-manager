"""GoDaddy — API Key + Secret"""

from . import BaseProvider
from ..core import get_public_ip, http_request, print_table

API_BASE = "https://api.godaddy.com"


class Provider(BaseProvider):
    name = "godaddy"
    label = "GoDaddy"
    config_fields = [
        ("key", "API Key", True),
        ("secret", "API Secret", True),
    ]

    def _headers(self):
        return {
            "Authorization": f"sso-key {self.creds()['key']}:{self.creds()['secret']}",
        }

    def list_domains(self, json_mode=False):
        data = http_request("GET", f"{API_BASE}/v1/domains", headers=self._headers())
        if isinstance(data, dict) and "error" in data:
            print(f"Error [{self.label}]: {data['error']}")
            return
        print_table(
            [(d.get("domain",""), d.get("status",""), d.get("expires",""),
              str(d.get("renewAuto",False))) for d in data],
            ["Domain", "Status", "Expires", "AutoRenew"], json_mode
        )

    def list_records(self, domain, json_mode=False):
        data = http_request("GET", f"{API_BASE}/v1/domains/{domain}/records",
                           headers=self._headers())
        if isinstance(data, dict) and "error" in data:
            print(f"Error [{self.label}]: {data['error']}")
            return
        print_table(
            [(r.get("type",""), r.get("name",""), r.get("data",""),
              str(r.get("ttl",3600))) for r in data],
            ["Type", "Name", "Value", "TTL"], json_mode
        )

    def update_record(self, domain, record_type, name, value, ttl=600):
        data = [{"type": record_type, "name": name, "data": value, "ttl": ttl}]
        result = http_request("PUT",
            f"{API_BASE}/v1/domains/{domain}/records/{record_type}/{name}",
            headers=self._headers(), data=data)
        if isinstance(result, dict) and "error" in result:
            print(f"Error [{self.label}]: {result['error']}")
            return False
        print(f"✅ {record_type} {name}.{domain} → {value}")
        return True

    def ddns(self, domain, record_type, name, ttl=600, quiet=False):
        ip = get_public_ip(4 if record_type == "A" else 6)
        if not ip:
            print(f"Error [{self.label}]: Could not detect public IP")
            return False
        records = http_request("GET",
            f"{API_BASE}/v1/domains/{domain}/records/{record_type}/{name}",
            headers=self._headers())
        current = records[0].get("data") if isinstance(records, list) and records else None
        if current == ip:
            if not quiet:
                print(f"✓ {record_type} {name}.{domain} already {ip}")
            return False
        return self.update_record(domain, record_type, name, ip, ttl)
