"""Gandi — API Key (Personal Access Token)"""

from ..core import get_public_ip, http_request, print_table
from . import BaseProvider

API = "https://api.gandi.net/v5"


class Provider(BaseProvider):
    name = "gandi"
    label = "Gandi"
    config_fields = [("token", "Personal Access Token", True)]

    def _h(self):
        return {"Authorization": f"Bearer {self.creds()['token']}"}

    def list_domains(self, json_mode=False):
        data = http_request("GET", f"{API}/domain/domains", headers=self._h())
        if isinstance(data, list):
            print_table([(d["fqdn"], d.get("state",""), d.get("dates",{}).get("registry_ends_at",""))
                       for d in data], ["Domain", "Status", "Expires"], json_mode)

    def list_records(self, domain, json_mode=False):
        data = http_request("GET", f"{API}/domain/domains/{domain}/records",
                           headers=self._h())
        if isinstance(data, list):
            rows = [(r["rrset_type"], r["rrset_name"], ", ".join(r["rrset_values"]),
                    str(r.get("rrset_ttl", 1800))) for r in data]
            print_table(rows, ["Type", "Name", "Value", "TTL"], json_mode)

    def update_record(self, domain, record_type, name, value, ttl=600):
        result = http_request("PUT",
            f"{API}/domain/domains/{domain}/records/{name}/{record_type}",
            headers=self._h(), data={"rrset_values": [value], "rrset_ttl": ttl})
        if isinstance(result, dict) and result.get("message"):
            print(f"✅ {record_type} {name}.{domain} → {value}")
            return True
        print(f"Error [{self.label}]: {result}")
        return False

    def ddns(self, domain, record_type, name, ttl=600, quiet=False):
        ip = get_public_ip(4 if record_type == "A" else 6)
        if not ip:
            print(f"Error [{self.label}]: Could not detect public IP")
            return False
        data = http_request("GET", f"{API}/domain/domains/{domain}/records/{name}/{record_type}",
                           headers=self._h())
        if isinstance(data, dict):
            current = ", ".join(data.get("rrset_values", []))
            if current == ip:
                if not quiet:
                    print(f"✓ {record_type} {name}.{domain} already {ip}")
                return False
        return self.update_record(domain, record_type, name, ip, ttl)
