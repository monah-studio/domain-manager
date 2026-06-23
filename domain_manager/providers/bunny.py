"""Bunny.net — API Key"""

from ..core import get_public_ip, http_request, print_table
from . import BaseProvider

API = "https://api.bunny.net"


class Provider(BaseProvider):
    name = "bunny"
    label = "Bunny.net"
    config_fields = [("key", "API Key", True)]

    def _h(self):
        return {"AccessKey": self.creds()["key"]}

    def list_domains(self, json_mode=False):
        data = http_request("GET", f"{API}/dnszone", headers=self._h())
        if isinstance(data, list):
            print_table([(d["Domain"], str(d.get("DateModified","")[:10])) for d in data],
                       ["Domain", "Modified"], json_mode)

    def list_records(self, domain, json_mode=False):
        zones = http_request("GET", f"{API}/dnszone", headers=self._h())
        zid = None
        if isinstance(zones, list):
            for z in zones:
                if z["Domain"] == domain:
                    zid = z["Id"]
                    break
        if not zid:
            print(f"Error [{self.label}]: Zone not found")
            return
        data = http_request("GET", f"{API}/dnszone/{zid}", headers=self._h())
        if isinstance(data, dict) and data.get("Records"):
            rows = [(r["Type"], r["Name"], r["Value"], str(r.get("Ttl",0)))
                   for r in data["Records"]]
            print_table(rows, ["Type", "Name", "Value", "TTL"], json_mode)

    def update_record(self, domain, record_type, name, value, ttl=600):
        zones = http_request("GET", f"{API}/dnszone", headers=self._h())
        zid = None
        if isinstance(zones, list):
            for z in zones:
                if z["Domain"] == domain:
                    zid = z["Id"]
                    break
        if not zid:
            return False
        data = http_request("GET", f"{API}/dnszone/{zid}", headers=self._h())
        if isinstance(data, dict) and data.get("Records"):
            for r in data["Records"]:
                if r["Name"] == name and r["Type"] == int(record_type):
                    result = http_request("DELETE",
                        f"{API}/dnszone/{zid}/records/{r['Id']}", headers=self._h())
                    break
        result = http_request("POST", f"{API}/dnszone/{zid}/records", headers=self._h(),
            data={"Type": int(record_type), "Name": name, "Value": value, "Ttl": ttl})
        print(f"✅ {record_type} {name}.{domain} → {value}")
        return True

    def ddns(self, domain, record_type, name, ttl=600, quiet=False):
        ip = get_public_ip(4 if record_type == "A" else 6)
        if not ip:
            return False
        return self.update_record(domain, record_type, name, ip, ttl)
