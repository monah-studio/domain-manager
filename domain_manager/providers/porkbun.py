"""Porkbun — cheap domain registrar with great API. API Key + Secret."""

from ..core import get_public_ip, http_request, print_table
from . import BaseProvider

API = "https://api.porkbun.com/api/json/v3"


class Provider(BaseProvider):
    name = "porkbun"
    label = "Porkbun"
    config_fields = [
        ("key", "API Key", True),
        ("secret", "Secret API Key", True),
    ]

    def _post(self, path, data=None):
        payload = {"apikey": self.creds()["key"], "secretapikey": self.creds()["secret"]}
        if data:
            payload.update(data)
        return http_request("POST", f"{API}{path}", data=payload)

    def list_domains(self, json_mode=False):
        data = self._post("/domain/listAll")
        if isinstance(data, dict) and data.get("status") == "SUCCESS":
            domains = [(d["domain"], d.get("status",""), d.get("expiry","")) for d in data.get("domains", [])]
            print_table(domains, ["Domain", "Status", "Expires"], json_mode)
        else:
            print(f"Error [{self.label}]: {data.get('message', str(data))}")

    def list_records(self, domain, json_mode=False):
        data = self._post(f"/dns/retrieve/{domain}")
        if isinstance(data, dict) and data.get("status") == "SUCCESS":
            records = [(r["type"], r["name"], r["content"], r.get("ttl",""))
                      for r in data.get("records", [])]
            print_table(records, ["Type", "Name", "Value", "TTL"], json_mode)
        else:
            print(f"Error [{self.label}]: {data.get('message', str(data))}")

    def update_record(self, domain, record_type, name, value, ttl=600):
        data = self._post(f"/dns/editByNameType/{domain}/{record_type}/{name}",
                         data={"content": [value], "ttl": ttl})
        if isinstance(data, dict) and data.get("status") == "SUCCESS":
            print(f"✅ {record_type} {name}.{domain} → {value}")
            return True
        print(f"Error [{self.label}]: {data.get('message', str(data))}")
        return False

    def ddns(self, domain, record_type, name, ttl=600, quiet=False):
        ip = get_public_ip(4 if record_type == "A" else 6)
        if not ip:
            print(f"Error [{self.label}]: Could not detect public IP")
            return False
        records_data = self._post(f"/dns/retrieve/{domain}")
        if isinstance(records_data, dict) and records_data.get("status") == "SUCCESS":
            for r in records_data.get("records", []):
                if r["type"] == record_type and r["name"] == name:
                    if r["content"].strip() == ip.strip():
                        if not quiet:
                            print(f"✓ {record_type} {name}.{domain} already {ip}")
                        return False
        return self.update_record(domain, record_type, name, ip, ttl)
