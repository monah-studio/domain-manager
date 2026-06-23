"""OVH — App Key + App Secret + Consumer Key"""

from ..core import get_public_ip, http_request, print_table, save_creds, load_creds
from . import BaseProvider
import time
import hashlib

API = "https://eu.api.ovh.com/1.0"


class Provider(BaseProvider):
    name = "ovh"
    label = "OVH"
    config_fields = [
        ("app_key", "Application Key", False),
        ("app_secret", "Application Secret", True),
        ("consumer_key", "Consumer Key", True),
    ]

    def _h(self):
        c = self.creds()
        ts = str(int(time.time()))
        body = ""
        to_sign = f"{c['app_secret']}+{c['consumer_key']}+GET+{API}/domain?ts={ts}"
        sig = hashlib.sha1(to_sign.encode()).hexdigest()
        return {
            "X-Ovh-Application": c["app_key"],
            "X-Ovh-Consumer": c["consumer_key"],
            "X-Ovh-Timestamp": ts,
            "X-Ovh-Signature": f"$1${sig}",
        }

    def list_domains(self, json_mode=False):
        data = http_request("GET", f"{API}/domain", headers=self._h())
        if isinstance(data, list):
            print_table([(d,) for d in data], ["Domain"], json_mode)

    def list_records(self, domain, json_mode=False):
        data = http_request("GET", f"{API}/domain/zone/{domain}/record", headers=self._h())
        if isinstance(data, list):
            rows = []
            for rid in data[:50]:
                r = http_request("GET", f"{API}/domain/zone/{domain}/record/{rid}", headers=self._h())
                if isinstance(r, dict):
                    rows.append((r.get("fieldType",""), r.get("subDomain",""), r.get("target",""), str(r.get("ttl",0))))
            print_table(rows, ["Type", "Name", "Value", "TTL"], json_mode)

    def update_record(self, domain, record_type, name, value, ttl=600):
        data = http_request("GET", f"{API}/domain/zone/{domain}/record", headers=self._h())
        if isinstance(data, list):
            for rid in data:
                r = http_request("GET", f"{API}/domain/zone/{domain}/record/{rid}", headers=self._h())
                if isinstance(r, dict) and r.get("fieldType") == record_type and r.get("subDomain","") == name:
                    http_request("PUT", f"{API}/domain/zone/{domain}/record/{rid}",
                        headers=self._h(), data={"target": value, "ttl": ttl})
                    http_request("POST", f"{API}/domain/zone/{domain}/refresh", headers=self._h())
                    print(f"✅ {record_type} {name}.{domain} → {value}")
                    return True
        print(f"Error [{self.label}]: Record not found")
        return False

    def ddns(self, domain, record_type, name, ttl=600, quiet=False):
        ip = get_public_ip(4 if record_type == "A" else 6)
        if not ip:
            return False
        data = http_request("GET", f"{API}/domain/zone/{domain}/record", headers=self._h())
        if isinstance(data, list):
            for rid in data:
                r = http_request("GET", f"{API}/domain/zone/{domain}/record/{rid}", headers=self._h())
                if isinstance(r, dict) and r.get("fieldType") == record_type and r.get("subDomain","") == name:
                    if r["target"].strip() == ip.strip():
                        if not quiet:
                            print(f"✓ {record_type} {name}.{domain} already {ip}")
                        return False
                    return self.update_record(domain, record_type, name, ip, ttl)
        return self.update_record(domain, record_type, name, ip, ttl)
