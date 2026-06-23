"""Vultr — Personal Access Token"""

from ..core import get_public_ip, http_request, print_table
from . import BaseProvider

API = "https://api.vultr.com/v2"


class Provider(BaseProvider):
    name = "vultr"
    label = "Vultr"
    config_fields = [("token", "Personal Access Token", True)]

    def _h(self):
        return {"Authorization": f"Bearer {self.creds()['token']}"}

    def list_domains(self, json_mode=False):
        data = http_request("GET", f"{API}/domains", headers=self._h())
        if isinstance(data, dict) and data.get("domains"):
            print_table([(d["domain"], d.get("status","")) for d in data["domains"]],
                       ["Domain", "Status"], json_mode)

    def list_records(self, domain, json_mode=False):
        data = http_request("GET", f"{API}/domains/{domain}/records", headers=self._h())
        if isinstance(data, dict) and data.get("records"):
            rows = [(r["type"], r["name"], r["data"], str(r.get("priority","")))
                   for r in data["records"]]
            print_table(rows, ["Type", "Name", "Value", "Priority"], json_mode)

    def update_record(self, domain, record_type, name, value, ttl=600):
        data = http_request("GET", f"{API}/domains/{domain}/records", headers=self._h())
        if isinstance(data, dict) and data.get("records"):
            for r in data["records"]:
                if r["type"] == record_type and r["name"] == name:
                    result = http_request("PATCH",
                        f"{API}/domains/{domain}/records/{r['id']}",
                        headers=self._h(), data={"data": value, "name": name, "type": record_type})
                    print(f"✅ {record_type} {name}.{domain} → {value}")
                    return True
        print(f"Error [{self.label}]: Record not found. Create via dashboard.")
        return False

    def ddns(self, domain, record_type, name, ttl=600, quiet=False):
        ip = get_public_ip(4 if record_type == "A" else 6)
        if not ip:
            print(f"Error [{self.label}]: Could not detect public IP")
            return False
        data = http_request("GET", f"{API}/domains/{domain}/records", headers=self._h())
        if isinstance(data, dict) and data.get("records"):
            for r in data["records"]:
                if r["type"] == record_type and r["name"] == name:
                    if r["data"].strip() == ip.strip():
                        if not quiet:
                            print(f"✓ {record_type} {name}.{domain} already {ip}")
                        return False
                    return self.update_record(domain, record_type, name, ip, ttl)
        return self.update_record(domain, record_type, name, ip, ttl)
