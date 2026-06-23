"""Dynu — free DDNS / DNS management. API Key."""

from ..core import get_public_ip, http_request, print_table
from . import BaseProvider

API = "https://api.dynu.com/v2"


class Provider(BaseProvider):
    name = "dynu"
    label = "Dynu"
    config_fields = [("token", "API Token", True)]

    def _h(self):
        return {"API-Key": self.creds()["token"], "accept": "application/json"}

    def list_domains(self, json_mode=False):
        data = http_request("GET", f"{API}/dns", headers=self._h())
        if isinstance(data, dict) and data.get("domains"):
            print_table([(d["name"], d.get("state","")) for d in data["domains"]],
                       ["Domain", "State"], json_mode)

    def list_records(self, domain, json_mode=False):
        data = http_request("GET", f"{API}/dns/{domain}/record", headers=self._h())
        if isinstance(data, dict) and data.get("records"):
            rows = [(r["recordType"], r["name"], r.get("textData","") or r.get("ipv4Address",""),
                    str(r.get("ttl",0))) for r in data["records"]]
            print_table(rows, ["Type", "Name", "Value", "TTL"], json_mode)

    def update_record(self, domain, record_type, name, value, ttl=600):
        data = http_request("GET", f"{API}/dns/{domain}/record", headers=self._h())
        if isinstance(data, dict) and data.get("records"):
            for r in data["records"]:
                if r["recordType"] == record_type and r["name"] == name:
                    payload = {"recordType": record_type, "name": name, "ttl": ttl}
                    if record_type in ("A", "AAAA"):
                        payload["ipv4Address" if record_type == "A" else "ipv6Address"] = value
                    else:
                        payload["textData"] = value
                    result = http_request("PUT", f"{API}/dns/{domain}/record/{r['id']}",
                        headers=self._h(), data=payload)
                    print(f"✅ {record_type} {name}.{domain} → {value}")
                    return True
        print(f"Error [{self.label}]: Record not found")
        return False

    def ddns(self, domain, record_type, name, ttl=600, quiet=False):
        ip = get_public_ip(4 if record_type == "A" else 6)
        if not ip:
            return False
        data = http_request("GET", f"{API}/dns/{domain}/record", headers=self._h())
        if isinstance(data, dict) and data.get("records"):
            for r in data["records"]:
                cur = r.get("ipv4Address","") or r.get("ipv6Address","") or ""
                if r["recordType"] == record_type and r["name"] == name:
                    if cur.strip() == ip.strip():
                        if not quiet:
                            print(f"✓ {record_type} {name}.{domain} already {ip}")
                        return False
                    return self.update_record(domain, record_type, name, ip, ttl)
        return self.update_record(domain, record_type, name, ip, ttl)
