"""Domain.com — User ID + API Key"""

from . import BaseProvider
from ..core import get_public_ip, http_request, print_table

API_BASE = "https://api.domain.com/v1"


class Provider(BaseProvider):
    name = "domaincom"
    label = "Domain.com"
    config_fields = [
        ("id", "User ID", False),
        ("key", "API Key", True),
    ]

    def _headers(self):
        c = self.creds()
        return {"X-Auth-User": c["id"], "X-Auth-Key": c["key"]}

    def list_domains(self, json_mode=False):
        data = http_request("GET", f"{API_BASE}/domains", headers=self._headers())
        if isinstance(data, dict) and "error" in data:
            print(f"Error [{self.label}]: {data['error']}")
            return
        domains = data if isinstance(data, list) else data.get("domains", [])
        print_table(
            [(d.get("domain",""), d.get("expires","")) for d in domains],
            ["Domain", "Expires"], json_mode
        )

    def list_records(self, domain, json_mode=False):
        data = http_request("GET", f"{API_BASE}/domains/{domain}/records",
                           headers=self._headers())
        if isinstance(data, dict) and "error" in data:
            print(f"Error [{self.label}]: {data['error']}")
            return
        records = data if isinstance(data, list) else data.get("records", [])
        print_table(
            [(r.get("type",""), r.get("name",""), r.get("value","")) for r in records],
            ["Type", "Name", "Value"], json_mode
        )

    def update_record(self, domain, record_type, name, value, ttl=600):
        result = http_request("PATCH", f"{API_BASE}/domains/{domain}/records",
            headers=self._headers(),
            data=[{"name": name, "type": record_type, "value": value}])
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
        records = self.list_records(domain, json_mode=True)
        return self.update_record(domain, record_type, name, ip, ttl)
