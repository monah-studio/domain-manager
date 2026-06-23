"""Hetzner — API Token"""

from ..core import get_public_ip, http_request, print_table
from . import BaseProvider

API = "https://dns.hetzner.com/api/v1"


class Provider(BaseProvider):
    name = "hetzner"
    label = "Hetzner DNS"
    config_fields = [("token", "API Token", True)]

    def _h(self):
        return {"Auth-API-Token": self.creds()["token"]}

    def _zone_id(self, domain):
        data = http_request("GET", f"{API}/zones?search_name={domain}", headers=self._h())
        if isinstance(data, dict) and data.get("zones"):
            for z in data["zones"]:
                if z["name"] == domain:
                    return z["id"]
        return None

    def list_domains(self, json_mode=False):
        data = http_request("GET", f"{API}/zones", headers=self._h())
        if isinstance(data, dict) and data.get("zones"):
            print_table([(z["name"], z["id"][:8]+"...") for z in data["zones"]],
                       ["Domain", "Zone ID"], json_mode)

    def list_records(self, domain, json_mode=False):
        zid = self._zone_id(domain)
        if not zid:
            print(f"Error [{self.label}]: Zone not found")
            return
        data = http_request("GET", f"{API}/records?zone_id={zid}", headers=self._h())
        if isinstance(data, dict) and data.get("records"):
            rows = [(r["type"], r["name"], r["value"], str(r.get("ttl",0)))
                   for r in data["records"]]
            print_table(rows, ["Type", "Name", "Value", "TTL"], json_mode)

    def update_record(self, domain, record_type, name, value, ttl=600):
        zid = self._zone_id(domain)
        if not zid:
            print(f"Error [{self.label}]: Zone not found")
            return False
        data = http_request("GET", f"{API}/records?zone_id={zid}", headers=self._h())
        if isinstance(data, dict) and data.get("records"):
            for r in data["records"]:
                if r["type"] == record_type and r["name"] == name:
                    result = http_request("PUT", f"{API}/records/{r['id']}",
                        headers=self._h(),
                        data={"zone_id": zid, "type": record_type, "name": name, "value": value, "ttl": ttl})
                    print(f"✅ {record_type} {name}.{domain} → {value}")
                    return True
        result = http_request("POST", f"{API}/records", headers=self._h(),
            data={"zone_id": zid, "type": record_type, "name": name, "value": value, "ttl": ttl})
        print(f"✅ {record_type} {name}.{domain} → {value} (created)")
        return True

    def ddns(self, domain, record_type, name, ttl=600, quiet=False):
        ip = get_public_ip(4 if record_type == "A" else 6)
        if not ip:
            print(f"Error [{self.label}]: Could not detect public IP")
            return False
        zid = self._zone_id(domain)
        if not zid:
            return self.update_record(domain, record_type, name, ip, ttl)
        data = http_request("GET", f"{API}/records?zone_id={zid}", headers=self._h())
        if isinstance(data, dict) and data.get("records"):
            for r in data["records"]:
                if r["type"] == record_type and r["name"] == name:
                    if r["value"].strip() == ip.strip():
                        if not quiet:
                            print(f"✓ {record_type} {name}.{domain} already {ip}")
                        return False
                    return self.update_record(domain, record_type, name, ip, ttl)
        return self.update_record(domain, record_type, name, ip, ttl)
