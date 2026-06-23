"""DigitalOcean — Personal Access Token"""

from ..core import get_public_ip, http_request, print_table
from . import BaseProvider

API = "https://api.digitalocean.com/v2"


class Provider(BaseProvider):
    name = "digitalocean"
    label = "DigitalOcean"
    config_fields = [("token", "Personal Access Token", True)]

    def _h(self):
        return {"Authorization": f"Bearer {self.creds()['token']}"}

    def list_domains(self, json_mode=False):
        data = http_request("GET", f"{API}/domains", headers=self._h())
        if isinstance(data, dict) and data.get("domains"):
            print_table([(d["name"], d.get("ttl",0)) for d in data["domains"]],
                       ["Domain", "TTL"], json_mode)

    def list_records(self, domain, json_mode=False):
        data = http_request("GET", f"{API}/domains/{domain}/records", headers=self._h())
        if isinstance(data, dict) and data.get("domain_records"):
            rows = [(r["type"], r["name"], r["data"], str(r.get("ttl",0)))
                   for r in data["domain_records"]]
            print_table(rows, ["Type", "Name", "Value", "TTL"], json_mode)

    def update_record(self, domain, record_type, name, value, ttl=600):
        data = http_request("GET", f"{API}/domains/{domain}/records", headers=self._h())
        if isinstance(data, dict) and data.get("domain_records"):
            for r in data["domain_records"]:
                if r["type"] == record_type and r["name"] == name:
                    rid = r["id"]
                    result = http_request("PUT", f"{API}/domains/{domain}/records/{rid}",
                        headers=self._h(), data={"type": record_type, "name": name, "data": value, "ttl": ttl})
                    print(f"✅ {record_type} {name}.{domain} → {value}")
                    return True
        result = http_request("POST", f"{API}/domains/{domain}/records",
            headers=self._h(), data={"type": record_type, "name": name, "data": value, "ttl": ttl})
        print(f"✅ {record_type} {name}.{domain} → {value} (created)")
        return True

    def ddns(self, domain, record_type, name, ttl=600, quiet=False):
        ip = get_public_ip(4 if record_type == "A" else 6)
        if not ip:
            print(f"Error [{self.label}]: Could not detect public IP")
            return False
        data = http_request("GET", f"{API}/domains/{domain}/records", headers=self._h())
        if isinstance(data, dict) and data.get("domain_records"):
            for r in data["domain_records"]:
                if r["type"] == record_type and r["name"] == name:
                    if r["data"].strip() == ip.strip():
                        if not quiet:
                            print(f"✓ {record_type} {name}.{domain} already {ip}")
                        return False
                    return self.update_record(domain, record_type, name, ip, ttl)
        return self.update_record(domain, record_type, name, ip, ttl)
