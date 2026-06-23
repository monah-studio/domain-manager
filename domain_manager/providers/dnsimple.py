"""DNSimple — API Token"""

from ..core import get_public_ip, http_request, print_table
from . import BaseProvider

API = "https://api.dnsimple.com/v2"


class Provider(BaseProvider):
    name = "dnsimple"
    label = "DNSimple"
    config_fields = [("token", "API Token", True)]

    def _h(self):
        return {"Authorization": f"Bearer {self.creds()['token']}"}

    def _account(self):
        data = http_request("GET", f"{API}/whoami", headers=self._h())
        if isinstance(data, dict) and data.get("data"):
            a = data["data"].get("account", {})
            return a.get("id")
        return None

    def list_domains(self, json_mode=False):
        aid = self._account()
        if not aid:
            return
        data = http_request("GET", f"{API}/{aid}/domains", headers=self._h())
        if isinstance(data, dict) and data.get("data"):
            print_table([(d["name"], str(d.get("expires_on",""))) for d in data["data"]],
                       ["Domain", "Expires"], json_mode)

    def list_records(self, domain, json_mode=False):
        aid = self._account()
        if not aid:
            return
        data = http_request("GET", f"{API}/{aid}/zones/{domain}/records", headers=self._h())
        if isinstance(data, dict) and data.get("data"):
            rows = [(r["type"], r["name"], r["content"], str(r.get("ttl",0)))
                   for r in data["data"]]
            print_table(rows, ["Type", "Name", "Value", "TTL"], json_mode)

    def update_record(self, domain, record_type, name, value, ttl=600):
        aid = self._account()
        if not aid:
            return False
        data = http_request("GET", f"{API}/{aid}/zones/{domain}/records", headers=self._h())
        if isinstance(data, dict) and data.get("data"):
            for r in data["data"]:
                if r["type"] == record_type and r["name"] == name:
                    result = http_request("PATCH",
                        f"{API}/{aid}/zones/{domain}/records/{r['id']}",
                        headers=self._h(), data={"content": value, "ttl": ttl})
                    print(f"✅ {record_type} {name}.{domain} → {value}")
                    return True
        result = http_request("POST", f"{API}/{aid}/zones/{domain}/records",
            headers=self._h(), data={"type": record_type, "name": name, "content": value, "ttl": ttl})
        print(f"✅ {record_type} {name}.{domain} → {value}")
        return True

    def ddns(self, domain, record_type, name, ttl=600, quiet=False):
        ip = get_public_ip(4 if record_type == "A" else 6)
        if not ip:
            return False
        aid = self._account()
        if not aid:
            return False
        data = http_request("GET", f"{API}/{aid}/zones/{domain}/records", headers=self._h())
        if isinstance(data, dict) and data.get("data"):
            for r in data["data"]:
                if r["type"] == record_type and r["name"] == name:
                    if r["content"].strip() == ip.strip():
                        if not quiet:
                            print(f"✓ {record_type} {name}.{domain} already {ip}")
                        return False
                    return self.update_record(domain, record_type, name, ip, ttl)
        return self.update_record(domain, record_type, name, ip, ttl)
